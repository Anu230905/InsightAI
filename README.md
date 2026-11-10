

# InsightAI – Agentic Data Intelligence and Decision Support System

InsightAI is a local AI-powered data analytics application designed to help users upload, explore, clean, analyse and interpret datasets using traditional data analytics and Generative AI.

## Features

1. Dataset Upload and Profiling
2. Data Quality Doctor
3. Data Cleaning and Repair Lab
4. SQL Analytics Studio
5. Natural Language to SQL
6. Smart Visualization Studio
7. Root Cause Analysis
8. What-If Simulation
9. AI Report Generator
10. Agentic AI Data Analyst

## Technology Stack

- Python
- Streamlit
- Pandas and NumPy
- DuckDB
- Plotly
- Ollama
- Qwen2.5 1.5B

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Insight_AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Ollama

Download Ollama from:

https://ollama.com/

Download the required local model:

```bash
ollama pull qwen2.5:1.5b
```

Make sure Ollama is running before using the AI modules.

### 6. Run the application

```bash
streamlit run app.py
```

## Project Architecture

The application is organized into modular backend components and a Streamlit frontend.

- `app.py` – Application interface and navigation
- `backend/` – Data processing, analytics, AI and simulation modules
- `data/` – Local datasets (not included in the repository)

## Note

InsightAI uses a locally running Ollama model. The model weights are not included in this repository and must be downloaded separately.

This project is an academic development project. Its AI-generated analysis and recommendations should be validated before making business decisions.
