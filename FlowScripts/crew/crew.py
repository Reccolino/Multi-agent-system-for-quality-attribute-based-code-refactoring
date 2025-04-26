import os
import yaml
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase
from crewai.project.annotations import agent, task, crew


@CrewBase
class CustomCrew:

    agents_config = 'config/agents.yaml'
    print(agents_config)
    tasks_config = 'config/tasks.yaml'
    llm = LLM(model="mistral/mistral-small-latest", api_key=os.getenv("MISTRAL_API_KEY"))

    @agent
    def first_agent(self) -> Agent:
        return Agent(
            config= self.agents_config['agente1'],
            verbose=True,
            llm=self.llm,
        )

    @agent
    def second_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['agente2'],
            verbose=True,
            llm=self.llm,
        )

    @task
    def first_task(self) -> Task:
        return Task(
            config=self.tasks_config['task1'],
        )

    @task
    def second_task(self) -> Task:
        return Task(
            config=self.tasks_config['task2'],
            context=[self.first_task]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the content writing crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )