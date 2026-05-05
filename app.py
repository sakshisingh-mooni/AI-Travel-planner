import streamlit as st
import json
import os
from datetime import datetime

@st.cache_resource(show_spinner="Loading AI agents... (first load only)")
def load_planner():
    from crew import run_travel_planner
    return run_travel_planner

@st.cache_resource(show_spinner=False)
def load_pdf_generator():
    from pdf_generator import generate_pdf
    return generate_pdf

run_travel_planner = load_planner()
generate_pdf = load_pdf_generator()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "destination": "",
        "budget": "",
        "interests": "",
        "days": 3
    }

if "user_id" not in st.session_state:
    # Unique session ID for memory scoping
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if "planning_count" not in st.session_state:
    st.session_state.planning_count = 0

# ─────────────────────────────────────────────
# SIDEBAR — User Profile + History
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("🧳 Travel Planner")
    st.caption("Powered by Multi-Agent AI")
    st.divider()

    st.subheader("📋 Your Profile")

    destination = st.text_input(
        "Destination",
        value=st.session_state.user_profile["destination"],
        placeholder="e.g. Tokyo, Japan"
    )

    budget = st.text_input(
        "Total Budget",
        value=st.session_state.user_profile["budget"],
        placeholder="e.g. ₹80,000 or $1500"
    )

    days = st.slider(
        "Trip Duration (days)",
        min_value=1,
        max_value=14,
        value=st.session_state.user_profile["days"],
        step=1
    )

    interests = st.text_area(
        "Interests & Preferences",
        value=st.session_state.user_profile["interests"],
        placeholder="e.g. street food, history, hiking, budget travel, photography",
        height=100
    )

    st.divider()

    # Refinement input — uses agent memory
    st.subheader("🔄 Refine Existing Plan")
    refinement = st.text_input(
        "Modify current plan",
        placeholder="e.g. make day 2 cheaper, add more food experiences"
    )

    col1, col2 = st.columns(2)
    with col1:
        plan_btn = st.button("🚀 Plan Trip", use_container_width=True, type="primary")
    with col2:
        refine_btn = st.button("✏️ Refine", use_container_width=True,
                               disabled=(st.session_state.current_plan is None))

    st.divider()

    # Session history
    if st.session_state.conversation_history:
        st.subheader("📜 Session History")
        for i, entry in enumerate(st.session_state.conversation_history):
            st.caption(f"**{i+1}.** {entry['destination']} — {entry['days']}d — {entry['timestamp']}")

    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.conversation_history = []
        st.session_state.current_plan = None
        st.session_state.planning_count = 0
        st.rerun()

# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────

st.title("🌍 AI Travel Planner")
st.caption("A multi-agent AI system that thinks, plans, budgets, and reviews your trip.")

# ─────────────────────────────────────────────
# PLAN GENERATION
# ─────────────────────────────────────────────

def validate_inputs(destination, budget, interests, days):
    errors = []
    if not destination.strip():
        errors.append("Please enter a destination.")
    if not budget.strip():
        errors.append("Please enter a budget.")
    if not interests.strip():
        errors.append("Please enter your interests.")
    if days < 1:
        errors.append("Trip must be at least 1 day.")
    return errors


