from procureme.clients.openai_chat import OpenAIClient
from procureme.agents.query_rewriter import QueryRewriterAgent
from procureme.agents.tool_executor import ToolExecutorAgent
from procureme.agents.answer_critique import AnswerCritiqueAgent
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Your job is to help the user with their questions.
You will receive user questions and information needed to answer the questions
If the information is missing to answer part of or the whole question, you will say that the information 
is missing. You will only use the information provided to you in the prompt to answer the questions.
You are not allowed to make anything up or use external information. You always respond with markdown format.
"""

class OrchrastratorAgent:
    def __init__(self, client: OpenAIClient, system_prompt: str | None = None):
        self.client = client
        self.system_prompt = system_prompt if system_prompt else SYSTEM_PROMPT
        self.query_rewriter_agent = QueryRewriterAgent(client)
        self.tool_selector_agent = ToolExecutorAgent(client)
        self.answer_critique_agent = AnswerCritiqueAgent(client)

    def chat(self, input: str, answers: list[dict[str, str]]):  
        logger.info(f"User input: {input}, with initial No. of User and Assistant turns: {len(answers)}")
        updated_question = self.query_rewriter_agent(input, answers)

        response  = self.tool_selector_agent(updated_question, answers)
        answers.append({"role": "assistant", "content": f"For the question: '{updated_question}', we have the answer: '{json.dumps(response)}'"})
        return answers


    def execute(self, input: str, answers: list[dict[str, str]] = None):
        answers = answers if answers else []
        answers = self.chat(input, answers)
        critique = self.answer_critique_agent(input, answers)

        if critique:
            answers = self.chat(" ".join(critique), answers)

        llm_response = self.client.chat(
            [
                {"role": "system", "content": self.system_prompt},
                *answers,
                {"role": "user", "content": f"The user question to answer: {input}"},
            ],
        )

        return llm_response
    
    def __call__(self, input: str, answers: list[dict[str, str]] = None) -> str:
        return self.execute(input, answers)
    

if __name__ == "__main__":
    from procureme.configurations.app_configs import Settings
    from procureme.configurations.aimodels import ChatModelSelection
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )

    settings = Settings()
    client = OpenAIClient(settings.OPENAI_API_KEY, ChatModelSelection.GPT4_1_MINI)
    agent = OrchrastratorAgent(client)
    query = "What do you know about Supplier: Alpha Suppliers Inc. and what it supplies?"
    response = agent(query)
    print(response)
    

