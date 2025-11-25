import streamlit as st
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import AgentTool
from pydantic import BaseModel, Field
import os


# ------------------------------
# Load API Key
# ------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("❌ API key missing in Streamlit Secrets!")
    st.stop()


# ------------------------------
# Custom Tool: USD ➜ BDT Converter
# ------------------------------
class ConvertArgs(BaseModel):
    usd: float = Field(..., description="Amount of USD")


class CurrencyConverter(AgentTool):
    name: str = "convert_usd_to_bdt"
    description: str = "Convert USD to Bangladeshi Taka"
    args_schema = ConvertArgs

    def run(self, args: ConvertArgs):
        rate = 120   # change later if live API added
        return {"bdt": args.usd * rate}


# ------------------------------
# LLM Model Setup
# ------------------------------
model = Gemini(model="gemini-2.0-flash")


agent = LlmAgent(
    model=model,
    tools=[CurrencyConverter()],
    code_executor=BuiltInCodeExecutor(),
    instructions=[
        "You are a currency conversion assistant.",
        "If a USD amount is given, convert it using the tool."
    ]
)

runner = InMemoryRunner(agent=agent)


# ------------------------------
# Streamlit UI
# ------------------------------
st.title("💱 Currency Converter AI")
st.write("Convert USD → BDT using AI tool")

user_input = st.text_input("Enter USD amount to convert:")

if st.button("Convert"):
    if not user_input.strip():
        st.warning("⚠ Please enter a value")
    else:
        response = runner.run(user_input)
        st.success(response)
