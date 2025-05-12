import json
import os

import requests
from crewai import Agent, LLM
from crewai.tools.base_tool import Tool, BaseTool, tool
from crewai_tools.tools.code_docs_search_tool.code_docs_search_tool import CodeDocsSearchTool

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER


@tool("classe_peggiore")
def classe_peggiore():
    """
    Restituisce il path della classe con peggior security_rating via SonarQube.
    Effettua una GET su /api/measures/component_tree e ordina per security_rating.
    """
    param = {
        "component": f"ProgettoApache_codec",
        "metricKeys":  # "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
        # "reliability_rating,sqale_rating,security_rating,cognitive_complexity,"
        # "blocker_violations,critical_violations",
            "security_rating, vulnerabilities",
        "qualifiers": "FIL",
        "s": "metric",
        "metricSort": "security_rating",
        "ps": 1,
        "asc": "false"
    }
    try:
        response = requests.get("http://localhost:9000/api/measures/component_tree", headers=HEADER, params=param)

        response.raise_for_status()
        print(json.dumps(response.json(), indent=4))

        with open(f"{DIRECTORY}/codec/{response.json().get("components")[0].get("path")}", "r",
                  encoding="utf-8") as f:
            code = f.read()

        return code

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")
    # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate


#CLASSE PER PERSONALIZZAZIONE AGENTI
class CustomAgent:


    #NEL COSTRUTTORE è DEFINITO IL MODELLO UTILIZZATO DA TUTTI GLI AGENTI
    llm = LLM(
        model="gemini/gemini-1.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    '''def __init__(self, LLM):
        self.llm= LLM '''  #questo vale se voglio usare diversi llm per gli agenti


    def first_agent(self):
        return Agent(
            role="Searcher class",
            goal="To connect with SonarQube and research a specific class",
            backstory="Connect Internet via HTTP",
            llm=self.llm,
            tools=[classe_peggiore],   #una qualità in piu di quest'agente: sa fare chiamate API a SonarQube
            verbose=True
        )

    #@agent
    def second_agent(self):
        return Agent(
            role="Prompt generator",
            goal="Generate a prompt to improve the code. In particular to improve {quality_attributes_to_improve} of the code",
            backstory="Knowledge of best practices and prompt engineering techniques to formulate a highly optimized prompt.",
            llm=self.llm,
            input_keys=["quality_attributes_to_improve"],
            verbose=True
        )


    #@agent
    def third_agent(self):
       return Agent(
            role="Expert on code refactoring",
            goal="To improve, when possible, the code of first agent"
                 " without generate errors and keeping the licenses ",
            llm=self.llm,
            backstory="Knowledge of Java language (version 17), Java's best practise and Java structure (Maven)",
            #input_keys=["file_content"],
            toosls= CodeDocsSearchTool(),
            ##tools= [search_tool]  posso inserire un tool di ricerca su Google
            #knowledge_sources  per migliorare ancora di piu la conscenza di Java ???

            # possiamo specializzare questo agente assegnandogli il tool di ricerca web (importandolo da librerie di CrewAI o di LangChain)
            # questo significa che l'agente ha la "skill" di fare ricerche sul web e, quindi, non rispondere solamente in base alle sue conoscenze
            verbose=True
        )



    def third_agent(self):
        return Agent(
            role="SonarQube and Json expert",
            goal="With the input of the previous agent, this agent must "
                 "verify the quality attribues of the second agent's code with {sonar_json}",
            backstory="Code of the second agent",
            llm=self.llm,
            input_keys=["sonar_json"],
            verbose=True
            #function_calling_llm  per far fare questa task "piu leggera" ad un llm piu economico e veloce ???
        )

