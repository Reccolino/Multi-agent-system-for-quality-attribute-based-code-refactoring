import os
import time
import requests
from crewai import Crew, Process

from agents import CustomAgent
from tasks import CustomTask

def run():
    agents = CustomAgent()
    tasks = CustomTask()

    query_writer = agents.first_agent()
    code_refactor = agents.second_agent()
    sonar_connector = agents.third_agent()
    #attributes_verify = agents.third_agent()   #colui che si dovrà connettere a SonarQube tramite chiamata API

    task1= tasks.first_task(query_writer)
    task2= tasks.second_task(code_refactor, task1)
    task3= tasks.third_task(sonar_connector, task2)


    url= 'https://sonarcloud.io/api/measures/component?metricKeys=ncloc%2Ccode_smells%2Ccomplexity&component=reccolino_progettoapache1'
    #url= 'https://localhost:9000/api/measures/component?metricKeys=ncloc%2Ccode_smells%2Ccomplexity&component= <  >' CHIAMATA A LOCALHOST
    #devi modellare l'url per farti restituire le metriche che ti interessano (metricKeys)
    #"http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate

    header = {
        'Authorization': f'Bearer {os.getenv("SONAR_CLOUD_API_TOKEN")}'   #il token si deve nascondere (mettilo nell'environment)
    }

    response= requests.get(url=url, headers=header)  #DA FARE IN UNA CLASSE A PARTE, OVVIAMENTE

    print(f"RESPONSE: {response.json()}")


    with open("EsempioClasse", "r") as file:
        file_data = file.read()

    with open("Errori", "r") as file:
        error_data = file.read()


    input = {
        "file_content": file_data,
        "error_content": error_data,
        "sonar_json": response.json()
        #"response": response
    }
    #print(input["file_content"])

    #CREAZIONE CREW
    crew = Crew(
        agents= [query_writer, code_refactor, sonar_connector],
        tasks= [task1,task2, task3],
        process= Process.sequential,
        verbose=True
    )


    return crew.kickoff(inputs=input)


if __name__ == '__main__':
    start_time= time.time()
    result = run()
    end_time = time.time()- start_time
    print(result)
    print(f"Tempo di esecuzione = {end_time}")
