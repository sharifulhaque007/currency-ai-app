import os
import streamlit as st
import anyio

from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
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
    instruction="You convert USD to BDT. Use the tool if a conversion request is given."
)
tool = CurrencyConverter(agent=agent)
agent.tools.append(tool)
runner = InMemoryRunner(agent=agent)

# -------------------------
# Streamlit UI
# -------------------------
st.title("💱 AI Currency Converter")
user_input = st.text_input("Ask something:", "Convert 50 USD to BDT")

if st.button("Convert"):
    # Safe async call from Streamlit main thread
    response = anyio.from_thread.run(runner.run, user_input)
    st.write(response)
