import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from requirements import CS_REQUIREMENTS, PREREQUISITE_CHAIN, COURSE_NAMES

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---- Data Fetching ----

def get_professors():
    """Fetch all professors who have taught CSC or CPE courses from PolyRatings."""
    url = "https://raw.githubusercontent.com/Polyratings/polyratings-data/refs/heads/data/professor-list.json"
    response = requests.get(url)
    professors = json.loads(response.text)
    return [p for p in professors if any(
        c.startswith("CSC") or c.startswith("CPE")
        for c in p.get("courses", [])
    )]

# ---- System Prompt ----

def build_system_prompt(professors):
    """Build the system prompt with all context Claude needs."""
    return f"""You are a Cal Poly SLO academic advisor chatbot.
You help CS students plan courses, check prerequisites, and choose professors.

Official CS degree requirements: {json.dumps(CS_REQUIREMENTS)}
Prerequisite chains: {json.dumps(PREREQUISITE_CHAIN)}
Course names: {json.dumps(COURSE_NAMES)}
CSC/CPE Professor data from PolyRatings: {json.dumps(professors)}

Old course number mappings (quarter system → semester system):
CSC 101=CSC 1001, CSC 202=CSC 2001, CSC 203=CSC 3001,
CSC 225=CPE 2300, CSC 248=CSC 2050, CSC 357=CSC 4553,
CSC 349=CSC 3449, CSC 307=CSC 3100.

GE Requirements (27 units total, 16 satisfied by major/support courses):
- 1A: Written Communication
- 1B: Critical Thinking
- 1C: Oral Communication
- 3A: Arts
- 3B: Humanities
- 4A: American Institutions
- 4B: Social and Behavioral Sciences
- 6: Ethnic Studies
- Upper Division 4: Social and Behavioral Sciences
- Areas 2, 5A, 5B, 5C, Upper Division 2/5 and 3 are satisfied by major/support courses.

Conversation guidelines:
1. Ask for major and completed courses (including GEs) upfront
2. Identify which GE areas are satisfied based on completed courses
3. Recommend next quarter options based on prerequisites
4. When professors are mentioned, look them up by last name in PolyRatings data
5. Ask about preferences (recorded lectures, workload, grading) before recommending professors
6. For roadmap requests: ask graduation year and courses per semester, then plan all the way to graduation respecting prerequisite chains

Always be concise and conversational. Never respond in JSON."""

# ---- Main Chat Loop ----

def chat():
    print("=== Cal Poly AI Advisor ===")
    print("Type 'quit' to exit\n")

    professors = get_professors()
    system_prompt = build_system_prompt(professors)
    conversation_history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "quit":
            print("Good luck with registration!")
            break

        if not user_input:
            continue

        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_history
        )

        assistant_message = response.content[0].text

        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        print(f"\nAdvisor: {assistant_message}\n")

chat()