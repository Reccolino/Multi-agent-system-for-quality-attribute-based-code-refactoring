from crewai import Crew, Process

from agents import CustomAgent
from tasks import CustomTask

def run():
    agents = CustomAgent()
    tasks = CustomTask()

    agente1 = agents.first_agent()
    agente2 = agents.second_agent()

    task1= tasks.first_task(agente1)
    task2= tasks.second_task(agente2, task1)

    #CREAZIONE CREW
    crew = Crew(
        agents= [agente1, agente2],
        tasks= [task1,task2],
        process= Process.sequential,
        verbose=True
    )

    return crew.kickoff()


if __name__ == '__main__':
    result = run()
    print(result)