"""
Test script extracted from eval.ipynb - runs the full evaluation pipeline.
"""
import os
import requests
import dotenv
import pandas as pd
import PyPDF2
import gdown
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

dotenv.load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Load dataset
df = pd.read_excel("candidate_dataset.xlsx", engine="openpyxl")
print(f"Loaded {len(df)} candidates")

# Helper functions
def extract_resume(url):
    if pd.isna(url): return ""
    path = "temp.pdf"
    gdown.download(url=str(url), output=path, quiet=True, fuzzy=True)
    try:
        reader = PyPDF2.PdfReader(path)
        return "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
    except:
        return ""

def fetch_github_data(github_url):
    if pd.isna(github_url) or not isinstance(github_url, str): return "None"
    username = github_url.rstrip('/').split('/')[-1]
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    res = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5", headers=headers)
    if res.status_code != 200: return "Error"
    repos = res.json()
    repo_details = []
    for r in repos:
        if not r.get('fork'):
            repo_details.append(f"{r['name']} | {r.get('language')} | {r.get('description')}")
    return "\n".join(repo_details) if repo_details else "No public repos"

# LangGraph evaluation
class EvaluationState(TypedDict):
    resume_text: str
    github_data: str
    jd_text: str
    resume_score: int
    resume_feedback: str
    github_score: int
    github_feedback: str

class EvaluationOutput(BaseModel):
    resume_score: int = Field(description="Resume match score from 0 to 100")
    resume_feedback: str = Field(description="Brief justification for resume score")
    github_score: int = Field(description="GitHub match score from 0 to 100")
    github_feedback: str = Field(description="Brief justification for GitHub score")

llm = ChatGroq(model="llama-3.3-70b-versatile").with_structured_output(EvaluationOutput)

def evaluate_candidate(state: EvaluationState):
    prompt = f"JD: {state['jd_text']}\nResume: {state['resume_text']}\nGitHub: {state['github_data']}\nEvaluate the candidate. Provide separate scores (0 to 100) and brief feedback for both the resume and the GitHub profile against the JD."
    result = llm.invoke(prompt)
    return {
        "resume_score": result.resume_score,
        "resume_feedback": result.resume_feedback,
        "github_score": result.github_score,
        "github_feedback": result.github_feedback
    }

workflow = StateGraph(EvaluationState)
workflow.add_node("evaluate", evaluate_candidate)
workflow.set_entry_point("evaluate")
workflow.add_edge("evaluate", END)
evaluator_app = workflow.compile()

# Main evaluation loop
job_description = "Looking for an AI Engineer with Python, LLMs, and backend experience."
evaluated_candidates = []

for index, row in df.iterrows():
    name = row.get('name', '')
    email = row.get('email', '')
    test_code = pd.to_numeric(row.get('test_code', 0), errors='coerce') or 0
    test_la = pd.to_numeric(row.get('test_la', 0), errors='coerce') or 0

    print(f"\n--- Processing candidate {index+1}/{len(df)}: {name} ---")

    resume_text = extract_resume(row.get('resume', ''))
    print(f"  Resume: {'extracted' if resume_text else 'FAILED'} ({len(resume_text)} chars)")

    github_data = fetch_github_data(row.get('github', ''))
    print(f"  GitHub: {github_data[:80]}...")

    if not resume_text:
        print("  SKIPPED (no resume)")
        continue

    inputs = {
        "resume_text": resume_text[:5000],
        "github_data": github_data,
        "jd_text": job_description
    }

    result = evaluator_app.invoke(inputs)
    print(f"  Resume Score: {result['resume_score']}, GitHub Score: {result['github_score']}")

    final_score = (0.40 * test_code) + (0.20 * result['github_score']) + (0.30 * result['resume_score']) + (0.10 * test_la)

    evaluated_candidates.append({
        "Name": name,
        "Email": email,
        "Resume Score": result['resume_score'],
        "GitHub Score": result['github_score'],
        "Test Code": test_code,
        "Test LA": test_la,
        "Final Score": round(final_score, 2)
    })

ranked_df = pd.DataFrame(evaluated_candidates).sort_values(by="Final Score", ascending=False).reset_index(drop=True)
print("\n\n=== FINAL RANKINGS ===")
print(ranked_df)
print("\n=== TOP 5 ===")
print(ranked_df.head(5))
