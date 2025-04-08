from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import WebsiteSearchTool

#CREAZIONE AGENT CON RELATIVE INFORMAZIONI

llm = LLM(
    #provider="mistral",
    model="mistral/mistral-small-latest",
    api_key="UtByQj2ZjUIUaVS07G5W5vwhV2PgjtUM"  #oppure metterlo nelle variabili d'ambiente del progetto
    #oppure creare file .env e specificarlo li, cosi che qui lo possa richiamare
)

#search_tool = WebsiteSearchTool()
'''model: str,
 timeout: float | int | None = None,
 temperature: float | None = None,
 top_p: float | None = None,
 n: int | None = None,
 stop: str | list[str] | None = None,
 max_completion_tokens: int | None = None,
 max_tokens: int | None = None,
 presence_penalty: float | None = None,
 frequency_penalty: float | None = None,
 logit_bias: dict[int, float] | None = None,
 response_format: Type[BaseModel] | None = None,
 seed: int | None = None,
 logprobs: int | None = None,
 top_logprobs: int | None = None,
 base_url: str | None = None,
 api_base: str | None = None,
 api_version: str | None = None,
 api_key: str | None = None,
 callbacks: list = [],
 reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
 stream: bool = False,
 **kwargs: Any) -> None'''

first_agent = Agent(
    role="Conoscenza tavoli da gioco del Texas Hold'em",
    goal="Tavolo da gioco",
    backstory="Conoscenza delle strategie, bui, stack, tornei, ecc.. del Poker Texas Hold'em",
    llm=llm
)
second_agent = Agent(
    role= "Rispondere alle mie domande sul poker",
    goal= "qualcosa",
    llm= llm,
    backstory= "Conoscenza dei punti del Poker Texas Hold'em",
    ##tools= [search_tool]
    #possiamo specializzare questo agente assegnandogli il tool di ricerca web (importandolo da librerie di CrewAI o di LangChain)
    #questo significa che l'agente ha la "skill" di fare ricerche sul web e, quindi, non rispondere solamente in base alle sue conoscenze
)
'''gent_executor – An instance of the CrewAgentExecutor class.
role – The role of the agent.
goal – The objective of the agent.
backstory – The backstory of the agent.
knowledge – The knowledge base of the agent.
config – Dict representation of agent configuration.
llm – The language model that will run the agent.
function_calling_llm – The language model that will handle the tool calling for this agent, it overrides the crew function_calling_llm.
max_iter – Maximum number of iterations for an agent to execute a task.
max_rpm – Maximum number of requests per minute for the agent execution to be respected.
verbose – Whether the agent execution should be in verbose mode.
allow_delegation – Whether the agent is allowed to delegate tasks to other agents.
tools – Tools at agents disposal
step_callback – Callback to be executed after each step of the agent execution.
knowledge_sources – Knowledge sources for the agent.
embedder – Embedder configuration for the agent.'''



#CREAZIONE TASK PER L'AGENT

first_task= Task(
    agent=first_agent,
    description="Esempio di tavolo da gioco da 8 persone",
    expected_output="Tavolo da gioco dettagliato con stack, aggressività, posizione e altri parametri (se necessari)"
)
second_task = Task(
    agent= second_agent,
    description= "Dimmi quali sono le mani in cui conviene andare All In preflop da UTG",
    expected_output= "Mani in cui mi conviene fare All in preflop da UTG ",
    context= [first_task]
)
'''agent – Agent responsible for task execution. Represents entity performing task.
async_execution – Boolean flag indicating asynchronous task execution.
callback – Function/ object executed post task completion for additional actions.
config – Dictionary containing task-specific configuration parameters.
context – List of Task instances providing task context or input data.
description – Descriptive text detailing task's purpose and execution.
expected_output – Clear definition of expected task outcome.
output_file – File path for storing task output.
output_json – Pydantic model for structuring JSON output.
output_pydantic – Pydantic model for task output.
security_config – Security configuration including fingerprinting.
tools – List of tools/ resources limited for task execution'''


#CREAZIONE CREW

crew= Crew(
    agents= [first_agent, second_agent],
    tasks= [first_task,second_task],
    process= Process.sequential,
    verbose=True
)
'''tasks – List of tasks assigned to the crew.
agents – List of agents part of this crew.
manager_llm – The language model that will run manager agent.
manager_agent – Custom agent that will be used as manager.
memory – Whether the crew should use memory to store memories of it's execution.
memory_config – Configuration for the memory to be used for the crew.
cache – Whether the crew should use a cache to store the results of the tools execution.
function_calling_llm – The language model that will run the tool calling for all the agents.
process – The process flow that the crew will follow (e. g., sequential, hierarchical).
verbose – Indicates the verbosity level for logging during execution.
config – Configuration settings for the crew.
max_rpm – Maximum number of requests per minute for the crew execution to be respected.
prompt_file – Path to the prompt json file to be used for the crew.
id – A unique identifier for the crew instance.
task_callback – Callback to be executed after each task for every agents execution.
step_callback – Callback to be executed after each step for every agents execution.
share_crew – Whether you want to share the complete crew information and execution with crewAI to make the library better, and allow us to train models.
planning – Plan the crew execution and add the plan to the crew.
chat_llm – The language model used for orchestrating chat interactions with the crew.
security_config – Security configuration for the crew, including fingerprinting.'''

result= crew.kickoff()

print(result)
