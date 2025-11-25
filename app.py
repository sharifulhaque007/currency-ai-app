import os
import streamlit as st
import asyncio

from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from pydantic import BaseModel, Field

# -------------------------
# Load API Key safely
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
    tools=[],
)

# Add tool
tool = CurrencyConverter(agent=agent)
agent.tools.append(tool)

runner = InMemoryRunner(agent=agent)

# -------------------------
# UI
# -------------------------
st.title("💱 AI Currency Converter")

user_input = st.text_input("Amount in USD:", "50")

def run_agent(amount_usd: float):
    """
    Run CurrencyConverter tool synchronously from Streamlit
    """
    # Create Pydantic args object
    args = ConvertArgs(amount=float(amount_usd))
    # Run the tool via runner
    return asyncio.run(tool.run(args))

if st.button("Convert"):
    try:
        response = run_agent(user_input)
        st.write(response)
    except Exception as e:
        st.error(f"❌ Error: {e}")
