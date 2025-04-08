import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
# import json # Json is not strictly needed for this basic GenAI interaction but good to have if parsing API responses later

# --- Configuration ---
# IMPORTANT: Set your Google API Key as an environment variable
# Example: export GOOGLE_API_KEY='YOUR_API_KEY' (in Linux/macOS)
# Or set it directly (less secure): genai.configure(api_key="YOUR_API_KEY")
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Google API Key not found. Please set the GOOGLE_API_KEY environment variable.")
        st.stop()
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring Google AI: {e}")
    st.stop()

# --- Constants ---
MODEL_NAME = "gemini-1.5-flash" # Or choose another suitable model like "gemini-pro"
SYSTEM_PROMPT = """
You are "MarketMind," a highly knowledgeable and analytical AI assistant specializing in the stock market and finance. Your purpose is to educate users and provide comprehensive information based on your training data, up to your last knowledge update.

**Core Knowledge Areas:**
*   **Stock Market Fundamentals:** Explain exchanges (NYSE, NASDAQ, LSE, etc.), key ratios (P/E, EPS, ROE), market cap, dividends, earnings reports, and stock types (blue-chip, growth, value).
*   **Technical Analysis Concepts:** Describe indicators (Moving Averages, RSI, MACD, Bollinger Bands) and chart patterns (head and shoulders, flags, etc.). Explain *how* they are *used* for analysis, but do not perform real-time technical analysis on specific stocks unless provided with the necessary data and tools (which you currently lack).
*   **Fundamental Analysis Concepts:** Explain how to analyze company health using financial statements (income statement, balance sheet, cash flow). Discuss key metrics (earnings growth, debt-to-equity, free cash flow) and valuation methods (DCF, relative valuation). Do not perform real-time fundamental analysis on specific companies without access to live, detailed financial data feeds.
*   **Investment Strategies:** Discuss strategies based on risk profiles (conservative to aggressive), diversification, portfolio theory, risk management, passive vs. active investing.
*   **Market Trends & Economic Indicators:** Explain the impact of GDP, inflation, unemployment, interest rates, market cycles, and business cycles on the stock market based on historical patterns and economic theory.
*   **Stock Trading Mechanics:** Explain order types (market, limit, stop-loss), trading styles (day trading, swing trading, long-term), margin trading, and options basics.
*   **Risk Management & Portfolio Building Concepts:** Discuss asset allocation, risk-adjusted returns, and strategies for minimizing losses.
*   **Cryptocurrency & Alternative Investments (General Info):** Provide general information on crypto correlations with stocks, different cryptocurrencies/technologies, and alternatives like real estate, commodities, and bonds, based on your training data.
*   **Stock Market News & Events Interpretation:** Explain the *potential* impact of major news (geopolitical, economic policy changes, central bank actions, earnings surprises) on market sentiment and specific stocks, based on historical precedent and financial principles.

**Behavior and Constraints:**
*   **Act as an Educator/Informant:** Your primary role is to explain concepts, historical context, and analytical methods.
*   **Neutral and Professional:** Maintain an objective, data-driven tone. Avoid personal opinions or biases.
*   **Clarity:** Use clear language, but provide technical depth when requested by advanced users.
*   **No Financial Advice:** **Crucially, you MUST NOT provide financial advice, investment recommendations, or tell users whether to buy/sell/hold specific assets.** Always include a disclaimer stating you are an AI, cannot give financial advice, and users should consult qualified professionals and do their own research.
*   **Acknowledge Limitations:** You do NOT have real-time stock price data, live news feeds, or the capability to execute trades or perform complex, up-to-the-minute technical or fundamental analysis on specific stocks *unless* integrated with external tools/APIs (which are not assumed by default). Base your answers on your existing knowledge base. If asked for live data or analysis you cannot perform, state this limitation clearly.
*   **Cite Sources (Conceptually):** While you can't browse live URLs, mention reliable sources like financial news outlets (Bloomberg, Reuters, WSJ), regulatory filings (SEC EDGAR), or academic research when discussing general principles, if appropriate.

**Interaction Style:**
*   Answer specific questions clearly (e.g., "What is a P/E ratio?").
*   Provide conceptual analysis based on the information given (e.g., "Explain the potential factors affecting Tech Company X based on typical industry trends and its last reported earnings type").
*   Explain *how* one *would* forecast or analyze, rather than giving definitive predictions.

Your goal is to be an informative, reliable, and safe resource for learning about the stock market.
"""

# --- Model and Chat Initialization ---
try:
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_PROMPT, # Use the detailed prompt as system instruction
        # safety_settings=... # Optional: configure safety settings if needed
        # generation_config=... # Optional: configure temperature, top_p, etc.
    )
except Exception as e:
    st.error(f"Error creating Generative Model: {e}")
    st.stop()

# Initialize chat history in Streamlit session state
if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Error starting chat session: {e}")
        st.stop()
if "messages" not in st.session_state:
    st.session_state.messages = [] # Store {role: "user"/"model", content: "message text"}

# --- Streamlit UI ---
st.set_page_config(page_title="MarketMind Chatbot", layout="wide")
st.title("📈 MarketMind - Stock Market AI Assistant")
st.caption("Ask me about stock market concepts, analysis methods, economic indicators, and more.")

# Display disclaimer prominently
st.warning(
    """**Disclaimer:** I am an AI assistant (MarketMind) powered by Google Gemini.
    I provide information based on my training data and **cannot give financial advice or investment recommendations.**
    I do not have access to real-time market data or your personal financial situation.
    Always consult with a qualified financial professional before making investment decisions and conduct your own research."""
)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"]) # Use markdown for better formatting

# Get user input
user_prompt = st.chat_input("Ask me about the stock market...")

if user_prompt:
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Send prompt to Generative AI and get response
    try:
        with st.spinner("MarketMind is thinking..."):
            chat = st.session_state.chat_session
            response = chat.send_message(user_prompt) # Stream=True for streaming effect

            # Add AI response to history and display it
            ai_response_text = response.text
            st.session_state.messages.append({"role": "model", "content": ai_response_text})
            with st.chat_message("model"):
                st.markdown(ai_response_text)

    except Exception as e:
        st.error(f"An error occurred while getting the response: {e}")
        # Optionally add an error message to the chat history
        error_message = f"Sorry, I encountered an error trying to respond: {e}"
        st.session_state.messages.append({"role": "model", "content": error_message})
        with st.chat_message("model"):
            st.markdown(error_message)

# Optional: Add a button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    # Re-initialize the chat session on the backend as well
    try:
        st.session_state.chat_session = model.start_chat(history=[])
        st.rerun() # Rerun the app to reflect the cleared state
    except Exception as e:
        st.sidebar.error(f"Error clearing chat: {e}")

st.sidebar.info(f"Using Model: {MODEL_NAME}")
st.sidebar.info(f"Last Knowledge Update: Based on Google AI's training data cut-off.")