def display_plan(plan):
    """Render the travel plan in a structured, readable layout."""

    if not plan:
        st.error("Could not generate a plan. Please try again.")
        return

    # ── Header ──
    st.success(f"✅ Plan ready for **{plan.get('destination', 'your destination')}** — {plan.get('total_days', days)} days")

    # ── Critic verdict ──
    critic = plan.get("critic_notes", "")
    verdict = plan.get("verdict", "")
    quality = plan.get("overall_quality_score", "")

    if verdict or quality:
        with st.expander("🔍 AI Quality Review", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if verdict == "APPROVED":
                    st.success(f"Verdict: {verdict}")
                elif verdict == "NEEDS REVISION":
                    st.warning(f"Verdict: {verdict}")
            with col2:
                if quality:
                    st.metric("Quality Score", f"{quality}/10")
            if critic:
                st.write(critic)
            issues = plan.get("issues_found", [])
            if issues:
                st.write("**Issues found:**")
                for issue in issues:
                    st.write(f"• {issue}")

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Itinerary", "💰 Budget", "🗺️ Destination Info", "💡 Tips"])

    with tab1:
        daily = plan.get("daily_itinerary", {})
        if not daily:
            st.info("Itinerary data not available.")
        else:
            for day_key, day_data in daily.items():
                day_num = day_key.replace("day_", "Day ")
                theme = day_data.get("theme", "") if isinstance(day_data, dict) else ""
                header = f"**{day_num.capitalize()}**" + (f" — *{theme}*" if theme else "")
                with st.expander(header, expanded=(day_key == "day_1")):
                    if isinstance(day_data, dict):
                        for period in ["morning", "afternoon", "evening"]:
                            period_data = day_data.get(period, {})
                            if period_data and isinstance(period_data, dict):
                                icon = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}[period]
                                st.markdown(f"{icon} **{period.capitalize()}**")
                                st.write(f"📍 {period_data.get('activity', '')} — {period_data.get('location', '')}")
                                cost = period_data.get("estimated_cost", "")
                                duration = period_data.get("duration_hours", "")
                                tip = period_data.get("tips", "")
                                if cost:
                                    st.caption(f"💸 {cost}" + (f"  |  ⏱ {duration}h" if duration else ""))
                                if tip:
                                    st.info(f"💡 {tip}", icon="💡")
                                st.write("")
                        daily_total = day_data.get("daily_total_estimate", "")
                        if daily_total:
                            st.success(f"**Estimated day total: {daily_total}**")
                    else:
                        st.write(day_data)

    with tab2:
        breakdown = plan.get("budget_breakdown", plan.get("breakdown", {}))
        sufficient = plan.get("is_budget_sufficient", True)

        if not sufficient:
            realistic = plan.get("realistic_minimum_if_insufficient", "")
            st.warning(f"⚠️ Your budget may be tight. Realistic minimum: **{realistic}**")

        if breakdown:
            cols = st.columns(3)
            items = list(breakdown.items())
            for i, (k, v) in enumerate(items):
                with cols[i % 3]:
                    label = k.replace("_", " ").title()
                    if isinstance(v, dict):
                        val = v.get("total", v.get("estimated", str(v)))
                        note = v.get("notes", "")
                    else:
                        val = str(v)
                        note = ""
                    st.metric(label, val)
                    if note:
                        st.caption(note)

        tips = plan.get("money_saving_tips", [])
        if tips:
            st.subheader("💡 Money-Saving Tips")
            for tip in tips:
                st.write(f"• {tip}")

        total_est = plan.get("total_estimated_cost", "")
        if total_est:
            st.info(f"**Total estimated cost: {total_est}**")

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            weather = plan.get("weather", "")
            if weather:
                st.subheader("🌤️ Weather")
                st.write(weather)

            sites = plan.get("top_sites", plan.get("sites", []))
            if sites:
                st.subheader("🏛️ Top Attractions")
                for site in sites:
                    if isinstance(site, dict):
                        st.write(f"**{site.get('name', '')}**")
                        st.caption(site.get("description", ""))
                    else:
                        st.write(f"• {site}")

        with col2:
            hotels = plan.get("hotel_areas", plan.get("hotels", []))
            if hotels:
                st.subheader("🏨 Recommended Stay Areas")
                for h in hotels:
                    if isinstance(h, dict):
                        st.write(f"**{h.get('area', h.get('name', ''))}**")
                        st.caption(h.get("why", h.get("price_range_per_night", "")))
                    else:
                        st.write(f"• {h}")

            food = plan.get("food_highlights", [])
            if food:
                st.subheader("🍜 Food Highlights")
                for item in food:
                    st.write(f"• {item}")

    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            safety = plan.get("safety_tips", [])
            if safety:
                st.subheader("🛡️ Safety Tips")
                for tip in safety:
                    st.write(f"• {tip}")

            cultural = plan.get("cultural_notes", [])
            if cultural:
                st.subheader("🎎 Cultural Notes")
                for note in cultural:
                    st.write(f"• {note}")

        with col2:
            gems = plan.get("hidden_gems", [])
            if gems:
                st.subheader("💎 Hidden Gems")
                for gem in gems:
                    st.write(f"• {gem}")

            packing = plan.get("packing_tips", [])
            if packing:
                st.subheader("🎒 Packing Tips")
                for tip in packing:
                    st.write(f"• {tip}")

    # ── PDF Export ──
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("📄 Export PDF", use_container_width=True):
            with st.spinner("Generating PDF..."):
                pdf_path = generate_pdf(plan)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download PDF",
                        data=f,
                        file_name=f"travel_plan_{plan.get('destination','trip').replace(' ','_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )


# ─────────────────────────────────────────────
# BUTTON HANDLERS
# ─────────────────────────────────────────────

if plan_btn:
    errors = validate_inputs(destination, budget, interests, days)
    if errors:
        for e in errors:
            st.error(e)
    else:
        # Save to session profile
        st.session_state.user_profile = {
            "destination": destination,
            "budget": budget,
            "interests": interests,
            "days": days
        }

        st.session_state.planning_count += 1

        with st.spinner(f"🤖 Agents are planning your {days}-day trip to {destination}... This takes 1-2 minutes."):
            try:
                plan = run_travel_planner(
                    destination=destination,
                    budget=budget,
                    interests=interests,
                    days=days,
                    user_id=st.session_state.user_id
                )
                st.session_state.current_plan = plan

                # Save to conversation history
                st.session_state.conversation_history.append({
                    "destination": destination,
                    "days": days,
                    "budget": budget,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "plan": plan
                })

            except Exception as e:
                st.error(f"Planning failed: {str(e)}")
                st.info("If you're hitting API rate limits, wait 60 seconds and try again.")
                st.stop()

if refine_btn and refinement.strip() and st.session_state.current_plan:
    # Build refined query — agents will use memory of previous run
    refined_interests = f"{interests}. REFINEMENT REQUEST: {refinement}"

    with st.spinner(f"🔄 Agents are refining your plan based on: '{refinement}'..."):
        try:
            plan = run_travel_planner(
                destination=destination,
                budget=budget,
                interests=refined_interests,
                days=days,
                user_id=st.session_state.user_id  # Same user_id = agents recall previous run
            )
            st.session_state.current_plan = plan

            st.session_state.conversation_history.append({
                "destination": f"{destination} (refined)",
                "days": days,
                "budget": budget,
                "timestamp": datetime.now().strftime("%H:%M"),
                "plan": plan
            })

        except Exception as e:
            st.error(f"Refinement failed: {str(e)}")

# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────

if st.session_state.current_plan:
    display_plan(st.session_state.current_plan)
else:
    # Landing state
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🧠 Manager Agent**\nOrchestrates the full plan — thinks before delegating")
    with col2:
        st.info("**🔍 Researcher + Budget Analyst**\nSearch the web for real, current data")
    with col3:
        st.info("**🗓️ Itinerary Builder + Critic**\nBuilds your plan, then reviews it for quality")

    st.markdown("---")
    st.caption("Enter your trip details in the sidebar and click **Plan Trip** to start.")
