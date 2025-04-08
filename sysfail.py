# -*- coding: utf-8 -*-
"""
Chatbot Development Prompt: Self-Aware Error Analysis and Handling
(Integrated with Streamlit and Google Generative AI - Revised for Robustness)

[Original comprehensive prompt documentation remains here - omitted for brevity]

--- End of Prompt ---

Below is a revised Python implementation using Streamlit and Google Generative AI,
addressing potential error points.
"""

import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
import json
import random
from collections import Counter
import traceback # For logging detailed errors

# --- Configuration ---
KNOWLEDGE_FILE = "knowledge_base_genai.json"
LOG_FILE = "error_log_genai.json"
DEFAULT_FALLBACK_RESPONSES = [
    "I'm sorry, I encountered an issue or couldn't understand clearly. Could you please rephrase?",
    "Hmm, I'm having trouble with that request. Let's try something else.",
    "My apologies, I can't seem to process that right now.",
]
SIMULATED_FAILURE_RATE = 0.10 # 10% chance to simulate a failure for demo
REFUSAL_PHRASES = ["i cannot", "i am unable", "i don't have information", "my apologies, but i", "as an ai", "i lack the ability"]

# --- Helper Functions ---

def load_json_robust(filename, default_data):
    """Loads data from JSON, handles errors, returns default if issues."""
    if not os.path.exists(filename):
        print(f"INFO: File '{filename}' not found. Returning default.")
        # Save default data if file doesn't exist on first load
        save_json_robust(filename, default_data)
        return default_data
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"WARNING: Could not decode JSON from {filename}. Attempting recovery.")
        backup_filename = f"{filename}.bad_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            os.rename(filename, backup_filename)
            print(f"INFO: Backed up corrupted file to {backup_filename}")
        except OSError as bk_err:
            print(f"ERROR: Could not backup corrupted file {filename}: {bk_err}")
        # Return default after failed load/backup
        return default_data
    except Exception as e:
        print(f"ERROR: Unexpected error loading {filename}: {e}")
        traceback.print_exc()
        return default_data

