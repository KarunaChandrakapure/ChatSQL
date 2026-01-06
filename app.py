import streamlit as st
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from langchain_groq import ChatGroq

st.set_page_config(page_title="Langchain : Chat with SQL DB",page_icon="🐦")
st.title("Lagchain : Chat with SQL DB")

LOCALBB="USE_LOCALDB"
MYSQL="USE_MYSQL"

radio_opt=["Use SQLLite Databse-Student.db","Connect to your MySQL Databse"]

selected_opt=st.sidebar.radio(label="Choose the DB which you want to chat",options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_uri=MYSQL
    mysql_host=st.sidebar.text_input("Provide MySql Host")
    mysql_users=st.sidebar.text_input("MYSQL User")
    mysql_password=st.sidebar.text_input("MySQL password", type="password")
    mysql_db=st.sidebar.text_input("MySQL database")
else:
    db_uri =LOCALBB


api_key = st.sidebar.text_input(label="GROQ API KEY", type="password")    


if not db_uri:
    st.info("Please add the database information and uri")
if not api_key:
    st.info("Please add the groq api key")

   
    
#llm=ChatGroq(groq_api_key=api_key,model='Llama3-8b-8192',streaming=True)  
if api_key:
   llm=ChatGroq(groq_api_key=api_key,model='gemma-7b-it',streaming=True) 

@st.cache_resource(ttl="2h")

def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri == LOCALBB:
        dbfilepath=(Path(__file__).parent/"student.db").absolute()
        print(dbfilepath)
        creator=lambda:sqlite3.connect(f"file:{dbfilepath}?mode=ro",uri=True)
        return SQLDatabase(create_engine("sqlite:///",creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))    
    
if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)    

toolkit=SQLDatabaseToolkit(db=db,llm=llm)      

agent=create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
   
)

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role":"assistant","content":"How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query=st.chat_input(placeholder="Ask anything from the database")    

if user_query:
    st.session_state.messages.append({"role":"user","content":"user_query"})
    st.chat_message("user").write(user_query)



    with st.chat_message("assistant"):
        streamlit_callback=StreamlitCallbackHandler(st.container())
        response=agent.run(user_query,callbacks=[streamlit_callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)




