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
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Fails gracefully if style.css is missing

# 1. Updated Page Config for Movie Theme
st.set_page_config(page_title="AI Movie Recommender", page_icon="🍿", layout="wide")

cargar_css("style.css")

# 2. Updated Titles
st.title("AI Movie Recommender & Searcher")

with st.sidebar:
    st.header("Configuration")
    google_api_key = st.text_input("Google API Key", type="password", help="Required to use Gemini.")
    st.markdown("Get your key at [Google AI Studio](https://aistudio.google.com/).")
    st.divider()
    if st.button("Clear History"):
        st.session_state.messages = []
        st.session_state.store = {}
        st.rerun()

# 3. Updated Onboarding Text
if not google_api_key:
    st.markdown("""
    This agent is a specialized **Cinema Expert** designed to recommend movies, look up cast and crew, and find the latest ratings.
    
    **What it can do:**
    * **IMDb & Web Search:** Uses DuckDuckGo to search for movie ratings (like IMDb/Rotten Tomatoes), latest cinema news, and reviews.
    * **Wikipedia Deep Dives:** Fetches detailed plot summaries, cast lists, and trivia from Wikipedia.
    * **Tailored Recommendations:** Remembers your chat history to give you personalized movie suggestions based on your taste!

    **To get started:**
                
    Please enter your **Google API Key** in the sidebar.
    """)
    st.stop()

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
    
    # 4. Drastically updated System Prompt to force the Cinema Expert persona
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an enthusiastic and highly knowledgeable AI Movie Recommender and Cinema Expert. "
                   "Based on the user's query and chat history, use the search tools to look up movie details, "
                   "find IMDb or Rotten Tomatoes ratings via DuckDuckGo, or retrieve deep lore and cast details via Wikipedia. "
                   "If the user asks for recommendations, provide a curated list of movies with short, spoiler-free "
                   "synopses, their genres, and why they fit the user's request. Format your answers beautifully using markdown."),
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

# 5. Themed Avatars
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🎬"
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

if user_input := st.chat_input("Ask for a movie recommendation or search for a film..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar="👤").write(user_input)

    with st.chat_message("assistant", avatar="🎬"):
        # 6. Themed Spinner
        with st.spinner("Grabbing the popcorn and searching..."):
            response = agent_with_history.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "default_session"}}
            )
            
            final_answer = response["output"]
            st.write(final_answer)
            
            st.session_state.messages.append({"role": "assistant", "content": final_answer})