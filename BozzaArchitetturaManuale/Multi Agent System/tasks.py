from crewai import Task


#CLASSE PER PERSONALIZZAZIONE TASK
class CustomTask:


    def first_task(self, agente):
        return Task(
            agent=agente,
            description="Make API call to find the worst classes of the directory in term of quality attribute"
                        "using a tool and passing {repository} as parameter of project key (then not full path, it's important, "
                        "but only {repository}). once you finish iterating on one class, start the loop again with the other class",
            expected_output= "LOCAL PATH and FULL code of the class",
            verbose=True,
            #input_keys=["repository"]

        )


    #@task
    def second_task(self, agente, task0):
        return Task(
            agent=agente,

            description="Analyze the code of previous task carefully and create a precise and comprehensive prompt that "
                        "instructs an AI system or automated tool to evaluate source code, focusing on backstory of agent and, if possible, on:"
                        "- Bad Practices (e.g., duplicated code, improper naming, code smells)"
                        "- Correctness (compliance with style and logic rules)"
                        "- Critical Security Issues (e.g., injection vulnerabilities, insecure APIs, buffer overflows). ",

            #SENZA TEMPLATE del file l'agente che opera su questo task non sa che input prendere
            #con input_keys=["file_content"] l'agente si aspetta un input ma poi devo specificarlo da qualche parte nel task tramite template
            #se il placeholder non c'è, l'agente non lo vedrà mai
            expected_output="A single, self-contained prompt in natural language, written in English, that clearly instructs "
                            "another AI agent on how to improve the security of the given code. It should be suitable to use "
                            "as direct input for a language model.",
            verbose=True,
            context=[task0],
            #input_keys=["code"]
        )

    def third_task(self, agente, task0, task1):
        return Task(
            agent=agente,
            description= "To refactor the {code} using {prompt} as input."
                         #"You must stop refactoring code at first half."
                        ,
            expected_output="COMPLETE Code refactoring",
            verbose=True,
            input_keys=["code", "prompt"],
            context=[task0, task1]

        )


    #@task
    def fourth_task(self, agente, task0, task1):
        return Task(
            agent=agente,
            description="The agent takes the code and the prompt of previous task (task0 and task1) as input and makes code refactoring, following these lines:"
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
            #input_keys=["code", "prompt"]
            #input_keys=["code"]

        )



    def code_replace_sonar_task(self, utility_agent, task0, task2):
        return Task(
            agent=utility_agent,
            description="Hai in input: "
                        "class_path: percorso LOCALE del file Java da aggiornare, fornito da task0. Fai code replace li."
                        "Inoltre, passa questo path al tool che fa SonarScanner",


            expected_output="Code replace avvenuto con successo nel path giusto e sonarscanner eseguito.",
            #input_keys=["class_path", "refactored_code"],
            context=[task0, task2],
            verbose=True,
            #output_file= "./ciao"
        )


