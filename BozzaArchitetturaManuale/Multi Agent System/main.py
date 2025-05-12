import json
import os
import time
import requests
from crewai import Crew, Process

from BozzaArchitetturaManuale.validation import HEADER, DIRECTORY
from agents import CustomAgent
from tasks import CustomTask

def run():

    global response

    agents = CustomAgent()
    tasks = CustomTask()

    query_writer = agents.first_agent()
    code_refactor = agents.second_agent()
    #sonar_connector = agents.third_agent()
    #attributes_verify = agents.third_agent()   #colui che si dovrà connettere a SonarQube tramite chiamata API

    task
    task1= tasks.first_task(query_writer)
    task2= tasks.second_task(code_refactor, task1)
    #task3= tasks.third_task(sonar_connector, task2)


    with open("EsempioClasse", "r") as file:
        file_data = file.read()

    input = {
        "file_content": file_data,
        "quality_attributes_to_improve": response.json()
        #"response": response
    }
    #print(input["file_content"])


    #CREAZIONE CREW
    crew = Crew(
        #agents= [query_writer, code_refactor], nnposso omettere tanto nelle task già specifico gli agenti che eseguiranno quella task
        tasks= [task1,task2],   #TODO: definisci task senza agenti che si connettono a sonar e che fanno replace del codice
        process= Process.sequential,
        verbose=True
    )


    return crew.kickoff(inputs=input)


def classe_peggiore():
    param = {
        "component": f"ProgettoApache_codec",
        "metricKeys":  # "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
        # "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
        # "blocker_violations,critical_violations",
            "security_rating, vulnerabilities",
        "qualifiers": "FIL",
        "s": "metric",
        "metricSort": "security_rating",
        "ps": 1,
        "asc": "false"
    }
    try:
        response = requests.get("http://localhost:9000/api/measures/component_tree", headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))

        #return response.json().get
    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")

    # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate


if __name__ == '__main__':
    start_time= time.time()
    for repository in os.listdir(DIRECTORY):

        if repository.startswith("."):  # come cartella .git
            continue

        classe = classe_peggiore()
        result = run()
        print(result)


    end_time = time.time()- start_time
    print(f"Tempo di esecuzione = {end_time}")
