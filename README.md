# SQL Assistant using LangChain, Claude & Streamlit

This repository contains logic for querying structured databases using **natural language** through:

- LangChain agents  
- LangGraph nodes  
- Anthropic Claude models  
- Streamlit UI

---

##  Project Structure

```text
myzid/
├── summary_table.xlsx     # Excel data source
├── mydb_sqlite.db         # Auto-generated SQLite DB
├── agent.py               # Streamlit app using LangChain Agent
├── langraph_node.py       # LangGraph node logic
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## ⚙️ Features

- Ask natural language questions  
- Claude 3.5 (via Anthropic API) converts to optimized SQL  
- Tool-using LangChain agent with memory  
- SQLite integration with Excel source  
- User-friendly Streamlit chat UI

---

## Installation

### 🔸 1. Clone the Repository

```bash
git clone <repo>
cd <folder>
```

### 🔸2. Using `venv` (alternative to conda)

```bash
python -m venv myenv
source myenv/bin/activate      # For Mac/Linux

# For Windows:
# myenv\Scripts\activate
```
### 🔸3. Install Requirements

```
pip install -r requirements.txt
```
### 🔸4. Set Anthropic Key
##### Option1:Set inside python code
```
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"
```
##### Option2:Set in terminal
```
export ANTHROPIC_API_KEY=your-api-key  
```
### 🔸5. Run the app
##### run agent.py or langraph_node.py
```
streamlit run agent.py/ streamlit run langraph_node.py
```
##### then open this in url  **http://localhost:8501**
### Example 
```text
What were the total orders in March?
How many sales occurred in April?
Show the top 10 products for store 1 in April.
```

# 🔸How to Create a Claude (Anthropic) API Key
```text
1. Go to https://console.anthropic.com/settings/keys
2. Sign in or create an account
3. Navigate to the API Keys section
4. Click "Create Key"
5. Copy the key and use it as ANTHROPIC_API_KEY in your app

⚠️ Important: Do not share your API key publicly or commit it to source control.
```