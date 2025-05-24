import json
import os
import subprocess

import requests
from crewai import Agent, LLM
from crewai.tools.base_tool import tool
from crewai_tools.tools.code_interpreter_tool.code_interpreter_tool import CodeInterpreterTool
from dask.config import paths
from litellm import completion
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import ModelResponse

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER

@tool("classe_peggiore")
def classe_peggiore(project_key : str):
    """
    Restituisce: il path della classe con peggior security_rating via SonarQube e il codice di quella classe .
    Effettua una GET su /api/measures/component_tree e ordina per security_rating e poi effettua un GET api/sources/raw per restituire il codice .
    """


    param = {
        "component": f"Progetto_{project_key}",
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

        #http://localhost:9000/api/sources/raw necessita della key del progetto come parametro (query string)  ==> la prendo dal JSON
        param2 = {
            "key": response.json().get("components")[0].get("key")
        }

        code = requests.get("http://localhost:9000/api/sources/raw", headers=HEADER, params=param2)
        #print(code)
        #print(code.text)

        #COSI FACENDO NON INCORRO IN ERRORI DEL TIPO:
        #l'agente mi fa un refactoring errato (cioè che SonarScanner restituisce Build Failure e, quindi, il codice non viene aggiornato),
        #ma il code replace va a buon fine. Allora alla prossima esecuzione il codice in input
        #sarà proprio quello generato dall'esecuzione precedente perchè con il codice vecchio (quello commentato qui sotto) l'agente
        #prendeva in input sempre il codice della classe peggiore, ma salvata in locale, non da SonarQube.
        #Invece, cosi, l'agente prende in input SEMPRE il codice da SonarQube cosi che se ad una esecuione ci sono errori di compilazione, per esempio,
        #viene fatto si code replace in locale, ma tanto si prende in input il codice da SonarQube che non è cambiato
        '''with open(f"{DIRECTORY}/commons-codec/{response.json().get("components")[0].get("path")}", "r",
                  encoding="utf-8") as f:
             code = f.read()'''

        project_root = f"{DIRECTORY}/{project_key}"

        #PER PROGETTI LPO BISOGNA TROVARE PATH CORRETTO PERCHE NON è IMMEDIATO COME PROGETTI APACHE
        for root, _, files in os.walk(project_root):
            for file in files:
                full_file_path = os.path.join(root, file)
                #uso normpath perche il json restituisce slash cosi: \ . Invece a me serve il path con slash cosi /
                if full_file_path.endswith(os.path.normpath(response.json()["components"][0]["path"])):
                    found_path = full_file_path
                    return f"LOCAL PATH= {found_path}"+ "\n\nCODE= " + code.text




        #PROBLEMA: è da gestire le classi
        #nel senso, se si avvia esecuzione e si vogliono far restituire, per esempio, 20 classi per progetto dalla prima chiamata,
        #l'agente ogni volta mi eseguirà sempre la prima classe, quindi, probabilmente, dovrò gestire il fatto che una classe
        #è stata già esaminata (è stato fatto code refactoring, sia che sia andato a buon fine che non)
        #e che quindi si deve passare alla classe successiva
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
    project_key = class_path.split('/')[2]
    print("PROJECT KEYYYY "+project_key)
    #QUESTO SOLO PER PROGETTI LPO
    directory_pom = class_path.split('/')[3]
    print("DIRECTORY POMMMM"+ directory_pom)
    try:
        subprocess.run([
            "mvn.cmd", "clean", "verify", "org.sonarsource.scanner.maven:sonar-maven-plugin:5.1.0.4751:sonar",
             f"-Dsonar.projectKey=Progetto_{project_key}",
             f"-Dsonar.projectName=Progetto_{project_key}",
             f"-Dsonar.host.url=http://localhost:9000",
             f"-Dsonar.token={os.getenv("SONAR_LOCAL_API_TOKEN")}",
             "-DskipTests"
             ],
            #cwd=os.path.join("cloned_repos_lpo", project_key),

            #QUESTO SOLO PER PROGETTI LPO
            cwd=os.path.join("cloned_repos_lpo", project_key, directory_pom),

            check=True
        )
    except subprocess.CalledProcessError:
        print("Errore durante l'analisi")

#CLASSE PER PERSONALIZZAZIONE AGENTI
class CustomAgent:


    #NEL COSTRUTTORE è DEFINITO IL MODELLO UTILIZZATO DA TUTTI GLI AGENTI
    #llm = LLM(
     #   model="gemini/gemini-1.5-flash",
      #  api_key=os.getenv("GOOGLE_API_KEY"),
       # max_tokens=128000,
        #stream=True
    #)
    llm = LLM(
        model="mistral/mistral-medium",  # 2 MINUTI CIRCA ma più improvement
        api_key=os.getenv("MISTRAL_API_KEY"),
        stream=True
    )

    '''def __init__(self, LLM):
        self.llm= LLM '''  #questo vale se voglio usare diversi llm per gli agenti


    def first_agent(self):    #STESSO AGENTE CHE FARà CHIAMATA API PER VERIFICARE QUALITY GATES
        return Agent(
            role="Searcher class",
            goal="To connect with SonarQube and research a specific classes of {{repository}}",
            backstory="Connect Internet via HTTP",
            llm=self.llm,
            tools=[classe_peggiore],   #una qualità in piu di quest'agente: sa fare chiamate API a SonarQube
            verbose=True,
            input_keys=["repository"]
        )


    #@agent
    def second_agent(self):
        return Agent(
            role="Security-Focused Static Code Analysis Expert and Prompt generator",
            goal="Generate precise prompts that guide an AI system to improve the SECURITY of code by identifying and mitigating common vulnerabilities"
,
            backstory="You were developed by a cybersecurity task force following a severe security breach"
                      " caused by unchecked vulnerabilities in a production codebase. Trained on thousands of open-source "
                      "repositories and static analysis rulesets, SentinelSec was designed with one mission: to detect "
                      "vulnerabilities and code quality issues before they can be exploited. As a relentless guardian of "
                      "clean and secure code, SentinelSec specializes in leveraging tools like SonarQube and its plugins—Sonar Way,"
                      " Checkstyle, PMD, and FindBugs—to scan for poor practices, potential bugs, and critical security flaws."
                      " With a deep understanding of secure development principles and automated inspection tools, you"
                      " act as the first line of defense in code validation.",

            llm=self.llm,
            #input_keys=["quality_attributes_to_improve"],
            verbose=True

        )


    #@agent
    def third_agent(self):
       return Agent(
            role="Expert on Java code refactoring",
            goal="To improve the code"
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

            #llm=LLM(
             # model="ollama/codellama:latest",
              #base_url="http://localhost:11434",
              #temperature=0.5
            #),
            llm=self.llm,      #50 SECONDI CIRCA ma meno improvement
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
            #input_keys = ["class_path", "refactored_code"],
            llm=self.llm
        )

