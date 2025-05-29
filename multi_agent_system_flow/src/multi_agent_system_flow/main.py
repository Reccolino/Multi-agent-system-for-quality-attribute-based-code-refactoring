import json
import os
from typing import List, Optional

import requests
from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, or_, router

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER
from multi_agent_system_flow.src.multi_agent_system_flow.crews.refactor_crew.refactor_crew import RefactorCrew

TENTATIVI_MAX: int = 3

class ExampleFlow(BaseModel):
    project_list: List[str] = []      #lista di progetti
    current_project: Optional[int] = 0    #serve a indicare quale progetto si sta elaborando
    classi: List[dict] = []     #lista di classi di un progetto
    current_class: Optional[int] = 0    #serve a indicare quale classe del progetto si sta facendo refactoring
    path_class: str = ""     #path della classe da passare alla Crew per poter fare code replace e per poter eseguire sonarScanner
    code_class: str = ""     #codice della classe da passare alla Crew per poter fare refactoring
    errors: str = ""         #errori (di compilazione o altri) da passare alla Crew per indirizzare agente a non commetterli
    validate: str = ""       #flag che verifica se il comando da terminale per una classe ha restituito Build Success o Build Failure
    tentativi: Optional[int] = 0    #contatore per tenere traccia del numero di tentativi su una singola classe


class OriginalFlow(Flow[ExampleFlow]):

    @start()
    def init(self):
        """
        Metodo che carica tutti i progetti nella project_list. Da qui si potrà accedere ai singoli progetti e alle classi dei progetti
        """
        self.state.project_list = [repository for repository in os.listdir("./cloned_repos_lpo")]
        print(self.state.project_list)


    @router(or_("init", "classes_for_project", "refactor_code"))
    def router(self, _=None):
        """
        Il router guarda lo stato e restituisce il nome del prossimo metodo da eseguire.
        """

        #Se non ho ancora caricato le classi per un progetto
        if not self.state.classi:
            return "percorso_progetto"


        #Se ho ancora classi residue per questo progetto
        if self.state.current_class < len(self.state.classi):
            return "percorso_classe"


        #Ho processato tutte le classi di questo progetto:
        #passo al prossimo progetto (se esiste) o termino
        self.state.current_project += 1
        if self.state.current_project < len(self.state.project_list):
            # resetto le classi per il nuovo progetto
            self.state.classi = []
            self.state.current_class = 0
            return "percorso_progetto"
        else:
            print("Tutti i progetti sono stati elaborati.")




    @listen("percorso_progetto")
    def classes_for_project(self):
        """
            Restituisce: il path della classe con peggior security_rating via SonarQube e il codice di quella classe .
            Effettua una GET su /api/measures/component_tree e ordina per security_rating  .
        """

        param = {
            "component": f"Progetto_{self.state.project_list[self.state.current_project]}",
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
            self.state.classi = response.json().get("components")

        except requests.exceptions.HTTPError as e:
            print(f"Errore HTTP ({e.response.status_code}) durante la ricerca: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Errore di rete o altro problema nella richiesta: {e}")
        # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate



    @listen("percorso_classe")
    def esec_class(self):
        """
        Effettua un GET api/sources/raw per restituire il codice e il path da refattorizzare di una classe specifica
        """
        if self.state.tentativi < TENTATIVI_MAX:   #cosi evito di rifare chiamata api inutilmente

            # http://localhost:9000/api/sources/raw necessita della key del progetto come parametro (query string)  ==> la prendo dal JSON
            classe_attuale = self.state.classi[self.state.current_class]
            param2 = {
                "key": classe_attuale.get("key")
            }

            code = requests.get("http://localhost:9000/api/sources/raw", headers=HEADER, params=param2)
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

            project_root = f"{DIRECTORY}/{self.state.project_list[self.state.current_project]}"

            # PER PROGETTI LPO BISOGNA TROVARE PATH CORRETTO PERCHE NON è IMMEDIATO COME PROGETTI APACHE
            for root, _, files in os.walk(project_root):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    # uso normpath perche il json restituisce slash cosi: \ . Invece a me serve il path con slash cosi /
                    if full_file_path.endswith(os.path.normpath(self.state.classi[self.state.current_class].get("path"))):
                        self.state.path_class = full_file_path
                        print(f"LOCAL PATH: {self.state.path_class}" + f"\n\nCODE:\n  + {self.state.code_class}")



    @listen("esec_class")
    def refactor_code(self):

        print(f"\nElaborando progetto: {self.state.project_list[self.state.current_project]}")
        print(f"\nClasse: {self.state.classi[self.state.current_class]}")

        if self.state.tentativi < TENTATIVI_MAX:    #questo posso farlo anche nel router (anzi forse la devo farlo)

            result = RefactorCrew().crew().kickoff(inputs={"code_class": self.state.code_class, "path_class": self.state.path_class, "errors": self.state.errors})

            self.state.validate= result["valid"]   #prendo il valore di valid restituito dall'output_pydantic della Crew
            self.state.errors= result["errors"]    #prendo il valore di errors restituito dall'output_pydantic della Crew

            print(f"VALIDATE: +{self.state.validate}")
            print(f"ERRORS: +{self.state.errors}")

            if self.state.validate:  #vuol dire Build Success
                self.state.current_class += 1   #passa alla prossima classe

            else:  #Build Failure (errori di compilazione o altro tipo di errore)
                self.state.tentativi += 1   #aumenta numero di tentativi e riesegui il refactoring su stessa classe

        else:    #arrivato a N tentativi

            self.state.current_class +=1   #passa avanti con la classe
            self.state.validate = ""   #riazzero validate
            self.state.errors = ""   #riazzero errors
            self.state.tentativi = 0   #riazzero tentativi per la prossima classe







def kickoff():
    flow = OriginalFlow()
    flow.kickoff()


def plot():
    flow = OriginalFlow()
    flow.plot()


if __name__ == "__main__":
    kickoff()
    plot()
