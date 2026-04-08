import streamlit as st
from crew import run_travel_planner
import json
import os
import traceback
import re
from pdf_generator import generate_pdf

st.set_page_config(page_title="AI Travel Planner", layout="wide")

# ---------------- HEADER ----------------
st.markdown("# 🌍 AI Travel Planner")
st.caption("Plan smart trips using AI agents ✨")
st.divider()

# ---------------- SESSION STATE ----------------
if "data" not in st.session_state:
    st.session_state.data = None

# ---------------- INPUTS ----------------
col1, col2, col3 = st.columns(3)

with col1:
    destination = st.text_input("📍 Destination", placeholder="e.g. Goa")

with col2:
    budget = st.text_input("💰 Budget", placeholder="e.g. 10000 INR")

with col3:
    interests = st.text_input("🎯 Interests", placeholder="beach, nightlife")

# ---------------- HELPER FUNCTION ----------------
def extract_json_from_raw(text):
    """Extract JSON block from messy CrewAI raw output"""
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        return None
    return None

# ---------------- GENERATE BUTTON ----------------
if st.button("🚀 Generate Travel Plan"):

    if not destination or not budget or not interests:
        st.warning("⚠️ Please fill all fields")
        st.stop()

    with st.spinner("🤖 Planning your trip..."):
        try:
            result = run_travel_planner(destination, budget, interests)

            st.info("🔍 Processing AI response...")

            data = None

            # ✅ Handle CrewOutput properly
            if hasattr(result, "json_dict") and result.json_dict:
                data = result.json_dict

            elif hasattr(result, "raw"):
                data = extract_json_from_raw(result.raw)

            elif hasattr(result, "tasks_output"):
                raw_text = str(result.tasks_output)
                data = extract_json_from_raw(raw_text)

            elif isinstance(result, dict):
                data = result

            if not data:
                st.error("❌ Could not extract structured data")
                st.write(result)
                st.stop()

            st.session_state.data = data
            st.success("✅ Travel Plan Ready!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.text(traceback.format_exc())

# ---------------- DISPLAY ----------------
if st.session_state.data:

    data = st.session_state.data

    st.divider()

    # 🌄 Banner Image
    st.image(f"https://source.unsplash.com/1200x400/?{destination},travel")

    col1, col2 = st.columns(2)

    # -------- LEFT --------
    with col1:
        st.subheader("📍 Top Places")

        sites = data.get("sites", [])
        if isinstance(sites, list):
            for site in sites[:5]:   # ✅ limit to 5
                st.markdown(f"- **{site.get('title','Place')}**")
        else:
            st.write("Not available")

        st.subheader("🌦️ Weather")
        st.write(data.get("weather", "Not available"))

    # -------- RIGHT --------
    with col2:
        st.subheader("🏨 Hotels")

        hotels = data.get("hotels", [])
        if isinstance(hotels, list):
            for h in hotels:
                if isinstance(h, dict):
                    st.markdown(f"- **{h.get('title')}**: {h.get('description')}")
                else:
                    st.markdown(f"- {h}")

        st.subheader("💰 Budget")
        st.write(data.get("budget", "Not available"))

    # -------- ITINERARY --------
    st.divider()
    st.subheader("🗺️ 3-Day Plan")

    for i in range(1, 4):
        st.markdown(f"**Day {i}:** {data.get(f'day{i}', 'Not available')}")

    # -------- PDF --------
    st.divider()
    st.subheader("📄 Export")

    try:
        pdf_file = generate_pdf(data)

        if os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📄 Download PDF",
                    f,
                    file_name="travel_plan.pdf"
                )
        else:
            st.error("PDF generation failed")

    except Exception as e:
        st.error(f"PDF Error: {e}")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("🚀 Built with CrewAI + Gemini")