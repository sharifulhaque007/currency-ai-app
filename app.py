import os
import streamlit as st
import asyncio
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# -------------------------
# API Key
# -------------------------
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("❌ GOOGLE_API_KEY missing in Streamlit Secrets")
    st.stop()

# -------------------------
# Tools
# -------------------------
def get_fee_for_payment_method(method: str) -> dict:
    fee_database = {
        "platinum credit card": 0.02,
        "gold debit card": 0.035,
        "bank transfer": 0.01,
    }
    fee = fee_database.get(method.lower())
    if fee is not None:
        return {"status": "success", "fee_percentage": fee}
    return {"status": "error", "error_message": f"Payment method '{method}' not found"}

def get_exchange_rate(base_currency: str, target_currency: str) -> dict:
    rate_database = {
        "usd": {"bdt": 120.00, "inr": 83.58, "eur": 0.93},
        "bdt": {"usd": 0.008, "inr": 0.80, "eur": 0.009},
    }
    rate = rate_database.get(base_currency.lower(), {}).get(target_currency.lower())
    if rate is not None:
        return {"status": "success", "rate": rate}
    return {"status": "error", "error_message": "Unsupported currency pair"}

# -------------------------
# Calculation Agent
# -------------------------
calculation_agent = LlmAgent(
    name="CalculationAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="Return ONLY a Python code block that prints the answer."
)

# -------------------------
# Main Currency Agent
# -------------------------
enhanced_currency_agent = LlmAgent(
    name="enhanced_currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="You are a currency converter assistant. Follow rules strictly.",
    tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)],
)

runner = InMemoryRunner(agent=enhanced_currency_agent)

# -------------------------
# Streamlit UI
# -------------------------
st.title("💱 AI Currency Converter")
user_input = st.text_input("Ask something like:", "Convert 500 USD to BDT using Gold Debit Card")

# -------------------------
# Safe Async runner
# -------------------------
def run_agent_sync(user_input: str):
    context = {"input": user_input}
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:  # No loop in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(runner.run(context))

if st.button("Convert"):
    response = run_agent_sync(user_input)
    st.write(response)
