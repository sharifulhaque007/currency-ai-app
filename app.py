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

# API key setup
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

# Helper functions - আপনার Kaggle code থেকে exactly
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

# আপনার Kaggle notebook এর exact code adapt করা
async def run_currency_conversion_kaggle(query):
    """Your exact Kaggle notebook code adapted for Streamlit"""
    try:
        # Retry config - আপনার Kaggle code থেকে
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        # Calculation Agent - আপনার Kaggle code থেকে
        calculation_agent = LlmAgent(
            name="CalculationAgent",
            model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
            instruction="""You are a specialized calculator that ONLY responds with Python code. You are forbidden from providing any text, explanations, or conversational responses.
            
            Your task is to take a request for a calculation and translate it into a single block of Python code that calculates the answer.
            
            **RULES:**
            1. Your output MUST be ONLY a Python code block.
            2. Do NOT write any text before or after the code block.
            3. The Python code MUST calculate the result.
            4. The Python code MUST print the final result to stdout.
            5. You are PROHIBITED from performing the calculation yourself. Your only job is to generate the code that will perform the calculation.
            
            Failure to follow these rules will result in an error.
            """,
            code_executor=BuiltInCodeExecutor(),
        )

        # Enhanced Currency Agent - আপনার Kaggle code থেকে
        enhanced_currency_agent = LlmAgent(
            name="enhanced_currency_agent",
            model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
            instruction="""You are a smart currency conversion assistant. You must strictly follow these steps and use the available tools.

            For any currency conversion request:

            1. Get Transaction Fee: Use the get_fee_for_payment_method() tool to determine the transaction fee.
            2. Get Exchange Rate: Use the get_exchange_rate() tool to get the currency conversion rate.
            3. Error Check: After each tool call, you must check the "status" field in the response. If the status is "error", you must stop and clearly explain the issue to the user.
            4. Calculate Final Amount (CRITICAL): You are strictly prohibited from performing any arithmetic calculations yourself. You must use the calculation_agent tool to generate Python code that calculates the final converted amount. This 
            code will use the fee information from step 1 and the exchange rate from step 2.
            5. Provide Detailed Breakdown: In your summary, you must:
                * State the final converted amount.
                * Explain how the result was calculated, including:
                    * The fee percentage and the fee amount in the original currency.
                    * The amount remaining after deducting the fee.
                    * The exchange rate applied.
            """,
            tools=[
                get_fee_for_payment_method,
                get_exchange_rate,
                AgentTool(agent=calculation_agent),
            ],
        )

        # Runner তৈরি করুন - আপনার Kaggle code মতো
        enhanced_runner = InMemoryRunner(agent=enhanced_currency_agent)
        
        # Kaggle notebook এ আপনি await currency_runner.run_debug() ব্যবহার করেছেন
        # Streamlit এ আমরা run_debug ব্যবহার করব
        response = await enhanced_runner.run_debug(input=query)
        return response
        
    except Exception as e:
        st.error(f"Kaggle style conversion error: {e}")
        return None

# Alternative approach - run_debug ছাড়া
async def run_conversion_direct(query):
    """Direct approach using the runner without debug"""
    try:
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        calculation_agent = LlmAgent(
            name="CalculationAgent",
            model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
            instruction="You output ONLY Python code for calculations.",
            code_executor=BuiltInCodeExecutor(),
        )

        currency_agent = LlmAgent(
            name="currency_agent",
            model=Gemini(model="gemini-1.5-flash", retry_options=retry_config),
            instruction="Convert currency using the available tools. Use calculator for all math.",
            tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)],
        )
        
        runner = InMemoryRunner(agent=currency_agent)
        
        # Try different method signatures
        try:
            # Method 1: Try without any parameters
            response = await runner.run_debug()
            return response
        except TypeError:
            try:
                # Method 2: Try with just the query
                response = await runner.run_debug(query)
                return response
            except TypeError:
                try:
                    # Method 3: Try run method instead
                    response = await runner.run(query)
                    return response
                except Exception as e:
                    st.error(f"All method attempts failed: {e}")
                    return None
        
    except Exception as e:
        st.error(f"Direct conversion error: {e}")
        return None

