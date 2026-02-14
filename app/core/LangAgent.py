import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama

from app.core.prompt import SYSTEM_PROMPT

checkpointer = InMemorySaver()

config = {
    "configurable": {
        "thread_id": "1"  
    }
}


async def chat_agent():
    llm = ChatOllama(model="lfm2.5-thinking:latest", temperature=0.9) 

    McpConfig={}

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
            {"role": "user", "content": "Hi how are you?"}
        ]
    }, config)

    print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())