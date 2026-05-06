---
title: AI Travel Planner
emoji: 🌍
colorFrom: blue
colorTo: green
sdk: streamlit
app_file: app.py
pinned: false
---

# 🌍 AI Travel Planner — Multi-Agent System using LangGraph

An intelligent travel planning application built on a **5-node LangGraph StateGraph pipeline** with a real conditional feedback loop. Agents reason, search the web, critique the plan, and revise — not just pass tasks along.

---

🚀 **Live Demo**: [Try it here](https://huggingface.co/spaces/Sakshisingh2710/AI-Travel-Planner)

## 📸 Demo

### Itinerary View
![Itinerary](assets/demo_1.png)

### Budget Breakdown
![Budget](assets/demo.png)
---

## 🏗️ Architecture

```
User Input (destination, budget, interests, days)
        │
        ▼
┌─────────────────┐     ┌──────────────────┐
│   Researcher    │────▶│  Budget Analyst  │
│  Web search:    │     │  Web search:     │
│  attractions,   │     │  real prices,    │
│  hotels, food   │     │  validates budget│
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │Itinerary Builder│◀─────────┐
                        │ Dynamic days    │          │
                        │ Morning/        │          │ NEEDS REVISION
                        │ Afternoon/      │          │
                        │ Evening         │          │
                        └────────┬────────┘          │
                                 │                   │
                                 ▼                   │
                        ┌─────────────────┐          │
                        │     Critic      │──────────┘
                        │ Checks: day     │
                        │ count, budget,  │  APPROVED
                        │ interest align  │──────────▶ Assembler ──▶ END
                        └─────────────────┘
```

---

## ✅ What Makes This Genuinely Agentic

| Feature | Implementation |
|---|---|
| **Graph-based execution** | LangGraph StateGraph with explicit nodes, edges, and shared TypedDict state |
| **Conditional feedback loop** | Critic routes back to Itinerary Builder on NEEDS REVISION verdict |
| **Real-time web search** | Serper API called directly inside Researcher and Budget nodes |
| **Dynamic trip planning** | User sets 1–14 days; itinerary adapts exactly |
| **Budget validation** | Budget Analyst flags insufficient budgets with realistic alternatives |
| **Token-efficient design** | Prompts capped at 1,500 tokens/call — works within Groq free tier |
| **Plan refinement** | User can modify current plan via natural language |
| **PDF export** | Full structured itinerary downloadable as PDF |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph 0.2+ |
| LLM | Groq (LLaMA 3.3-70B Versatile) — free tier |
| Web Search | Serper API |
| Frontend | Streamlit |
| PDF Export | fpdf2 |
| Language | Python 3.10+ |

---

## 🚀 Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/sakshisingh-mooni/AI-Travel-planner
cd AI-Travel-planner
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up API keys
Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

### 4. Run
```bash
streamlit run app.py
```

---

## 🔑 API Keys (Both Free)

- **Groq**: [console.groq.com](https://console.groq.com) — 14,400 requests/day free
- **Serper**: [serper.dev](https://serper.dev) — 2,500 searches/month free

---

## 📁 Project Structure

```
├── crew.py              # LangGraph 5-node pipeline with conditional feedback loop
├── app.py               # Streamlit UI with session history and plan refinement
├── pdf_generator.py     # Structured PDF export
├── requirements.txt
├── .env                 # Your API keys (not committed)
├── .gitignore
└── assets/
    └── demo.png         # App screenshot
```

---

## 🔄 Why LangGraph over CrewAI

This project was initially built with CrewAI. It was migrated to LangGraph after hitting:
- **Version instability** — CrewAI 1.14.0 removed `LongTermMemory`/`ShortTermMemory` as importable classes without a major version bump
- **Token overhead** — CrewAI's hierarchical + planning mode consumed 15,000+ tokens per request, exceeding Groq free tier limits before agents ran
- **Opaque execution** — debugging agent failures required guessing; LangGraph makes every node and state transition explicit and inspectable
