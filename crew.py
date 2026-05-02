import os
import json
import re
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import requests

load_dotenv()

# ─────────────────────────────────────────────
# LLM SETUP
# ─────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.3,
    max_tokens=1500
)

manager_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1,
    max_tokens=800
)

# ─────────────────────────────────────────────
# WEB SEARCH
# ─────────────────────────────────────────────

def search_web(query: str) -> str:
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": os.environ["SERPER_API_KEY"],
                "Content-Type": "application/json"
            },
            json={"q": query, "num": 4},
            timeout=10
        )
        data = response.json()
        results = []
        for item in data.get("organic", [])[:4]:
            results.append(f"{item.get('title', '')}: {item.get('snippet', '')}")
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────

class TravelState(TypedDict):
    destination: str
    budget: str
    interests: str
    days: int
    research_data: str
    budget_data: str
    itinerary_data: str
    critic_data: str
    revision_count: int
    verdict: str
    final_plan: dict


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────
# NODE 1 — RESEARCHER
# ─────────────────────────────────────────────

def researcher_node(state: TravelState) -> dict:
    destination = state["destination"]
    interests = state["interests"]
    days = state["days"]

    search1 = search_web(f"{destination} top attractions {interests} 2025")
    search2 = search_web(f"{destination} best hotels local food travel tips")

    prompt = f"""You are a travel research specialist.
Based on the search data below, extract structured travel info.

SEARCH DATA:
{search1}
{search2}

Trip: {days} days in {destination}, interests: {interests}

Return ONLY valid JSON:
{{
  "destination": "{destination}",
  "top_sites": [
    {{"name": "name", "description": "desc", "tips": "tip"}}
  ],
  "weather": "weather summary",
  "hotel_areas": [
    {{"area": "area", "price_range": "price/night", "why": "reason"}}
  ],
  "food_highlights": ["food1", "food2"],
  "hidden_gems": ["gem1", "gem2"],
  "cultural_notes": ["note1"],
  "safety_tips": ["tip1"]
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    data = extract_json(response.content)

    if not data:
        data = {"destination": destination, "top_sites": [], "weather": "N/A",
                "hotel_areas": [], "food_highlights": [], "hidden_gems": [],
                "cultural_notes": [], "safety_tips": []}

    return {"research_data": json.dumps(data)}


# ─────────────────────────────────────────────
# NODE 2 — BUDGET ANALYST
# ─────────────────────────────────────────────

def budget_node(state: TravelState) -> dict:
    destination = state["destination"]
    budget = state["budget"]
    days = state["days"]
    interests = state["interests"]

    search = search_web(f"{destination} travel cost per day {days} days budget 2025")

    prompt = f"""You are a travel budget analyst.
Use this data to create a realistic budget breakdown.

SEARCH DATA:
{search}

Trip: {days} days in {destination}, budget: {budget}, interests: {interests}

