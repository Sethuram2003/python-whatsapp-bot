import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import sys

from app.core.prompt import SYSTEM_PROMPT

load_dotenv()

checkpointer = InMemorySaver()

def find_python_path():
    """Find Python binary path with packages"""
    return sys.executable 

python_executable = find_python_path()
current_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    "configurable": {
        "thread_id": "1"  
    }
}


async def chat_agent():
    llm = ChatOllama(model="llama3.1:8b", temperature=0.9) 

    McpConfig={
            "pipe_status": {
            "command": "python3", 
            "args": ["/Users/sethuramgauthamr/Documents/Projects/python-whatsapp-bot/app/core/McpServers/PipeStatus/main.py"],
            "transport": "stdio"
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
            {"role": "user", "content": "What pipes are directly connected to pipe B23"}
        ]
    }, config)

    print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())