import os
import shutil
import stat
import subprocess

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import FILE_REPORT_PRE_REFACTORING, \
    FILE_REPORT_POST_REFACTORING
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY_REPOS


def scanner_da_terminale(param, path):
    """
    Scrive su terminale il comando Maven_Sonar per poter fare lo scanner di ogni progetto

    Args:
        param: i parametri del progetto cosi che SonarQube lo riconosca e lo possa scannerizzare (nome, project_key)
        path: percoro su cui eseguire il comando

    """
    #path = os.path.normpath(path)
    try:
        subprocess.run(["mvn.cmd", "jacoco:report"], cwd=path, check=False)


        comando = [
            "mvn.cmd", "clean", "install", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
            f"-Dsonar.projectKey={param.get("project")}",
            f"-Dsonar.projectName={param.get("name")}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
        ]

        jacoco_path = os.path.join(path, "target/site/jacoco/jacoco.xml")
        if os.path.exists(jacoco_path):    #PER I PROGETTI APACHE
            comando.append(f"-Dsonar.coverage.jacoco.xmlReportPaths={jacoco_path}")
        else:
            print("Nessun report JaCoCo trovato: la coverage non sarà inclusa in SonarQube.")

        subprocess.run(comando, cwd=path, check=True)
        print("Analisi completata")


    except subprocess.CalledProcessError:
        print("Errore durante l'analisi")



def search_pom(repository):
        print(repository)
        for type_folder in ("lpo", "apache"):
            project_root = os.path.join(str(DIRECTORY_REPOS), type_folder, repository)
            if not os.path.isdir(project_root):
                continue

            # cammina ricorsivamente a partire da cloned_repos/type_folder/repository
            for root, _, files in os.walk(project_root):
                if "pom.xml" in files:
                    print(f"Trovato pom.xml in: {root}")
                    return root
        return None


def remove_readonly(func, path, _):
    """Rende scrivibile un file/cartella bloccata altrimenti la cancellazione di elimina_da_locale non funziona"""
    os.chmod(path, stat.S_IWRITE)
    func(path)



def elimina_da_locale(progetto_da_eliminare):
    for root, dirs, _ in os.walk(DIRECTORY_REPOS):
        for d in dirs:
            if d == progetto_da_eliminare:
                path = os.path.join(root, d)
                try:
                    shutil.rmtree(path, onerror=remove_readonly)
                    print(f"Progetto eliminato: {path}")
                    return
                except Exception as e:
                    print(f"Errore durante la rimozione finale di {path}: {e}")
                    #return

    print(f"Progetto_{progetto_da_eliminare} non trovato in {DIRECTORY_REPOS}")



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




def final_report_excel():
    df_pre = pd.read_csv(FILE_REPORT_PRE_REFACTORING)
    df_post= pd.read_csv(FILE_REPORT_POST_REFACTORING)

    df_pre.to_excel(f"{FILE_REPORT_PRE_REFACTORING}.xlsx", index=False)
    df_post.to_excel(f"{FILE_REPORT_POST_REFACTORING}.xlsx", index=False)