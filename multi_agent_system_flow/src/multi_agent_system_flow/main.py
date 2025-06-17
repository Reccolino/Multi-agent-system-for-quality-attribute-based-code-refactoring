import os
import time
import warnings
from typing import List, Optional
import pandas as pd

from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start, or_, router
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import APACHE_PATH, LPO_PATH
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY_REPOS, Validation
from multi_agent_system_flow.src.multi_agent_system_flow.crews.refactor_crew.refactor_crew import RefactorCrew
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import classes_for_project, \
    esec_class

ATTEMPTS_MAX: int = 3
attempts_tot: int = 0
time_for_project: List[float] = []

class ExampleFlow(BaseModel):
    directory: str = ""      #directory where execution takes place
    project_list: List[str] = []        #list of projects
    current_project: Optional[int] = 0         #indicates which project is being processed
    classes: List[dict] = []         #list of classes of a project
    current_class: Optional[int] = 0        #indicates which class of the project is being refactored
    path_class: str = ""       #path of the class to pass to the Crew for code replacement and to run SonarScanner
    code_class: str = ""       #code of the class to pass to the Crew for refactoring
    errors: Optional[str] = ""       #errors (compilation or others) to pass to the Crew to guide the agent to avoid committing them
    is_validate: Optional[bool] = True       #flag that checks if the terminal command for a class returned Build Success or Build Failure
    attempts: Optional[int] = 0       #counter to keep track of the number of attempts on a single class
    #value_metric_pre: Optional[int] = 0   #FOR RQ3
    #value_metric_post: Optional[int] = 0   #FOR RQ3
    project_start_times: List[float] = []    #list of start execution time for every project

class OriginalFlow(Flow[ExampleFlow]):

    @start()
    def init(self):
        """
        Method that loads all projects into the project_list. From here, you can access individual projects and their classes.
        """

        global time_for_project
        self.state.project_list = [repository for repository in os.listdir(self.state.directory)]
        print(self.state.project_list)
        time_for_project = [0.0 for _ in self.state.project_list]
        self.state.project_start_times = [0.0 for _ in self.state.project_list]



    @router(or_("init", "classes_for_project", "refactor_code"))
    def router(self, _=None):
        """
        The router checks the current state and returns the name of the next method to execute.
        """

        #If I haven't loaded the classes for a project yet
        if not self.state.classes:
            return "project_roadmap"


        #If I still have remaining classes for this project
        if self.state.current_class < len(self.state.classes):
            return "class_roadmap"


        #I have processed all the classes of this project:
        # move on to the next project (if it exists) or terminate
        time_for_project[self.state.current_project] = time.time() - self.state.project_start_times[
            self.state.current_project]
        self.state.current_project += 1
        if self.state.current_project < len(self.state.project_list):
            # resetto le classi per il nuovo progetto
            self.state.classes = []
            self.state.current_class = 0
            return "percorso_progetto"
        else:
            print("All projects have been processed")




    @listen("project_roadmap")
    def classes_for_project(self):
        """
        Returns: the path of the class with the worst security_rating via SonarQube and its code.
        Performs a GET request to /api/measures/component_tree and sorts by security_rating.
        """

        self.state.project_start_times[self.state.current_project] = time.time()   #faccio partire tempo per progetto

        response = classes_for_project(self.state.project_list[self.state.current_project])

        #DA SCOMMENTARE PER RQ3
        '''all_components = response.json().get("components", [])
        filtered = [c for c in all_components if c.get("measures")]   #ho solo le classi che hanno effettivamente una measure
        #questo perchè può essere che un progetto abbia 1 solo vulnerabilities e il json mi restituisce le prime 3 classi
        #ma cosi mi restituisce la classe dove è presente effettivamente il vulnerabilities e altre 2 classi che non hanno problemi
        #quindi per quelle due che senso ha fare refactoring ?
        print(f"FILTERED {filtered}")
        self.state.classes = filtered'''
        self.state.classes = response     #load the classes from JSON




    @listen("class_roadmap")
    def esec_class(self):
        """
        Performs a GET request to api/sources/raw to return the code and the path to be refactored of a specific class
        """

        if self.state.attempts < ATTEMPTS_MAX:

            #http://localhost:9000/api/sources/raw requires the project key as a query string parameter  ==> I retrieve it from the JSON
            actual_class = self.state.classes[self.state.current_class]
            print(f"Actual Class= {actual_class}")
            code = esec_class(actual_class)

            self.state.code_class = code.text

            #self.state.value_metric_pre = int(metrics(classe_attuale.get("key")))  #DA SCOMMENTARE PER LA RQ3

            project_root = f"{self.state.directory}{self.state.project_list[self.state.current_project]}"

            #FOR LPO PROJECTS THE PATH IS NOT IMMEDIATLY AS APACHE PROJECT
            for root, _, files in os.walk(project_root):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    #I use normpath because the JSON returns backslashes like this: \ . But I need the path with forward slashes like this: /
                    if full_file_path.endswith(os.path.normpath(self.state.classes[self.state.current_class].get("path"))):
                        self.state.path_class = full_file_path
                        print(f"LOCAL PATH: {self.state.path_class}" + f"\nCODE:\n{self.state.code_class}")



    @listen("esec_class")
    def refactor_code(self):
        global attempts_tot

        print(f"\nElaborando progetto: {self.state.project_list[self.state.current_project]}")
        print(f"\nClasse: {self.state.classes[self.state.current_class]}")

        if self.state.attempts < ATTEMPTS_MAX:

            #obviously, on the first iteration, self.state.scanner_result is empty;
            #then, if the first attempt results in Build Failure,
            #it contains the errors returned by SonarScanner.
            result = RefactorCrew().crew().kickoff(
                inputs={"code_class": self.state.code_class, "path_class": self.state.path_class,
                        "errors": self.state.errors})


            self.state.is_validate = result["valid"]
            self.state.errors = result["errors"].strip() or "errors"
            #if errors is an empty string "", then I set self.state.errors simply to "errors"
            #so that templating in task2 works in both cases.

            #self.state.value_metric_post = result["metric"]   #DA SCOMMENTARE PER LA RQ3

            print(f"VALIDATE: {self.state.is_validate}")
            #print(f"ETRIC VALUE: {self.state.value_metric_pre}")   #DA SCOMMENTARE PER LA RQ3


            if self.state.is_validate:  #vuol dire Build Success
                '''if self.state.value_metric_post <= self.state.value_metric_pre:   #c'è stato un miglioramento
                    print(f"VULNERABILITIES PRIMA: {self.state.value_metric_pre}")
                    print(f"VULNERABILITIES DOPO: {self.state.value_metric_post}")
                    self.state.attempts += 1  #aumenta numero di tentativi e riesegui il refactoring su stessa classe
                    attempts_tot += 1
                else:'''   #DA SCOMMENTARE PER LA RQ3
                self.state.current_class += 1   #passa alla prossima classe
                self.state.is_validate = ""
                self.state.errors = ""
                self.state.attempts = 0  # riazzero attempts per la prossima classe
                # self.state.value_metric_pre = 0
                # self.state.value_metric_post = 0

            else:  #Build Failure (errori di compilazione o altro tipo di errore)
                self.state.attempts += 1   #aumenta numero di attempts e riesegui il refactoring su stessa classe
                attempts_tot += 1
                print(F"Total Attempts for now: {attempts_tot}")

        else:    #arrivato a N attempts
            print("\nClass already iterated 3 times, move on to the next class or next project")
            self.state.current_class +=1   #passa avanti con la classe
            self.state.is_validate= ""
            self.state.errors= ""
            self.state.attempts = 0   #riazzero attempts per la prossima classe
            #self.state.value_metric_pre = 0      #DA SCOMMENTARE PER LA RQ3
            #self.state.value_metric_post = 0     #DA SCOMMENTARE PER LA RQ3



