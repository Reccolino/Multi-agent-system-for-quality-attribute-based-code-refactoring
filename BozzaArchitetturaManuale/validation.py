import json
import os
import shutil
import stat
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Final

import pandas as pd
from git import Repo
import requests

#puoi creare Singleton che esegue tutti questi metodi per un'unica istanza

BASE_URL= "https://github.com"
ORG_URL= "apache"
TOPIC_URL= "commons"
DIRECTORY= "./cloned_repos"
_FILE_REPORT = "attributes_before_refactoring"   #attributo privato

#header che contiene il token di SonarQube, usato in tutte le chiamate API
HEADER: Final[dict[str, str]] = {
    "Authorization": f"Bearer {os.getenv("SONAR_LOCAL_API_TOKEN")}"
}

commons_projects = [
    "lang",
    "io",
    "math",
    "compress",
    "collections",
    "codec",
    "cli",
    "logging",
    "beanutils",
    "configuration",
    "validator",
]


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
   def risultati(self):
       """
       Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto
       Args:
          directory: directory che contiene tutti i progetti salvati in locale (non è detto anche su SonarQube)
       Return:
          Dataframe con i risultati
       """
       pass




class Validation(BaseValidation):


    def clone_progetti_Git(self):
        for project in commons_projects:
            url = f"{BASE_URL}/{ORG_URL}/{TOPIC_URL}-{project}.git"
            path = f"{DIRECTORY}/{project}"
            print(f"Clonando {url}")
            Repo.clone_from(url, path, recurse_submodules=True)
            time.sleep(2)   #pausa tra un project e un altro per non sovraccaricare server Git (quindi per non farmi bloccare)

            #repo = Repo.clone_from(url, path, recurse_submodules=True)  #!!!!!!
            #repo.submodule_update(recursive=True, init=True)  #!!!!!

    #QUESTO è UN CLONE MANUALE, POI ANDRA FATTO IN MODO DINAMICO MODELLANDO LA RICHIESTA A GIT TRAMITE response, header e API key
    #PROBLEMA: l'api key di github supporta al max 60 richieste all'ora



    def creazione_progetti_Sonar(self):

        for repository in os.listdir(DIRECTORY):

            if repository.startswith("."):    #come cartella .git
                continue

            param = {
                "name": f"ProgettoApache_{repository}",
                "project": f"ProgettoApache_{repository}"
            }

            url = "http://localhost:9000/api/projects/create"

            try:
               response = requests.post(url, headers= HEADER, params= param)

               response.raise_for_status()
               print(f"ProgettoApache_{repository} creato")
               self.scanner_da_terminale(param, os.path.join(DIRECTORY, repository))

            except requests.exceptions.HTTPError as e:
               print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_{repository}: {e}")

            except requests.exceptions.RequestException as e:
               print(f"Errore di rete o altro problema nella richiesta: {e}")


    @staticmethod
    def scanner_da_terminale(param, path):
        """
        Scrive su terminale il comando Maven_Sonar per poter fare lo scanner di ogni progetto

        Args:
            param: i parametri del progetto cosi che SonarQube lo riconosca e lo possa scannerizzare (nome, project_key)
            path: percoro su cui eseguire il comando

        """
        try:
            subprocess.run([
                "mvn.cmd", "clean", "verify", "jacoco:report", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
                f"-Dsonar.projectKey={param.get("project")}",
                f"-Dsonar.projectName={param.get("name")}",
                f"-Dsonar.host.url=http://localhost:9000",
                f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",
                "-Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml"

            ],

            #"mvn.cmd", "clean", "verify", "sonar:sonar",
             #   f"-Dsonar.projectKey={param.get("project")}",
              #  f"-Dsonar.projectName={param.get("name")}",
               # f"-Dsonar.host.url=http://localhost:9000",
                #f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
            #],
                cwd=path,
                check=True)
            print("Analisi completata")
        except subprocess.CalledProcessError:
            print("Errore durante l'analisi")


    @staticmethod
    def elimina_da_Sonar(progetto_da_eliminare):

        param = {
            "project": f"ProgettoApache_{progetto_da_eliminare}"
        }
        url = "http://localhost:9000/api/projects/delete"

        try:
            response = requests.post(url, headers=HEADER, params=param)

            response.raise_for_status()
            print(f"Progetto {progetto_da_eliminare} eliminato da SonarQube")

        except requests.exceptions.HTTPError as e:
            print(f"Errore HTTP ({e.response.status_code}) durante l'eliminazione da SonarQube: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Errore di rete o altro problema nella richiesta: {e}")


    @staticmethod
    def remove_readonly(func, path, _):
        """Rende scrivibile un file/cartella bloccata altrimenti la cancellazione di elimina_da_locale non funziona"""
        os.chmod(path, stat.S_IWRITE)
        func(path)


    @staticmethod
    def elimina_da_locale(progetto_da_eliminare):
        path = f"{DIRECTORY}/{progetto_da_eliminare}"

        try:
            shutil.rmtree(path, onerror=Validation.remove_readonly)
            print(f"Directory rimossa: {path}")
        except Exception as e:
            print(f"Errore durante la rimozione finale di {path}: {e}")
            #return


    @staticmethod
    def crea_report(data_json, project, data_file):

        valori_metriche = {}

        for measure in data_json["component"]["measures"]:
            metrica = measure.get("metric")
            valori_metriche[metrica] = measure.get("value", "N/A")

        dati = {
            "Progetto": [project],
            "Coverage": [valori_metriche.get("coverage", "N/A")],
            "Vulnerabilities": [valori_metriche.get("vulnerabilities", "N/A")],
            "Security Rating": [valori_metriche.get("security_rating", "N/A")],
            "Bugs": [valori_metriche.get("bugs", "N/A")],
            "Reliabilty Rating":  [valori_metriche.get("reliability_rating", "N/A")],
            "Code Smells": [valori_metriche.get("code_smells", "N/A")],
            "Maintainability Rating": [valori_metriche.get("sqale_rating", "N/A")],
            "Cognitive Complexity":  [valori_metriche.get("cognitive_complexity", "N/A")],
            "Duplicated Lines Density": [valori_metriche.get("duplicated_lines_density", "N/A")],
            "Blocker Violations": [valori_metriche.get("blocker_violations", "N/A")],
            "Critical Violations": [valori_metriche.get("critical_violations", "N/A")]
        }

        df = pd.DataFrame(dati)
        file_esiste = os.path.isfile(data_file)
        #se il file .csv esiste già allora non ripetere l'header (Progetto, Bugs, Coverage, ecc...)
        df.to_csv(f"{data_file}",mode='a', index=False, header=not file_esiste)



    def risultati(self):

        for project in os.listdir(DIRECTORY):

            if project.startswith("."):  # come cartella .git
                continue

            # devi modellare l'url per farti restituire le metriche che ti interessano (metricKeys)
            # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate

            param={
                "component": f"ProgettoApache_{project}",
                "metricKeys": "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
                              "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
                              "blocker_violations,critical_violations"
            }
            '''
            Size:
            ncloc, files, functions, classes, directories
            Complexity:
            complexity, cognitive_complexity, function_complexity
            Coverage:
            coverage, line_coverage, branch_coverage, lines_to_cover
            Duplication:
            duplicated_lines_density, duplicated_blocks, duplicated_files
            Reliability:
            bugs, new_bugs, reliability_rating
            Maintainability:
            code_smells, new_maintainability_rating
            Security:
            vulnerabilities, new_vulnerabilities, security_rating
            Test:
            tests, test_success_density, test_errors, test_failures
            Documentation:
            comment_lines, comment_lines_density
            Technical Debt:
            sqale_index(technical debt in minutes), sqale_debt_ratio, sqale_rating
            Issues:
            blocker_violations, critical_violations, major_violations, minor_violations
            Quality Gate:
            alert_status, quality_gate_details'''

            #al posto di fare due chiamate (una per vedere se il progetto è presente su Sonar e una per mostrare le metriche dei progetti)
            #ne faccio una sola che fa entrambe le funzioni: uso la chiamata delle metriche --> se mi restituisce 4040 significa che
            #il progetto non è presente su Sonar e, quindi, va eliminato

            url = "http://localhost:9000/api/measures/component"

            try:
                response = requests.get(url, headers=HEADER, params=param)

                #response.raise_for_status()
                #in questo caso 404 non mi deve generare l'eccezione: voglio esplicitamente controllare
                #se la response sia 404 per eliminare il progetto

                #SUPPONENDO che l'url sia corretto (se una metricKey è sbagliata ritorna 404 anche in quel caso) --> forse è da migliorare
                if response.status_code == 404:  # se il progetto è mancante la chiamata restituirà 404
                    print("Progetto mancante in SonarQube  --> allora va eliminato in locale")
                    self.elimina_da_locale(project)
                    #return

                #print(f"L'analisi di {project} ha restituito: {response.json()}")

                #se il progetto è su SonarQube, ma lo scanner aveva dato problemi, allora quel progetto è rimasto su Sonar
                #ma senza l'analisi statica del codice. Questo significa che è un progetto inutile che va tolto da Sonar (e in locale)
                if not(response.json().get("component").get("measures")):
                    print("Json vuoto")
                    print("Elimina progetto da SonarQube e in locale")
                    self.elimina_da_Sonar(project)
                    self.elimina_da_locale(project)

                else :
                    self.crea_report(response.json(), project, _FILE_REPORT)

                            #TODo: QUI VA FATTO L'IF (MINING) CON LA SOGLIA MASSIMA DELLE METRICHE DEI PROGETTI ---> DA FARE PIU AVANTI

            except requests.exceptions.RequestException as e:
                 print(f"Errore di rete o altro problema nella richiesta: {e}")
                 return

        print(pd.read_csv("attributes_before_refactoring").to_string())



validation = Validation()
#validation.clone_progetti_Git()
#validation.creazione_progetti_Sonar()
#validation.risultati()

