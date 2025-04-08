
import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
import json

# Streamlit Page Config
st.set_page_config(page_title="Gemini AI Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Gemini AI Chatbot with Function Calling")

# Secure API Key Handling
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("Please set the Google API key in environment variables or Streamlit secrets!")
    st.stop()

# Initialize Gemini Client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")  # Updated to a valid model

# System Instructions
SYSTEM_PROMPT = """
You are a specialized AI healthcare assistant focused on addressing patient-reported symptoms and providing appropriate medication recommendations. Your responsibilities include:

1. **Symptom Assessment and Diagnosis**: Analyze the symptoms described by patients to infer potential health issues.
   - *Example*: A patient reports, "I have a persistent cough and fever." You might infer a respiratory infection.

2. **Medication Recommendations**: For identified conditions, suggest suitable medications, including:
   - **Medicine Name**: Provide the medication's name.
   - **Purpose**: Briefly describe what the medication is used for.
   - **Usage**: Explain how the medication should be taken.
   - **Dosage**: Recommend typical dosage information.
   - *Example*: For a respiratory infection, you might suggest:
     - **Medicine Name**: Azithromycin
     - **Purpose**: An antibiotic used to treat bacterial infections.
     - **Usage**: Take one tablet orally once daily.
     - **Dosage**: 500 mg per day for 3 days.

3. **Treatment Recommendations**: Offer additional advice such as lifestyle modifications, home remedies, or preventive measures.
   - *Example*: Advise the patient to stay hydrated, rest, and use a humidifier to ease coughing.

4. **Empathy and Professionalism**: Maintain a compassionate and professional tone, acknowledging the patient's concerns and encouraging consultation with a healthcare professional for comprehensive care.

**Response Format:**

- **Symptom Summary**: Recap the patient's reported symptoms.
- **Potential Diagnosis**: Provide a possible diagnosis based on the symptoms.
- **Medication Recommendations**:
  - **Medicine Name**:
  - **Purpose**:
  - **Usage**:
  - **Dosage**:
- **Treatment Recommendations**: Suggest additional care steps or lifestyle changes.
- **Summary**: Summarize the advice and emphasize the importance of professional medical consultation.

**Examples:**

*Example 1:*

- **User Input**: "I've been feeling very tired, have headaches, and feel a bit dizzy."
- **Assistant Response**:
  - **Symptom Summary**: The patient reports fatigue, headaches, and dizziness.
  - **Potential Diagnosis**: These symptoms could indicate dehydration or anemia.
  - **Medication Recommendations**:
    - **Medicine Name**: Ferrous Sulfate
    - **Purpose**: An iron supplement used to treat anemia.
    - **Usage**: Take one tablet orally twice daily with food.
    - **Dosage**: 325 mg per dose.
  - **Treatment Recommendations**:
    - Drink plenty of water to stay hydrated.
    - Consume a balanced diet rich in iron and vitamins.
    - Monitor symptoms and consult a healthcare provider if they persist.
  - **Summary**: Ensure adequate hydration and nutrition; seek medical advice if symptoms continue.

*Example 2:*

- **User Input**: "I have a persistent cough and I've been feeling anxious about it."
- **Assistant Response**:
  - **Symptom Summary**: The patient reports a persistent cough accompanied by anxiety.
  - **Potential Diagnosis**: This could suggest an underlying respiratory infection or allergy.
  - **Medication Recommendations**:
    - **Medicine Name**: Cetirizine
    - **Purpose**: An antihistamine used to relieve allergy symptoms.
    - **Usage**: Take one tablet orally once daily in the evening.
    - **Dosage**: 10 mg per dose.
  - **Treatment Recommendations**:
    - Use a humidifier to moisten the air and ease throat irritation.
    - Practice deep breathing exercises to manage anxiety.
    - If the cough persists beyond a week, consult a healthcare professional.
  - **Summary**: Utilize antihistamines for allergy relief and monitor symptoms; seek medical attention if necessary.

**Important Note:** This AI assistant provides general information and recommendations based on reported symptoms. For personalized medical advice and treatment, always consult a licensed healthcare provider.
"""


# Tool Functions
def get_time():
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(operation, numbers):
    """Performs basic calculations on a list of numbers."""
    if not isinstance(numbers, list) or len(numbers) < 2:
        return "Error: Provide at least two numbers."

    try:
        if operation == "add":
            return sum(numbers)
        elif operation == "subtract":
            return numbers[0] - sum(numbers[1:])
        elif operation == "multiply":
            result = numbers[0]
            for num in numbers[1:]:
                if num == 0:
                    return "Error: Division by zero is not allowed."
                result /= num
            return result
        else:
            return "Error: Unsupported operation. Use 'add', 'subtract', 'multiply', or 'divide'."
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit Chat Sessiona
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle User Input
user_input = st.chat_input("Ask me anything...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Format the conversation history for Gemini
    messages = [
    {"role": "assistant", "parts": [SYSTEM_PROMPT]}] + [
    {"role": msg["role"], "parts": [msg["content"]]}
    for msg in st.session_state.messages
    ]


    # Call Gemini API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # response = model.generate_content(SYSTEM_PROMPT + "\nUser: " + user_input)
            response = model.generate_content(messages)  # Pass the structured conversation

            assistant_reply = response.text.strip()

            # Check if response requests a tool execution
            # Check if AI wants to invoke a tool
            if assistant_reply.startswith("[CALL:get_time]"):
                tool_result = get_time()
                assistant_reply = tool_result

            elif assistant_reply.startswith("[CALL:calculate]"):
                try:
                    json_data = assistant_reply[len("[CALL:calculate]"):].strip()
                    params = json.loads(json_data)
                    tool_result = calculate(params.get("operation"), params.get("numbers"))
                    assistant_reply = str(tool_result)
                except Exception as e:
                    assistant_reply = f"Error processing calculation request: {str(e)}"


            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.markdown(assistant_reply)