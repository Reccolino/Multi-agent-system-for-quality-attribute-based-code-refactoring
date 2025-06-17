import json
import os
import time
from abc import ABC, abstractmethod
from typing import Final
from git import Repo
import requests

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import header_git, DIRECTORY_REPOS, \
    APACHE_PATH, LPO_PATH
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import crea_progetto, \
     restituisci_metriche_pre_kickoff, restituisci_metriche_post_kickoff
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.utility_methods import final_report_excel


class BaseValidation(ABC):

   @abstractmethod
   def clone_progetti_apache(self):
       pass

   @abstractmethod
   def clone_progetti_lpo(self):
       pass

   #i clone li tengo separati perchè hanno una logica leggermente diversa nella lettura del JSON (anche se era
   #possibile crere un solo metodo e controllare la directory con un if, ma si è preferiti fare cosi)

   @abstractmethod
   def creazione_progetti_Sonar(self, directory):
       """
       Crea i progetti locali su SonarQube
       Args:
           directory: directory che contiene tutti i progetti salvati in locale
       """
       pass

   @abstractmethod
   def risultati_pre_refactoring(self, directory):
       """
       Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto.
       Pulizia dei progetti: eliminazione di quelli non significativi ai fini dell'approccio

       Return:
          Dataframe con i risultati pre refactoring
       """
       pass

   @abstractmethod
   def risultati_post_refactoring(self, directory):
       """
       Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto, dopo il refactoring del MAS.
       Creazione grafici per trovare differenze fra prima e dopo refactoring.
       """
       pass




class Validation(BaseValidation):



    def clone_progetti_apache(self):

        repos_url= "https://api.github.com/search/repositories?q=apache+commons+language:java&per_page=10"

        response = requests.get(repos_url, headers=header_git)
        repos = response.json()
        #path = f"{DIRECTORY_REPOS}"
        #print(json.dumps(repos, indent=3))

        for repository in repos["items"]:
            clone_url = repository.get("clone_url")
            print(f"Clonando {clone_url}")
            path_destinazione = f"{DIRECTORY_REPOS}{APACHE_PATH}{repository.get("name")}"

            Repo.clone_from(clone_url, path_destinazione)
            time.sleep(2)  # pausa tra un project e un altro per non sovraccaricare server Git (quindi per non farmi bloccare)




    def clone_progetti_lpo(self):
        repos_url = f"https://api.github.com/orgs/LPODISIM2024/repos?type=private"

        response = requests.get(repos_url, headers=header_git)
        repos = response.json()
        # path = f"{DIRECTORY_REPOS}"
        # print(json.dumps(repos, indent=3))

        for repository in repos:
            url = repository.get("clone_url")
            print(f"Clonando {url}")
            path_destinazione = f"{DIRECTORY_REPOS}{LPO_PATH}{repository.get("name")}"

            Repo.clone_from(url, path_destinazione)
            time.sleep(2)  # pausa tra un project e un altro per non sovraccaricare server Git (quindi per non farmi bloccare)



    def creazione_progetti_Sonar(self, dir):

        for repository in os.listdir(dir):

            if repository.startswith("."):    #come cartella .git
                continue

            crea_progetto(repository)




    def risultati_pre_refactoring(self, dir):

        for project in os.listdir(dir):

            if project.startswith("."):  # come cartella .git
                continue

            restituisci_metriche_pre_kickoff(project)



    def risultati_post_refactoring(self, dir):

        for project in os.listdir(dir):

            if project.startswith("."):  # come cartella .git
                continue

            restituisci_metriche_post_kickoff(project)

        final_report_excel()


