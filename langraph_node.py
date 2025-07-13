
import uuid
import os
import pandas as pd
import streamlit as st
from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.utilities import SQLDatabase
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from sqlalchemy import create_engine

os.environ["ANTHROPIC_API_KEY"] = ""
model = ChatAnthropic(model="claude-3-5-sonnet-20241022")

df = pd.read_excel("summary_table.xlsx")
engine = create_engine("sqlite:///mydb_sqlite.db")
df.to_sql("summary_data", con=engine, if_exists="replace", index=False)

db = SQLDatabase.from_uri("sqlite:///mydb_sqlite.db")
table_info = db.get_table_info()
dialect = db.dialect
store_id = 1

generate_query_system_prompt = f"""
You are an expert SQL assistant specialized in writing accurate and optimized queries for the {dialect} dialect, specifically for SQLite.

Your task is to generate a syntactically correct and efficient SQL query that answers the user's question, while strictly following these requirements:

- Use only the tables provided in the schema: {table_info}
- Always include a WHERE clause to filter data for only the specified store ID: {store_id}
- Do not use SELECT *; instead, select only the columns relevant to the question
- Ensure all columns used exist in the schema; do not invent columns
- If the question refers to a specific month (like March or April), filter data using SQLite’s `strftime('%m', activity_date)` format. For example, March is '03', April is '04'
- If the user asks for both March and April, filter using `IN ('03', '04')`
- If the user doesn't ask for a specific number of results, use `LIMIT 10`
- Prefer aggregation (e.g. SUM, COUNT) when the question implies totals or summaries
- Return only the final SQL query — no extra text
-Note: If the user asks for data for a specific time period (like a year or month), ensure that time period exists in the available data; 
 if not, return a message saying the "NO Data Available"
"""

class CustomState(TypedDict):
    messages: List[BaseMessage]
    sql_query: Optional[str]

def generate_sql_query(state: CustomState) -> CustomState:
    user_message = state["messages"][-1].content
    messages = [
        SystemMessage(content=generate_query_system_prompt),
        HumanMessage(content=user_message),
    ]
    sql_response = model.invoke(messages)
    sql_query = sql_response.content.strip()
    return {"messages": state["messages"], "sql_query": sql_query}

def execute_sql_query(state: CustomState) -> CustomState:
    try:
        result = db.run(state["sql_query"])
        response_text = f"Query Results:\n{result}"
    except Exception as e:
        response_text = f"Error executing query: {str(e)}"
    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "sql_query": state["sql_query"]
    }

workflow = StateGraph(state_schema=CustomState)
workflow.add_node("generate_query", generate_sql_query)
workflow.add_node("execute_query", execute_sql_query)
workflow.set_entry_point("generate_query")
workflow.add_edge("generate_query", "execute_query")
app = workflow.compile(checkpointer=MemorySaver())

st.set_page_config(page_title="LangChain SQL Assistant", layout="centered")
st.title("💬 Natural Language to SQL Assistant")
st.markdown("Ask a question like: **What were the total orders in March?**")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

user_prompt = st.chat_input("Enter your question")

if user_prompt:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    user_msg = HumanMessage(content=user_prompt)
    state = {
        "messages": st.session_state.messages + [user_msg],
        "sql_query": None
    }

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for event in app.stream(state, config=config, stream_mode="values"):
                last_ai_msg = event["messages"][-1]
                sql = event["sql_query"]
            st.markdown(f"** Generated SQL Query:**\n```sql\n{sql}\n```")
            st.markdown(f"** Result:**\n```\n{last_ai_msg.content}\n```")

    # Save both messages to session state
    st.session_state.messages.append(user_msg)
    st.session_state.messages.append(last_ai_msg)

