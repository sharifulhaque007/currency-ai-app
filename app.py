import streamlit as st
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.runners import InMemoryRunner
from google.adk.code_executors import BuiltInCodeExecutor
from pydantic import BaseModel, Field
import asyncio
import os

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
# Tool
# -------------------------
class CurrencyConverter(AgentTool):
    name: str = "usd_to_bdt"
    description: str = "Convert USD to Bangladeshi Taka"
    args_schema = ConvertArgs

    async def run(self, args: ConvertArgs):
        rate = 120
        return {"result": f"{args.amount * rate} BDT"}

# -------------------------
# Setup Model + Agent
# -------------------------
model = Gemini(model="gemini-2.0-flash")

agent = LlmAgent(
    name="currency_bot",
    model=model,
    instruction="You convert USD to BDT. If conversion request comes, use the tool."
)

tool = CurrencyConverter(agent=agent)
agent.tools.append(tool)

runner = InMemoryRunner(agent=agent)

# -------------------------
# UI
# -------------------------
st.title("💱 AI Currency Converter")
user_input = st.text_input("Ask something:", "Convert 50 USD to BDT")

if st.button("Convert"):
    # Safe async execution in Streamlit
    async def run_agent():
        return await runner.run(user_input)
    
    response = asyncio.run(run_agent())
    st.write(response)
