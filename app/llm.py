import logging
import os

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)
client = AsyncAnthropic(max_retries=3, timeout=30)
DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")


async def complete(
    system_prompt: str, content: str, max_tokens: int, model: str = DEFAULT_MODEL
) -> str:
    msg = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )

    log.info(
        "llm model=%s input_tokens=%d output_tokens=%d stop=%s",
        model,
        msg.usage.input_tokens,
        msg.usage.output_tokens,
        msg.stop_reason,
    )
    for block in msg.content:
        if isinstance(block, TextBlock):
            return block.text
    raise ValueError(f"LLM không trả về text (stop_reason={msg.stop_reason})")
