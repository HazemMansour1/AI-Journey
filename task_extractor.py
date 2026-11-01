
import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()


# Raw information extracted by the LLM
class ExtractedTask(BaseModel):
    task: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"] | None = None
    deadline: str | None = None
    duration_value: float | None = Field(default=None, gt=0)
    duration_unit: Literal["minute", "hour", "day", "week"] | None = None


# Final structure used by our application
class Task(BaseModel):
    task: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"] | None = None
    deadline: str | None = None
    estimated_hours: float | None = Field(default=None, ge=0)


# Convert extracted duration into working hours
def convert_to_hours(value, unit, hours_per_day=8, days_per_week=5):

    if value is None and unit is None:
        return None

    if value is None or unit is None:
        raise ValueError("Incomplete duration information")

    conversion_factors = {
        "minute": 1 / 60,
        "hour": 1,
        "day": hours_per_day,
        "week": hours_per_day * days_per_week
    }

    return round(value * conversion_factors[unit], 2)


# Extract and process task
def extract_task(
    user_text: str,
    hours_per_day: float = 8,
    days_per_week: int = 5
) -> Task:

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        timeout=30.0,
        max_retries=0
    )

    completion = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": """
                You are a task extraction assistant.

                Extract:
                - task: concise task description
                - priority: high, medium, low, or null
                - deadline: deadline text or null
                - duration_value: numeric effort estimate or null
                - duration_unit: minute, hour, day, week, or null

                IMPORTANT:
                - Do NOT convert durations into hours.
                - Extract the original numeric duration.
                - Normalize units to singular form.
                - Distinguish deadlines from effort estimates.
                - "Finish in 2 months" indicates a deadline.
                - "It might take 1 week" indicates effort.
                - Do not treat deadlines as effort.
                - Use null for missing information.
                - Return only a valid JSON object.
                """
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        response_format={"type": "json_object"}
    )

    response = completion.choices[0].message.content

    if not response:
        raise ValueError("The model returned an empty response.")

    # Step 1: Validate LLM extraction
    extracted = ExtractedTask.model_validate_json(response)

    # Step 2: Convert duration using Python
    hours = convert_to_hours(
    extracted.duration_value,
    extracted.duration_unit,
    hours_per_day=hours_per_day,
    days_per_week=days_per_week
    )
    
    # Step 3: Return validated final task
    return Task(
        task=extracted.task,
        priority=extracted.priority,
        deadline=extracted.deadline,
        estimated_hours=hours
    )