def save_json_robust(filename, data):
    """Saves data to JSON, handles errors."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # print(f"DEBUG: Data saved to {filename}") # Optional
        return True
    except IOError as e:
        print(f"ERROR: Could not write to file {filename}: {e}")
        st.toast(f"Error saving data to {filename}!", icon="❌")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error saving {filename}: {e}")
        st.toast(f"Error saving data to {filename}!", icon="❌")
        traceback.print_exc()
        return False

# --- SelfAwareChatbot Class (Stateful Logic) ---
class SelfAwareChatbotStreamlit:
    DEFAULT_KNOWLEDGE = {
        "help": "I'm an AI assistant powered by Google Gemini. Ask me anything! Use sidebar commands for error analysis and log management."
    }

    def __init__(self, knowledge_file=KNOWLEDGE_FILE, log_file=LOG_FILE):
        self.knowledge_file = knowledge_file
        self.log_file = log_file
        self.learned_knowledge = load_json_robust(self.knowledge_file, default_data=self.DEFAULT_KNOWLEDGE.copy())
        self.error_logs = load_json_robust(self.log_file, default_data=[])
        print(f"INFO: Chatbot instance initialized/reloaded. Knowledge items: {len(self.learned_knowledge)}, Error logs: {len(self.error_logs)}.")

    def log_error(self, user_input, bot_response, error_type, confidence=None, genai_error=None):
        """Logs an error interaction."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "bot_response": bot_response,
            "error_type": error_type,
            "simulated_confidence": f"{confidence:.2f}" if confidence is not None else None,
            "genai_error_details": str(genai_error) if genai_error else None,
            "feedback_provided": None
        }
        # Ensure logs are always a list
        if not isinstance(self.error_logs, list):
             print(f"WARNING: Error logs were not a list ({type(self.error_logs)}). Resetting.")
             self.error_logs = []
        self.error_logs.append(log_entry)
        print(f"DEBUG: Logging error - Type: {error_type}, Input: '{user_input}'")
        if save_json_robust(self.log_file, self.error_logs):
            return len(self.error_logs) - 1 # Return index only if save succeeded
        else:
             # If save failed, potentially remove the log entry from memory too?
             # Or just signal failure. For now, just return None.
             return None

    def add_feedback_to_log(self, log_index, feedback):
        """Adds user feedback to a specific log entry."""
        if isinstance(self.error_logs, list) and 0 <= log_index < len(self.error_logs):
            self.error_logs[log_index]["feedback_provided"] = feedback
            print(f"INFO: Feedback added to log index {log_index}")
            return save_json_robust(self.log_file, self.error_logs) # Return True if save successful
        else:
            print(f"ERROR: Invalid log index ({log_index}) or logs not a list.")
            st.error("Failed to save feedback - log index invalid.")
            return False

    def generate_response(self, user_input, chat_history):
        """Generates response via GenAI, handles errors, simulates failures."""
        error_log_index = None
        bot_response_text = random.choice(DEFAULT_FALLBACK_RESPONSES)
        error_type = None
        genai_error_info = None
        sim_confidence = 1.0

        cleaned_input = user_input.lower().strip()
        if not cleaned_input:
            return "Please provide some input!", None # Handle empty input case

        # Check learned knowledge first (simple override)
        if cleaned_input in self.learned_knowledge:
             bot_response_text = self.learned_knowledge[cleaned_input]
             print(f"DEBUG: Used learned response for '{cleaned_input}'")
             # Decide if learned responses can also fail (for now, assume they succeed)
             return bot_response_text, None

        # --- Call Google Generative AI ---
        if 'genai_model' not in globals():
             st.error("GenAI Model not configured properly.")
             return "Error: AI Model not available.", None

        try:
            # Simple context strategy (last 5 turns)
            context_history = []
            for msg in chat_history[-5:]: # Ensure format is correct for GenAI
                 role = msg["role"]
                 # Gemini API expects 'user' and 'model' roles
                 if role == "assistant":
                      role = "model"
                 context_history.append({"role": role, "parts": [{"text": msg["content"]}]})

            # Create a new chat session for each request (stateless approach)
            # For conversational context, manage history more carefully
            # Note: This simple history might not be ideal for long conversations
            # For true chat, use model.start_chat(history=...)
            # Here, we are just sending history as part of the prompt content for simplicity
            prompt_for_genai = "\n".join([f"{msg['role']}: {msg['parts'][0]['text']}" for msg in context_history])
            prompt_for_genai += f"\nuser: {user_input}" # Add current input

            # print(f"DEBUG: Sending to GenAI:\n{prompt_for_genai}") # Be cautious with PII
            response = genai_model.generate_content(prompt_for_genai)

            # --- Process Response & Detect Failures ---
            if response and hasattr(response, 'text'):
                bot_response_text = response.text

                # 1. Check for refusal
                if any(phrase in bot_response_text.lower() for phrase in REFUSAL_PHRASES):
                    error_type = "Refusal"
                    sim_confidence = 0.3
                    print(f"DEBUG: Detected potential refusal.")
                    # Optional: Use a fallback message instead of the refusal?
                    # bot_response_text = random.choice(DEFAULT_FALLBACK_RESPONSES)

                # 2. Simulate random low confidence failure
                elif random.random() < SIMULATED_FAILURE_RATE:
                    error_type = "Simulated Low Confidence"
                    sim_confidence = random.uniform(0.1, 0.5)
                    bot_response_text = random.choice(DEFAULT_FALLBACK_RESPONSES) # Override response for demo
                    print(f"DEBUG: Simulating low confidence failure.")

            elif response and hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 # Handle cases where the content was blocked by safety filters
                 error_type = "Content Blocked"
                 sim_confidence = 0.1
                 genai_error_info = f"Blocked due to {response.prompt_feedback.block_reason}"
                 bot_response_text = f"My response was blocked due to safety settings ({response.prompt_feedback.block_reason}). Please try phrasing differently."
                 print(f"WARN: GenAI content blocked: {genai_error_info}")

            else:
                 # Unexpected response structure from API
                 error_type = "API Response Format Error"
                 sim_confidence = 0.2
                 genai_error_info = "Unexpected GenAI response structure"
                 bot_response_text = random.choice(DEFAULT_FALLBACK_RESPONSES)
                 print(f"ERROR: Unexpected GenAI response format: {response}")


        except Exception as e:
            print(f"ERROR: Google Generative AI API call failed: {e}")
            traceback.print_exc()
            error_type = "API Error"
            genai_error_info = e
            sim_confidence = 0.0
            bot_response_text = "I'm sorry, I encountered a technical difficulty trying to generate a response."

        # --- Logging ---
        if error_type:
            log_idx = self.log_error(
                user_input=user_input,
                bot_response=bot_response_text, # Log the final text sent to user
                error_type=error_type,
                confidence=sim_confidence,
                genai_error=genai_error_info
            )
            # Only set the index if logging was successful
            if log_idx is not None:
                 error_log_index = log_idx


        return bot_response_text, error_log_index

    def analyze_errors(self):
        """Performs basic analysis on error logs. Returns analysis text & learning candidate."""
        analysis_output = ["--- Analyzing Error Logs ---"]
        if not isinstance(self.error_logs, list) or not self.error_logs:
            analysis_output.append("No errors logged or logs are invalid.")
            analysis_output.append("--- Analysis Complete ---")
            return "\n".join(analysis_output), None

        error_counts = Counter()
        # Initialize counters for specific error types we might want to analyze inputs for
        inputs_by_error_type = {e_type: Counter() for e_type in ["Knowledge Gap", "Refusal", "Simulated Low Confidence", "API Error", "Content Blocked", "API Response Format Error"]}
        inputs_with_feedback = Counter()

        for log in self.error_logs:
             # Basic validation of log entry structure
            if not isinstance(log, dict):
                 print(f"WARNING: Skipping invalid log entry (not a dict): {log}")
                 continue
            e_type = log.get('error_type', 'Unknown')
            error_counts[e_type] += 1

            user_input_raw = log.get('user_input', '')
            user_input_clean = user_input_raw.lower().strip()
            if not user_input_clean: continue

            # Add input to the counter for its specific error type
            if e_type in inputs_by_error_type:
                 inputs_by_error_type[e_type][user_input_clean] += 1
            # Can add handling for 'Unknown' error types if needed

            feedback = log.get('feedback_provided')
            # Consider feedback valid if it's not None and not one of the skip markers
            if feedback and feedback not in ["skipped", "skipped_empty", "skipped_eof"] and not str(feedback).startswith("error:"):
                 inputs_with_feedback[user_input_clean] += 1

        analysis_output.append("Error Type Summary:")
        if not error_counts:
             analysis_output.append(" - No errors found in logs.")
        else:
            for e_type, count in error_counts.most_common():
                analysis_output.append(f"- {e_type}: {count} occurrence(s)")

        # Identify potential learning candidate (most frequent input causing Refusal/Knowledge Gap)
        learning_candidate = None
        highest_freq = 1 # Only consider inputs that occurred more than once

        # Check Refusals first, then Knowledge Gaps (can adjust priority)
        candidate_types_priority = ["Refusal", "Knowledge Gap"]
        for e_type in candidate_types_priority:
             if e_type in inputs_by_error_type and inputs_by_error_type[e_type]:
                  top_input_info = inputs_by_error_type[e_type].most_common(1)[0]
                  top_input_str = top_input_info[0]
                  top_input_count = top_input_info[1]
                  analysis_output.append(f"\nMost frequent input for '{e_type}': '{top_input_str}' ({top_input_count} times)")
                  if top_input_count > highest_freq:
                       highest_freq = top_input_count
                       learning_candidate = (e_type, top_input_str) # Store (type, input) tuple

        if inputs_with_feedback:
             analysis_output.append("\nInputs with User Feedback Provided (Top 5):")
             for inp, count in inputs_with_feedback.most_common(5):
                  analysis_output.append(f"- '{inp}' ({count} feedback instance(s))")
             # Could prioritize learning based on feedback count as well
             # Example: if inputs_with_feedback.most_common(1)[0][1] > highest_freq: ...

        analysis_output.append("--- Analysis Complete ---")
        return "\n".join(analysis_output), learning_candidate

    def add_learned_knowledge(self, keyword, response):
        """Adds or updates a learned keyword/response pair."""
        if not keyword or not response:
             print("WARNING: Attempted to learn empty keyword or response.")
             return False
        # Ensure knowledge base is a dictionary
        if not isinstance(self.learned_knowledge, dict):
             print(f"WARNING: Learned knowledge was not a dict ({type(self.learned_knowledge)}). Resetting.")
             self.learned_knowledge = self.DEFAULT_KNOWLEDGE.copy()

        self.learned_knowledge[keyword.lower().strip()] = response.strip()
        print(f"INFO: Learned knowledge added/updated for keyword '{keyword}'")
        return save_json_robust(self.knowledge_file, self.learned_knowledge)

    def clear_log_file_data(self):
        """Clears the error log data and saves."""
        self.error_logs = []
        if save_json_robust(self.log_file, self.error_logs):
            print("INFO: Error log cleared.")
            return True
        return False

    def reset_knowledge_data(self):
        """Resets learned knowledge to default and saves."""
        self.learned_knowledge = self.DEFAULT_KNOWLEDGE.copy()
        if save_json_robust(self.knowledge_file, self.learned_knowledge):
            print("INFO: Learned knowledge reset to default.")
            return True
        return False

