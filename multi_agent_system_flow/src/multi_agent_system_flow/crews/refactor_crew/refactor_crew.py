import os
import subprocess

import requests
from crewai import Agent, Crew, Process, Task, LLM, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional, Any

from crewai.tools import tool
from crewai_tools.tools.file_writer_tool.file_writer_tool import FileWriterTool
from pydantic import BaseModel


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@tool("sonar-scanner", result_as_answer=True)
def sonar_scanner(path_class: str):
    """
    Esegue comandi Maven e di SonarScanner nella root del progetto
    :param path_class:
    :return: True if Build Success, False if Build Failure with errors
    """

    #normalizza il percorso per il sistema operativo
    path_class = os.path.normpath(path_class)
    parts = path_class.split(os.sep)

    project_key = parts[1]
    print("PROJECT KEY: ", project_key)

    #QUESTO SOLO PER PROGETTI LPO
    directory_pom = parts[2]
    print("DIRECTORY POM: ", directory_pom)

    try:
        subprocess.run([
            "mvn.cmd", "clean", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar" ,
            f"-Dsonar.projectKey=Progetto_{project_key}",
            f"-Dsonar.projectName=Progetto_{project_key}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",
            "-DskipTests"
        ],
            #cwd=os.path.join("cloned_repos_lpo", project_key),

            #QUESTO SOLO PER PROGETTI LPO
            cwd=os.path.join("cloned_repos_lpo", project_key, directory_pom),
            capture_output=True,
            text=True,
            check=True
        )
        #valid = "BUILD SUCCESS" in result.stdout
        return RefactoringVerificator(valid=True, errors="")

    except subprocess.CalledProcessError as e:
        error_lines = [line for line in e.stdout.splitlines() if "[ERROR]" in line]
        errors_filtered = "\n".join(error_lines)
        return RefactoringVerificator(valid=False, errors=errors_filtered)


@tool("code_replace")
def code_replace(path_class: str, code: str) -> str:
    """
    Sovrascrive il file Java in class_path con il contenuto refactored_code,
    usando scrittura atomica (tmp + os.replace).
    Ritorna un messaggio di successo o solleva errore.
    """
    tmp = path_class + ".tmp"
    try:
        # Scrittura atomica
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path_class)
        return f"Code replace completato in {path_class}"
    except Exception as e:
        return f"Errore durante code replace: {e}"



def build_result(output: TaskOutput) -> bool:
    return output.pydantic.valid != True


class QualityVerificator(BaseModel):
    quality_gates: bool
    failed_quality: Optional[str]


class RefactoringVerificator(BaseModel):
    valid: bool
    errors: Optional[str]


@CrewBase
class RefactorCrew:
    """RefactorCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    llm = LLM(
        model="mistral/mistral-medium",
        api_key=os.getenv("MISTRAL_API_KEY"),
        stream=True,
        temperature=0.0
    )

    '''llm_fast= LLM(
        model="gemini/gemini-1.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        stream=True
     )'''

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
            llm=self.llm,
            #memory=True
        )

    @agent
    def code_refactor(self) -> Agent:
        return Agent(
            config=self.agents_config['code_refactor'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
            reasoning=True,
            #memory=True
        )

    @agent
    def code_replace_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['code_replace_agent'],  # type: ignore[index]
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
    def riassunto_errori(self) -> Agent:
        return Agent(
            config=self.agents_config['riassunto_errori'],  # type: ignore[index]
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
            # context=[self.first_task],
            verbose=True
        )

    @task
    def task2(self) -> Task:
        return Task(
            config=self.tasks_config['task2'],  # type: ignore[index]
            #context=[self.task1],
            verbose=True
        )

    @task
    def task3(self) -> Task:
        return Task(
            config=self.tasks_config['task3'],  # type: ignore[index]
            # context=[self.task2],
            verbose=False,
            tools=[code_replace],
            #output_pydantic=RefactoringVerificator
        )

    @task
    def task4(self) -> Task:
        return Task(
            config=self.tasks_config['task4'],  # type: ignore[index]
            # context=[self.task2],
            verbose=False,
            tools=[sonar_scanner],
            #output_pydantic=RefactoringVerificator
        )

    @task
    def conditional_task5(self) -> Task:
        return Task(
            config=self.tasks_config['conditional_task5'],  # type: ignore[index]
            # context=[self.task2],
            verbose=False,
            tools=[code_replace],
            condition=build_result,
            #output_pydantic=RefactoringVerificator
            # output_pydantic=RefactoringVerificator
        )

    @task
    def conditional_task6(self) -> Task:
        return Task(
            config=self.tasks_config['conditional_task6'],  # type: ignore[index]
            # context=[self.task2],
            verbose=False,
            #tools=[code_replace],
            condition=build_result,
            output_pydantic=RefactoringVerificator
            # output_pydantic=RefactoringVerificator
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
            verbose=True,
            #memory=True,
            #embedder={
            #   "provider": "ollama",
            #  "config":{"model": "nomic-embed-text:latest"}
            #}
        )
