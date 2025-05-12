import time
from crewai import Crew, Process
from agents import CustomAgent
from tasks import CustomTask


def run():

    global response

    agents = CustomAgent()
    tasks = CustomTask()

    searcher_class = agents.first_agent()
    query_writer = agents.second_agent()
    code_refactor = agents.third_agent()
    #sonar_connector = agents.third_agent()
    #attributes_verify = agents.third_agent()   #colui che si dovrà connettere a SonarQube tramite chiamata API

    task0 = tasks.first_task(searcher_class)
    task1= tasks.second_task(query_writer)
    task2= tasks.third_task(code_refactor, task1)
    #task3= tasks.third_task(sonar_connector, task2)


    input = {
        #"repository": repository,
        "quality_attributes_to_improve": "security_rating"
        #"response": response
    }
    #print(input["file_content"])


    #CREAZIONE CREW
    crew = Crew(
        #agents= [query_writer, code_refactor], nnposso omettere tanto nelle task già specifico gli agenti che eseguiranno quella task
        tasks= [task0, task1,task2],   #TODO: definisci task senza agenti che si connettono a sonar e che fanno replace del codice
        process= Process.sequential,
        verbose=True
    )


    return crew.kickoff(inputs=input)




if __name__ == '__main__':
    start_time= time.time()

    result = run()
    print(result)

    end_time = time.time()- start_time
    print(f"Tempo di esecuzione = {end_time}")

'''for repository in os.listdir(DIRECTORY):

    if repository.startswith("."):  # come cartella .git
        continue

    #classe = classe_peggiore(repository)'''



