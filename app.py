import streamlit as st
from google import genai
import requests

# --- 1. UI Setup ---
st.set_page_config(page_title="Student AI Tutor", layout="centered")
st.title("📚 Student AI Tutor")
st.subheader("Ask questions about the AI Integration course")

# Sidebar for the API Key
with st.sidebar:
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Get an API key at [Google AI Studio](https://aistudio.google.com/)")

# --- 2. Knowledge Base Loader ---
@st.cache_data # Cache the document so it doesn't download on every interaction
def load_context_from_url(doc_url):
    try:
        # Convert the standard /edit URL to a plain text export URL
        # From: https://docs.google.com/document/d/DOC_ID/edit...
        # To:   https://docs.google.com/document/d/DOC_ID/export?format=txt
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        
        response = requests.get(export_url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error loading document: {e}"

# The URL you provided
DOC_URL = "https://docs.google.com/document/d/1L-ZDGHXLOtzO2VmgSKtKYAmSnnMLJEymnf4ZAF2ZxtM/edit?usp=sharing"

# Load the context automatically when the app starts
COURSE_CONTEXT = load_context_from_url(DOC_URL)

# --- 3. Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What would you like to know?"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif "Error loading document" in COURSE_CONTEXT:
        st.error(COURSE_CONTEXT)
    else:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare prompt with the live context
        full_prompt = f"Using the following context: \n\n{COURSE_CONTEXT}\n\nQuestion: {prompt}"

        # Call Gemini API
        try:
            client = genai.Client(api_key=api_key)
            
            with st.chat_message("assistant"):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config={
                        'system_instruction': "You are a supportive, patient tutor. Use the provided context to answer questions. If the answer isn't in the context, tell the student but try to explain the general concept simply."
                    }
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"An error occurred: {e}")