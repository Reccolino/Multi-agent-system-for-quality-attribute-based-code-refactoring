import os
import subprocess
import requests
from crewai import Agent, Crew, Process, Task, LLM, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tools import tool
from pydantic import BaseModel
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import DIRECTORY_REPOS, HEADER



# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@tool("sonar-scanner", result_as_answer=True)
def sonar_scanner(path_class: str):
    """
    Executes Maven and SonarScanner commands in the project root
    :param path_class:
    :return: True if Build Success, False if Build Failure with errors
    """

    #normalize the path for the operating system
    path_class = os.path.normpath(path_class)
    parts = path_class.split(os.sep)

    project_type = parts[1]
    project_key = parts[2]
    directory_pom = ""

    for root, dir, files in os.walk(f"{DIRECTORY_REPOS}/{project_type}/{project_key}"):
        if "pom.xml" in files:
            directory_pom = root
            break

    try:
        subprocess.run(["mvn.cmd", "clean", "install", "verify"], cwd=os.path.join(directory_pom), check=True)

        comando = [
            "mvn.cmd", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar" ,
            f"-Dsonar.projectKey=Project_{project_key}",
            f"-Dsonar.projectName=Project_{project_key}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
        ]

        jacoco_path = os.path.join(directory_pom, "target/site/jacoco/jacoco.xml")
        if os.path.exists(jacoco_path):  # PER I PROGETTI APACHE
            comando.append(f"-Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml")
        else:
            print("No JaCoCo report found: coverage will not be included in SonarQube")


        result = subprocess.run(comando,
            cwd=os.path.join(directory_pom),
            capture_output=True,
            text=True,
            check=True
        )
        print("OUTPUT MAVEN:\n", result.stdout)

#------------------------------------RESEARCH QUESTION 3-------------------------------------------------#

        url = "http://localhost:9000/api/measures/component"
        param = {
            "component": f"Project_{project_key}",
            "metricKeys": "vulnerabilities"
        }
        try:
            response = requests.get(url, headers=HEADER, params=param)

            response.raise_for_status()
            print(response.json().get("component").get("measures")[0].get("value"))
            valore_metrica=int(response.json().get("component").get("measures")[0].get("value"))

#----------------------------------------------------------------------------------------------------------#

            return RefactoringVerificator(valid=True, errors="", metric=valore_metrica)

        except requests.exceptions.HTTPError as e:
            error_response = e.response.json()
            error_msg = error_response.get("errors", [{}])[0].get("msg", "No message")
            if "Component" in error_msg:
                print("Error: Project non found")
                #elimina_da_locale(project)
            elif "metric" in error_msg:
                print("Error: MetricKey not valid.")
            else:
                print(f"Unknown error : {error_msg}")


        except requests.exceptions.RequestException as e:
            print(f"Network error or other issue in the request: {e}")
            return

    except subprocess.CalledProcessError as e:
        error_lines = [line for line in e.stdout.splitlines() if "[ERROR]" in line]
        errors_filtered = "\n".join(error_lines)    #filtro gli errori senza caricare errors con righe inutili
        return RefactoringVerificator(valid=False, errors=errors_filtered, metric=0)


@tool("code_replace")
def code_replace(path_class: str, code: str) -> str:
    """
    Overwrites the Java file at class_path with the content refactored_code,
    using atomic writing (tmp + os.replace).
    Returns a success message or raises an error.
    """

    tmp = path_class + ".tmp"
    try:

        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path_class)
        return f"Code replace complete in {path_class}"
    except Exception as e:
        return f"Error during code replace: {e}"



class RefactoringVerificator(BaseModel):
    valid: bool
    errors: Optional[str]
    metric: int


@CrewBase
class RefactorCrew:
    """RefactorCrew crew"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)   #richiesto da CrewAI
        #attributo per salvare il risultato di task4
        self.refactoring_output: Optional[RefactoringVerificator] = None

    def _save_task4_result(self, output: TaskOutput) -> None:
        """
        This method is called after `task4` has produced a RefactoringVerificator.
        We save it in the attribute self.refactoring_output so it can be used
        in all subsequent tasks.
        """

        if getattr(output, "pydantic", None) is not None:     #dammi l’attributo pydantic dell’oggetto output se esiste, altrimenti None
            self.refactoring_output = output.pydantic
            print("Refactoring_output:", self.refactoring_output)


    def build_result(self, output: TaskOutput) -> bool:
        """
        Returns False if I want to SKIP the conditional task,
        that is, when task4.valid == True.
        Otherwise (valid=False or result not yet available) returns True => EXECUTE THE TASK.
        """

        if self.refactoring_output is None or self.refactoring_output.valid is False :
            return True
        return False


    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    '''llm = LLM(
        model="mistral/mistral-medium",
        api_key=os.getenv("MISTRAL_API_KEY"),
        stream=True,
        temperature=0.4,
        top_p=0.6,
        frequency_penalty=0.1,
        presence_penalty=0.1,
        seed=42,
        #stop=["###FINE"]
    )'''

    llm= LLM(
        model="mistral/codestral-2501",
        api_key=os.getenv("MISTRAL_API_KEY"),
        stream=True,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0.2,
        presence_penalty=0.0,
        n=1,
        reasoning_effort="high"
        #stop=["###FINE"]
     )

    llm_refactoring = LLM (
        model="mistral/codestral-2501",
        api_key=os.getenv("MISTRAL_API_KEY"),
        stream=True,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0.2,
        presence_penalty=0.0,
        n=1,
        reasoning_effort="high"
    )
    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def query_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['query_writer'],  # type: ignore[index]
            verbose=True,
            llm=self.llm
        )

    @agent
    def code_refactor(self) -> Agent:
        return Agent(
            config=self.agents_config['code_refactor'],  # type: ignore[index]
            verbose=True,
            llm=self.llm_refactoring
        )

    @agent
    def code_replacer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_replacer'],  # type: ignore[index]
            verbose=False,
            llm=self.llm
        )

    @agent
    def sonar_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['sonar_agent'],  # type: ignore[index]
            verbose=False,
            llm=self.llm
        )

    @agent
    def error_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['error_summarizer'],  # type: ignore[index]
            verbose=False,
            llm=self.llm
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def task1(self) -> Task:
        return Task(
            config=self.tasks_config['task1'],  # type: ignore[index]
            verbose=True
        )

    @task
    def task2(self) -> Task:
        return Task(
            config=self.tasks_config['task2'],  # type: ignore[index]
            verbose=True
        )

    @task
    def task3(self) -> Task:
        return Task(
            config=self.tasks_config['task3'],  # type: ignore[index]
            verbose=False,
            tools=[code_replace]
        )

    @task
    def task4(self) -> Task:
        return Task(
            config=self.tasks_config['task4'],  # type: ignore[index]
            verbose=False,
            tools=[sonar_scanner],
            output_pydantic=RefactoringVerificator,
            callback=self._save_task4_result
        )

    @task
    def conditional_task5(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['conditional_task5'],  # type: ignore[index]
            verbose=False,
            tools=[code_replace],
            condition=self.build_result
        )

    @task
    def conditional_task6(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['conditional_task6'],  # type: ignore[index]
            verbose=False,
            condition=self.build_result,
            output_pydantic=RefactoringVerificator
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RefactorCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True
        )
