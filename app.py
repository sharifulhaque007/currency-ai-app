import streamlit as st
import asyncio
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor
import os

# -------------------------
# API Key
# -------------------------
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("❌ GOOGLE_API_KEY missing")
    st.stop()

# -------------------------
# Example tools
# -------------------------
def get_fee(method: str) -> dict:
    return {"status": "success", "fee_percentage": 0.02}

def get_rate(base: str, target: str) -> dict:
    return {"status": "success", "rate": 120}

# -------------------------
# Agents
# -------------------------
calc_agent = LlmAgent(
    name="calc",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="Return ONLY a Python code block that prints the answer."
)

currency_agent = LlmAgent(
    name="currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="Convert currencies using tools",
    tools=[get_fee, get_rate, AgentTool(agent=calc_agent)]
)

runner = InMemoryRunner(agent=currency_agent)

# -------------------------
# Streamlit UI
# -------------------------
st.title("💱 AI Currency Converter")
user_input = st.text_input("Ask:", "Convert 50 USD to BDT")

def run_agent_sync(user_input: str):
    context = {"input": user_input}
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(runner.run(context))

if st.button("Convert"):
    result = run_agent_sync(user_input)
    st.write(result)
