import os
import shutil
import stat
import subprocess
from typing import Final

from git import Repo
import requests


BASE_URL= "https://github.com"
ORG_URL= "apache"
TOPIC_URL= "commons"
DIRECTORY= "./cloned_repos"

HEADER: Final[dict[str, str]] = {
    "Authorization": f"Bearer {os.getenv("SONAR_LOCAL_API_TOKEN")}"
}
#header che contiene il token di SonarQube, usato in tutte le chiamate API


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

'''
def clone_progetti_Git():
    for project in commons_projects:
        url = f"{BASE_URL}/{ORG_URL}/{TOPIC_URL}-{project}.git"
        path = f"./cloned_repos/{project}"
        print(f"Clonando {url}")
        Repo.clone_from(url, path, single_branch=True)'''
#QUESTO è UN CLONE MANUALE, POI ANDRA FATTO IN MODO DINAMICO MODELLANDO LA RICHIESTA A GIT TRAMITE response, header e API key
#PROBLEMA: l'api key di github supporta al max 60 richieste all'ora



def creazione_progetti_Sonar(directory):
    """
    Crea i progetti locali su SonarQube

    Args:
        directory: directory che contiene tutti i progetti salvati in locale

    """
    for repository in os.listdir(directory):

        if repository.startswith("."):    #come cartella .git
            continue

        param = {
            "name": f"ProgettoApache{repository}",
            "project": f"ProgettoApache{repository}"
        }
        response = requests.post(
            "http://localhost:9000/api/projects/create",
            headers= HEADER,
            params= param)

        if response.status_code==200:
            print("Progetto creato")
            scanner_da_terminale(param, os.path.join(directory, repository))
            #join: ./cloned_repos\codec, per esempio

        else:
            print("Problemi, Problemi, Problemi !!!")
            print(response.status_code)
            #break



def scanner_da_terminale(param, path):
    """
    Scrive su terminale il comando Maven_Sonar per poter fare lo scanner di ogni progetto

    Args:
        param: i parametri del progetto cosi che SonarQube lo riconosca e lo possa scannerizzare (nome, project_key)
        path: percoro su cui eseguire il comando

    """
    try:
        subprocess.run([
            "mvn.cmd", "clean", "verify", "sonar:sonar",
            f"-Dsonar.projectKey={param.get("project")}",
            f"-Dsonar.projectName={param.get("name")}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
        ],
            cwd=path,
            check=True)
        print("Analisi completata")
    except subprocess.CalledProcessError:
        print("Errore durante l'analisi")



def elimina_da_Sonar(progetto_da_eliminare):
    #ORA RIMUOVO DA SONARQUBE
    param = {
        "project": f"ProgettoApache{progetto_da_eliminare}"
    }
    response = requests.post("http://localhost:9000/api/projects/delete",
                           headers=HEADER,
                            params=param)

    print("WEEEE")
    if response.status_code==200:
        print(f"Progetto {progetto_da_eliminare} eliminato")
    else:
        print("Problemi nell'eliminazione da SonarQube")
        print(response)



def remove_readonly(func, path, _):
    """Rende scrivibile un file/cartella bloccata altrimenti la cancellazione di elimina_da_locale non funziona"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def elimina_da_locale(progetto_da_eliminare):
    path = f"{DIRECTORY}/{progetto_da_eliminare}"
    try:
        shutil.rmtree(path, onerror=remove_readonly)
        print(f"Directory rimossa: {path}")
    except Exception as e:
        print(f"Errore durante la rimozione finale di {path}: {e}")


def risultati(directory):
    """
    Visualizzazione dei risultati dell'analisi statica che SonarQube ha effettuato per ogni progetto

    Args:
        directory: directory che contiene tutti i progetti salvati in locale (non è detto anche su SonarQube)

    Return:
        Json dei risultati di ogni progetto
    """


    for project in os.listdir(directory):

        if project.startswith("."):  # come cartella .git
            continue

        # devi modellare l'url per farti restituire le metriche che ti interessano (metricKeys)
        # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate

        param={
            "component": f"ProgettoApache{project}",
            "metricKeys": "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density"
        }

        #al posto di fare due chiamate (una per vedere se il progetto è presente su Sonar e una per mostrare le metriche dei progetti)
        #ne faccio una sola che fa entrambe le funzioni: uso la chiamata delle metriche --> se mi restituisce 4040 significa che
        #il progetto non è presente su Sonar e, quindi, va eliminato
        response = requests.get(f"http://localhost:9000/api/measures/component",
                                headers=HEADER,
                                params=param)

        if response.status_code==200:
            print(f"L'analisi di {project} ha restituito: {response.json()}")


            #se il progetto è su SonarQube, ma lo scanner aveva dato problemi, allora quel progetto è rimasto su Sonar
            #ma senza l'analisi statica del codice. Questo significa che è un progetto inutile che va tolto da Sonar (e in locale)
            if not(response.json().get("component").get("measures")):
                print("Json vuoto")
                print("Elimina progetto da SonarQube e in locale")
                elimina_da_Sonar(project)
                elimina_da_locale(project)


                #TOD: QUI VA FATTO L'IF CON LA SOGLIA MASSIMA DELLE METRICHE DEI PROGETTI ---> DA FARE PIU AVANTI


        elif (response.status_code == 404):  # se il progetto è mancante la chiamat restituirà 404
            print("Progetto mancante in SonarQube  --> allora eliminalo in locale")
            elimina_da_locale(project)

        else:
            print("Altro problema")
            print(response)



#clone_progetti_Git()
#creazione_progetti_Sonar(DIRECTORY)
risultati(DIRECTORY)

