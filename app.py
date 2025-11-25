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
# Currency Tool
# -------------------------
class ConvertArgs(BaseModel):
    usd: float = Field(..., description="Amount of USD")


class CurrencyConverter(AgentTool):
    name = "usd_to_bdt"
    description = "Convert USD to Bangladeshi Taka"
    args_schema = ConvertArgs

    def run(self, args: ConvertArgs):
        rate = 120  # static rate for now
        return {"bdt": args.usd * rate}


# -------------------------
# Model & Agent
# -------------------------
model = Gemini(model="gemini-2.0-flash")

agent = LlmAgent(
    name="CurrencyAgent",
    model=model,
    code_executor=BuiltInCodeExecutor(),
    tools=[],   # empty for now, will attach later
    instructions=[
        "You are a currency conversion agent.",
        "When someone asks conversion, call the tool."
    ]
)

# Tool must be registered AFTER agent exists
tool = CurrencyConverter(agent=agent)
agent.tools.append(tool)

runner = InMemoryRunner(agent=agent)


# -------------------------
# UI
# -------------------------
st.title("💱 AI Currency Converter")
query = st.text_input("Enter conversion query:", "Convert 40 USD to BDT")

if st.button("Convert"):
    response = runner.run(query)
    st.success(response)
