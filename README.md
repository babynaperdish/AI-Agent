# AI Fitness & Nutrition Assistant

An AI-powered fitness and nutrition assistant built with Python, LangChain, LangGraph, and Ollama. It helps users generate personalized meal ideas, explore recipes, calculate daily calorie and macronutrient targets, and track their daily nutrition intake through FatSecret integration.

## Features

- **AI-Powered Recipe Generation** — Generate meal ideas based on preferred ingredients, food preferences, and dietary requirements.
- **Daily Nutrition Targets** — Calculate daily calorie and macronutrient goals.
- **Meal Planning** — Get meal suggestions based on nutrition targets and remaining daily intake.
- **FatSecret Integration** — Retrieve calories, protein, fat, and carbohydrate data from the user's food diary.
- **Local Language Model** — Run the assistant using a locally hosted LLM through Ollama.

## Tech Stack

- **Language:** Python
- **LLM Framework:** LangChain
- **Agent Orchestration:** LangGraph
- **Local LLM Runtime:** Ollama
- **Data Validation:** Pydantic
- **Nutrition Tracking:** FatSecret API

## Requirements

- Python 3.14 or newer
- [Ollama](https://ollama.com/)
- A FatSecret account and API credentials for food diary integration

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/babynaperdish/AI-Agent.git
cd AI-Agent
```

### 2. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama

Install Ollama from [ollama.com](https://ollama.com/), then download the model used by the application:

```bash
ollama pull qwen3.5:4b
```

Make sure Ollama is running before starting the assistant.

### 5. Configure FatSecret

To enable food diary integration, configure your FatSecret API credentials and complete the OAuth authorization flow.

**Security:** Never commit API secrets, access tokens, or personal authentication files to the repository.

## Usage

Run the assistant from the project directory:

```bash
python agent.py
```

Interact with the assistant through the terminal to request recipes, meal suggestions, and nutrition information.

## Project Structure

```text
AI-Agent/
├── agent.py             # Main AI agent and nutrition tools
├── fatsecret_auth.py    # FatSecret authentication
├── fatsecret_diary.py   # Food diary integration
├── stuff.py             # Supporting functionality
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Locked dependency versions
└── README.md            # Project documentation
```

## Current Status

This project is under active development. Features and behavior may change as the agent, nutrition calculations, and external API integration are improved.

## Planned Improvements

- More reliable nutrition calculations and target management
- More detailed recipes with ingredient quantities and cooking instructions
- Improved personalization based on dietary preferences and goals
- Better error handling for missing or unavailable food diary data
- Expanded meal planning and nutrition tracking

## Disclaimer

AI-generated recipes and nutrition estimates are approximate and should not replace professional medical or dietary advice.

## Author

**babynaperdish**

[GitHub Profile](https://github.com/babynaperdish)
