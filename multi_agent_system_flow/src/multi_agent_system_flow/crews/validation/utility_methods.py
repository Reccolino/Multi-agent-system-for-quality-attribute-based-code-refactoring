import os
import shutil
import stat
import subprocess

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY


def scanner_da_terminale(param, path):
    """
    Scrive su terminale il comando Maven_Sonar per poter fare lo scanner di ogni progetto

    Args:
        param: i parametri del progetto cosi che SonarQube lo riconosca e lo possa scannerizzare (nome, project_key)
        path: percoro su cui eseguire il comando

    """
    try:
        subprocess.run([
            # PER PROGETTI LPO STUDENTI
            "mvn.cmd", "clean", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
            f"-Dsonar.projectKey={param.get("project")}",
            f"-Dsonar.projectName={param.get("name")}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",

            # PER PROGETTI APACHE CON JACOCO
            # "mvn.cmd", "clean", "verify", "jacoco:report", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
            # f"-Dsonar.projectKey={param.get("project")}",
            # f"-Dsonar.projectName={param.get("name")}",
            # f"-Dsonar.host.url=http://localhost:9000",
            # f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",
            # "-Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml"

        ],

            # PER PROGETTI APACHE SENZA JACOCO
            # "mvn.cmd", "clean", "verify", "sonar:sonar",
            # f"-Dsonar.projectKey={param.get("project")}",
            # f"-Dsonar.projectName={param.get("name")}",
            # f"-Dsonar.host.url=http://localhost:9000",
            # f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
            # ],
            cwd=path,
            check=True)
        print("Analisi completata")
    except subprocess.CalledProcessError:
        print("Errore durante l'analisi")



def search_pom(repository):
        print(repository)
        print(f"{DIRECTORY}/{repository}")
        for root, dir, files in os.walk(f"{DIRECTORY}/{repository}"):
            if "pom.xml" in files:
                return root



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
        #return



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




def grafici(file_pre_refactoring, file_post_refactoring):

    before = pd.read_csv(file_pre_refactoring)
    after = pd.read_csv(file_post_refactoring)

    metrics = ["Security Rating", "Vulnerabilities", "Bugs", "Code Smells", "Duplicated Lines Density", "Cognitive Complexity"]
    projects = before["Progetto"]
    n_projects = len(projects)
    n_metrics = len(metrics)

    # Posizioni x
    index = np.arange(n_projects)
    bar_width = 0.35
    spacing = 0.15  # spazio tra gruppi di barre per ogni metrica

    # Imposta dimensione dinamica del grafico
    fig, ax = plt.subplots(figsize=(14, 6))

    # Colori diversi per ogni metrica
    colors = ['skyblue', 'lightgreen', 'salmon', 'gold', 'orchid']

    # Offset per ogni metrica (per affiancarle)
    for i, metric in enumerate(metrics):
        before_vals = before[metric]
        after_vals = after[metric]

        # Calcolo posizione orizzontale (shift per ogni metrica)
        pos = index + (i - n_metrics / 2) * (bar_width + spacing / n_metrics)

        ax.bar(pos, before_vals, bar_width, label=f"{metric} (Prima)", color=colors[i], alpha=0.6)
        ax.bar(pos + bar_width, after_vals, bar_width, label=f"{metric} (Dopo)", color=colors[i], alpha=1.0)

    # Etichette e layout
    ax.set_title("Confronto metriche di qualità - Prima vs Dopo Refactoring")
    ax.set_xlabel("Progetto")
    ax.set_ylabel("Valore")
    ax.set_xticks(index)
    ax.set_xticklabels(projects, rotation=45, ha="right")
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.show()