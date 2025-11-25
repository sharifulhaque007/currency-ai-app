import streamlit as st
import asyncio
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# -------------------------
#  CONFIG
# -------------------------
API_KEY = st.secrets["GOOGLE_API_KEY"]

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    max_delay=45,
)

model = Gemini(
    model_name="gemini-2.0-flash",
    api_key=API_KEY,
    http_retry=retry_config,
)

# -------------------------
#  CUSTOM TOOL EXAMPLE
# -------------------------
class exchangerate(AgentTool):
    name: str = "exchange_rate"
    description: str = "Convert USD to BDT using fixed multiplier"
    args_schema: type = dict

    def run(self, amount: dict) -> dict:
        value = amount.get("usd", 0)
        return {"bdt": value * 120}


# -------------------------
#  LLM AGENT
# -------------------------
agent = LlmAgent(
    model=model,
    tools=[exchangerate()],
    code_executor=BuiltInCodeExecutor(),
    instructions=[
        "You are a currency converter bot.",
        "If user gives USD amount convert it using the tool."
    ],
)

runner = InMemoryRunner(agent=agent)


# -------------------------
#  ASYNC HELPER
# -------------------------
def run_async(task):
    """Safely run async code inside Streamlit."""
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(task)
    except RuntimeError:
        return asyncio.run(task)


# -------------------------
#  UI
# -------------------------
st.title("💱 Currency AI Convertor")

user_input = st.text_input("Enter text or amount to convert:")

if st.button("Convert"):
    response = run_async(runner.run(user_input))
    st.write(response)
