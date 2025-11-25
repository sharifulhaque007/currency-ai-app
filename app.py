import streamlit as st
import os
import asyncio

# Streamlit পেজ কনফিগারেশন
st.set_page_config(
    page_title="Currency Converter AI",
    page_icon="💱",
    layout="wide"
)

st.title("💱 AI Currency Converter")
st.markdown("এই অ্যাপ্লিকেশনটি আপনাকে বিভিন্ন কারেন্সি কনভার্ট করতে সাহায্য করবে।")

# API key setup
api_key = st.text_input("Google API Key", type="password")

if not api_key:
    st.warning("⚠️ Please enter your Google API Key to continue")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

try:
    from google.genai import types
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.runners import InMemoryRunner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import AgentTool
    from google.adk.code_executors import BuiltInCodeExecutor
    
    st.success("✅ Google ADK loaded successfully!")
    
except ImportError as e:
    st.error(f"❌ Failed to import Google ADK: {e}")
    st.stop()

# Helper functions
def get_fee_for_payment_method(method: str) -> dict:
    fee_database = {
        "platinum credit card": 0.02,
        "gold debit card": 0.035,
        "bank transfer": 0.01,
        "credit card": 0.025,
        "debit card": 0.03,
        "paypal": 0.029,
        "cash": 0.0
    }
    fee = fee_database.get(method.lower())
    if fee is not None:
        return {"status": "success", "fee_percentage": fee}
    else:
        return {"status": "error", "error_message": f"Payment method '{method}' not found"}

def get_exchange_rate(base_currency: str, target_currency: str) -> dict:
    rate_database = {
        "usd": {"bdt": 120.00, "eur": 0.93, "inr": 83.58},
        "bdt": {"usd": 0.0083, "eur": 0.0078, "inr": 0.70},
        "eur": {"usd": 1.08, "bdt": 128.21}
    }
    base = base_currency.lower()
    target = target_currency.lower()
    rate = rate_database.get(base, {}).get(target)
    if rate is not None:
        return {"status": "success", "rate": rate}
    else:
        return {"status": "error", "error_message": f"Unsupported currency pair: {base_currency}/{target_currency}"}

# Agent setup function
def create_currency_agent():
    # Calculation Agent
    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(model="gemini-1.5-flash"),
        instruction="""You are a calculator that outputs ONLY Python code. No explanations.""",
        code_executor=BuiltInCodeExecutor(),
    )

    # Main Currency Agent
    currency_agent = LlmAgent(
        name="currency_agent",
        model=Gemini(model="gemini-1.5-flash"),
        instruction="""You are a currency conversion assistant. Use the tools to:
        1. Get payment method fees
        2. Get exchange rates  
        3. Use calculator for math
        4. Provide detailed breakdown""",
        tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)],
    )
    
    return currency_agent

# Async conversion function
async def run_conversion(query):
    try:
        agent = create_currency_agent()
        runner = InMemoryRunner(agent=agent)
        session_service = InMemorySessionService()
        
        # Create session with required parameters
        session = await session_service.create_session(
            app_name="currency_converter",
            user_id="user_001"
        )
        
        # Run the conversion
        response = await runner.run(session=session, input=query)
        return response
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Streamlit UI
st.header("💰 Currency Conversion")

amount = st.number_input("Amount", value=100.0)
base_currency = st.selectbox("From", ["USD", "BDT", "EUR"])
target_currency = st.selectbox("To", ["BDT", "USD", "EUR"])
payment_method = st.selectbox("Payment Method", ["Bank Transfer", "Platinum Credit Card", "Gold Debit Card"])

if st.button("Convert"):
    if base_currency == target_currency:
        st.error("Please select different currencies")
    else:
        with st.spinner("Converting..."):
            query = f"Convert {amount} {base_currency} to {target_currency} using {payment_method}"
            response = asyncio.run(run_conversion(query))
            
            if response:
                st.success("Conversion Complete!")
                for message in response.messages:
                    if hasattr(message, 'content'):
                        for part in message.content.parts:
                            if hasattr(part, 'text'):
                                st.write(part.text)
            else:
                st.error("Conversion failed")

# Fallback manual calculator
st.header("🔢 Manual Calculator")
manual_amount = st.number_input("Manual Amount", value=100.0)
if st.button("Quick Calculate"):
    if base_currency == "USD" and target_currency == "BDT":
        result = manual_amount * 120
        st.info(f"${manual_amount} USD = {result:.2f} BDT")
    elif base_currency == "BDT" and target_currency == "USD":
        result = manual_amount * 0.0083
        st.info(f"{manual_amount} BDT = ${result:.4f} USD")
