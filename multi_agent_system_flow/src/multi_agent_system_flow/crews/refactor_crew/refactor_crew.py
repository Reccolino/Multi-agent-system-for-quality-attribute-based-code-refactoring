import os
import subprocess

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, output_pydantic
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional

from crewai.tools import tool
from crewai_tools.tools.file_writer_tool.file_writer_tool import FileWriterTool
from pydantic import BaseModel


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@tool("sonar_scanner", result_as_answer=True)
def sonar_scanner(path_class: str):
    """
    Esegue comandi Maven e di SonarScanner nella root del progetto
    :param path_class:
    :return: True if Build Success, False if Build Failure with errors
    """
    project_key = path_class.split('/')[2]
    print("PROJECT KEY:  "+project_key)
    #QUESTO SOLO PER PROGETTI LPO
    directory_pom = path_class.split('/')[3]
    print("DIRECTORY POM:  "+ directory_pom)
    try:
        subprocess.run([
            "mvn.cmd", "clean", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
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
        return RefactoringVerificator(valid=True)

    except subprocess.CalledProcessError as e:
        return RefactoringVerificator(valid=False, errors=e.stdout)


code_replace = FileWriterTool()      #tool che fa code replace


class RefactoringVerificator(BaseModel):
    errors: Optional[str]
    valid: bool


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
        stream=True
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
    def utility_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['utility_agent'],  # type: ignore[index]
            verbose=True,
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
            verbose=True,
            tools=[code_replace],
            #output_pydantic=RefactoringVerificator
        )

    @task
    def task4(self) -> Task:
        return Task(
            config=self.tasks_config['task4'],  # type: ignore[index]
            #context=[self.task2],
            verbose=True,
            tools=[sonar_scanner],
            output_pydantic=RefactoringVerificator
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RefactorCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            #memory=True,
            #embedder={
             #   "provider": "ollama",
              #  "config":{"model": "nomic-embed-text:latest"}
            #}
        )
