from fpdf import FPDF
import os
from datetime import datetime


def safe(text) -> str:
    """Convert anything to a latin-1 safe string for fpdf."""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


class TravelPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 13)
        self.set_text_color(26, 86, 160)
        self.cell(0, 10, "AI Travel Planner", ln=True, align="C")
        self.set_draw_color(26, 86, 160)
        self.line(10, 20, 200, 20)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Generated {datetime.now().strftime('%d %b %Y')}", align="C")

    def section(self, title: str):
        self.ln(4)
        self.set_font("Arial", "B", 11)
        self.set_text_color(26, 86, 160)
        self.cell(0, 8, safe(title), ln=True)
        self.set_draw_color(200, 210, 230)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_text_color(30, 30, 30)

    def body(self, text: str, indent: int = 0):
        self.set_font("Arial", "", 10)
        self.set_text_color(50, 50, 50)
        self.set_x(10 + indent)
        self.multi_cell(190 - indent, 6, safe(text))

    def bold(self, text: str, indent: int = 0):
        self.set_font("Arial", "B", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(10 + indent)
        self.multi_cell(190 - indent, 7, safe(text))

    def bullet(self, text: str):
        self.body(f"• {text}", indent=4)

    def kv(self, key: str, value: str):
        self.set_font("Arial", "B", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(10)
        self.cell(45, 6, safe(f"{key}:"))
        self.set_font("Arial", "", 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, safe(value))


def generate_pdf(plan: dict) -> str:
    pdf = TravelPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    destination = plan.get("destination", "Trip")
    total_days = plan.get("total_days", "?")
    budget = plan.get("budget", "N/A")

    # ── Title block ──
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(26, 86, 160)
    pdf.cell(0, 12, safe(destination), ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, safe(f"{total_days}-Day Trip  |  Budget: {budget}"), ln=True, align="C")
    pdf.ln(4)

    # ── Quality verdict ──
    verdict = plan.get("verdict", "")
    score = plan.get("quality_score", "")
    notes = plan.get("critic_notes", "")
    if verdict:
        pdf.section("AI Quality Review")
        if verdict:
            pdf.kv("Verdict", verdict)
        if score:
            pdf.kv("Quality Score", f"{score}/10")
        if notes:
            pdf.body(notes)

    # ── Daily Itinerary ──
    daily = plan.get("daily_itinerary", {})
    if daily:
        pdf.section("Day-by-Day Itinerary")
        for day_key in sorted(daily.keys()):
            day_data = daily[day_key]
            theme = ""
            if isinstance(day_data, dict):
                theme = day_data.get("theme", "")

            day_label = day_key.replace("day_", "Day ").capitalize()
            heading = f"{day_label}" + (f" — {theme}" if theme else "")
            pdf.bold(heading)

            if isinstance(day_data, dict):
                for period in ["morning", "afternoon", "evening"]:
                    period_data = day_data.get(period, {})
                    if not period_data or not isinstance(period_data, dict):
                        continue
                    icons = {"morning": "Morning", "afternoon": "Afternoon", "evening": "Evening"}
                    pdf.set_font("Arial", "BI", 9)
                    pdf.set_text_color(80, 100, 140)
                    pdf.set_x(14)
                    pdf.cell(0, 6, icons[period], ln=True)

                    activity = period_data.get("activity", "")
                    location = period_data.get("location", "")
                    cost = period_data.get("cost", period_data.get("estimated_cost", ""))
                    tip = period_data.get("tip", period_data.get("tips", ""))

                    if activity:
                        line = activity
                        if location:
                            line += f" @ {location}"
                        pdf.body(line, indent=8)
                    if cost:
                        pdf.body(f"Cost: {cost}", indent=8)
                    if tip:
                        pdf.set_font("Arial", "I", 9)
                        pdf.set_text_color(80, 80, 80)
                        pdf.set_x(18)
                        pdf.multi_cell(0, 5, safe(f"Tip: {tip}"))
                        pdf.set_text_color(50, 50, 50)

                day_total = day_data.get("day_total", day_data.get("daily_total_estimate", ""))
                if day_total:
                    pdf.set_font("Arial", "B", 9)
                    pdf.set_text_color(26, 86, 160)
                    pdf.set_x(14)
                    pdf.cell(0, 6, safe(f"Estimated day total: {day_total}"), ln=True)
                    pdf.set_text_color(30, 30, 30)
            else:
                pdf.body(str(day_data), indent=8)
            pdf.ln(2)

    # ── Budget Breakdown ──
    breakdown = plan.get("budget_breakdown", {})
    if breakdown:
        pdf.section("Budget Breakdown")
        sufficient = plan.get("is_budget_sufficient", True)
        if not sufficient:
            minimum = plan.get("realistic_minimum", "")
            pdf.body(f"WARNING: Budget may be insufficient. Realistic minimum: {minimum}")
            pdf.ln(1)

        for k, v in breakdown.items():
            label = k.replace("_", " ").title()
            if isinstance(v, dict):
                val = v.get("total", v.get("estimated", ""))
                note = v.get("notes", "")
                text = val + (f" ({note})" if note else "")
            else:
                text = str(v)
            pdf.kv(label, text)

        total_est = plan.get("total_estimated_cost", "")
        if total_est:
            pdf.ln(1)
            pdf.bold(f"Total Estimated Cost: {total_est}")

        tips = plan.get("money_saving_tips", [])
        if tips:
            pdf.ln(2)
            pdf.bold("Money-Saving Tips:")
            for tip in tips:
                pdf.bullet(str(tip))

    # ── Accommodation ──
    acc = plan.get("accommodation", {})
    if acc and isinstance(acc, dict) and acc.get("name"):
        pdf.section("Recommended Accommodation")
        pdf.kv("Name", acc.get("name", ""))
        pdf.kv("Area", acc.get("area", ""))
        pdf.kv("Price/Night", acc.get("price_per_night", ""))

    # ── Destination Info ──
    weather = plan.get("weather", "")
    sites = plan.get("top_sites", [])
    food = plan.get("food_highlights", [])
    hotels = plan.get("hotel_areas", [])

    if weather or sites or food or hotels:
        pdf.section("Destination Overview")

        if weather:
            pdf.kv("Weather", weather)

        if sites:
            pdf.ln(1)
            pdf.bold("Top Attractions:")
            for site in sites:
                if isinstance(site, dict):
                    name = site.get("name", "")
                    desc = site.get("description", "")
                    tip = site.get("tips", "")
                    pdf.bullet(name + (f": {desc}" if desc else "") + (f" | Tip: {tip}" if tip else ""))
                else:
                    pdf.bullet(str(site))

        if hotels:
            pdf.ln(1)
            pdf.bold("Stay Areas:")
            for h in hotels:
                if isinstance(h, dict):
                    pdf.bullet(f"{h.get('area', '')} — {h.get('price_range', '')} — {h.get('why', '')}")
                else:
                    pdf.bullet(str(h))

        if food:
            pdf.ln(1)
            pdf.bold("Food Highlights:")
            for item in food:
                pdf.bullet(str(item))

    # ── Tips ──
    gems = plan.get("hidden_gems", [])
    cultural = plan.get("cultural_notes", [])
    safety = plan.get("safety_tips", [])
    packing = plan.get("packing_tips", [])
    transport = plan.get("transport_tips", "")
    restaurants = plan.get("top_restaurants", [])

    if any([gems, cultural, safety, packing, transport, restaurants]):
        pdf.section("Tips & Extras")

        if restaurants:
            pdf.bold("Top Restaurants:")
            for r in restaurants:
                pdf.bullet(str(r))
            pdf.ln(1)

        if gems:
            pdf.bold("Hidden Gems:")
            for g in gems:
                pdf.bullet(str(g))
            pdf.ln(1)

        if cultural:
            pdf.bold("Cultural Notes:")
            for c in cultural:
                pdf.bullet(str(c))
            pdf.ln(1)

        if safety:
            pdf.bold("Safety Tips:")
            for s in safety:
                pdf.bullet(str(s))
            pdf.ln(1)

        if packing:
            pdf.bold("Packing Tips:")
            for p in packing:
                pdf.bullet(str(p))
            pdf.ln(1)

        if transport:
            pdf.bold("Local Transport:")
            pdf.body(str(transport))

    # ── Save ──
    filename = f"travel_plan_{destination.replace(' ', '_').replace(',', '')}.pdf"
    output_path = os.path.join(os.getcwd(), filename)
    pdf.output(output_path)
    return output_path
