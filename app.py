import streamlit as st
import os
import asyncio
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# Streamlit পেজ কনফিগারেশন
st.set_page_config(
    page_title="Currency Converter AI",
    page_icon="💱",
    layout="wide"
)

# টাইটেল এবং ডেস্ক্রিপশন
st.title("💱 AI Currency Converter")
st.markdown("""
এই অ্যাপ্লিকেশনটি আপনাকে বিভিন্ন কারেন্সি কনভার্ট করতে এবং পেমেন্ট মেথডের ফি হিসাব করতে সাহায্য করবে।
""")

# সাইডবারে API key ইনপুট
st.sidebar.header("🔐 Configuration")
api_key = st.sidebar.text_input("Google API_KEY", type="password")

if not api_key:
    st.warning("⚠️ Please enter your Google API Key in the sidebar to continue")
    st.stop()

# API key সেটআপ
try:
    os.environ["GOOGLE_API_KEY"] = api_key
    st.success("✅ API Key configured successfully!")
except Exception as e:
    st.error(f"❌ Error setting up API Key: {e}")
    st.stop()

# রিট্রি কনফিগারেশন
retry_config = types.HttpRetryOptions(
    attempts=3,
    exp_base=2,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Helper functions - আপনার Kaggle কোড থেকে
def get_fee_for_payment_method(method: str) -> dict:
    """Looks up the transaction fee percentage for a given payment method."""
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
        return {
            "status": "error",
            "error_message": f"Payment method '{method}' not found"
        }

def get_exchange_rate(base_currency: str, target_currency: str) -> dict:
    """Looks up and returns the exchange rate between two currencies."""
    rate_database = {
        "usd": {
            "eur": 0.93,
            "jpy": 157.50,
            "inr": 83.58,
            "bdt": 120.00,
            "gbp": 0.80,
            "aud": 1.52
        },
        "bdt": {
            "eur": 0.0078,
            "jpy": 1.31,
            "inr": 0.70,
            "usd": 0.0083,
            "gbp": 0.0067,
            "aud": 0.0127
        },
        "eur": {
            "usd": 1.08,
            "bdt": 128.21,
            "gbp": 0.86,
            "jpy": 169.35
        }
    }

    base = base_currency.lower()
    target = target_currency.lower()

    rate = rate_database.get(base, {}).get(target)
    if rate is not None:
        return {"status": "success", "rate": rate}
    else:
        return {
            "status": "error",
            "error_message": f"Unsupported currency pair: {base_currency}/{target_currency}"
        }

# Agents তৈরি করা
def setup_agents():
    """Setup all required agents"""
    # Calculation Agent
    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
        instruction="""You are a specialized calculator that ONLY responds with Python code.
        Your task is to take a request for a calculation and translate it into a single block of Python code.
        Rules:
        1. Output MUST be ONLY Python code
        2. No text before or after the code block
        3. Code MUST calculate the result
        4. Code MUST print the final result
        """,
        code_executor=BuiltInCodeExecutor(),
    )

    # Enhanced Currency Agent
    enhanced_currency_agent = LlmAgent(
        name="enhanced_currency_agent",
        model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
        instruction="""You are a smart currency conversion assistant. Follow these steps:
        1. Use get_fee_for_payment_method() for transaction fees
        2. Use get_exchange_rate() for conversion rates
        3. Check "status" field for errors
        4. Use calculation_agent for all calculations
        5. Provide detailed breakdown including fee percentage, fee amount, remaining amount, and exchange rate
        """,
        tools=[
            get_fee_for_payment_method,
            get_exchange_rate,
            AgentTool(agent=calculation_agent),
        ],
    )
    
    return enhanced_currency_agent

# Async function for running the agent
async def run_currency_conversion(query):
    """Run the currency conversion asynchronously"""
    try:
        # Agent setup
        agent = setup_agents()
        runner = InMemoryRunner(agent=agent)
        session_service = InMemorySessionService()
        
        # Create a new session with required parameters
        session = await session_service.create_session(
            app_name="currency_converter_app",
            user_id="streamlit_user"
        )
        
        # Run the query
        response = await runner.run(session=session, input=query)
        return response
        
    except Exception as e:
        st.error(f"Agent execution error: {e}")
        return None

# Helper function to display response
def display_response(response):
    """Display the agent response in a formatted way"""
    if not response:
        return
        
    for message in response.messages:
        if hasattr(message, 'content') and hasattr(message.content, 'parts'):
            for part in message.content.parts:
                if hasattr(part, 'text') and part.text:
                    # Format the response nicely
                    text = part.text
                    if "```" in text:
                        # Code block formatting
                        st.code(text, language="python")
                    else:
                        st.write(text)

# Streamlit UI
st.header("💰 Currency Conversion")

col1, col2 = st.columns(2)

with col1:
    amount = st.number_input("Amount", min_value=0.01, value=100.0, step=10.0)
    base_currency = st.selectbox("From Currency", ["USD", "BDT", "EUR", "GBP", "JPY", "INR", "AUD"])
    
with col2:
    target_currency = st.selectbox("To Currency", ["BDT", "USD", "EUR", "GBP", "JPY", "INR", "AUD"])
    payment_method = st.selectbox("Payment Method", [
        "Bank Transfer", 
        "Platinum Credit Card", 
        "Gold Debit Card",
        "Credit Card",
        "Debit Card",
        "PayPal",
        "Cash"
    ])

# কনভার্সান বাটন
if st.button("🚀 Convert Currency", type="primary"):
    if base_currency == target_currency:
        st.error("❌ Please select different currencies for conversion")
    else:
        with st.spinner("🔄 Processing your conversion..."):
            try:
                # Query তৈরি করুন
                query = f"Convert {amount} {base_currency} to {target_currency} using {payment_method}. Show me the precise calculation."
                
                # Async function run করুন
                response = asyncio.run(run_currency_conversion(query))
                
                if response:
                    st.success("✅ Conversion Complete!")
                    st.markdown("---")
                    display_response(response)
                else:
                    st.error("❌ No response received from the agent")
                
            except Exception as e:
                st.error(f"❌ Error during conversion: {e}")

# সরলীকৃত manual calculation (fallback)
st.markdown("---")
st.header("🔢 Quick Manual Calculation")

col3, col4 = st.columns(2)

with col3:
    st.subheader("💳 Payment Method Fees")
    fees_info = {
        "Bank Transfer": "1%",
        "Platinum Credit Card": "2%", 
        "Gold Debit Card": "3.5%",
        "Credit Card": "2.5%",
        "Debit Card": "3%",
        "PayPal": "2.9%",
        "Cash": "0%"
    }
    
    for method, fee in fees_info.items():
        st.write(f"**{method}**: {fee} fee")

with col4:
    st.subheader("🌍 Exchange Rates (Sample)")
    st.write("USD to BDT: 120.00")
    st.write("BDT to USD: 0.0083")
    st.write("USD to EUR: 0.93")
    st.write("EUR to BDT: 128.21")

# ফুটার
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit and Google ADK</p>
</div>
""", unsafe_allow_html=True)