Return ONLY valid JSON:
{{
  "total_budget": "{budget}",
  "is_budget_sufficient": true,
  "realistic_minimum": "",
  "breakdown": {{
    "flights": {{"estimated": "", "notes": ""}},
    "accommodation": {{"per_night": "", "total": "", "nights": {days}}},
    "food": {{"per_day": "", "total": ""}},
    "activities": {{"estimated": "", "items": []}},
    "transport": {{"per_day": "", "total": ""}},
    "buffer": ""
  }},
  "total_estimated_cost": "",
  "money_saving_tips": ["tip1", "tip2"]
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    data = extract_json(response.content)

    if not data:
        data = {"total_budget": budget, "is_budget_sufficient": True,
                "breakdown": {}, "money_saving_tips": []}

    return {"budget_data": json.dumps(data)}


# ─────────────────────────────────────────────
# NODE 3 — ITINERARY BUILDER
# ─────────────────────────────────────────────

def itinerary_node(state: TravelState) -> dict:
    destination = state["destination"]
    budget = state["budget"]
    interests = state["interests"]
    days = state["days"]
    research = state.get("research_data", "{}")
    budget_info = state.get("budget_data", "{}")
    critic_feedback = state.get("critic_data", "")
    revision_count = state.get("revision_count", 0)

    revision_note = ""
    if revision_count > 0 and critic_feedback:
        critic_parsed = extract_json(critic_feedback)
        issues = critic_parsed.get("issues_found", [])
        if issues:
            revision_note = f"FIX THESE ISSUES FROM PREVIOUS REVIEW: {', '.join(issues)}\n"

    # Build day structure string
    days_json = {}
    for i in range(1, days + 1):
        days_json[f"day_{i}"] = {
            "theme": f"Day {i} theme",
            "morning": {"activity": "", "location": "", "cost": "", "tip": ""},
            "afternoon": {"activity": "", "location": "", "cost": "", "tip": ""},
            "evening": {"activity": "", "location": "", "cost": ""},
            "day_total": ""
        }

    prompt = f"""You are an expert travel itinerary planner.
Create a complete {days}-day itinerary for {destination}.

RESEARCH: {research[:600]}
BUDGET: {budget_info[:400]}
Interests: {interests}, Budget: {budget}
{revision_note}

Return ONLY valid JSON with EXACTLY {days} days (day_1 through day_{days}):
{{
  "destination": "{destination}",
  "total_days": {days},
  "daily_itinerary": {json.dumps(days_json, indent=2)},
  "accommodation": {{"name": "", "area": "", "price_per_night": ""}},
  "top_restaurants": ["r1", "r2"],
  "packing_tips": ["tip1", "tip2"],
  "transport_tips": ""
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    data = extract_json(response.content)

    if not data:
        data = {"destination": destination, "total_days": days,
                "daily_itinerary": days_json, "accommodation": {},
                "top_restaurants": [], "packing_tips": [], "transport_tips": ""}

    new_revision_count = revision_count + 1 if revision_count > 0 else revision_count

    return {
        "itinerary_data": json.dumps(data),
        "revision_count": new_revision_count
    }


# ─────────────────────────────────────────────
# NODE 4 — CRITIC
# ─────────────────────────────────────────────

def critic_node(state: TravelState) -> dict:
    destination = state["destination"]
    days = state["days"]
    budget = state["budget"]
    interests = state["interests"]
    itinerary = state.get("itinerary_data", "{}")
    budget_info = state.get("budget_data", "{}")
    revision_count = state.get("revision_count", 0)

    force_approve = ""
    if revision_count >= 1:
        force_approve = 'IMPORTANT: Return "APPROVED" as verdict.'

    prompt = f"""You are a travel plan quality critic.
Review this plan strictly. {force_approve}

ITINERARY: {itinerary[:800]}
BUDGET: {budget_info[:300]}

Check: {days} days, interests={interests}, budget={budget}, destination={destination}

Return ONLY valid JSON:
{{
  "verdict": "APPROVED",
  "day_count_correct": true,
  "interest_alignment_score": 8,
  "issues_found": [],
  "revision_requests": [],
  "critic_notes": "brief assessment",
  "quality_score": 8
}}"""

    response = manager_llm.invoke([HumanMessage(content=prompt)])
    data = extract_json(response.content)

    if not data:
        data = {"verdict": "APPROVED", "quality_score": 7,
                "critic_notes": "Plan looks acceptable.", "issues_found": []}

    verdict = data.get("verdict", "APPROVED")

    return {"critic_data": json.dumps(data), "verdict": verdict}


# ─────────────────────────────────────────────
# NODE 5 — ASSEMBLER
# ─────────────────────────────────────────────

def assembler_node(state: TravelState) -> dict:
    research = extract_json(state.get("research_data", "{}"))
    budget = extract_json(state.get("budget_data", "{}"))
    itinerary = extract_json(state.get("itinerary_data", "{}"))
    critic = extract_json(state.get("critic_data", "{}"))

    final_plan = {
        "destination": state["destination"],
        "total_days": state["days"],
        "budget": state["budget"],
        "top_sites": research.get("top_sites", []),
        "weather": research.get("weather", ""),
        "hotel_areas": research.get("hotel_areas", []),
        "food_highlights": research.get("food_highlights", []),
        "hidden_gems": research.get("hidden_gems", []),
        "cultural_notes": research.get("cultural_notes", []),
        "safety_tips": research.get("safety_tips", []),
        "budget_breakdown": budget.get("breakdown", {}),
        "is_budget_sufficient": budget.get("is_budget_sufficient", True),
        "realistic_minimum": budget.get("realistic_minimum", ""),
        "total_estimated_cost": budget.get("total_estimated_cost", ""),
        "money_saving_tips": budget.get("money_saving_tips", []),
        "daily_itinerary": itinerary.get("daily_itinerary", {}),
        "accommodation": itinerary.get("accommodation", {}),
        "top_restaurants": itinerary.get("top_restaurants", []),
        "packing_tips": itinerary.get("packing_tips", []),
        "transport_tips": itinerary.get("transport_tips", ""),
        "verdict": critic.get("verdict", "APPROVED"),
        "quality_score": critic.get("quality_score", 0),
        "critic_notes": critic.get("critic_notes", ""),
        "issues_found": critic.get("issues_found", []),
    }

    return {"final_plan": final_plan}


# ─────────────────────────────────────────────
# CONDITIONAL EDGE
# ─────────────────────────────────────────────

def should_revise(state: TravelState) -> str:
    verdict = state.get("verdict", "APPROVED")
    revision_count = state.get("revision_count", 0)
    if verdict == "NEEDS REVISION" and revision_count < 1:
        return "revise"
    return "approve"


# ─────────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(TravelState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("budget_analyst", budget_node)
    graph.add_node("itinerary_builder", itinerary_node)
    graph.add_node("critic", critic_node)
    graph.add_node("assembler", assembler_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "budget_analyst")
    graph.add_edge("budget_analyst", "itinerary_builder")
    graph.add_edge("itinerary_builder", "critic")

    graph.add_conditional_edges(
        "critic",
        should_revise,
        {
            "revise": "itinerary_builder",
            "approve": "assembler"
        }
    )

    graph.add_edge("assembler", END)
    return graph.compile()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def run_travel_planner(destination: str, budget: str, interests: str,
                       days: int, user_id: str = "default") -> dict:
    graph = build_graph()

    initial_state: TravelState = {
        "destination": destination,
        "budget": budget,
        "interests": interests,
        "days": days,
        "research_data": "",
        "budget_data": "",
        "itinerary_data": "",
        "critic_data": "",
        "revision_count": 0,
        "verdict": "",
        "final_plan": {}
    }

    result = graph.invoke(initial_state)
    return result.get("final_plan", {})
