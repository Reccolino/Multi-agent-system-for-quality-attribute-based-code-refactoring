import os
import time

from crewai import Crew, Process

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY
from agents import CustomAgent
from tasks import CustomTask



def run(repository):

    global response

    agents = CustomAgent()
    tasks = CustomTask()

    searcher_class = agents.first_agent()
    query_writer = agents.second_agent()
    code_refactor = agents.third_agent()
    utility_agent = agents.fourth_agent()
    #sonar_connector = agents.third_agent()
    #attributes_verify = agents.third_agent()   #colui che si dovrà connettere a SonarQube tramite chiamata API


    task0 = tasks.first_task(searcher_class)
    task1= tasks.second_task(query_writer, task0)
    task2= tasks.fourth_task(code_refactor, task0, task1)
    task3= tasks.code_replace_sonar_task(utility_agent, task0, task2)
    #task4= tasks.sonar_task(utility_agent, task0)

    #con solo task1 e task2 con classe in input alla crew MISTRAL-MEDIUM funziona molto bene

    '''input = {
        #"repository": repository,
        "quality_attributes_to_improve": "security_rating"
        #"response": response
    }'''
    #print(input["file_content"])

    #code_source = classe_peggiore()
    #print(code_source)
    #input = {
   #     "code": code_source
   # }
    #source = StringKnowledgeSource(name="code", content=code_source)

    input = {
        "repository": repository
    }

    #CREAZIONE CREW
    crew = Crew(
        #agents= [query_writer, code_refactor], nnposso omettere tanto nelle task già specifico gli agenti che eseguiranno quella task
        tasks= [task0,task1, task2, task3],
        process= Process.sequential,
        verbose=True,
        #memory=True
        #embedder={
         #   "provider": "ollama",
          #      "config": {
           #         "model": "nomic-embed-text",
            #        "base_url": "http://localhost:11434"
             #   }
        #}
    )


    return crew.kickoff(inputs=input)




if __name__ == '__main__':
    start_time= time.time()

    for repository in os.listdir(DIRECTORY):

        if repository.startswith("."):  # come cartella .git
            continue
        result = run(repository)
        print(result)

        #classe = classe_peggiore(repository)'''

    end_time = time.time()- start_time
    print(f"Tempo di esecuzione = {end_time}")


