
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from task_extractor import extract_task
from database import (save_task, get_all_tasks, update_task_priority,delete_task,create_tasks_table)


create_tasks_table()
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
               
                    st.session_state.extracted_task = task.model_dump(mode="json")
                    st.session_state.task_saved = False
                    st.session_state.saved_task_id = None


                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    # Display saved result
        
    if st.session_state.get("extracted_task") is not None:

        st.json(st.session_state.extracted_task)

        if st.session_state.get("task_saved"):
            st.success(
                f"Task saved! ID: {st.session_state.saved_task_id}"
            )

        elif st.button("💾 Save Task"):
            task_id = save_task(
                st.session_state.extracted_task
            )

            st.session_state.task_saved = True
            st.session_state.saved_task_id = task_id

            st.success(f"Task saved! ID: {task_id}")
    
    # Display all saved tasks
    
    # Display and manage saved tasks
    st.divider()
    st.subheader("📚 My Saved Tasks")

    tasks = get_all_tasks()

    if tasks:

        st.subheader("✏️ Update Task Priority")

        # Create options using each task's ID
        task_options = {
            f"{task['id']} - {task['task']}": task['id']
            for task in tasks
        }

        selected_task = st.selectbox(
            "Choose a task",
            options=list(task_options.keys())
        )

        new_priority = st.selectbox(
            "New priority",
            options=["low", "medium", "high"]
        )

        if st.button("Update Priority"):

            task_id = task_options[selected_task]

            updated = update_task_priority(
                task_id,
                new_priority
            )

            if updated:
                st.success("Task updated successfully!")
            else:
                st.warning("Task not found.")
        
       

        
        # Display tasks with individual delete buttons
        tasks = get_all_tasks()

        st.subheader("📚 My Saved Tasks")

        # Table headers
        headers = st.columns([1, 4, 2, 2, 2, 1])

        for col, title in zip(
            headers,
            ["ID", "Task", "Priority", "Deadline", "Hours", "Delete"]
        ):
            col.write(f"**{title}**")

        # Task rows
        for task in tasks:

            cols = st.columns([1, 4, 2, 2, 2, 1])

            cols[0].write(task["id"])
            cols[1].write(task["task"])
            cols[2].write(task["priority"])
            cols[3].write(task["deadline"] or "-")
            cols[4].write(
                task["estimated_hours"]
                if task["estimated_hours"] is not None
                else "-"
                )

            if cols[5].button(
                "🗑️",
                key=f"delete_{task['id']}"
            ):
                delete_task(task["id"])
                st.rerun()


    else:
        st.info("No saved tasks yet.")


