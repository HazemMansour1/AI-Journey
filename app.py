
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("OpenRouter API key not found. Check your .env file.")
    st.stop()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    timeout=30.0,
    max_retries=0
)

# System instructions
SYSTEM_PROMPT = """
You are an AI Engineering tutor.
Explain concepts simply and concisely.
Give practical examples.
When asked coding questions, guide the user
instead of immediately providing full solutions.
"""

# App title
st.title("🤖 My AI Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Accept user input
if prompt := st.chat_input("Ask me anything..."):

    # Save user's message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Display user's message
    with st.chat_message("user"):
        st.write(prompt)

    # Generate and stream AI response
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ] + st.session_state.messages,
                stream=True
            )

            # Stream incoming text chunks
            def stream_response():
                for chunk in stream:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content

            # Display response progressively
            response = st.write_stream(stream_response())

            if not response:
                response = "No text response received."
                st.write(response)

        except Exception as e:
            # Remove the failed user message from history
            st.session_state.messages.pop()
            st.error(f"API request failed: {e}")
            st.stop()

    # Save complete assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
