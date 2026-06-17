import json
import os
from datetime import date

import requests
import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv
from rag import add_rag_context_to_message, get_professors, retrieve_rag_context
from advisor_core import (
    INCOMPLETE_VALIDATION_NOTE,
    ROADMAP_INSTRUCTION,
    _next_term,
    _strip_roadmap_block,
    build_system_prompt,
    generate_validated_reply,
)

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---- Main Chat Loop ----

def chat():
    print("=== Cal Poly AI Advisor ===")
    print("Type 'quit' to exit\n")

    try:
        professors = get_professors()
    except (requests.RequestException, json.JSONDecodeError) as exc:
        print(f"Could not load PolyRatings data: {exc}")
        professors = []

    # Build the prompt once for the session — a CLI run is short enough that the date
    # won't roll over mid-session. Reuse the same next-term value for the validator.
    today = date.today()
    next_term = _next_term(today)
    system_prompt = build_system_prompt(today, next_term)
    conversation_history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "quit":
            print("Good luck with registration!")
            break

        if not user_input:
            continue

        rag_result = retrieve_rag_context(user_input, professors=professors)
        if rag_result.sources:
            print(f"Retrieved context: {', '.join(rag_result.sources)}")

        message_with_context = add_rag_context_to_message(user_input, rag_result)
        message_with_context += ROADMAP_INSTRUCTION
        messages = conversation_history + [{"role": "user", "content": message_with_context}]

        try:
            raw_reply, remaining = generate_validated_reply(
                client, messages, system_prompt, earliest_term=next_term
            )
        except anthropic.APIError:
            print("\nAdvisor: I'm briefly unavailable — please try again in a moment.\n")
            continue

        assistant_message = _strip_roadmap_block(raw_reply)
        # If the loop exhausted retries with a still-invalid plan, never present it as verified.
        if remaining:
            assistant_message += INCOMPLETE_VALIDATION_NOTE

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        print(f"\nAdvisor: {assistant_message}\n")

if __name__ == "__main__":
    chat()
