import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from requirements import CS_REQUIREMENTS, PREREQUISITE_CHAIN

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_professors():
    url = "https://raw.githubusercontent.com/Polyratings/polyratings-data/refs/heads/data/professor-list.json"
    response = requests.get(url)
    professors = json.loads(response.text)
    
    # Keep anyone who has taught a CSC or CPE course
    csc_profs = [p for p in professors if any(
        c.startswith("CSC") or c.startswith("CPE") 
        for c in p.get("courses", [])
    )]
    return csc_profs

def chat():
    print("=== Cal Poly AI Advisor ===")
    print("Type 'quit' to exit\n")
    
    professors = get_professors()
    conversation_history = []
    
    system_prompt = f"""You are a Cal Poly SLO academic advisor chatbot. 
You help students plan their courses, check prerequisites, and choose professors.

Official CS degree requirements: {json.dumps(CS_REQUIREMENTS)}
Prerequisite chains: {json.dumps(PREREQUISITE_CHAIN)}
CSC/CPE Professor data from PolyRatings: {json.dumps(professors)}

Old course numbers map to new ones: CSC 101=CSC 1001, CSC 102=CSC 1001, 
CSC 202=CSC 2001, CSC 203=CSC 3001, CSC 225=CPE 2300, CSC 248=CSC 2050, 
CSC 357=CSC 4553, CSC 349=CSC 3449, CSC 307=CSC 3100.

Guide the conversation naturally:
1. First ask for major and completed courses
2. Then recommend next quarter options
3. If they mention specific courses they're considering, ask what professors are available
4. Ask about their preferences (recorded lectures, workload, grading style)
5. Give professor recommendations based on PolyRatings data and their preferences

Respond conversationally, not as JSON. Be concise and helpful.
When a user mentions specific professor names, search the PolyRatings data by last name to find their ratings. Always look up professors by name, not by course code."""

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