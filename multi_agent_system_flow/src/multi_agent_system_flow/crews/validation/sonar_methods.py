import json
import random
import time

import requests

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import HEADER, \
    FILE_REPORT_PRE_REFACTORING, FILE_REPORT_POST_REFACTORING, METRIC_TO_REFACTOR
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.utility_methods import scanner_da_terminale, \
    search_pom, delete_locally, create_report



def create_project(project):
    url = "http://localhost:9000/api/projects/create"

    param = {
        "name": f"Project_{project}",
        "project": f"Project_{project}"
    }
    try:
        response = requests.post(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(f"Project_{project} created")
        pom_path = search_pom(project)

        if pom_path is not None:
           scanner_da_terminale(param, pom_path)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error({e.response.status_code}) during the creation of Project_{project}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")



def delete_project(project):
    url = "http://localhost:9000/api/projects/delete"

    param = {
        "project": f"Project_{project}"
    }

    try:
        response = requests.post(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(f"Project {project} delete from SonarQube")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error ({e.response.status_code}) during the deletion from SonarQube: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")



def returns_metrics_pre_kickoff(project):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"Project_{project}",
        "metricKeys": "ncloc,bugs,vulnerabilities,code_smells,coverage, test_success_density, test_failures,"
                      "duplicated_lines_density,"
                      "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
                      "blocker_violations,critical_violations"
    }
    '''
    POSSIBLE METRICS :
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


    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(response.json())

        measures = response.json().get("component").get("measures")

        # If the project is on SonarQube, but the scanner had issues,
        # then the project remains on Sonar without static code analysis.
        # This means it is a useless project that should be removed from Sonar (and locally).
        if not measures:
            print("Delete the project from SonarQube and locally because it did not pass SonarScanner")
            delete_project(project)
            delete_locally(project)
        else:
            metrics_dict = {item["metric"]: float(item["value"]) for item in measures if "value" in item}
            ncloc = metrics_dict.get("ncloc", 0.0)  # lines of code

            if ncloc < 800:
                print("Delete the project from SonarQube and locally because it has fewer than 800 lines of code")
                delete_project(project)
                delete_locally(project)
            else:
                create_report(response.json(), project, FILE_REPORT_PRE_REFACTORING)


    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        error_msg = error_response.get("errors", [{}])[0].get("msg", "No message")
        if "Component" in error_msg:
            print("Error: Project not found")
            delete_locally(project)
        elif "metric" in error_msg:
            print("Error: MetricKey not valid.")
        else:
            print(f"Unknown error: {error_msg}")
        # print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")
        return



def returns_metrics_post_kickoff(project):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"Project_{project}",
        "metricKeys": "ncloc,bugs,vulnerabilities,code_smells,coverage,test_success_density, test_failures,"
                      "duplicated_lines_density,"
                      "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
                      "blocker_violations,critical_violations"
    }
    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()

        create_report(response.json(), project, FILE_REPORT_POST_REFACTORING)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error ({e.response.status_code}) during the call: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")




def classes_for_project(project):

#-----------------------------------------RQ1/RQ2----------------------------------------------------------#
    '''url = "http://localhost:9000/api/components/tree"
    try:
        params = {
            "component": f"Project_{project}",
            "qualifiers": "FIL",
            "ps": 500
        }
        response = requests.get(url, headers=HEADER, params=params)
        comps = response.json()
        response.raise_for_status()
        all_files = comps["components"]
        return all_files


    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error ({e.response.status_code}) during the research: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")'''

#-------------------------------------------------------------------------------------------------------------#



#-----------------------------------------RESEARCH QUESTION 3--------------------------------------------------#

    url = "http://localhost:9000/api/measures/component_tree"
    param = {
        "component": f"Project_{project}",
        "metricKeys":  f"{METRIC_TO_REFACTOR}",
        "qualifiers": "FIL",
        "s": "metric",
        "metricSort": f"{METRIC_TO_REFACTOR}",
        "ps": 5,                    #here you cn modify the number of classes by sonarqube
        "asc": "false"
    }

    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))
        #print(response)
        return response

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error ({e.response.status_code}) during the research: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")


#---------------------------------------------------------------------------------------------------#



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
        print(f"HTTP Error ({e.response.status_code}) during the research: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")





def metrics(project):
    url = "http://localhost:9000/api/measures/component"
    param = {
        "component": f"Project_{project}",
        "metricKeys": f"{METRIC_TO_REFACTOR}"
    }


    try:
        response = requests.get(url, headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))
        #I have already done all the checks during the validation phase
        return response.json().get("component").get("measures")[0].get("value")

    except requests.exceptions.HTTPError as e:
        print(f"Unknown Error: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Network error or other issue in the request: {e}")



