#!/usr/bin/env python
import json
import os
from typing import List, Optional

import requests
from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, or_

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER
from multi_agent_system_flow.src.multi_agent_system_flow.crews.refactor_crew.refactor_crew import RefactorCrew


class ExampleFlow(BaseModel):
    project_list: List[str] = []
    current_project: Optional[int] = 0
    path_class: str = ""
    code_class: str = ""

class OriginalFlow(Flow[ExampleFlow]):

    @start()
    def init(self):
        self.state.project_list = [repository for repository in os.listdir("./cloned_repos_lpo")]

        return self.state.project_list[self.state.current_project]

    #l'or puo dare risultati indesiderati. Forse meglio usare @router e gestire meglio il flusso
    @listen(or_("init", "refactor_code"))
    def classe_peggiore(self, _):
        """
            Restituisce: il path della classe con peggior security_rating via SonarQube e il codice di quella classe .
            Effettua una GET su /api/measures/component_tree e ordina per security_rating e poi effettua un GET api/sources/raw per restituire il codice .
            """
        project = self.state.project_list[self.state.current_project]

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
            response = requests.get("http://localhost:9000/api/measures/component_tree", headers=HEADER, params=param)

            response.raise_for_status()
            print(json.dumps(response.json(), indent=4))

            # http://localhost:9000/api/sources/raw necessita della key del progetto come parametro (query string)  ==> la prendo dal JSON
            param2 = {
                "key": response.json().get("components")[0].get("key")
            }

            code = requests.get("http://localhost:9000/api/sources/raw", headers=HEADER, params=param2)
            # print(code)
            # print(code.text)
            self.state.code_class = code.text
            # COSI FACENDO NON INCORRO IN ERRORI DEL TIPO:
            # l'agente mi fa un refactoring errato (cioè che SonarScanner restituisce Build Failure e, quindi, il codice non viene aggiornato),
            # ma il code replace va a buon fine. Allora alla prossima esecuzione il codice in input
            # sarà proprio quello generato dall'esecuzione precedente perchè con il codice vecchio (quello commentato qui sotto) l'agente
            # prendeva in input sempre il codice della classe peggiore, ma salvata in locale, non da SonarQube.
            # Invece, cosi, l'agente prende in input SEMPRE il codice da SonarQube cosi che se ad una esecuione ci sono errori di compilazione, per esempio,
            # viene fatto si code replace in locale, ma tanto si prende in input il codice da SonarQube che non è cambiato
            '''with open(f"{DIRECTORY}/commons-codec/{response.json().get("components")[0].get("path")}", "r",
                      encoding="utf-8") as f:
                 code = f.read()'''

            project_root = f"{DIRECTORY}/{project}"

            # PER PROGETTI LPO BISOGNA TROVARE PATH CORRETTO PERCHE NON è IMMEDIATO COME PROGETTI APACHE
            for root, _, files in os.walk(project_root):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    # uso normpath perche il json restituisce slash cosi: \ . Invece a me serve il path con slash cosi /
                    if full_file_path.endswith(os.path.normpath(response.json()["components"][0]["path"])):
                        self.state.path_class = full_file_path
                        print(f"LOCAL PATH: {self.state.path_class}" + f"\n\nCODE:\n  + {self.state.code_class}")
                        return {
                            "path_class":self.state.path_class,
                            "code_class":self.state.code_class
                        }
            # PROBLEMA: è da gestire le classi
            # nel senso, se si avvia esecuzione e si vogliono far restituire, per esempio, 20 classi per progetto dalla prima chiamata,
            # l'agente ogni volta mi eseguirà sempre la prima classe, quindi, probabilmente, dovrò gestire il fatto che una classe
            # è stata già esaminata (è stato fatto code refactoring, sia che sia andato a buon fine che non)
            # e che quindi si deve passare alla classe successiva
        except requests.exceptions.HTTPError as e:
            print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Errore di rete o altro problema nella richiesta: {e}")
        # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate



    @listen("classe_peggiore")
    def refactor_code(self, data):
        path_class = data["path_class"]
        code_class = data["code_class"]

        print(f"Elaborando progetto: {self.state.project_list[self.state.current_project]}")

        try:
            result = RefactorCrew().crew().kickoff(inputs={"code_class": code_class, "path_class": path_class})
            print(result.raw)
        except Exception as e:
            print(f"Errore durante il kickoff del crew: {e}")


        self.state.current_project += 1
        if self.state.current_project < len(self.state.project_list):
            next_project = self.state.project_list[self.state.current_project]
            return self.classe_peggiore(next_project)
        else:
            print("Tutti i progetti sono stati elaborati.")
            return None
        # return result.raw


def kickoff():
    flow = OriginalFlow()
    flow.kickoff()


def plot():
    flow = OriginalFlow()
    flow.plot()


if __name__ == "__main__":
    kickoff()
    plot()
