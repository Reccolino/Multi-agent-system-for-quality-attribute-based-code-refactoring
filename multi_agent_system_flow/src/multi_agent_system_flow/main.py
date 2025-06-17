import os
import time
import warnings
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, or_, router
from scipy.optimize import direct

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import APACHE_PATH, LPO_PATH
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY_REPOS, Validation
from multi_agent_system_flow.src.multi_agent_system_flow.crews.refactor_crew.refactor_crew import RefactorCrew
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import classes_for_project, \
    esec_class, metrics

TENTATIVI_MAX: int = 3
tentativi_tot: int = 0
tempo_per_progetto: List[float] = []

class ExampleFlow(BaseModel):
    directory: str = ""     #directory su cui fare esecuzione
    project_list: List[str] = []      #lista di progetti
    current_project: Optional[int] = 0    #serve a indicare quale progetto si sta elaborando
    classi: List[dict] = []     #lista di classi di un progetto
    current_class: Optional[int] = 0    #serve a indicare quale classe del progetto si sta facendo refactoring
    path_class: str = ""     #path della classe da passare alla Crew per poter fare code replace e per poter eseguire sonarScanner
    code_class: str = ""     #codice della classe da passare alla Crew per poter fare refactoring
    errors: Optional[str] = ""         #errori (di compilazione o altri) da passare alla Crew per indirizzare agente a non commetterli
    is_validate: Optional[bool] = True        #flag che verifica se il comando da terminale per una classe ha restituito Build Success o Build Failure
    tentativi: Optional[int] = 0    #contatore per tenere traccia del numero di tentativi su una singola classe
    #value_metric_pre: Optional[int] = 0   #DA SCOMMENTARE PER LA RQ2
    #value_metric_post: Optional[int] = 0   #DA SCOMMENTARE PER LA RQ2
    project_start_times: List[float] = []

class OriginalFlow(Flow[ExampleFlow]):

    @start()
    def init(self):
        """
        Metodo che carica tutti i progetti nella project_list. Da qui si potrà accedere ai singoli progetti e alle classi dei progetti
        """
        global tempo_per_progetto
        self.state.project_list = [repository for repository in os.listdir(self.state.directory)]
        print(self.state.project_list)
        tempo_per_progetto = [0.0 for _ in self.state.project_list]
        self.state.project_start_times = [0.0 for _ in self.state.project_list]



    @router(or_("init", "classes_for_project", "refactor_code"))
    def router(self, _=None):
        """
        Il router guarda lo stato e restituisce il nome del prossimo metodo da eseguire.
        """

        #Se non ho ancora caricato le classi per un progetto
        if not self.state.classi:
            return "percorso_progetto"


        #Se ho ancora classi residue per questo progetto
        if self.state.current_class < len(self.state.classi):
            return "percorso_classe"


        #Ho processato tutte le classi di questo progetto:
        #passo al prossimo progetto (se esiste) o termino
        tempo_per_progetto[self.state.current_project] = time.time() - self.state.project_start_times[
            self.state.current_project]
        self.state.current_project += 1
        if self.state.current_project < len(self.state.project_list):
            # resetto le classi per il nuovo progetto
            self.state.classi = []
            self.state.current_class = 0
            return "percorso_progetto"
        else:
            print("Tutti i progetti sono stati elaborati.")




    @listen("percorso_progetto")
    def classes_for_project(self):
        """
            Restituisce: il path della classe con peggior security_rating via SonarQube e il codice di quella classe .
            Effettua una GET su /api/measures/component_tree e ordina per security_rating  .
        """
        self.state.project_start_times[self.state.current_project] = time.time()   #faccio partire tempo per progetto

        response = classes_for_project(self.state.project_list[self.state.current_project])

        #DA SCOMMENTARE PER RQ2
        '''all_components = response.json().get("components", [])
        filtered = [c for c in all_components if c.get("measures")]   #ho solo le classi che hanno effettivamente una measure
        #questo perchè può essere che un progetto abbia 1 solo vulnerabilities e il json mi restituisce le prime 3 classi
        #ma cosi mi restituisce la classe dove è presente effettivamente il vulnerabilities e altre 2 classi che non hanno problemi
        #quindi per quelle due che senso ha fare refactoring ?
        print(f"FILTERED {filtered}")
        self.state.classi = filtered'''
        self.state.classi = response     #carica le classi dal JSON




    @listen("percorso_classe")
    def esec_class(self):
        """
        Effettua un GET api/sources/raw per restituire il codice e il path da refattorizzare di una classe specifica
        """
        if self.state.tentativi < TENTATIVI_MAX:   #cosi evito di rifare chiamata api inutilmente

            # http://localhost:9000/api/sources/raw necessita della key del progetto come parametro (query string)  ==> la prendo dal JSON
            classe_attuale = self.state.classi[self.state.current_class]
            print(f"CLASSE ATTUALE= {classe_attuale}")
            code = esec_class(classe_attuale)

            self.state.code_class = code.text

            #self.state.value_metric_pre = int(metrics(classe_attuale.get("key")))  #DA SCOMMENTARE PER LA RQ2

            project_root = f"{self.state.directory}{self.state.project_list[self.state.current_project]}"

            # PER PROGETTI LPO BISOGNA TROVARE PATH CORRETTO PERCHE NON è IMMEDIATO COME PROGETTI APACHE
            for root, _, files in os.walk(project_root):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    # uso normpath perche il json restituisce slash cosi: \ . Invece a me serve il path con slash cosi /
                    if full_file_path.endswith(os.path.normpath(self.state.classi[self.state.current_class].get("path"))):
                        self.state.path_class = full_file_path
                        print(f"LOCAL PATH: {self.state.path_class}" + f"\nCODE:\n{self.state.code_class}")



    @listen("esec_class")
    def refactor_code(self):
        global tentativi_tot

        print(f"\nElaborando progetto: {self.state.project_list[self.state.current_project]}")
        print(f"\nClasse: {self.state.classi[self.state.current_class]}")

        if self.state.tentativi < TENTATIVI_MAX:

            #ovviamente alla prima iterazione self.state.scanner_result è vuoto, poi se al primo tentativo Build Failure allora
            #contiene gli errori che ha restituito SonarScanner
            result = RefactorCrew().crew().kickoff(
                inputs={"code_class": self.state.code_class, "path_class": self.state.path_class,
                        "errors": self.state.errors})


            self.state.is_validate = result["valid"]
            self.state.errors = result["errors"].strip() or "errors"
            #se errors è "" allora self.state.errors lo faccio diventare semplicemente "errors"
            #cosi che il templating nella task2 funzioni in entrambi i casi

            #self.state.value_metric_post = result["metric"]   #DA SCOMMENTARE PER LA RQ2

            print(f"VALIDATE: {self.state.is_validate}")
            #print(f"VALORE METRICA: {self.state.value_metric_pre}")   #DA SCOMMENTARE PER LA RQ2


            if self.state.is_validate:  #vuol dire Build Success
                '''if self.state.value_metric_post <= self.state.value_metric_pre:   #c'è stato un miglioramento
                    print(f"VULNERABILITIES PRIMA: {self.state.value_metric_pre}")
                    print(f"VULNERABILITIES DOPO: {self.state.value_metric_post}")
                    self.state.tentativi += 1  #aumenta numero di tentativi e riesegui il refactoring su stessa classe
                    tentativi_tot += 1
                else:'''   #DA SCOMMENTARE PER LA RQ2
                self.state.current_class += 1   #passa alla prossima classe
                self.state.is_validate = ""
                self.state.errors = ""
                self.state.tentativi = 0  # riazzero tentativi per la prossima classe
                # self.state.value_metric_pre = 0
                # self.state.value_metric_post = 0

            else:  #Build Failure (errori di compilazione o altro tipo di errore)
                self.state.tentativi += 1   #aumenta numero di tentativi e riesegui il refactoring su stessa classe
                tentativi_tot += 1
                print(F"TENTATIVI TOT PER ORA: {tentativi_tot}")

        else:    #arrivato a N tentativi
            print("\nClasse già iterata 3 volte, passa alla prossima classe o al prossimo progetto")
            self.state.current_class +=1   #passa avanti con la classe
            self.state.is_validate= ""
            self.state.errors= ""
            self.state.tentativi = 0   #riazzero tentativi per la prossima classe
            #self.state.value_metric_pre = 0      #DA SCOMMENTARE PER LA RQ2
            #self.state.value_metric_post = 0     #DA SCOMMENTARE PER LA RQ2



