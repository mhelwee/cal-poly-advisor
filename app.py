import json
import os
from datetime import date

import requests
import anthropic
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
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

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)
# Server-side (filesystem) sessions: chat history can exceed the ~4KB browser cookie
# limit, which silently drops turns. Only a session id rides in the cookie now.
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Shown to the student when the model API fails; the real error is logged server-side.
ADVISOR_UNAVAILABLE = "The advisor is briefly unavailable — please resend your message in a moment."

# Load professor data once at startup. If PolyRatings is unavailable, course RAG still works.
try:
    all_professors = get_professors()
except (requests.RequestException, json.JSONDecodeError) as exc:
    print(f"Could not load PolyRatings data: {exc}")
    all_professors = []


@app.route("/")
def index():
    session["history"] = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "Send me a course planning question and I can help."}), 400

    history = session.get("history", [])

    rag_result = retrieve_rag_context(user_message, professors=all_professors)
    print(f"RAG sources: {rag_result.sources}")
    message_with_context = add_rag_context_to_message(user_message, rag_result)
    message_with_context += ROADMAP_INSTRUCTION

    messages = history + [{"role": "user", "content": message_with_context}]

    # Rebuild the prompt per request so today's date stays current, and use the SAME
    # next-term value in the prompt and the validator. Identical content still hits the
    # prompt cache; it only changes once a day when the date rolls over.
    today = date.today()
    next_term = _next_term(today)
    system_prompt = build_system_prompt(today, next_term)

    try:
        raw_reply, remaining = generate_validated_reply(
            client, messages, system_prompt, earliest_term=next_term
        )
    except (anthropic.APIConnectionError, anthropic.RateLimitError):
        app.logger.exception("Anthropic API unavailable (connection/rate limit)")
        return jsonify({"response": ADVISOR_UNAVAILABLE}), 503
    except anthropic.APIStatusError:
        app.logger.exception("Anthropic API returned an error status")
        return jsonify({"response": ADVISOR_UNAVAILABLE}), 502
    except anthropic.APIError:
        app.logger.exception("Anthropic API error")
        return jsonify({"response": ADVISOR_UNAVAILABLE}), 502

    assistant_message = _strip_roadmap_block(raw_reply)
    # If the loop exhausted retries with a still-invalid plan, never present it as verified.
    if remaining:
        assistant_message += INCOMPLETE_VALIDATION_NOTE

    # Store the clean user message and the student-facing (block-stripped) reply.
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})

    session["history"] = history

    return jsonify({"response": assistant_message})

if __name__ == "__main__":
    app.run(debug=True)
