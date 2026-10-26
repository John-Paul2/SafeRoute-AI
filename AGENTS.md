# AGENTS.md — SafeRoute AI

Project: Micro Project 14 – AI-Based Road Accident Prediction (Traffic Mgmt / Insurance).
Integrated COs: CO3 (knowledge representation), CO4 (probabilistic reasoning), CO5 (ML).
Also covering CO1 (agent PEAS) and CO2 (A* search).
Read PLAN.md for scope and DESIGN.md for UI. Both are source of truth.

Stack (pin versions in requirements.txt / package.json):
- Backend: Python 3.10/3.11, Django 5 + Django REST Framework, django-cors-headers
- ML: pandas, scikit-learn, xgboost, joblib
- Probabilistic: pgmpy
- Rules: experta (if it breaks on this Python version, implement a small forward-chaining
  rule engine in plain Python with the same Fact/Rule structure and tell me)
- Routing: osmnx, networkx
- Frontend: React + Vite + TypeScript, Tailwind CSS, react-leaflet (no API token), React Flow (Bayesian net view)

Rules:
1. Work in small steps; after each step run the code/tests and show me the output.
2. No hardcoded fake results. Every number in the UI must come from the backend.
3. Pre-train and cache everything (models/*.joblib, bn.pkl, graph.graphml). API calls must respond in <1.5s.
4. Every module gets a short docstring mapping it to its CO (for my viva).
5. Use a US city for the OSM graph (dataset is US-only). Default: a ~5–10 km area, ≤20k nodes.
6. Keep code simple and commented; I must be able to explain it.
7. Never commit the raw dataset.

Folder structure:
saferoute/
  backend/ (manage.py, config/, api/, ml/, bn/, rules/, routing/, data/, models/)
  frontend/ (src/components, src/api, src/styles)
  notebooks/  docs/  README.md