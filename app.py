import streamlit as st
from langchain.tools import BaseTool, tool
from langchain_core.tools import StructuredTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda

def cargar_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Agent", page_icon="🤖", layout="wide")

cargar_css("style.css")

st.title("Agent")

with st.sidebar:
    st.header("Configuration")
    google_api_key = st.text_input("Google API Key", type="password", help="Required to use Gemini.")
    st.markdown("Get you key at [Google AI Studio](https://aistudio.google.com/).")
    st.divider()
    if st.button("Clear History"):
        st.session_state.messages = []
        st.session_state.store = {}
        st.rerun()

if not google_api_key:
    st.markdown("""
    This agent is designed to answer your questions by autonomously searching the web and Wikipedia for the most accurate and up-to-date information.
    
    **What it can do:**
    * **Web Search:** Uses DuckDuckGo to find real-time news, current events, and general web results.
    * **Wikipedia Research:** Dives into Wikipedia to fetch detailed facts, summaries, and historical data.
    * **Contextual Memory:** It remembers your chat history, so you can ask natural follow-up questions.

    **To get started:**
    Please enter your **Google API Key** in the sidebar.
    """)

@st.cache_resource
def get_tools():
    search = DuckDuckGoSearchRun()
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return [search, wikipedia]

def get_session_history(session_id: str):
    if "store" not in st.session_state:
        st.session_state.store = {}
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = ChatMessageHistory()
    return st.session_state.store[session_id]

def ensure_string_output(agent_result: dict) -> dict:
    output_value = agent_result.get('output')
    if isinstance(output_value, list):
        concatenated_text = ""
        for item in output_value:
            if isinstance(item, dict) and item.get('type') == 'text':
                concatenated_text += item.get('text', '')
            elif isinstance(item, str):
                concatenated_text += item
        agent_result['output'] = concatenated_text
    elif not isinstance(output_value, str):
        agent_result['output'] = str(output_value)
    return agent_result

def initialize_agent(api_key):
    llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=api_key)
    tools = get_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Based on user query and the chat history, look for information using DuckDuckGo Search and Wikipedia and then give the final answer."),
        ("placeholder", "{history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    agent_executor_with_formatted_output = agent_executor | RunnableLambda(ensure_string_output)
    
    agent_with_history = RunnableWithMessageHistory(
        agent_executor_with_formatted_output,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    return agent_with_history

agent_with_history = initialize_agent(google_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking and using tools..."):
            response = agent_with_history.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "default_session"}}
            )
            
            final_answer = response["output"]
            st.write(final_answer)
            
            st.session_state.messages.append({"role": "assistant", "content": final_answer})