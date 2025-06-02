import json
import os
import subprocess

import requests

from BozzaArchitetturaManuale.validation import HEADER


def classes_for_project(url, project):
    param = {
        "component": f"Progetto_{project}",
        "metricKeys":  # "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
        # "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
        # "blocker_violations,critical_violations",
            "security_rating, vulnerabilities",
        "qualifiers": "FIL",
        "s": "metric",
        "metricSort": "security_rating",
        "ps": 3,
        "asc": "false"
    }
    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))
        print(response)
        return response

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")
    # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate



def esec_class(url, classe):
    param = {
        "key": classe.get("key")
    }

    try:

        response = requests.get(url, headers=HEADER, params=param)
        #print(json.dumps(response.json(), indent=4))
        response.encoding = 'utf-8'
        print(response)
        return response

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")








'''def check_quality_gates(path_class: str):
    """
    Esegue comandi Maven e di SonarScanner nella root del progetto
    :param path_class:
    :return: True if Build Success, False if Build Failure with errors
    """
    project_key = path_class.split('/')[2]
    print("PROJECT KEY:  "+project_key)


    try:
        response = requests.get(
            "http://localhost:9000/api/qualitygates/project_status",
            params={"projectKey": "your_project_key"},
            auth=("your_api_key", "")  # Username è la API key, password vuota
        )
    except subprocess.CalledProcessError as e:
        return RefactoringVerificator(valid=False, errors=e.stdout)'''