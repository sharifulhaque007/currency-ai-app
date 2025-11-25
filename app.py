import streamlit as st
import anyio
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# Dummy tools
def get_fee_for_payment_method(method: str):
    fee_db = {"gold debit card": 0.035, "platinum credit card": 0.02, "bank transfer": 0.01}
    fee = fee_db.get(method.lower())
    return {"status": "success", "fee_percentage": fee} if fee else {"status": "error", "error_message": "Not found"}

def get_exchange_rate(base, target):
    rates = {"usd": {"bdt": 120.0}, "bdt": {"usd": 0.008}}
    rate = rates.get(base.lower(), {}).get(target.lower())
    return {"status": "success", "rate": rate} if rate else {"status": "error", "error_message": "Not found"}

# Agents
calculation_agent = LlmAgent(
    name="calc_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="Return ONLY Python code block printing answer."
)

currency_agent = LlmAgent(
    name="currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="You are a currency assistant.",
    tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)]
)

runner = InMemoryRunner(agent=currency_agent)

# Streamlit UI
st.title("💱 AI Currency Converter")
user_input = st.text_input("Enter conversion request:", "Convert 500 USD to BDT using Gold Debit Card")

if st.button("Convert"):
    context = {"input": user_input}
    # async-safe call
    response = anyio.from_thread.run(runner.run, context)
    st.write(response)
