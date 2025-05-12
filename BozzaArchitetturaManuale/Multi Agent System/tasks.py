import json

import requests
from crewai import Task
from crewai.project import task

from BozzaArchitetturaManuale.validation import DIRECTORY, HEADER


#CLASSE PER PERSONALIZZAZIONE TASK
class CustomTask:

    def first_task(self, agente):
        return Task(
            agent=agente,
            description="Make API call to return the worst class path of the directory in term of quality attribute",
            expected_output= "Class path",
            #input_keys=["repository"]
        )


    #@task
    def second_task(self, agente):
        return Task(
            agent=agente,
            description="Analyze the code and generate a well-structured and clear prompt, "
                        "so that another agent can easily understand it and use it to improve the code.",
            #SENZA TEMPLATE del file l'agente che opera su questo task non sa che input prendere
            #con input_keys=["file_content"] l'agente si aspetta un input ma poi devo specificarlo da qualche parte nel task tramite template
            #se il placeholder non c'è, l'agente non lo vedrà mai
            expected_output="Optimized prompt to be used as input for another Agent",
            #input_keys=["file_content"]
        )

    #@task
    def third_task(self, agente, task1):
        return Task(
            agent=agente,
            description="The agent takes the prompt as input, executes it, and returns the code generated from"
                        " the code refactoring, while trying to preserve the structure and method public signatures of "
                        "the original code, as well as the relationships with other classes (inheritance, "
                        "abstract classes, etc.), the constructor and the name of class. Therefore, do not drastically change the code, "
                        "but improve it only where necessary. P.S.: There is no need to include test cases."
                        "P.S.: remove unnecessary comments so that I can fit the entire code you "
                        "generate for me without running into model token limits",
            expected_output="Refactor code",
            context=[task1]
        )

    def fourth_task(selfself, agente, task2):
        return Task(
            agent=agente,
            description="You need to connect to the project that is on sonarqube via api call. Once connected, "
                        "a json with the quality attributes will be returned. The task is to check the "
                        "quality attributes, in particular: duplicate lines and complexity",
            expected_output="The quality attributes are satisfied ? I want an answer",
            context=[task2]
        )