# --- Google Generative AI Setup ---
# Use a flag in session state to configure only once per session
if 'genai_configured' not in st.session_state:
    st.session_state.genai_configured = False
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=GOOGLE_API_KEY)
        genai_model = genai.GenerativeModel('gemini-1.5-flash') # Or another suitable model
        st.session_state.genai_configured = True
        print("INFO: Google Generative AI configured successfully.")
    except KeyError:
        st.error("ERROR: GOOGLE_API_KEY not found in st.secrets. Please add it to your .streamlit/secrets.toml file.")
        st.stop()
    except Exception as e:
        st.error(f"ERROR: Could not configure Google Generative AI: {e}")
        traceback.print_exc()
        # Don't stop here, maybe user can still use learned responses or analyze logs
        st.warning("GenAI features will be unavailable.")


# --- Streamlit UI ---
st.set_page_config(page_title="Self-Aware Chatbot", layout="wide")
st.title("🤖 Self-Aware Chatbot Demo (v2)")
st.caption("Using Google Generative AI with improved error handling and state management")

# --- Initialize Session State (Robustly) ---
# Ensures chatbot instance is created/reloaded correctly
if "chatbot" not in st.session_state:
    st.session_state.chatbot = SelfAwareChatbotStreamlit()
    print("INFO: Created chatbot instance in session state.")
