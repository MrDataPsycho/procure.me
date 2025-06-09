import asyncio
import json
from pathlib import Path
import aiofiles
from pydantic import BaseModel
from typing import Optional
from procureme.clients.openai_chat import OpenAIClient
from procureme.configurations.aimodels import ChatModelSelection
from procureme.configurations.app_configs import Settings
import typer
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError
import logging


app = typer.Typer()

logger = logging.getLogger("contract_etl")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

class ContractSummary(BaseModel):
    cwid: str
    short_summary: Optional[str]
    medium_summary: Optional[str]
    long_summary: Optional[str]


# System prompts
SHORT_PROMPT = "Summarize the contract briefly under 5 sentences for executive overview in makrdown format. Do not made up any information yourself."
MEDIUM_PROMPT = "Provide a medium-length summary (~6-8 sentences) highlighting the key aspects of the contract in makrdown format.  Do not made up any information yourself."
LONG_PROMPT = "Provide a detailed summary of the contract, including context, objectives, obligations, and key terms, buyer, supplier, purchase date, expiration date in makrdown format.  Do not made up any information yourself."


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True
)
async def generate_summary(prompt: str, content: str, client: OpenAIClient) -> str:
    messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]
    response = await client.chat_async(messages, temperature=0.4)
    return response


async def process_contract(file_path: Path, output_dir: Path, client: OpenAIClient) -> None:
    logger.info(f"Processing {file_path} ...")
    async with aiofiles.open(file_path, "r") as f:
        data = json.loads(await f.read())

    base_content = data["text"]

    short_task = generate_summary(SHORT_PROMPT, base_content, client)
    medium_task = generate_summary(MEDIUM_PROMPT, base_content, client)
    long_task = generate_summary(LONG_PROMPT, base_content, client)

    short, medium, long = await asyncio.gather(short_task, medium_task, long_task)


    cwid = file_path.stem.split(".")[0]

    summary = ContractSummary(
        cwid=cwid,
        short_summary=short,
        medium_summary=medium,
        long_summary=long
    )

    output_path = output_dir / f"{summary.cwid}.json"
    async with aiofiles.open(output_path, "w") as f:
        await f.write(summary.model_dump_json(indent=2))

    logger.info(f"✅ Summary generated for {output_dir}")


@app.command()
def main(
    src: Path = typer.Option(Path("data/silver/contracts"), help="Directory containing contract metadata JSON files"),
    dst: Path = typer.Option(Path("data/gold/summaries"), help="Directory to save summary JSON files"),
    model: str = typer.Option(ChatModelSelection.GPT4_1_MINI, help="OpenAI model to use"),
    limit: Optional[int] = typer.Option(None, help="Process only N number of files"),
):
    """Generate short, medium, and long summaries for each contract."""

    logger.info(f"Using OpenAI model: {model}")

    settings = Settings()
    client = OpenAIClient(api_key=settings.OPENAI_API_KEY, model=model)


    async def runner():
        dst.mkdir(parents=True, exist_ok=True)
        files = list(src.glob("*.json"))
        if limit:
            files = files[:limit]
        logger.info(f"Processing {len(files)} contract(s)...")
        await asyncio.gather(*(process_contract(f, dst, client) for f in files))

    asyncio.run(runner())

if __name__ == "__main__":
    app()