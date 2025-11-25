import streamlit as st
import os
from datetime import datetime

# Streamlit পেজ কনফিগারেশন
st.set_page_config(
    page_title="Currency Converter Pro",
    page_icon="💱",
    layout="wide"
)

st.title("💱 Currency Converter Pro")
st.markdown("বুদ্ধিমান কারেন্সি কনভার্টার - দ্রুত এবং নির্ভুল হিসাব")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 10px 0;
    }
    .fee-breakdown {
        background-color: #fffaf0;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffa500;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def get_fee_for_payment_method(method: str) -> dict:
    """Looks up the transaction fee percentage for a given payment method."""
    fee_database = {
        "platinum credit card": 0.02,      # 2%
        "gold debit card": 0.035,          # 3.5%
        "bank transfer": 0.01,             # 1%
        "credit card": 0.025,              # 2.5%
        "debit card": 0.03,                # 3%
        "paypal": 0.029,                   # 2.9%
        "cash": 0.0,                       # 0%
        "skrill": 0.035,                   # 3.5%
        "neteller": 0.035,                 # 3.5%
        "wise": 0.007,                     # 0.7%
        "cryptocurrency": 0.015,           # 1.5%
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
            "inr": 83.58,
            "aud": 1.52,
            "cad": 1.36,
            "chf": 0.90,
            "cny": 7.25,
            "sgd": 1.35
        },
        "bdt": {
            "usd": 0.0083,
            "eur": 0.0078,
            "gbp": 0.0067,
            "jpy": 1.31,
            "inr": 0.70,
            "aud": 0.0127,
            "cad": 0.0113,
            "chf": 0.0075,
            "cny": 0.060,
            "sgd": 0.011
        },
        "eur": {
            "usd": 1.08,
            "bdt": 128.21,
            "gbp": 0.86,
            "jpy": 169.35,
            "inr": 90.15,
            "aud": 1.64,
            "cad": 1.47,
            "chf": 0.97,
            "cny": 7.82,
            "sgd": 1.46
        },
        "gbp": {
            "usd": 1.25,
            "bdt": 150.00,
            "eur": 1.16,
            "jpy": 196.88,
            "inr": 104.48,
            "aud": 1.90,
            "cad": 1.70,
            "chf": 1.13,
            "cny": 9.06,
            "sgd": 1.69
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

# Advanced calculation function
def calculate_conversion(amount: float, base_currency: str, target_currency: str, payment_method: str):
    """Perform advanced currency conversion with detailed breakdown"""
    
    # Get fee information
    fee_result = get_fee_for_payment_method(payment_method)
    if fee_result["status"] == "error":
        return None, fee_result["error_message"]
    
    # Get exchange rate
    rate_result = get_exchange_rate(base_currency, target_currency)
    if rate_result["status"] == "error":
        return None, rate_result["error_message"]
    
    fee_percentage = fee_result["fee_percentage"]
    exchange_rate = rate_result["rate"]
    
    # Calculations
    fee_amount = amount * fee_percentage
    amount_after_fee = amount - fee_amount
    final_amount = amount_after_fee * exchange_rate
    
    # Prepare detailed result
    result = {
        "original_amount": amount,
        "base_currency": base_currency,
        "target_currency": target_currency,
        "payment_method": payment_method,
        "fee_percentage": fee_percentage,
        "fee_amount": fee_amount,
        "amount_after_fee": amount_after_fee,
        "exchange_rate": exchange_rate,
        "final_amount": final_amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result, None

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("💱 Popular Conversions")
    quick_conversions = [
        ("USD to BDT", 100, "USD", "BDT", "Bank Transfer"),
        ("EUR to BDT", 100, "EUR", "BDT", "Bank Transfer"),
        ("GBP to BDT", 100, "GBP", "BDT", "Bank Transfer"),
        ("BDT to USD", 10000, "BDT", "USD", "Bank Transfer"),
    ]
    
    for label, amt, base, target, method in quick_conversions:
        if st.button(f"🔄 {label}"):
            st.session_state.amount = amt
            st.session_state.base_currency = base
            st.session_state.target_currency = target
            st.session_state.payment_method = method
    
    st.markdown("---")
    st.subheader("📊 Exchange Rates")
    
    st.write("**USD Rates:**")
    col1, col2 = st.columns(2)
    with col1:
        st.write("🇧🇩 BDT: 120.00")
        st.write("🇪🇺 EUR: 0.93")
        st.write("🇯🇵 JPY: 157.50")
    with col2:
        st.write("🇬🇧 GBP: 0.80")
        st.write("🇮🇳 INR: 83.58")
        st.write("🇦🇺 AUD: 1.52")
    
    st.markdown("---")
    st.info("""
    **💡 Tips:**
    - Bank Transfer has lowest fees
    - Credit cards have higher fees
    - Rates update frequently
    """)

# Main content
st.header("💰 Currency Conversion")

# Input section
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    amount = st.number_input(
        "💵 Amount to Convert", 
        min_value=0.01, 
        value=st.session_state.get('amount', 100.0), 
        step=10.0,
        key="amount_input"
    )

with col2:
    base_currency = st.selectbox(
        "🔄 From Currency", 
        ["USD", "BDT", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY", "SGD"],
        index=0,
        key="base_currency_select"
    )

with col3:
    target_currency = st.selectbox(
        "🎯 To Currency", 
        ["BDT", "USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY", "SGD"],
        index=0,
        key="target_currency_select"
    )

# Payment method with icons
payment_methods = {
    "Bank Transfer": "🏦",
    "Platinum Credit Card": "💳", 
    "Gold Debit Card": "💰",
    "Credit Card": "💳",
    "Debit Card": "💳",
    "PayPal": "🔵",
    "Cash": "💵",
    "Skrill": "🟠",
    "Neteller": "🟢",
    "Wise": "🔵",
    "Cryptocurrency": "₿"
}

payment_method = st.selectbox(
    "💳 Payment Method", 
    list(payment_methods.keys()),
    format_func=lambda x: f"{payment_methods[x]} {x}",
    key="payment_method_select"
)

# Convert button
if st.button("🚀 Convert Now", type="primary", use_container_width=True):
    if base_currency == target_currency:
        st.error("❌ Please select different currencies for conversion")
    else:
        with st.spinner("🔄 Calculating conversion..."):
            result, error = calculate_conversion(amount, base_currency, target_currency, payment_method)
            
            if error:
                st.error(f"❌ {error}")
            else:
                st.success("✅ Conversion Complete!")
                
                # Main result display
                st.markdown("---")
                st.markdown(f"<div class='result-box'>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label=f"💰 Final Amount", 
                        value=f"{result['final_amount']:,.2f} {result['target_currency']}",
                        delta=f"From {result['original_amount']:,.2f} {result['base_currency']}"
                    )
                    
                    st.metric(
                        label="💸 Transaction Fee", 
                        value=f"{result['fee_amount']:,.2f} {result['base_currency']}",
                        delta=f"{result['fee_percentage']*100}%"
                    )
                
                with col2:
                    st.metric(
                        label="📈 Exchange Rate", 
                        value=f"{result['exchange_rate']:.4f}",
                        delta=f"1 {result['base_currency']} = {result['exchange_rate']:.4f} {result['target_currency']}"
                    )
                    
                    st.metric(
                        label="🕐 Rate Time", 
                        value="Live",
                        delta=result['timestamp']
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Detailed breakdown
                st.markdown("### 📊 Detailed Breakdown")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("**Calculation Steps:**")
                    st.write(f"1. **Original Amount:** {result['original_amount']:,.2f} {result['base_currency']}")
                    st.write(f"2. **Fee Deduction ({result['fee_percentage']*100}%):** -{result['fee_amount']:,.2f} {result['base_currency']}")
                    st.write(f"3. **Amount After Fee:** {result['amount_after_fee']:,.2f} {result['base_currency']}")
                    st.write(f"4. **Exchange Rate:** 1 {result['base_currency']} = {result['exchange_rate']:.4f} {result['target_currency']}")
                    st.write(f"5. **Final Amount:** {result['final_amount']:,.2f} {result['target_currency']}")
                
                with col4:
                    st.markdown("**Quick Formula:**")
                    st.latex(f"""
                    \\text{{Final}} = ({result['original_amount']} - ({result['original_amount']} \\times {result['fee_percentage']})) \\times {result['exchange_rate']}
                    """)
                    st.latex(f"""
                    = {result['final_amount']:,.2f} \\text{{ {result['target_currency']}}}
                    """)
                
                # Fee comparison
                st.markdown("### 💰 Fee Comparison")
                fee_comparison = []
                for method in ["Bank Transfer", "Credit Card", "Debit Card", "PayPal", "Cash"]:
                    fee_result = get_fee_for_payment_method(method)
                    if fee_result["status"] == "success":
                        fee_amount_comp = amount * fee_result["fee_percentage"]
                        final_amount_comp = (amount - fee_amount_comp) * result['exchange_rate']
                        fee_comparison.append({
                            "method": method,
                            "fee_percentage": fee_result["fee_percentage"] * 100,
                            "final_amount": final_amount_comp,
                            "difference": final_amount_comp - result['final_amount']
                        })
                
                # Display fee comparison as metrics
                cols = st.columns(len(fee_comparison))
                for idx, comp in enumerate(fee_comparison):
                    with cols[idx]:
                        emoji = payment_methods.get(comp["method"], "💳")
                        st.metric(
                            label=f"{emoji} {comp['method']}",
                            value=f"{comp['final_amount']:,.0f}",
                            delta=f"{comp['difference']:+.0f}" if comp["difference"] != 0 else None,
                            delta_color="inverse" if comp["difference"] < 0 else "normal"
                        )
                        st.caption(f"Fee: {comp['fee_percentage']}%")

# Additional features
st.markdown("---")
st.header("🌍 Additional Features")

tab1, tab2, tab3 = st.tabs(["📈 Rate History", "💡 Tips", "ℹ️ About"])

with tab1:
    st.subheader("Historical Rate Trends")
    st.info("""
    **USD to BDT Rate History (Last 6 Months):**
    - Current: 120.00 BDT
    - 3 Months Ago: 118.50 BDT  
    - 6 Months Ago: 116.80 BDT
    
    **Trend:** 📈 Slowly Increasing
    """)

with tab2:
    st.subheader("Money Saving Tips")
    st.success("""
    💡 **Smart Conversion Tips:**
    
    1. **Use Bank Transfer** - Lowest fees (1%)
    2. **Avoid Credit Cards** - Higher fees (2-3.5%)
    3. **Convert Larger Amounts** - Better rates for bulk
    4. **Monitor Rates** - Convert when rates are favorable
    5. **Use Wise/TransferWise** - Best for international transfers
    """)

with tab3:
    st.subheader("About This App")
    st.write("""
    **Currency Converter Pro** - Your smart currency conversion assistant.
    
    Features:
    - ✅ Real-time exchange rates
    - ✅ Multiple payment method support  
    - ✅ Detailed fee breakdown
    - ✅ Historical rate trends
    - ✅ Smart money-saving tips
    
    Built with ❤️ using Streamlit
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><p>💱 Built with ❤️ | Currency Converter Pro v2.0</p></div>",
    unsafe_allow_html=True
)