else:
     # Optional: If you want to ensure it reloads data from files on every run
     # st.session_state.chatbot = SelfAwareChatbotStreamlit()
     # print("INFO: Reloaded chatbot instance in session state.")
     pass # Usually, keeping the instance is fine

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]
if "last_error_log_index" not in st.session_state:
    st.session_state.last_error_log_index = None
if "feedback_requested" not in st.session_state:
    st.session_state.feedback_requested = False
if "learning_candidate" not in st.session_state:
    st.session_state.learning_candidate = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
# Flags for confirmation dialogs
if "confirm_clear_log" not in st.session_state:
    st.session_state.confirm_clear_log = False
if "confirm_reset_kb" not in st.session_state:
     st.session_state.confirm_reset_kb = False
if "show_log" not in st.session_state:
     st.session_state.show_log = False


# --- Sidebar ---
with st.sidebar:
    st.header("Controls & Analysis")

    # Analyze Button
    if st.button("Analyze Errors", key="analyze_btn"):
        st.session_state.feedback_requested = False # Clear feedback state
        st.session_state.confirm_clear_log = False
        st.session_state.confirm_reset_kb = False
        with st.spinner("Analyzing logs..."):
            analysis_text, candidate = st.session_state.chatbot.analyze_errors()
            # Store results in session state to persist across reruns
            st.session_state.analysis_results = analysis_text
            st.session_state.learning_candidate = candidate
        st.toast("Analysis complete!", icon="📊")
        st.rerun() # Rerun to display analysis results below

    # Display Analysis Results (if available)
    if st.session_state.analysis_results:
        st.subheader("Analysis Results")
        st.text_area("Log Analysis", value=st.session_state.analysis_results, height=250, key="analysis_display", disabled=True)

        # Learning UI (Conditional)
        if st.session_state.learning_candidate:
            st.subheader("Simulated Learning Opportunity")
            error_type, input_to_learn = st.session_state.learning_candidate
            # Sanitize key slightly (replace spaces, limit length) - basic protection
            sanitized_input_key = "".join(filter(str.isalnum, input_to_learn)).lower()[:20]

            st.write(f"Frequent input causing '{error_type}':")
            st.info(f"`{input_to_learn}`")

            learn_response_key = f"learn_response_{sanitized_input_key}"
            new_response = st.text_input("Enter desired response for this input:", key=learn_response_key)

            col_learn, col_skip = st.columns(2)
            with col_learn:
                learn_btn_key = f"learn_btn_{sanitized_input_key}"
                if st.button("Learn This Response", key=learn_btn_key):
                    if new_response:
                        if st.session_state.chatbot.add_learned_knowledge(input_to_learn, new_response):
                            st.toast(f"Learned response for '{input_to_learn}'!", icon="💡")
                            # Clear state after learning
                            st.session_state.learning_candidate = None
                            st.session_state.analysis_results = None
                            st.rerun()
                        else:
                             st.error("Failed to save learned response.")
                    else:
                        st.warning("Please enter a response to learn.")
            with col_skip:
                 skip_learn_btn_key = f"skip_learn_btn_{sanitized_input_key}"
                 if st.button("Skip Learning", key=skip_learn_btn_key):
                      st.toast("Skipped learning for this item.", icon=" N ")
                      st.session_state.learning_candidate = None
                      # Keep analysis results visible until next analysis run
                      st.rerun()
        st.divider() # Add divider after analysis/learning section

    # Log Management Buttons
    st.subheader("Log Management")
    if st.button("View/Hide Error Log", key="toggle_log_btn"):
        st.session_state.show_log = not st.session_state.show_log # Toggle
        # Clear other states when toggling log view
        st.session_state.feedback_requested = False
        st.session_state.confirm_clear_log = False
        st.session_state.confirm_reset_kb = False
        st.rerun()

    # Display Log (Conditional)
    if st.session_state.show_log:
         st.write("Error Logs:")
         # Add error handling for displaying JSON
         try:
             if isinstance(st.session_state.chatbot.error_logs, list):
                st.json(st.session_state.chatbot.error_logs, expanded=False)
             else:
                 st.error("Log data is not in the expected format (list).")
                 st.write(st.session_state.chatbot.error_logs) # Show raw data if possible
         except Exception as display_e:
              st.error(f"Error displaying log data: {display_e}")


    # Clear Log Button & Confirmation
    if st.button("Clear Error Log", key="clear_log_btn", type="secondary"):
         st.session_state.confirm_clear_log = True
         # Clear other states
         st.session_state.feedback_requested = False
         st.session_state.confirm_reset_kb = False
         st.rerun()

    if st.session_state.confirm_clear_log:
         st.warning("Are you sure you want to clear the entire error log?")
         col1, col2 = st.columns(2)
         with col1:
              if st.button("Yes, Clear Log", type="primary", key="confirm_clear_yes"):
                    if st.session_state.chatbot.clear_log_file_data():
                        st.toast("Error log cleared!", icon="🗑️")
                    else:
                         st.error("Failed to clear error log.")
                    # Reset state regardless of success/failure to clear confirmation
                    st.session_state.confirm_clear_log = False
                    st.session_state.show_log = False # Hide log after clearing
                    st.rerun()
         with col2:
              if st.button("Cancel Clear", key="confirm_clear_no"):
                    st.session_state.confirm_clear_log = False
                    st.rerun()

    # Knowledge Base Management
    st.divider()
    st.subheader("Knowledge Base")
    if st.button("Reset Learned Knowledge", key="reset_kb_btn", type="secondary"):
        st.session_state.confirm_reset_kb = True
        # Clear other states
        st.session_state.feedback_requested = False
        st.session_state.confirm_clear_log = False
        st.rerun()

    if st.session_state.confirm_reset_kb:
         st.warning("Reset learned knowledge to default?")
         col1, col2 = st.columns(2)
         with col1:
              if st.button("Yes, Reset KB", type="primary", key="confirm_reset_yes"):
                    if st.session_state.chatbot.reset_knowledge_data():
                        st.toast("Knowledge base reset!", icon="🔄")
                    else:
                         st.error("Failed to reset knowledge base.")
                    st.session_state.confirm_reset_kb = False
                    st.rerun()
         with col2:
              if st.button("Cancel Reset KB", key="confirm_reset_no"):
                    st.session_state.confirm_reset_kb = False
                    st.rerun()

