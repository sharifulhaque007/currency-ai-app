import streamlit as st
import os
import asyncio

# Streamlit পেজ কনফিগারেশন
st.set_page_config(
    page_title="Currency Converter AI",
    page_icon="💱",
    layout="centered"
)

st.title("💱 AI Currency Converter")
st.markdown("এই অ্যাপ্লিকেশনটি আপনাকে বিভিন্ন কারেন্সি কনভার্ট করতে সাহায্য করবে।")

# API key setup - সাইডবারে রাখলাম better UX এর জন্য
with st.sidebar:
    st.header("🔐 Configuration")
    api_key = st.text_input("Google API Key", type="password", key="api_key")
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API Key configured!")
        
        st.markdown("---")
        st.subheader("💡 Help")
        st.info("""
        **How to use:**
        1. Enter API Key
        2. Select currencies & amount
        3. Click Convert button
        4. View AI-powered results
        """)

# API key না থাকলে বাকি部分 দেখাবে না
if not api_key:
    st.warning("⚠️ Please enter your Google API Key in the sidebar to continue")
    
    # Demo information show করবে
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Supported Payment Methods")
        st.write("""
        - Bank Transfer (1% fee)
        - Platinum Credit Card (2% fee) 
        - Gold Debit Card (3.5% fee)
        - Credit Card (2.5% fee)
        - Debit Card (3% fee)
        - PayPal (2.9% fee)
        - Cash (0% fee)
        """)
    
    with col2:
        st.subheader("🌍 Supported Currencies")
        st.write("""
        - USD (US Dollar)
        - BDT (Bangladeshi Taka)
        - EUR (Euro)
        - GBP (British Pound)
        - JPY (Japanese Yen)
        - INR (Indian Rupee)
        """)
    
    st.stop()

# API key থাকলে বাকি code load করবে
try:
    from google.genai import types
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.runners import InMemoryRunner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import AgentTool
    from google.adk.code_executors import BuiltInCodeExecutor
    
except ImportError as e:
    st.error(f"❌ Failed to import Google ADK: {e}")
    st.error("Please check if google-adk is installed: pip install google-adk")
    st.stop()

# Helper functions
def get_fee_for_payment_method(method: str) -> dict:
    """Looks up the transaction fee percentage for a given payment method."""
    fee_database = {
        "platinum credit card": 0.02,      # 2%
        "gold debit card": 0.035,          # 3.5%
        "bank transfer": 0.01,             # 1%
        "credit card": 0.025,              # 2.5%
        "debit card": 0.03,                # 3%
        "paypal": 0.029,                   # 2.9%
        "cash": 0.0                        # 0%
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
            "bdt": 120.00,
            "eur": 0.93,
            "gbp": 0.80,
            "jpy": 157.50,
            "inr": 83.58
        },
        "bdt": {
            "usd": 0.0083,
            "eur": 0.0078,
            "gbp": 0.0067,
            "jpy": 1.31,
            "inr": 0.70
        },
        "eur": {
            "usd": 1.08,
            "bdt": 128.21,
            "gbp": 0.86,
            "jpy": 169.35
        },
        "gbp": {
            "usd": 1.25,
            "bdt": 150.00,
            "eur": 1.16
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

# Agent setup function
def create_currency_agent():
    """Create the currency conversion agent with tools"""
    # Calculation Agent
    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(model="gemini-1.5-flash"),
        instruction="""You are a specialized calculator that ONLY responds with Python code.
        Rules:
        1. Output MUST be ONLY Python code
        2. No text before or after the code block  
        3. Code MUST calculate the result
        4. Code MUST print the final result
        Example input: "Calculate 100 * 0.02"
        Example output: 
        ```python
        result = 100 * 0.02
        print(result)
        ```""",
        code_executor=BuiltInCodeExecutor(),
    )

    # Main Currency Agent
    currency_agent = LlmAgent(
        name="currency_agent",
        model=Gemini(model="gemini-1.5-flash"),
        instruction="""You are a smart currency conversion assistant. Follow these steps strictly:

        1. FIRST use get_fee_for_payment_method() to get the transaction fee
        2. THEN use get_exchange_rate() to get the conversion rate  
        3. Check the "status" field in both responses - if "error", stop and explain
        4. FINALLY use the calculation_agent tool to perform ALL mathematical calculations
        5. Provide a clear breakdown showing:
           - Original amount
           - Fee percentage and amount
           - Amount after fee deduction
           - Exchange rate used
           - Final converted amount

        You are PROHIBITED from doing calculations yourself. Always use the calculation_agent.
        """,
        tools=[
            get_fee_for_payment_method,
            get_exchange_rate, 
            AgentTool(agent=calculation_agent),
        ],
    )
    
    return currency_agent

# Async conversion function - FIXED VERSION
async def run_conversion(query):
    """Run the currency conversion asynchronously"""
    try:
        agent = create_currency_agent()
        runner = InMemoryRunner(agent=agent)
        session_service = InMemorySessionService()
        
        # Create session with required parameters
        session = await session_service.create_session(
            app_name="currency_converter_app",
            user_id="streamlit_user_001"
        )
        
        # DEBUG: Session object inspect করুন
        st.sidebar.write("🔍 Session Info:")
        st.sidebar.write(f"Session Type: {type(session)}")
        st.sidebar.write(f"Session Attributes: {dir(session)}")
        
        # Try different possible session ID attributes
        session_id = None
        
        # Try different possible attribute names
        if hasattr(session, 'session_id'):
            session_id = session.session_id
        elif hasattr(session, 'id'):
            session_id = session.id
        elif hasattr(session, 'name'):
            session_id = session.name
        else:
            # If no session ID found, use the session object itself
            st.sidebar.warning("Using session object directly")
            response = await runner.run(session=session, input=query)
            return response
        
        st.sidebar.write(f"Using Session ID: {session_id}")
        
        # Run the conversion with session_id
        response = await runner.run(session_id=session_id, input=query)
        return response
        
    except Exception as e:
        st.error(f"Agent execution error: {e}")
        return None

