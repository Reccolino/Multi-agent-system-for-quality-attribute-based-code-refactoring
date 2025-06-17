import os
import shutil
import stat
import subprocess
import pandas as pd

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.costants import FILE_REPORT_PRE_REFACTORING, \
    FILE_REPORT_POST_REFACTORING
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY_REPOS


def scanner_da_terminale(param, path):
    """
    Writes to the terminal the Maven_Sonar command to run the scanner on each project.

    Args:
        param: project parameters so that SonarQube can recognize and scan it (name, project_key)
        path: path where to execute the command
    """

    #path = os.path.normpath(path)
    try:
        subprocess.run(["mvn.cmd", "clean", "install", "verify"], cwd=path, check=True)
        subprocess.run(["mvn.cmd", "jacoco:report"], cwd=path, check=False)

        jacoco_path = os.path.join(path, "target/site/jacoco/jacoco.xml")

        comando = [
            "mvn.cmd", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
            f"-Dsonar.projectKey={param.get("project")}",
            f"-Dsonar.projectName={param.get("name")}",
            f"-Dsonar.host.url=http://localhost:9000",
            f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}"
        ]


        if os.path.exists(jacoco_path):    #PER I PROGETTI APACHE
            comando.append(f"-Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml")
        else:
            print("No JaCoCo report found: coverage will not be included in SonarQube")

        subprocess.run(comando, cwd=path, check=True)
        print("Analysis completed")


    except subprocess.CalledProcessError:
        print("Error during the analysis")



def search_pom(repository):
        print(repository)
        for type_folder in ("lpo", "apache"):
            project_root = os.path.join(str(DIRECTORY_REPOS), type_folder, repository)
            if not os.path.isdir(project_root):
                continue

            for root, _, files in os.walk(project_root):
                if "pom.xml" in files:
                    print(f"Founded pom.xml in: {root}")
                    return root
        return None


def remove_readonly(func, path, _):
    """Makes a locked file/folder writable; otherwise, deletion in elimina_da_locale won't work."""

    os.chmod(path, stat.S_IWRITE)
    func(path)



def delete_locally(project_to_delete):
    for root, dirs, _ in os.walk(DIRECTORY_REPOS):
        for d in dirs:
            if d == project_to_delete:
                path = os.path.join(root, d)
                try:
                    shutil.rmtree(path, onerror=remove_readonly)
                    print(f"Project deleted: {path}")
                    return
                except Exception as e:
                    print(f"Error during the final removal of {path}: {e}")
                    #return

    print(f"Project_{project_to_delete} not found in {DIRECTORY_REPOS}")



def create_report(data_json, project, data_file):

    metrics_values = {}

    for measure in data_json["component"]["measures"]:
        metrics = measure.get("metric")
        metrics_values[metrics] = measure.get("value", "N/A")

    dati = {
        "Project": [project],
        "Coverage": [metrics_values.get("coverage", "N/A")],
        "Vulnerabilities": [metrics_values.get("vulnerabilities", "N/A")],
        "Security Rating": [metrics_values.get("security_rating", "N/A")],
        "Bugs": [metrics_values.get("bugs", "N/A")],
        "Reliabilty Rating":  [metrics_values.get("reliability_rating", "N/A")],
        "Code Smells": [metrics_values.get("code_smells", "N/A")],
        "Maintainability Rating": [metrics_values.get("sqale_rating", "N/A")],
        "Cognitive Complexity":  [metrics_values.get("cognitive_complexity", "N/A")],
        "Duplicated Lines Density": [metrics_values.get("duplicated_lines_density", "N/A")],
        "Blocker Violations": [metrics_values.get("blocker_violations", "N/A")],
        "Critical Violations": [metrics_values.get("critical_violations", "N/A")]
    }

    df = pd.DataFrame(dati)
    file_exist = os.path.isfile(data_file)
    #if the file .csv already exist, don't repeat Header (Project, Bugs, Coverage, ecc..)
    df.to_csv(f"{data_file}",mode='a', index=False, header=not file_exist)




def final_report_excel():
    df_pre = pd.read_csv(FILE_REPORT_PRE_REFACTORING)
    df_post= pd.read_csv(FILE_REPORT_POST_REFACTORING)

    df_pre.to_excel(f"{FILE_REPORT_PRE_REFACTORING}.xlsx", index=False)
    df_post.to_excel(f"{FILE_REPORT_POST_REFACTORING}.xlsx", index=False)