# --- Main Chat Area ---

# Display chat messages
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Use a unique key for each message display if needed, though usually not required
        st.markdown(message["content"], unsafe_allow_html=False) # Avoid unsafe_allow_html unless necessary

# --- Feedback Input Area (Conditional based on state) ---
# Ensure index is valid before showing feedback area
if st.session_state.feedback_requested and isinstance(st.session_state.last_error_log_index, int):
    st.info("My last response might not have been adequate. Could you provide feedback or clarification?")
    feedback_key = f"feedback_input_{st.session_state.last_error_log_index}"
    feedback_text = st.text_area("Your Feedback:", key=feedback_key, placeholder="Enter feedback here...")

    fb_col1, fb_col2 = st.columns(2)
    with fb_col1:
        submit_fb_key = f"submit_fb_{st.session_state.last_error_log_index}"
        if st.button("Submit Feedback", key=submit_fb_key):
            if feedback_text:
                if st.session_state.chatbot.add_feedback_to_log(st.session_state.last_error_log_index, feedback_text):
                    st.toast("Thank you for your feedback!", icon="✅")
                # Else: error handled/printed in add_feedback_to_log
                st.session_state.feedback_requested = False # Turn off feedback mode
                st.rerun()
            else:
                st.warning("Please enter feedback before submitting.")
    with fb_col2:
        skip_fb_key = f"skip_fb_{st.session_state.last_error_log_index}"
        if st.button("Skip Feedback", key=skip_fb_key):
            if st.session_state.chatbot.add_feedback_to_log(st.session_state.last_error_log_index, "skipped"):
                st.toast("Feedback skipped.", icon=" N ")
            # Else: error handled/printed
            st.session_state.feedback_requested = False # Turn off feedback mode
            st.rerun()


