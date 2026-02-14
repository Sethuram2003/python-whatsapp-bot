import shelve
import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent


llm = ChatOllama(
    model="lfm2.5-thinking:latest",   
    temperature=0.7,
)

agent = create_react_agent(
    model=llm,
)

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as db:
        return db.get(wa_id, [])

def store_thread(wa_id, messages):
    with shelve.open("threads_db", writeback=True) as db:
        db[wa_id] = messages


def generate_response(message_body, wa_id, name):

    conversation_history = check_if_thread_exists(wa_id)

    if not conversation_history:
        logging.info(f"Creating new conversation for {name} ({wa_id})")
        conversation_history = []

    conversation_history.append(
        HumanMessage(content=message_body)
    )

    result = agent.invoke({
        "messages": conversation_history
    })

    updated_messages = result["messages"]

    store_thread(wa_id, updated_messages)

    ai_response = updated_messages[-1].content

    logging.info(f"Generated message: {ai_response}")

    return ai_response
