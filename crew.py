import os
import json
import re
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

load_dotenv()

# ---------------- HELPER ----------------
def extract_json(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        return None
    return None


def run_travel_planner(destination, budget, interests):

    search_tool = SerperDevTool()

    llm = LLM(
        model="gemini-3-flash-preview",
        temperature=0.2,
        api_key=os.environ["GOOGLE_API_KEY"]
    )

    # ---------------- AGENTS ----------------
    researcher = Agent(
        role="Travel Researcher",
        goal="Find structured travel data (sites, weather, hotels)",
        backstory="Expert in travel research",
        verbose=False,
        memory=True,
        llm=llm,
        tools=[search_tool]
    )

    budget_planner = Agent(
        role="Budget Planner",
        goal="Estimate travel cost breakdown",
        backstory="Expert in travel budgeting",
        verbose=False,
        memory=True,
        llm=llm,
        tools=[search_tool]
    )

    itinerary_planner = Agent(
        role="Itinerary Planner",
        goal="Generate structured final travel plan",
        backstory="Expert in itinerary planning",
        verbose=False,
        llm=llm,
        tools=[search_tool]
    )

    # ---------------- TASKS ----------------

    research_task = Task(
        description=f"""
        Find travel info for {destination}.

        Return STRICT JSON ONLY:
        {{
            "sites": [
            {{"title": "", "description": ""}}
            ],
            "weather": "",
            "hotels": []
        }}

        Rules:
        - Max 5 sites
        - Short descriptions
        - No extra text
        """,
        expected_output="Strict JSON with keys: sites, weather, hotels",
        agent=researcher
    )

    budget_task = Task(
        description=f"""
        Estimate travel budget for {destination}.

        Budget input: {budget}

        Return STRICT JSON ONLY:
        {{
            "flights": "",
            "hotels": "",
            "food": "",
            "activities": "",
            "total": ""
        }}

        Rules:
        - Use same currency
        - Keep values short
        - No extra text
        """,
        expected_output="Strict JSON with cost breakdown",
        agent=budget_planner
    )

    itinerary_task = Task(
        description=f"""
        Create FINAL travel plan for {destination}.

        Inputs:
        - Budget: {budget}
        - Interests: {interests}

        Use previous tasks data.

        Return STRICT JSON ONLY:
        {{
            "sites": [],
            "weather": "",
            "hotels": [],
            "budget": "{budget}",
            "budget_breakdown": {{
                "flights": "",
                "hotels": "",
                "food": "",
                "activities": "",
                "total": ""
            }},
            "day1": "",
            "day2": "",
            "day3": ""
        }}

        Rules:
        - STRICT JSON ONLY
        - No explanation
        - Clean and concise
        """,
        expected_output="Final structured JSON travel plan",
        agent=itinerary_planner,
        context=[research_task, budget_task]
    )

    # ---------------- CREW ----------------
    crew = Crew(
        agents=[researcher, budget_planner, itinerary_planner],
        tasks=[research_task, budget_task, itinerary_task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff(inputs={
        "destination": destination,
        "budget": budget,
        "interests": interests
    })

    # ---------------- CLEAN OUTPUT ----------------

    # 1. Best case
    if hasattr(result, "json_dict") and result.json_dict:
        return result.json_dict

    # 2. Try raw
    if hasattr(result, "raw"):
        data = extract_json(result.raw)
        if data:
            return data

    # 3. Try tasks_output
    if hasattr(result, "tasks_output"):
        data = extract_json(str(result.tasks_output))
        if data:
            return data

    # 4. If already dict
    if isinstance(result, dict):
        return result

    # 5. Fallback
    return {
        "sites": [],
        "weather": "Not available",
        "hotels": [],
        "budget": budget,
        "budget_breakdown": {},
        "day1": "Not available",
        "day2": "Not available",
        "day3": "Not available"
    }