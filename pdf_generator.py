from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(data):
    doc = SimpleDocTemplate("travel_plan.pdf")
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("AI Travel Plan", styles["Title"]))

    content.append(Paragraph(f"Sites: {data.get('sites')}", styles["Normal"]))
    content.append(Paragraph(f"Weather: {data.get('weather')}", styles["Normal"]))
    content.append(Paragraph(f"Hotels: {data.get('hotels')}", styles["Normal"]))

    content.append(Paragraph(f"Day 1: {data.get('day1')}", styles["Normal"]))
    content.append(Paragraph(f"Day 2: {data.get('day2')}", styles["Normal"]))
    content.append(Paragraph(f"Day 3: {data.get('day3')}", styles["Normal"]))

    doc.build(content)

    return "travel_plan.pdf"