def kickoff(directory):
    flow = OriginalFlow()
    flow.kickoff({"directory": directory})


def plot():
    flow = OriginalFlow()
    flow.plot()


if __name__ == "__main__":

    validator = Validation()

    scelta = input("Quale dataset vuoi processare? [lpo/apache/entrambi]: ").strip().lower()

    start_time = time.time()

    if scelta in ["lpo", "entrambi"]:
        print("\n--- Avvio procedura per LPO ---\n")
        #commenta prossime 3 righe dopo la prima esecuzione
        validator.clone_progetti_lpo()
        validator.creazione_progetti_Sonar(f"{DIRECTORY_REPOS}{LPO_PATH}")
        validator.risultati_pre_refactoring(f"{DIRECTORY_REPOS}{LPO_PATH}")
        kickoff(f"{DIRECTORY_REPOS}{LPO_PATH}")
        print(f"TEMPI LPO: {tempo_per_progetto}")
        print("Attributi pre-refactoring (LPO):")
        print(pd.read_csv("attributes_before_refactoring").to_string())
        validator.risultati_post_refactoring(f"{DIRECTORY_REPOS}{LPO_PATH}")
        print("Attributi post-refactoring (LPO):")
        print(pd.read_csv("attributes_post_refactoring").to_string())


    if scelta in ["apache", "entrambi"]:
        print("\n--- Avvio procedura per Apache ---\n")
        #commenta prossime 3 righe dopo la prima esecuzione
        #validator.clone_progetti_apache()
        #validator.creazione_progetti_Sonar(f"{DIRECTORY_REPOS}{APACHE_PATH}")
        #validator.risultati_pre_refactoring(f"{DIRECTORY_REPOS}{APACHE_PATH}")
        kickoff(f"{DIRECTORY_REPOS}{APACHE_PATH}")
        print(f"TEMPI Apache: {tempo_per_progetto}")
        print("Attributi pre-refactoring (Apache):")
        print(pd.read_csv("attributes_before_refactoring").to_string())
        validator.risultati_post_refactoring(f"{DIRECTORY_REPOS}{APACHE_PATH}")
        print("Attributi post-refactoring (Apache):")
        print(pd.read_csv("attributes_post_refactoring").to_string())


    print(f"\nTENTATIVI TOTALI= {tentativi_tot}")
    total_time = time.time() - start_time
    print(f"Tempo di esecuzione TOTALE= {total_time:.2f} secondi")

    plot()



