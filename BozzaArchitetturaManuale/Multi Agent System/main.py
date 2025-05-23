import json
import os
import time

import requests
from crewai import Crew, Process
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER
from agents import CustomAgent
from tasks import CustomTask



def run():

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

    #CREAZIONE CREW
    crew = Crew(
        #agents= [query_writer, code_refactor], nnposso omettere tanto nelle task già specifico gli agenti che eseguiranno quella task
        tasks= [task0,task1, task2, task3],
        process= Process.sequential,
        verbose=True,

        #embedder={
         #   "provider": "ollama",
          #      "config": {
           #         "model": "nomic-embed-text",
            #        "base_url": "http://localhost:11434"
             #   }
        #}
    )


    return crew.kickoff()




if __name__ == '__main__':
    start_time= time.time()

    result = run()
    print(result)

    end_time = time.time()- start_time
    print(f"Tempo di esecuzione = {end_time}")

'''for repository in os.listdir(DIRECTORY):

    if repository.startswith("."):  # come cartella .git
        continue

    #classe = classe_peggiore(repository)'''



