import os

from crewai import Agent
from crewai import LLM


class CustomAgent():
    def __init__(self):
        self.llm= LLM (model="mistral/mistral-small-latest", api_key=os.getenv("MISTRAL_API_KEY"))


    def first_agent(self):
        return Agent(
            role="Conoscenza tavoli da gioco del Texas Hold'em",
            goal="Tavolo da gioco",
            backstory="Conoscenza delle strategie, bui, stack, tornei, ecc.. del Poker Texas Hold'em",
            llm=self.llm
        )

    def second_agent(self):
        return Agent(
            role="Rispondere alle mie domande sul poker",
            goal="qualcosa",
            llm=self.llm,
            backstory="Conoscenza dei punti del Poker Texas Hold'em",
            ##tools= [search_tool]
            # possiamo specializzare questo agente assegnandogli il tool di ricerca web (importandolo da librerie di CrewAI o di LangChain)
            # questo significa che l'agente ha la "skill" di fare ricerche sul web e, quindi, non rispondere solamente in base alle sue conoscenze
        )

