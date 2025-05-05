import os

from crewai import Agent, LLM
from crewai_tools.tools.code_docs_search_tool.code_docs_search_tool import CodeDocsSearchTool

from langchain_huggingface import HuggingFaceEndpoint


#CLASSE PER PERSONALIZZAZIONE AGENTI
class CustomAgent():



    #NEL COSTRUTTORE è DEFINITO IL MODELLO UTILIZZATO DA TUTTI I MODELLI
    def __init__(self):
        self.llm= LLM(
            model="gemini/gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY")

        )


    #@agent
    def first_agent(self):
        return Agent(
            role="Prompt generator",
            goal="Generate a prompt to improve the {file_content} code",
            backstory="Knowledge of best practices and prompt engineering techniques to formulate a highly optimized prompt.",
            llm=self.llm,
            input_keys=["file_content"]
        )

    #@agent
    def second_agent(self):
        return Agent(
            role="Expert on code refactoring",
            goal="To improve, when possible, the code of first agent, without generate errors and keeping the licenses ",
            llm=self.llm,
            backstory="Knowledge of Java language (version 17), Java's best practise and Java structure (Maven)",
            input_keys=["file_content"],
            toosls= CodeDocsSearchTool()
            ##tools= [search_tool]  posso inserire un tool di ricerca su Google
            #knowledge_sources  per migliorare ancora di piu la conscenza di Java ???

            # possiamo specializzare questo agente assegnandogli il tool di ricerca web (importandolo da librerie di CrewAI o di LangChain)
            # questo significa che l'agente ha la "skill" di fare ricerche sul web e, quindi, non rispondere solamente in base alle sue conoscenze
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

