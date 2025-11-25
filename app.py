import os
import streamlit as st

from google.genai import types
from google.adk.tools import AgentTool
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.code_executors import BuiltInCodeExecutor
from pydantic import BaseModel, Field


# -------------------------
# Load API Key
# -------------------------
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("❌ GOOGLE_API_KEY missing in Streamlit Secrets")
    st.stop()


# -------------------------
# Tool Schema
# -------------------------
class ConvertArgs(BaseModel):
    amount: float = Field(..., description="Amount in USD")


# -------------------------
# Tool Definition
# -------------------------
class CurrencyConverter(AgentTool):
    name: str = "usd_to_bdt"
    description: str = "Convert USD to Bangladeshi Taka"
    args_schema = ConvertArgs

    async def run(self, args: ConvertArgs):
        rate = 120  # static exchange rate
        return {"bdt": args.amount * rate}


# -------------------------
# Model
# -------------------------
model = Gemini(model="gemini-2.0-flash")


# -------------------------
# Agent
# -------------------------
agent = LlmAgent(
    name="currency_bot",
    model=model,
    instructions="You help convert USD to BDT. Use the tool whenever conversion is asked.",
    tools=[], 
    code_executor=BuiltInCodeExecutor()
)

# attach tool (agent must exist first)
tool = CurrencyConverter(agent=agent)
agent.tools.append(tool)

# runner
runner = InMemoryRunner(agent=agent)


# -------------------------
# UI
# -------------------------
st.title("💱 AI Currency Converter")

user_input = st.text_input("Enter request:", "Convert 50 USD to BDT")

if st.button("Convert"):
    try:
        output = runner.run(user_input)
        st.success(output)
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
