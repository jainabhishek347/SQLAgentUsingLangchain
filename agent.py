
import os
import uuid
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from langchain_community.utilities import SQLDatabase
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

os.environ["ANTHROPIC_API_KEY"] = ""  # Replace with your key
model = ChatAnthropic(model="claude-3-5-sonnet-20241022")

# ==================== SQLite Setup ====================

df = pd.read_excel("summary_table.xlsx")
engine = create_engine("sqlite:///mydb_sqlite.db")
df.to_sql("summary_data", con=engine, if_exists="replace", index=False)

# ==================== SQL DB ====================
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

Additional important instructions:
- If the user asks for data from a time period outside existing data, do not generate a SQL query. Instead, return this exact message: NO Data Available
- Do not explain why data is unavailable.
- Do not add helpful suggestions or interpretations.
- If data exists, return only a concise one-line answer like: "There were 24 total orders in March 2020."
- Do not return summaries, trends, detailed analysis, or breakdowns by day.
- Your output must always be either:
  1. A single valid SQL query, OR
  2. A one-line numeric result as shown above, OR
  3. The exact phrase: NO Data Available
"""


# ==================== Tool ====================
@tool
def handle_sql_query(question: str) -> str:
    """Generate and execute SQL query from a natural language question."""
    messages = [
        SystemMessage(content=generate_query_system_prompt),
        HumanMessage(content=question)
    ]
    try:
        sql_query = model.invoke(messages).content.strip()
        result = db.run(sql_query)
        return f"**Generated SQL:**\n```sql\n{sql_query}\n```\n\n**Result:**\n```\n{result}\n```"
    except Exception as e:
        return f" Error during execution: {str(e)}"

# ==================== Agent Setup ====================
tools = [handle_sql_query]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that understands natural language and answers questions using a SQL database."),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

memory = st.session_state.memory
print("Current memory:", memory.chat_memory.messages)


agent = create_tool_calling_agent(llm=model, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=False)

# ==================== Streamlit UI ====================
st.set_page_config(page_title="SQL Agent", layout="centered")
st.title("SQL Assistant")
st.markdown("Ask natural language questions about your SQLite database (e.g., **What were the total orders in March?**)")

# Session setup
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

user_input = st.chat_input("Ask a question about the database...")

if user_input:

    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            last_two_messages = st.session_state.chat_history[-2:] if len(st.session_state.chat_history) >= 2 else st.session_state.chat_history
            chat_history_text = "\n".join([f"{role}: {message}" for role, message in last_two_messages])
            st.write('chat history text:',chat_history_text)
            full_input = f"{chat_history_text}\nuser: {user_input}"
            response = agent_executor.invoke({"input": full_input})
            if isinstance(response["output"], list):
                assistant_output = response["output"][0]["text"]
            else:
                assistant_output = response["output"]
            st.markdown(assistant_output)

    # Save assistant response
    st.session_state.chat_history.append(("assistant", assistant_output))
