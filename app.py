
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from task_extractor import extract_task

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("OpenRouter API key not found.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    timeout=30.0,
    max_retries=0
)

SYSTEM_PROMPT = """
You are an AI Engineering tutor.
Explain concepts simply and concisely.
Give practical examples.
When asked coding questions, guide the user
instead of immediately providing full solutions.
"""

st.title("🤖 My AI Assistant")

# Create application tabs
chat_tab, task_tab = st.tabs([
    "💬 AI Chat",
    "📋 Task Extractor"
])


# ===================================
# TAB 1: AI CHAT
# ===================================

with chat_tab:

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask me anything..."):

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

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

                def stream_response():
                    for chunk in stream:
                        if chunk.choices:
                            content = chunk.choices[0].delta.content
                            if content:
                                yield content

                response = st.write_stream(stream_response())

                if not response:
                    response = "No text response received."
                    st.write(response)

            except Exception as e:
                st.session_state.messages.pop()
                st.error(f"API request failed: {e}")
                st.stop()

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


# ===================================
# TAB 2: AI TASK EXTRACTOR
# ===================================

with task_tab:

    st.subheader("📋 AI Task Extractor")

    st.write(
        "Describe a task naturally and let AI "
        "extract its structured information."
    )

    # Task input form
    with st.form("task_form"):

        task_text = st.text_area(
            "Describe your task:",
            placeholder=(
                "Finish my RAG project by Friday. "
                "It's urgent and takes 3 hours."
            ),
            height=120
        )
        
        st.subheader("⚙️ Working Schedule")

        hours_per_day = st.number_input(
            "Working hours per day",
            min_value=0.5,
            max_value=24.0,
            value=8.0,
            step=0.5
        )

        days_per_week = st.slider(
            "Working days per week",
            min_value=1,
            max_value=7,
            value=5
        )

        submitted = st.form_submit_button(
            "✨ Extract Task"
        )

    if submitted:

        # Clear previous result
        st.session_state.extracted_task = None

        if not task_text.strip():
            st.warning("Please enter a task description.")

        else:
            with st.spinner("Extracting task..."):
                try:
                    task = extract_task(task_text, hours_per_day, days_per_week)

                    # Store validated result
                    st.session_state.extracted_task = (
                        task.model_dump()
                    )

                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    # Display saved result
    if st.session_state.get("extracted_task") is not None:

        st.success("Task extracted successfully!")

        st.json(st.session_state.extracted_task)
