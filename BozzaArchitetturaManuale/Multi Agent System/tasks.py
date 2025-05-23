import json
import os

import requests
from crewai import Task
from crewai.project import task


from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER


#CLASSE PER PERSONALIZZAZIONE TASK
class CustomTask:


    def first_task(self, agente):
        return Task(
            agent=agente,
            description="Make API call to find the worst class of the directory in term of quality attribute",
            expected_output= "LOCAL PATH and FULL code",
            verbose=True,

        )


    #@task
    def second_task(self, agente, task0):
        return Task(
            agent=agente,

            description="Analyze the {code} carefully and generate a clear, concise, and actionable prompt "
                        "that will help another agent improve the *security* of the code. ",
            #SENZA TEMPLATE del file l'agente che opera su questo task non sa che input prendere
            #con input_keys=["file_content"] l'agente si aspetta un input ma poi devo specificarlo da qualche parte nel task tramite template
            #se il placeholder non c'è, l'agente non lo vedrà mai
            expected_output="A single, self-contained prompt in natural language, written in English, that clearly instructs "
                            "another AI agent on how to improve the security of the given code. It should be suitable to use "
                            "as direct input for a language model.",
            verbose=True,
            context=[task0],
            input_keys=["code"]
        )

    def third_task(self, agente, task1):
        return Task(
            agent=agente,
            description= "To refactor the {code}."
                         #"You must stop refactoring code at first half."
                        ,
            expected_output="Full Code refactoring",
            verbose=True,
            input_keys=["code"],
            context=[task1]

        )


    #@task
    def fourth_task(self, agente, task0, task1):
        return Task(
            agent=agente,
            description="The agent takes the {code} and the {prompt} as input and makes code refactoring, following these lines:"
                        "- preserve the structure, the number and ALL signatures of the original code's method"
                        "- preserve all the relationships with other classes (inheritance, "
                        "abstract classes, etc.)"
                        "- preserve ALL number and signature of constructors and the names of classes. THIS IS IMPORTANT !! "
                        "- do not drastically changes of the code,but improve it only where necessary "
                        "- keep absolutely the licenses"
                        "- not include test cases"
                        "- do not syntax errors"
                        "- if necessary, remove unnecessary comments so that I can fit the entire code you "
                        "generate for me without running into model token limits",
            #description="You will be given code snippets or segments for improvement. "
             #           "Your task is to interact with the user when necessary to clarify context or requirements. "
              #          "Then, suggest clear, maintainable refactorings that preserve original functionality. "
               #         "Prioritize clarity and maintainability. When applicable, apply well-known design patterns. "
                #        "Optimize performance only if it doesn't compromise readability or introduce premature "
                 #       "optimization issues. Identify and address potential errors and edge cases for robustness. "
                  #      "For every improvement or change, provide concise, informative explanations detailing why"
                   #     " the change is beneficial",
            expected_output="Full Code refactoring",
            verbose=True,
            context=[task0, task1],
            input_keys=["code", "prompt"]
            #input_keys=["code"]

        )



    def code_replace_sonar_task(self, utility_agent, task0, task2):
        return Task(
            agent=utility_agent,
            description="Hai in input:"
                        "- {class_path}: percorso LOCALE del file Java da aggiornare, fornito da task0"
                        "- {refactored_code}: stringa con il codice Java refactorizzato, fornito da task2"
                        "**Istruzioni**: " 
                        "1. **Importa** il modulo `json`.  "
                        "2. Costruisci un dict Python:"
                           "payload = {"
                             "class_path: {class_path},"
                             "refactored_code: {refactored_code} "
                        "}"
                        "e usa json.dumps(payload)"
                        "Semplicemente poi chiama il tool `code_replace passando come parametri le i valori delle chiavi del payload json` "
                        "e restituisci il suo output. Poi esegui SonarScanner nella root del progetto",


            expected_output="Nuova classe scritta nel path giusto e sonarscanner eseguito",
            input_keys=["class_path", "refactored_code"],
            context=[task0, task2],
            verbose=True
        )