# --- User Input Chat Box ---
# Disable input while feedback is being requested to avoid confusing state
chat_input_disabled = st.session_state.feedback_requested or \
                      st.session_state.confirm_clear_log or \
                      st.session_state.confirm_reset_kb

if prompt := st.chat_input("Ask me anything...", disabled=chat_input_disabled, key="main_chat_input"):
    # Clear potentially stale states on new input
    st.session_state.feedback_requested = False
    st.session_state.last_error_log_index = None
    st.session_state.analysis_results = None
    st.session_state.learning_candidate = None
    st.session_state.confirm_clear_log = False
    st.session_state.confirm_reset_kb = False

    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message immediately (before spinner) - feels more responsive
    with st.chat_message("user"):
         st.markdown(prompt)

    # Generate and display bot response
    if not st.session_state.genai_configured:
         # Handle case where GenAI failed to initialize
         with st.chat_message("assistant"):
             fallback_resp = st.session_state.chatbot.learned_knowledge.get(prompt.lower().strip(), "Sorry, AI features are unavailable.")
             st.markdown(fallback_resp)
             st.session_state.messages.append({"role": "assistant", "content": fallback_resp})
    else:
         # Generate response using the chatbot instance
        with st.spinner("Thinking..."):
            bot_response, error_index = st.session_state.chatbot.generate_response(prompt, st.session_state.messages)

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(bot_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Handle potential error and feedback request *after* displaying response
        if error_index is not None:
            st.session_state.last_error_log_index = error_index
            st.session_state.feedback_requested = True # Trigger feedback UI on next rerun
            st.rerun() # Rerun immediately to show feedback section
        else:
             # No error, ensure feedback is off if it was somehow left on
             st.session_state.feedback_requested = False
             # No immediate rerun needed if no error occurred

elif chat_input_disabled:
     st.caption("Please resolve the pending action (feedback or confirmation) before sending a new message.")