import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from app.core.prompt import SYSTEM_PROMPT, IMAGE_SYSTEM_PROMPT

load_dotenv()

checkpointer = InMemorySaver()

async def image_summarization_agent():
    llm = ChatOllama(model="qwen3.5:397b-cloud")
    agent = create_agent(
        llm,
        system_prompt=IMAGE_SYSTEM_PROMPT
    )

    return agent


async def chat_agent():
    llm = ChatOllama(model="kimi-k2:1t-cloud")

    McpConfig={
            "tavily-mcp": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "transport": "stdio",
      "env": {
        "TAVILY_API_KEY": os.getenv("tavily_mcp_api_key"),
        "DEFAULT_PARAMETERS": "{\"include_images\": false, \"max_results\": 15, \"search_depth\": \"advanced\"}"
      }
    }
        }
    

    client = MultiServerMCPClient(McpConfig)
    tools = await client.get_tools()

    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

    return agent