# Alternative approach - Kaggle notebook style
async def kaggle_style_conversion(query):
    """Use the exact same approach as your Kaggle notebook"""
    try:
        # Replicate your exact Kaggle setup
        calculation_agent = LlmAgent(
            name="CalculationAgent",
            model=Gemini(model="gemini-1.5-flash"),
            instruction="""You output ONLY Python code. No text.""",
            code_executor=BuiltInCodeExecutor(),
        )

        currency_agent = LlmAgent(
            name="currency_agent", 
            model=Gemini(model="gemini-1.5-flash"),
            instruction="""Convert currency using tools. Use calculator for math.""",
            tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)],
        )
        
        runner = InMemoryRunner(agent=currency_agent)
        
        # Try the Kaggle notebook approach directly
        response = await runner.run(input=query)
        return response
        
    except Exception as e:
        st.error(f"Kaggle style error: {e}")
        return None

# Display response function
def display_response(response):
    """Display the agent response in a formatted way"""
    if response and hasattr(response, 'messages'):
        for message in response.messages:
            if hasattr(message, 'content') and hasattr(message.content, 'parts'):
                for part in message.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text = part.text.strip()
                        if text:
                            # Format code blocks
                            if "```python" in text or "```" in text:
                                st.code(text, language="python")
                            else:
                                st.write(text)

# Main UI
st.header("💰 Currency Conversion")

# Input fields
col1, col2 = st.columns(2)

with col1:
    amount = st.number_input(
        "Amount to Convert", 
        min_value=0.01, 
        value=100.0, 
        step=10.0,
        help="Enter the amount you want to convert"
    )
    base_currency = st.selectbox(
        "From Currency", 
        ["USD", "BDT", "EUR", "GBP", "JPY", "INR"],
        help="Select the currency you have"
    )
    
with col2:
    target_currency = st.selectbox(
        "To Currency", 
        ["BDT", "USD", "EUR", "GBP", "JPY", "INR"],
        help="Select the currency you want"
    )
    payment_method = st.selectbox(
        "Payment Method", 
        [
            "Bank Transfer", 
            "Platinum Credit Card", 
            "Gold Debit Card",
            "Credit Card",
            "Debit Card", 
            "PayPal",
            "Cash"
        ],
        help="Select your payment method for fee calculation"
    )

# Convert buttons with different approaches
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Convert (Standard)", type="primary", use_container_width=True):
        if base_currency == target_currency:
            st.error("❌ Please select different currencies for conversion")
        else:
            with st.spinner("🔄 AI is processing your conversion..."):
                try:
                    # Create the query
                    query = f"Convert {amount} {base_currency} to {target_currency} using {payment_method}. Provide detailed breakdown with all calculations."
                    
                    # Try the standard approach first
                    response = asyncio.run(run_conversion(query))
                    
                    # Display results
                    st.markdown("---")
                    if response:
                        st.success("✅ Conversion Complete!")
                        display_response(response)
                    else:
                        st.error("❌ No response received from the AI agent")
                        
                except Exception as e:
                    st.error(f"❌ Error during conversion: {e}")

with col2:
    if st.button("🔄 Convert (Kaggle Style)", use_container_width=True):
        if base_currency == target_currency:
            st.error("❌ Please select different currencies for conversion")
        else:
            with st.spinner("🔄 Using Kaggle notebook approach..."):
                try:
                    # Create the query
                    query = f"Convert {amount} {base_currency} to {target_currency} using {payment_method}. Provide detailed breakdown with all calculations."
                    
                    # Try Kaggle notebook approach
                    response = asyncio.run(kaggle_style_conversion(query))
                    
                    # Display results
                    st.markdown("---")
                    if response:
                        st.success("✅ Conversion Complete!")
                        display_response(response)
                    else:
                        st.error("❌ No response from Kaggle approach")
                        
                except Exception as e:
                    st.error(f"❌ Kaggle style error: {e}")

# Quick manual calculation fallback
st.markdown("---")
st.header("🔢 Quick Manual Preview")

if st.button("Show Manual Calculation", help="Quick calculation without AI"):
    try:
        # Get fee
        fee_result = get_fee_for_payment_method(payment_method)
        if fee_result["status"] == "error":
            st.error(f"❌ {fee_result['error_message']}")
            st.stop()
            
        fee_percentage = fee_result["fee_percentage"]
        fee_amount = amount * fee_percentage
        amount_after_fee = amount - fee_amount
        
        # Get exchange rate
        rate_result = get_exchange_rate(base_currency, target_currency)
        if rate_result["status"] == "error":
            st.error(f"❌ {rate_result['error_message']}")
            st.stop()
            
        exchange_rate = rate_result["rate"]
        final_amount = amount_after_fee * exchange_rate
        
        # Display manual results
        st.success("💰 Manual Calculation Results:")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.metric("Original Amount", f"{amount:.2f} {base_currency}")
            st.metric("Fee Percentage", f"{fee_percentage*100}%")
            st.metric("Fee Amount", f"{fee_amount:.2f} {base_currency}")
            
        with col4:
            st.metric("Amount After Fee", f"{amount_after_fee:.2f} {base_currency}")
            st.metric("Exchange Rate", f"{exchange_rate}")
            st.metric("Final Amount", f"{final_amount:.2f} {target_currency}")
        
    except Exception as e:
        st.error(f"Manual calculation error: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><p>Built with ❤️ using Streamlit and Google ADK</p></div>",
    unsafe_allow_html=True
)