# Display response function - আপনার Kaggle helper function adapt করা
def show_python_code_and_result(response):
    """Your Kaggle notebook helper function adapted for Streamlit"""
    if not response:
        return
        
    # Check if response is a list (like in Kaggle) or an object
    if isinstance(response, list):
        messages = response
    elif hasattr(response, 'messages'):
        messages = response.messages
    else:
        st.write("Unknown response format:")
        st.write(response)
        return
        
    for i in range(len(messages)):
        message = messages[i]
        # Check if the response contains a valid function call result from the code executor
        if (hasattr(message, 'content') and 
            hasattr(message.content, 'parts') and 
            message.content.parts and 
            len(message.content.parts) > 0):
            
            part = message.content.parts[0]
            if (hasattr(part, 'function_response') and
                part.function_response and
                hasattr(part.function_response, 'response')):
                
                response_code = part.function_response.response
                if isinstance(response_code, dict) and "result" in response_code and response_code["result"] != "```":
                    if "tool_code" in response_code["result"]:
                        st.write("**Generated Python Code:**")
                        st.code(response_code["result"].replace("tool_code", ""), language="python")
                    else:
                        st.write("**Generated Python Response:**")
                        st.write(response_code["result"])
            elif hasattr(part, 'text') and part.text:
                # Display regular text response
                text = part.text.strip()
                if text:
                    if "```" in text:
                        st.code(text, language="python")
                    else:
                        st.write(text)

# Simple manual agent execution
async def manual_agent_execution(query):
    """Manual agent execution mimicking Kaggle"""
    try:
        # Create agents exactly like Kaggle
        calculation_agent = LlmAgent(
            name="CalculationAgent",
            model=Gemini(model="gemini-1.5-flash"),
            instruction="Output ONLY Python code for calculations. No text.",
            code_executor=BuiltInCodeExecutor(),
        )

        currency_agent = LlmAgent(
            name="currency_agent",
            model=Gemini(model="gemini-1.5-flash"),
            instruction="Convert currency. Use tools for fees, rates, and calculations.",
            tools=[get_fee_for_payment_method, get_exchange_rate, AgentTool(agent=calculation_agent)],
        )
        
        runner = InMemoryRunner(agent=currency_agent)
        
        # Try the exact Kaggle approach
        response = await runner.run_debug(query)
        return response
        
    except Exception as e:
        st.error(f"Manual agent error: {e}")
        return None

# Main UI
st.header("💰 Currency Conversion")

# Input fields
col1, col2 = st.columns(2)

with col1:
    amount = st.number_input(
        "Amount to Convert", 
        min_value=0.01, 
        value=100.0, 
        step=10.0
    )
    base_currency = st.selectbox(
        "From Currency", 
        ["USD", "BDT", "EUR", "GBP", "JPY", "INR"]
    )
    
with col2:
    target_currency = st.selectbox(
        "To Currency", 
        ["BDT", "USD", "EUR", "GBP", "JPY", "INR"]
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
        ]
    )

# Convert button
if st.button("🚀 Convert Currency", type="primary", use_container_width=True):
    if base_currency == target_currency:
        st.error("❌ Please select different currencies for conversion")
    else:
        with st.spinner("🔄 AI is processing your conversion..."):
            try:
                # Create the query
                query = f"Convert {amount} {base_currency} to {target_currency} using {payment_method}. Show me the precise calculation."
                
                # Try manual agent execution first
                st.write("Trying manual agent execution...")
                response = asyncio.run(manual_agent_execution(query))
                
                if response:
                    st.success("✅ Conversion Complete!")
                    st.markdown("---")
                    show_python_code_and_result(response)
                else:
                    st.error("❌ Manual agent failed. Showing manual calculation instead.")
                    
                # Always show manual calculation as fallback
                st.markdown("---")
                st.header("🔢 Manual Calculation Results")
                show_manual_calculation(amount, base_currency, target_currency, payment_method)
                        
            except Exception as e:
                st.error(f"❌ Error during conversion: {e}")
                st.markdown("---")
                st.header("🔢 Manual Calculation Results")
                show_manual_calculation(amount, base_currency, target_currency, payment_method)

# Manual calculation function
def show_manual_calculation(amount, base_currency, target_currency, payment_method):
    """Show manual calculation results"""
    try:
        # Get fee
        fee_result = get_fee_for_payment_method(payment_method)
        if fee_result["status"] == "error":
            st.error(f"❌ {fee_result['error_message']}")
            return
            
        fee_percentage = fee_result["fee_percentage"]
        fee_amount = amount * fee_percentage
        amount_after_fee = amount - fee_amount
        
        # Get exchange rate
        rate_result = get_exchange_rate(base_currency, target_currency)
        if rate_result["status"] == "error":
            st.error(f"❌ {rate_result['error_message']}")
            return
            
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
        
        # Show calculation breakdown
        st.markdown("### 📊 Calculation Breakdown")
        st.write(f"```")
        st.write(f"Original Amount: {amount} {base_currency}")
        st.write(f"Fee ({fee_percentage*100}%): {fee_amount:.2f} {base_currency}")
        st.write(f"Amount after fee: {amount_after_fee:.2f} {base_currency}")
        st.write(f"Exchange rate: 1 {base_currency} = {exchange_rate} {target_currency}")
        st.write(f"Final amount: {final_amount:.2f} {target_currency}")
        st.write(f"```")
        
    except Exception as e:
        st.error(f"Manual calculation error: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><p>Built with ❤️ using Streamlit and Google ADK</p></div>",
    unsafe_allow_html=True
)
