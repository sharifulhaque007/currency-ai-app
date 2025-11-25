import os
import streamlit as st
import anyio

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# ---------------- SAFE SECRET LOADING ----------------
def load_api_key():
    # Local environment variable support
    if os.getenv("GOOGLE_API_KEY"):
        return os.getenv("GOOGLE_API_KEY")
    
    # Streamlit Cloud secret support
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]

    # Clear error message if secret missing
    st.error("""
    ❌ GOOGLE_API_KEY not found!

    Fix this by going to:

    ▶️ Streamlit → Dashboard → App → Settings → Secrets

    And add EXACTLY:

    GOOGLE_API_KEY = "your_key_here"
    """)
    st.stop()

API_KEY = load_api_key()
os.environ["GOOGLE_API_KEY"] = API_KEY
# -----------------------------------------------------

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Tools
def get_fee_for_payment_method(method: str) -> dict:
    fee_database = {
        "platinum credit card": 0.02,
        "gold debit card": 0.035,
        "bank transfer": 0.01,
    }
    fee = fee_database.get(method.lower())
    if fee:
        return {"status": "success", "fee_percentage": fee}
    return {"status": "error", "error_message": f"Payment method '{method}' not found"}

def get_exchange_rate(base_currency: str, target_currency: str) -> dict:
    rate_database = {
        "usd": {"bdt": 120.00, "inr": 83.58, "eur": 0.93},
        "bdt": {"usd": 0.008, "inr": 0.80, "eur": 0.009},
    }
    base = base_currency.lower()
    target = target_currency.lower()
    rate = rate_database.get(base, {}).get(target)
    if rate:
        return {"status": "success", "rate": rate}
    return {"status": "error", "error_message": "Unsupported currency pair"}

# Agents
calculation_agent = LlmAgent(
    name="CalculationAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="Return ONLY a Python code block that prints the answer."
)

enhanced_currency_agent = LlmAgent(
    name="enhanced_currency_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You are a currency converter assistant. Follow rules strictly.",
    tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)]
)

runner = InMemoryRunner(agent=enhanced_currency_agent)

# Streamlit UI
st.title("💱 AI Currency Converter")
user_input = st.text_input("Ask something like:", "Convert 500 USD to BDT using Gold Debit Card")


if st.button("Convert"):

    async def safe_run():
        return await runner.run(user_input)

    try:
        # If Streamlit runtime already has loop
        response = asyncio.run(safe_run())
    except RuntimeError:
        # Fallback for Streamlit Cloud
        response = asyncio.get_event_loop().create_task(safe_run())

    st.write(response)
