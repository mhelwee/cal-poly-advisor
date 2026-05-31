import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from requirements import CS_REQUIREMENTS, PREREQUISITE_CHAIN

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("=== Cal Poly AI Advisor ===")
major = input("Enter your major: ")
print("Enter completed courses one at a time. Type 'done' when finished.")

completed = []
while True:
    course = input("Course: ").strip().upper().replace("  ", " ")
    if course == "DONE":
        break
    completed.append(course)

student = {
    "major": major,
    "completed_courses": completed
}

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a Cal Poly SLO academic advisor. Old course numbers map to new ones: CSC 101=CSC 1001, CSC 102=CSC 1001, CSC 202=CSC 2001, CSC 203=CSC 3001, CSC 225=CPE 2300, CSC 248=CSC 2050, CSC 357=CSC 4553, CSC 349=CSC 3449, CSC 307=CSC 3100. Apply these mappings before checking requirements. Always respond with valid JSON only, no extra text.",
    messages=[
        {"role": "user", "content": f"""
        Student completed courses: {student['completed_courses']}
        
        Official CS degree requirements: {json.dumps(CS_REQUIREMENTS)}
        Prerequisite chains: {json.dumps(PREREQUISITE_CHAIN)}
        
        Return a JSON object with:
        - remaining_requirements: list of required courses not yet completed
        - next_quarter_recommendation: 3-4 courses the student can take next (prerequisites satisfied)
        - warnings: any workload or prerequisite warnings
        """}
    ]
)

raw = response.content[0].text
clean = raw.replace("```json", "").replace("```", "").strip()
result = json.loads(clean)
print(json.dumps(result, indent=2))