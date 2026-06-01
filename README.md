# Cal Poly AI Academic Advisor

An AI-powered academic advising chatbot for Cal Poly SLO students. Built with Python and the Claude API.

## What it does

- Takes your major and completed courses as input
- Maps old quarter-system course numbers to new semester numbers automatically
- Checks your progress against official CS degree requirements
- Recommends courses for next quarter based on prerequisites
- Pulls live professor ratings from PolyRatings and recommends professors based on your preferences
- Holds context across a full conversation - ask follow-up questions naturally

## Skills demonstrated

- **Prompt engineering** - structured system prompts that control AI behavior
- **Structured outputs** - Claude returns JSON that the program can use
- **Agent design** - multi-turn conversation with persistent context
- **External API integration** - live data from PolyRatings
- **Python + Flask** - clean, modular code with a web frontend

## How to run it

1. Clone the repo
2. Install dependencies: `pip install anthropic python-dotenv requests flask`
3. Create a `.env` file with your Anthropic API key: `ANTHROPIC_API_KEY=your-key-here`
4. Run the web app: `python app.py` then open `http://localhost:5000`
5. Or run the terminal version: `python advisor.py`

## Project structure

- `advisor.py` - terminal chatbot version
- `app.py` - Flask web app version
- `requirements.py` - Cal Poly CS degree requirements and course names
- `templates/index.html` - chat UI

## Built by

Marc Helwee - Cal Poly SLO Computer Science