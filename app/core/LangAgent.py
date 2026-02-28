import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from app.core.prompt import SYSTEM_PROMPT 

load_dotenv()

checkpointer = InMemorySaver()

config = {
    "configurable": {
        "thread_id": "1"  
    }
}

async def chat_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b")
    # llm = ChatOllama(model="llama3.1:8b")

    McpConfig={
            "googlescholar": {
                "url": "http://simplemcp:8001/mcp",
                "transport": "streamable_http",
                "headers": {
                    "X-API-Key": os.getenv("API_KEY"),
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


async def main():
    agent = await chat_agent()

    response = await agent.ainvoke({
        "messages": [
            {"role": "user", "content": "What are the tools you have"}
        ]
    }, config)

    print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())