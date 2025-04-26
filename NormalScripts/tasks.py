from crewai import Task

#CLASSE PER PERSONALIZZAZIONE TASK
class CustomTask():

    def first_task(self, agente):
        return Task(
            agent=agente,
            description="Esempio di tavolo da gioco da 8 persone",
            expected_output="Tavolo da gioco dettagliato con stack, aggressività, posizione e altri parametri (se necessari)"
        )

    def second_task(self, agente, task1):
        return Task(
            agent=agente,
            description="Dimmi quali sono le mani in cui conviene andare All In preflop da UTG",
            expected_output="Mani in cui mi conviene fare All in preflop da UTG ",
            context=[task1]
        )