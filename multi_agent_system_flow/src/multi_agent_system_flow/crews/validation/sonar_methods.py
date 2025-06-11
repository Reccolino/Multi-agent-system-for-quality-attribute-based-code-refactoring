import json
import random

import requests

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import HEADER, \
    FILE_REPORT_PRE_REFACTORING, FILE_REPORT_POST_REFACTORING
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.utility_methods import scanner_da_terminale, \
    search_pom, elimina_da_locale, crea_report


def crea_progetto(project):
    url = "http://localhost:9000/api/projects/create"

    param = {
        "name": f"Progetto_{project}",
        "project": f"Progetto_{project}"
    }
    try:
        response = requests.post(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(f"Progetto_{project} creato")
        pom_path = search_pom(project)
        scanner_da_terminale(param, pom_path)  # os.path.join(DIRECTORY, pom_path))

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_{project}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")



def elimina_progetto(project):
    url = "http://localhost:9000/api/projects/delete"

    param = {
        "project": f"Progetto_{project}"
    }

    try:
        response = requests.post(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(f"Progetto {project} eliminato da SonarQube")

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante l'eliminazione da SonarQube: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")



def restituisci_metriche_pre_kickoff(project):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"Progetto_{project}",
        "metricKeys": "ncloc,bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
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

    # al posto di fare due chiamate (una per vedere se il progetto è presente su Sonar e una per mostrare le metriche dei progetti)
    # ne faccio una sola che fa entrambe le funzioni: uso la chiamata delle metriche --> se mi restituisce 4040 significa che
    # il progetto non è presente su Sonar e, quindi, va eliminato

    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        # in questo caso 404 non mi deve generare l'eccezione: voglio esplicitamente controllare
        # se la response sia 404 per eliminare il progetto

        # SUPPONENDO che l'url sia corretto (se una metricKey è sbagliata ritorna 404 anche in quel caso) --> forse è da migliorare
        # if response.status_code == 404:  # se il progetto è mancante la chiamata restituirà 404
        #  print("Progetto mancante in SonarQube  --> allora va eliminato in locale")
        #  self.elimina_da_locale(project)
        # return

        # print(f"L'analisi di {project} ha restituito: {response.json()}")
        # print(response.json().get("component").get("measures")[2].get("value"))
        # se il progetto è su SonarQube, ma lo scanner aveva dato problemi, allora quel progetto è rimasto su Sonar
        # ma senza l'analisi statica del codice. Questo significa che è un progetto inutile che va tolto da Sonar (e in locale)
        if not (response.json().get("component").get("measures")):
            # print("Json vuoto")
            print("Elimina progetto da SonarQube e in locale perchè non ha passato il SonarScanner")
            elimina_progetto(project)
            elimina_da_locale(project)

        elif int(response.json().get("component").get("measures")[8].get("value")) < 800:
            print("Elimina progetto da SonarQube e in locale perchè ha meno di 800 righe di codice")
            elimina_progetto(project)
            elimina_da_locale(project)

        else:
            crea_report(response.json(), project, FILE_REPORT_PRE_REFACTORING)


    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        error_msg = error_response.get("errors", [{}])[0].get("msg", "No message")
        if "Component" in error_msg:
            print("Errore: Progetto non trovato.")
            elimina_da_locale(project)
        elif "metric" in error_msg:
            print("Errore: MetricKey non valida.")
        else:
            print(f"Errore sconosciuto: {error_msg}")
        # print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")
        return



def restituisci_metriche_post_kickoff(project):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"Progetto_{project}",
        "metricKeys": "ncloc,bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
                      "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
                      "blocker_violations,critical_violations"
    }
    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()

        crea_report(response.json(), project, FILE_REPORT_POST_REFACTORING)

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la chiamata: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")

    '''try:
        new_code_params = param.copy()
        new_code_params.update({
            "metricKeys": "new_ncloc,new_bugs,new_vulnerabilities,new_code_smells,new_coverage,new_duplicated_lines_density,"
                          "new_reliability_rating,new_sqale_rating,new_security_rating,new_cognitive_complexity,"
                          "new_blocker_violations,new_critical_violations",
            "additionalFields": "period",
            #"strategy": "new_code_period"
        })

        response = requests.get(url, headers=HEADER, params=new_code_params)
        response.raise_for_status()
        crea_report(response.json(), project, FILE_REPORT_POST_REFACTORING_NEW_CODE)

    except requests.exceptions.HTTPError as e:
        print(f"[NEW CODE] Errore HTTP ({e.response.status_code}): {e}")
    except requests.exceptions.RequestException as e:
        print(f"[NEW CODE] Errore di rete: {e}")'''



def classes_for_project(project):

    #PER LA RQ1 PRENDO IN MODO RANDOMICO 4 CLASSI
    url = "http://localhost:9000/api/components/tree"
    try:
        params = {
            "component": f"Progetto_{project}",
            "qualifiers": "FIL",
            "ps": 500
        }
        response = requests.get(url, headers=HEADER, params=params)
        comps = response.json()
        response.raise_for_status()
        #print(json.dumps(response.json(), indent=4))
        all_files = comps["components"]

        #filtro SOLO classi JAVA (quindi NO classi xml o altre estensioni)
        java_files = [file for file in all_files if file["path"].endswith(".java")]

        if len(java_files) >= 6:
            random_classes = random.sample(java_files, k=6)
        #random_classes = random.sample(comps["components"], k=6)
            return random_classes

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")


    # PER LA RQ2 PRENDO LE CLASSI IN BASE ALL'ORDINAMENTO DI UNA METRICA SCELTA
    '''url = "http://localhost:9000/api/measures/component_tree"
    param = {
        "component": f"Progetto_{project}",
        "metricKeys":  # "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
        # "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
        # "blocker_violations,critical_violations",
            "vulnerabilities",
        "qualifiers": "FIL",
        "s": "metric",
        "metricSort": "vulnerabilities",
        "ps": 4,
        "asc": "false"
    }
    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))
        #print(response)
        return response'''




def esec_class(classe):
    url = "http://localhost:9000/api/sources/raw"

    param = {
        "key": classe.get("key")
    }

    try:

        response = requests.get(url, headers=HEADER, params=param)
        #print(json.dumps(response.json(), indent=4))
        response.encoding = 'utf-8'
        #print(response)
        return response

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")





def metrics(classe):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"{classe}",

        "metricKeys": "vulnerabilities"
    }


    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))
        #i controlli li ho già fatti tutti nella fase di validation
        return response.json().get("component").get("measures")[0].get("value")

    except requests.exceptions.HTTPError as e:
        print(f"Errore sconosciuto: {e}")
        # print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")
        #return


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