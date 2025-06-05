import json
import os
import time
from abc import ABC, abstractmethod
from typing import Final
from git import Repo
import requests

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import header_git, DIRECTORY, \
    FILE_REPORT_PRE_REFACTORING, FILE_REPORT_POST_REFACTORING
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import crea_progetto, \
     restituisci_metriche_pre_kickoff, restituisci_metriche_post_kickoff
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.utility_methods import grafici



class BaseValidation(ABC):

   @abstractmethod
   def clone_progetti_Git(self):
       pass

   @abstractmethod
   def creazione_progetti_Sonar(self):
       """
       Crea i progetti locali su SonarQube
       Args:
           directory: directory che contiene tutti i progetti salvati in locale
       """
       pass

   @abstractmethod
   def risultati_pre_refactoring(self):
       """
       Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto.
       Pulizia dei progetti: eliminazione di quelli non significativi ai fini dell'approccio

       Return:
          Dataframe con i risultati pre refactoring
       """
       pass

   @abstractmethod
   def risultati_post_refactoring(self):
       """
       Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto, dopo il refactoring del MAS.
       Creazione grafici per trovare differenze fra prima e dopo refactoring.

       Return:
          Grouped Chart con i risultati
       """
       pass




class Validation(BaseValidation):



    def clone_progetti_Git(self):

        #repos_url= "https://api.github.com/search/repositories?q=apache+commons+language:java&per_page=25"
        repos_url = f"https://api.github.com/orgs/LPODISIM2024/repos?type=private"

        response = requests.get(repos_url, headers=header_git)
        repos = response.json()
        #path = f"{DIRECTORY}"
        #print(json.dumps(repos, indent=3))

        '''for repository in repos["items"]:
            clone_url = repository.get("clone_url")
            print(f"Clonando {clone_url}")
            path_destinazione = f"{DIRECTORY}/{repository.get("name")}"

            Repo.clone_from(clone_url, path_destinazione)
            time.sleep(2)  # pausa tra un project e un altro per non sovraccaricare server Git (quindi per non farmi bloccare)'''

        for repository in repos:
            url = repository.get("clone_url")
            print(f"Clonando {url}")
            path_destinazione = f"{DIRECTORY}/{repository.get("name")}"

            Repo.clone_from(url, path_destinazione)
            time.sleep(2)   #pausa tra un project e un altro per non sovraccaricare server Git (quindi per non farmi bloccare)




    def creazione_progetti_Sonar(self):

        for repository in os.listdir(DIRECTORY):

            if repository.startswith("."):    #come cartella .git
                continue

            crea_progetto(repository)




    def risultati_pre_refactoring(self):

        for project in os.listdir(DIRECTORY):

            if project.startswith("."):  # come cartella .git
                continue

            restituisci_metriche_pre_kickoff(project)



    def risultati_post_refactoring(self):

        for project in os.listdir(DIRECTORY):

            if project.startswith("."):  # come cartella .git
                continue

            restituisci_metriche_post_kickoff(project)

        grafici(FILE_REPORT_PRE_REFACTORING, FILE_REPORT_POST_REFACTORING)







#validator = Validation()
#validator.clone_progetti_Git()
#validator.creazione_progetti_Sonar()
#validator.risultati()
#print(pd.read_csv("attributes_before_refactoring").to_string())

'''param = {
    "component": f"Progetto_gioco-oca-univaq-vmd",
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

    param2={
        "key": response.json().get("components")[0].get("key")
    }

    code = requests.get(f"http://localhost:9000/api/sources/raw", headers=HEADER, params=param2)
    #print(code)
    #print(code.text)
    project_root = f"{DIRECTORY}/gioco-oca-univaq-vmd"

    for root, _, files in os.walk(project_root):
        for file in files:
            full_path = os.path.join(root, file)
            if full_path.endswith(os.path.normpath(response.json()["components"][0]["path"])):
                found_path = full_path
                print(f"LOCAL PATH= {found_path}" + "\n\nCODE= " + code.text)
                break

except requests.exceptions.HTTPError as e:
    print(f"Errore HTTP ({e.response.status_code}), progetto non trovato: {e}")

except requests.exceptions.RequestException as e:
    print(f"Errore di rete o altro problema nella richiesta: {e}")'''

