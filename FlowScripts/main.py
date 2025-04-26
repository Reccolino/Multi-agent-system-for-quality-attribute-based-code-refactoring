from crewai import Flow
from crewai.flow.flow import start, listen
from FlowScripts.crew.crew import CustomCrew


class ExampleFlow(Flow):
    @start()
    def generazione_tavolo(self):
        print("Generazione tavolo Texas Hold'em")


    @listen(generazione_tavolo)
    def consiglio(self,generazione_tavolo):
        print("Consiglio mano in base al tavolo")
        result = CustomCrew().crew().kickoff()
        #non cosi
        print(result.raw)
        #return result.raw


flow = ExampleFlow()
print(flow.kickoff())
print(flow.plot())