def kickoff(directory):
    flow = OriginalFlow()
    flow.kickoff({"directory": directory})


def plot():
    flow = OriginalFlow()
    flow.plot()


if __name__ == "__main__":

    validator = Validation()

    scelta = input("Which dataset do you want to process? [lpo/apache/both]: ").strip().lower()

    start_time = time.time()

    if scelta in ["lpo", "both"]:
        print("\n--- Starting procedure for LPO ---\n")
        #comment out the next 3 lines after the first execution

        validator.clone_lpo_projects()
        validator.creation_sonar_projects(f"{DIRECTORY_REPOS}{LPO_PATH}")
        validator.results_pre_refactoring(f"{DIRECTORY_REPOS}{LPO_PATH}")

        kickoff(f"{DIRECTORY_REPOS}{LPO_PATH}")

        print(f"Execution Times for Students projects: {time_for_project}")
        print("Attributes pre-refactoring (LPO):")
        print(pd.read_csv("attributes_before_refactoring").to_string())

        validator.results_post_refactoring(f"{DIRECTORY_REPOS}{LPO_PATH}")

        print("Attributes post-refactoring (LPO):")
        print(pd.read_csv("attributes_post_refactoring").to_string())


    if scelta in ["apache", "both"]:
        print("\n--- Starting procedure for Apache ---\n")
        #comment out the next 3 lines after the first execution

        #validator.clone_apache_projects()
        validator.creation_sonar_projects(f"{DIRECTORY_REPOS}{APACHE_PATH}")
        #validator.results_pre_refactoring(f"{DIRECTORY_REPOS}{APACHE_PATH}")

        kickoff(f"{DIRECTORY_REPOS}{APACHE_PATH}")

        print(f"Execution Times for Apache projects: {time_for_project}")
        print("Attributes pre-refactoring (Apache):")
        print(pd.read_csv("attributes_before_refactoring").to_string())

        validator.results_post_refactoring(f"{DIRECTORY_REPOS}{APACHE_PATH}")

        print("Attributes post-refactoring (Apache):")
        print(pd.read_csv("attributes_post_refactoring").to_string())


    print(f"\nTOTAL ATTEMPTS= {attempts_tot}")
    total_time = time.time() - start_time
    print(f"TOTAL Execution Time= {total_time:.2f} secondi")

    plot()



