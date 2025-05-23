import json
import os
import subprocess

import requests
from crewai import Agent, LLM
from crewai.tools.base_tool import tool
from crewai_tools.tools.code_interpreter_tool.code_interpreter_tool import CodeInterpreterTool
from litellm import completion
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import ModelResponse

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

        return (f"LOCAL PATH= {DIRECTORY}/codec/{response.json().get("components")[0].get("path")}"
                +"\n\nCODE= "+code)

    except requests.exceptions.HTTPError as e:
        print(f"Errore HTTP ({e.response.status_code}) durante la creazione di ProgettoApache_codec: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Errore di rete o altro problema nella richiesta: {e}")
    # "http://localhost:9000/api/qualitygates/project_status?projectKey=progetto-java"  ULR per vedere se il progetto passa il Quality Gate



@tool("code_replace")
def code_replace(class_path: str, refactored_code: str) -> str:
    """
    Sovrascrive il file Java in class_path con il contenuto refactored_code,
    usando scrittura atomica (tmp + os.replace).
    Ritorna un messaggio di successo o solleva errore.
    """
    tmp = class_path + ".tmp"
    try:
        # Scrittura atomica
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(refactored_code)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, class_path)
        return f"Code replace completato in {class_path}"
    except Exception as e:
        return f"Errore durante code replace: {e}"


@tool("sonar_scanner")
def sonar_scanner(class_path: str):
    """
    Esegue comandi Maven e di SonarScanner nella root del progetto
    :param class_path:
    :return:
    """
    directory = class_path.split('/')[2]
    try:
        subprocess.run([
            "mvn.cmd", "clean", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar", "-X",
             f"-Dsonar.projectKey=ProgettoApache_{directory}",
             f"-Dsonar.projectName=ProgettoApache_{directory}",
             f"-Dsonar.host.url=http://localhost:9000",
             f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",
             "-DskipTests"
             ],
            cwd=os.path.join("cloned_repos", directory),
            check=True
        )
    except subprocess.CalledProcessError:
        print("Errore durante l'analisi")

#CLASSE PER PERSONALIZZAZIONE AGENTI
class CustomAgent:


    #NEL COSTRUTTORE è DEFINITO IL MODELLO UTILIZZATO DA TUTTI GLI AGENTI
    llm = LLM(
        model="gemini/gemini-1.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        max_tokens=128000,
        stream=True
    )

    '''def __init__(self, LLM):
        self.llm= LLM '''  #questo vale se voglio usare diversi llm per gli agenti


    def first_agent(self):    #STESSO AGENTE CHE FARà CHIAMATA API PER VERIFICARE QUALITY GATES
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
            goal="Generate precise prompts that guide an AI system to improve the SECURITY of code by identifying and mitigating common vulnerabilities"
,
            backstory=" You are a seasoned software security engineer and prompt engineer with extensive knowledge "
                        "of secure coding practices, vulnerability mitigation strategies, and OWASP Top 10 threats. "
                        "You specialize in analyzing source code to identify weak points and generate optimized prompts "
                        "that guide AI systems to refactor or review code with a focus on improving its security. "
                        "Your prompts are precise, actionable, and aligned "
                        "with best practices in application security and modern software development.",

            llm=self.llm,
            #input_keys=["quality_attributes_to_improve"],
            verbose=True

        )


    #@agent
    def third_agent(self):
       return Agent(
            role="Expert on java code refactoring",
            goal="To improve, when possible, the code"
                 " without generate errors, keeping the structure and the licenses of the code and following previous agent's prompt",
            #llm=LLM(  #HUGGINGFACE
              #api_key=os.getenv("HF_TOKEN"),
             # model="huggingface/meta-llama/Llama-3.3-70B-Instruct",
              #task="code-generation",
                #model_kwargs={"temperature": 0.7, "max_new_tokens": 512},
                #options={"timeout": 120}
            #),
            #llm=LLM(
             #   model="cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast",
              #  api_key=os.getenv("CLOUDFLARE_API_KEY"),
               # account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID"),
                #temperature=0.8,
                #max_tokens= 2046
            #),
           llm=LLM(
             model="mistral/mistral-medium",   #2 MINUTI CIRCA ma più improvement
             api_key=os.getenv("MISTRAL_API_KEY"),
             stream=True
           ),
            #llm=LLM(
             # model="ollama/codellama:latest",
              #base_url="http://localhost:11434",
              #temperature=0.5
            #),
            #llm=self.llm,      #50 SECONDI CIRCA ma meno improvement
            backstory="Software engineer with 20 years of experience in Java development. Specialized in refactoring,"
                      " security, performance tuning, and design patterns. "
                      "Has worked with Maven and static analysis tools such as PMD, Checkstyle, and SonarQube.",
            #input_keys=["file_content"],
            ##tools= [search_tool]  posso inserire un tool di ricerca su Google
            #knowledge_sources  per migliorare ancora di piu la conscenza di Java ???

            # possiamo specializzare questo agente assegnandogli il tool di ricerca web (importandolo da librerie di CrewAI o di LangChain)
            # questo significa che l'agente ha la "skill" di fare ricerche sul web e, quindi, non rispondere solamente in base alle sue conoscenze
            verbose=True,
            #input_keys=["code"]

        )



    '''def third_agent(self):
        return Agent(
            role="SonarQube and Json expert",
            goal="With the input of the previous agent, this agent must "
                 "verify the quality attribues of the second agent's code with {sonar_json}",
            backstory="Code of the second agent",
            llm=self.llm,
            verbose=True
            #function_calling_llm  per far fare questa task "piu leggera" ad un llm piu economico e veloce ???
        )'''

    def fourth_agent(self):
        return Agent(
            name = "UpdaterAndScanner",
            role = "DevOps e quality checker",
            goal = "Scrive il codice refactorizzato nel file Java e avvia SonarScanner",
            backstory="DevOps e quality checker",
            tools = [code_replace, sonar_scanner],
            verbose = True,
            input_keys = ["class_path", "refactored_code"],
            llm=self.llm
        )

