import logging
from enum import StrEnum
from procureme.configurations.app_configs import Settings
from procureme.dbmodels.doc_summery import ContractSummary
from procureme.dbmodels.doc_metadata import ContractMetadata
from procureme.vectordb.utils import get_vector_store
from sqlmodel import Session, create_engine, select
import json
import pandas as pd


class SummaryType(StrEnum):
    """Summary types to query from databse"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

logger = logging.getLogger(__name__)

answer_given_description = {
    "type": "function",
    "function": {
        "name": "answer_given",
        "description": "If the conversation already contains a complete answer to the question, "
        "use this tool to extract it. Additionally, if the user engages in small talk, "
        "use this tool to remind them that you can only answer questions about contracts.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Respond directly with the answer",
                }
            },
            "required": ["answer"],
        },
    },
}


def answer_given(answer: str):
    """Extract the answer from a given text."""
    logger.info("Answer found in text: %s", answer)
    return answer


respond_unrelated_question_description = {
    "type": "function",
    "function": {
        "name": "respond_unrelated_question",
        "description": "Respond with a message if the question is not related to the source document.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user question or query to find the answer for",
                }
            },
            "required": ["question"],
        },
    },
}


def respond_unrelated_question_tool(question: str):
    return f"The source document does not contain the answer to the question: {question}"



vectordb_retriver_tool_description = {
    "type": "function",
    "function": {
        "name": "retriver_tool",
        "description": "Query the vector database with a user question to pull the most relevant chunks. When other tools don't fit, fallback to use this one.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user question or query to find the answer for",
                }
            },
            "required": ["question"],
        },
    },
}


def vector_db_retriver_tool(question: str) -> str:
    """Query the database with a user question."""
    logger.info("=== Entering Retrival Tool ===")
    try:
        vector_store = get_vector_store()
        documents = vector_store.search(query=question, top_k=5)
        document_ids = [f"{doc['doc_id']}-{doc['part']}" for doc in documents]

        logger.info(f"Following document parts is retrieved: {document_ids}")
        context = "\n\n".join(
            [f"--- [CONTEXT_DOCUMENT_NAME]: {doc['doc_id']} [CONTEXT_DOCUMENT_NAME_PARTITION_NUMBER]: {doc['part']} ---\n[CONTENT]:\n{doc['content']}\n\n" for doc in documents]
        )
        logger.info("Retrival Tool executed successfully.")
        return context
    except Exception as e:
        return [f"Could not query vector store, cause an error: {e}"]
    

sumery_retriver_tool_description = {
    "type": "function",
    "function": {
        "name": "summery_retriver_tool",
        "description": "Query the database with a user provide cwid and summary type to pull the most relevant summary. The tool is only when only user ask to get summary of a contract.",
        "parameters": {
            "type": "object",
            "properties": {
                "cwid": {
                    "type": "string",
                    "description": "The CWID of the contract",
                },
                "summary_type": {
                    "type": "string",
                    "enum": ["short", "medium", "long"],
                }
            },
            "required": ["cwid", "summary_type"],
        },
    },
}


def summery_retriver_tool(cwid: str, summary_type: SummaryType = SummaryType.SHORT) -> str:
    logger.info("=== Entering Summery Retrival Tool ===")

    settings = Settings()
    engine = create_engine(settings.pg_database_url)

    with Session(engine) as session:
        statement = select(ContractSummary).where(ContractSummary.cwid == cwid)
        result = session.exec(statement).first()

        if not result:
            return f"No contract found with CWID: {cwid}"

        if summary_type == "short":
            summary = result.summary_short
        elif summary_type == "medium":
            summary = result.summary_medium
        elif summary_type == "long":
            summary = result.summary_long
        else:
            raise ValueError("Invalid summary type. Use 'short', 'medium', or 'long'.")
        if not summary:
            raise ValueError(f"{summary_type.capitalize()} summary is not available for CWID: {cwid}")
        
        logger.info("Summery Retrival Tool executed successfully.")
        return summary
    

compare_contract_tool_description = {
    "type": "function",
    "function": {
        "name": "compare_contract_tool",
        "description": "Query the database with a list of CWID to compare the contracts. The tool is only when only user ask to compare contracts.",
        "parameters": {
            "type": "object",
            "properties": {
                "cwid": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "The CWID of the contracts to compare",
                }
            },
            "required": ["cwid"],
        },
    },
}

def compare_contract_tool(cwid: list[str]) -> str:
    logger.info("=== Entering Compare Contract Tool ===")
    settings = Settings()
    engine = create_engine(settings.pg_database_url)

    with Session(engine) as session:
        statement = select(ContractMetadata).where(ContractMetadata.cwid.in_(cwid))
        result = session.exec(statement).all()
        if not result:
            return f"No contract found with CWID: {(', '.join(cwid))}"
        
        contracts_data = {contract.cwid: contract.model_dump() for contract in result}
        df = pd.DataFrame(contracts_data)
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Field"}, inplace=True)
        markdown_table = df.to_markdown(index=False)
        logger.info("Compare Contract Tool executed successfully.")
        return markdown_table
    

_tools = {
    "retriver_tool": {
        "description": vectordb_retriver_tool_description,
        "function": vector_db_retriver_tool
    },
    # "answer_given": {
    #     "description": answer_given_description,
    #     "function": answer_given
    # },
    "summery_retriver_tool": {
        "description": sumery_retriver_tool_description,
        "function": summery_retriver_tool
    },
    "compare_contract_tool": {
        "description": compare_contract_tool_description,
        "function": compare_contract_tool
    },
    # "respond_unrelated_question": {
    #     "description": respond_unrelated_question_description,
    #     "function": respond_unrelated_question_tool
    # }
}



def handle_tool_calls(llm_tool_calls: list[dict[str, any]]):
    logger.info("=== Selecting Tools ===")
    output = []
    available_tools = [tool["description"]["function"]["name"] for tool in _tools.values()]
    if llm_tool_calls:
        tool_list = [tool_call.function.name for tool_call in llm_tool_calls]
        logger.info(f"Follwing tools are selected for execution: {tool_list} from available tools: {available_tools}")
        for tool_call in llm_tool_calls:
            function_to_call = _tools[tool_call.function.name]["function"]
            function_args = json.loads(tool_call.function.arguments)
            res = function_to_call(**function_args)
            output.append(res)
    logger.info(f"Tool execution finished!")
    return output


def get_tool_descriptions() -> list[str]:
    description = [tool["description"] for tool in _tools.values()]
    return description


if __name__ == "__main__":
    print(get_tool_descriptions())
