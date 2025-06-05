import os
import time
import warnings
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel

from crewai.flow.flow import Flow, listen, start, or_, router

from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.validation import DIRECTORY, Validation
from multi_agent_system_flow.src.multi_agent_system_flow.crews.refactor_crew.refactor_crew import RefactorCrew
from multi_agent_system_flow.src.multi_agent_system_flow.crews.validation.sonar_methods import classes_for_project, \
    esec_class, metrics

TENTATIVI_MAX: int = 3
tentativi_tot: int = 0

class ExampleFlow(BaseModel):
    project_list: List[str] = []      #lista di progetti
    current_project: Optional[int] = 0    #serve a indicare quale progetto si sta elaborando
    classi: List[dict] = []     #lista di classi di un progetto
    current_class: Optional[int] = 0    #serve a indicare quale classe del progetto si sta facendo refactoring
    path_class: str = ""     #path della classe da passare alla Crew per poter fare code replace e per poter eseguire sonarScanner
    code_class: str = ""     #codice della classe da passare alla Crew per poter fare refactoring
    errors: Optional[str] = ""         #errori (di compilazione o altri) da passare alla Crew per indirizzare agente a non commetterli
    validate: bool        #flag che verifica se il comando da terminale per una classe ha restituito Build Success o Build Failure
    tentativi: Optional[int] = 0    #contatore per tenere traccia del numero di tentativi su una singola classe
    value_metric_pre: Optional[int] = 0
    value_metric_post: Optional[int] = 0

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

        response = classes_for_project(self.state.project_list[self.state.current_project])
        all_components = response.json().get("components", [])

        filtered = [c for c in all_components if c.get("measures")]   #ho solo le classi che hanno effettivamente una measure
        #questo perchè può essere che un progetto abbia 1 solo vulnerabilities e il json mi restituisce le prime 3 classi
        #ma cosi mi restituisce la classe dove è presente effettivamente il vulnerabilities e altre 2 classi che non hanno problemi
        #quindi per quelle due che senso ha fare refactoring ?
        print(f"FILTERED {filtered}")
        self.state.classi = filtered
        #self.state.classi = response.json().get("components")     #carica le classi dal JSON




    @listen("percorso_classe")
    def esec_class(self):
        """
        Effettua un GET api/sources/raw per restituire il codice e il path da refattorizzare di una classe specifica
        """
        if self.state.tentativi < TENTATIVI_MAX:   #cosi evito di rifare chiamata api inutilmente

            # http://localhost:9000/api/sources/raw necessita della key del progetto come parametro (query string)  ==> la prendo dal JSON
            classe_attuale = self.state.classi[self.state.current_class]
            print(f"CLASSE ATTUALE= {classe_attuale}")
            code = esec_class(classe_attuale)

            self.state.code_class = code.text
            #print(f"CLASSE ATTUAL KEY {classe_attuale.get("key")}")
            self.state.value_metric_pre = int(metrics(classe_attuale.get("key")))

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
                        print(f"LOCAL PATH: {self.state.path_class}" + f"\nCODE:\n{self.state.code_class}")



    @listen("esec_class")
    def refactor_code(self):
        global tentativi_tot

        print(f"\nElaborando progetto: {self.state.project_list[self.state.current_project]}")
        print(f"\nClasse: {self.state.classi[self.state.current_class]}")

        if self.state.tentativi < TENTATIVI_MAX:

            #ovviamente alla prima iterazione self.state.scanner_result è vuoto, poi se al primo tentativo Build Failure allora
            #contiene gli errori che ha restituito SonarScanner
            result = RefactorCrew().crew().kickoff(
                inputs={"code_class": self.state.code_class, "path_class": self.state.path_class,
                        "errors": self.state.errors})


            self.state.validate = result["valid"]
            self.state.errors = result["errors"]
            self.state.value_metric_post = result["metric"]

            print(f"VALIDATE: {self.state.validate}")
            print(f"VALORE METRICA: {self.state.value_metric_pre}")


            if self.state.validate:  #vuol dire Build Success
                if self.state.value_metric_post <= self.state.value_metric_pre:   #c'è stato un miglioramento
                    print(f"VULNERABILITIES PRIMA: {self.state.value_metric_pre}")
                    print(f"VULNERABILITIES DOPO: {self.state.value_metric_post}")
                    self.state.tentativi += 1  #aumenta numero di tentativi e riesegui il refactoring su stessa classe
                    tentativi_tot += 1
                else:
                    self.state.current_class += 1   #passa alla prossima classe

            else:  #Build Failure (errori di compilazione o altro tipo di errore)
                self.state.tentativi += 1   #aumenta numero di tentativi e riesegui il refactoring su stessa classe
                tentativi_tot += 1

        else:    #arrivato a N tentativi
            print("\nClasse già iterata 3 volte, passa alla prossima classe o al prossimo progetto")
            self.state.current_class +=1   #passa avanti con la classe
            self.state.validate= ""
            self.state.errors= ""
            self.state.tentativi = 0   #riazzero tentativi per la prossima classe
            self.state.value_metric_pre = 0
            self.state.value_metric_post = 0



def kickoff():
    flow = OriginalFlow()
    flow.kickoff()


def plot():
    flow = OriginalFlow()
    flow.plot()


if __name__ == "__main__":
    #warnings.filterwarnings("ignore")


    validator = Validation()
# COMMENTA PROSSIME 4 RIGHE DOPO LA PRIMA ESECUZIONE !!!
    #validator.clone_progetti_Git()
    #validator.creazione_progetti_Sonar()
    #validator.risultati_pre_refactoring()
    #print(pd.read_csv("attributes_before_refactoring").to_string())
    start_time = time.time()
    kickoff()
    print(f"TENTATIVI TOTALI= {tentativi_tot}")
    end_time = time.time() - start_time
    print(f"Tempo di esecuzione TOTALE= {end_time}")

    plot()   #del Flow

    print(pd.read_csv("attributes_before_refactoring").to_string())
    validator.risultati_post_refactoring()
    print(pd.read_csv("attributes_post_refactoring").to_string())




