# namespace std;
import os
import uuid
import smtplib
import requests
import gdown
import PyPDF2
import pandas as pd
import time
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = {}

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

class EmailRequest(BaseModel):
    candidate_email: str
    candidate_name: str
    test_link: str
    sender_email: str
    app_password: str
    email_message: str

llm = ChatGroq(model="llama-3.3-70b-versatile").with_structured_output(EvaluationOutput)

def evaluate_candidate(state: EvaluationState):
    print("-> Invoking LLM for evaluation...")
    prompt = f"JD: {state['jd_text']}\nResume: {state['resume_text']}\nGitHub: {state['github_data']}\nEvaluate the candidate. Provide separate scores (0 to 100) and brief feedback."
    try:
        result = llm.invoke(prompt)
        print("-> LLM evaluation successful.")
        return {
            "resume_score": result.resume_score, 
            "resume_feedback": result.resume_feedback,
            "github_score": result.github_score,
            "github_feedback": result.github_feedback
        }
    except Exception as e:
        print(f"!!! LLM Error: {e}")
        return {"resume_score": 0, "resume_feedback": "Error", "github_score": 0, "github_feedback": "Error"}

workflow = StateGraph(EvaluationState)
workflow.add_node("evaluate", evaluate_candidate)
workflow.set_entry_point("evaluate")
workflow.add_edge("evaluate", END)
evaluator_app = workflow.compile()

def extract_resume(url):
    if pd.isna(url) or not str(url).strip(): 
        print("-> No resume URL provided.")
        return ""
    
    print(f"-> Downloading PDF from: {url}")
    path = f"temp_{uuid.uuid4().hex}.pdf"
    gdown.download(url=str(url), output=path, quiet=True, fuzzy=True)
    
    try:
        reader = PyPDF2.PdfReader(path)
        text = "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
        os.remove(path)
        print("-> PDF extraction successful.")
        return text
    except Exception as e:
        print(f"!!! PDF Error extracting {url}: {e}")
        if os.path.exists(path): os.remove(path)
        return ""

def fetch_github_data(github_url):
    if pd.isna(github_url) or not isinstance(github_url, str) or not github_url.strip():
        print("-> No GitHub URL provided.")
        return "None"
    
    username = github_url.rstrip('/').split('/')[-1]
    print(f"-> Fetching GitHub data for user: {username}")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    try:
        res = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5", headers=headers)
        if res.status_code != 200: 
            print(f"!!! GitHub API Error: Status {res.status_code}")
            return "Error"
        repos = res.json()
        repo_details = [f"{r['name']} | {r.get('language')} | {r.get('description')}" for r in repos if not r.get('fork')]
        print("-> GitHub data fetched successfully.")
        return "\n".join(repo_details) if repo_details else "No public repos"
    except Exception as e:
        print(f"!!! GitHub Exception: {e}")
        return "Error"

def send_test_link(to_email, candidate_name, test_link, sender_email, app_password, email_message):
    print(f"-> Preparing email for {to_email}")
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Action Required: Visl AI Labs Assessment"
    
    body = email_message.replace("{name}", candidate_name).replace("{link}", test_link)
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"-> Connecting to SMTP server to send to {to_email}...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"-> Email successfully sent to {to_email}")
    except Exception as e:
        print(f"!!! Email Error for {to_email}: {e}")
        raise e

def process_evaluation(task_id: str, file_path: str, jd_text: str, assessment_link: str, sender_email: str, app_password: str, weight_resume: float, weight_github: float, weight_test_code: float, weight_test_la: float):
    print(f"\n========== STARTING TASK: {task_id} ==========")
    print(f"-> Weights - Resume: {weight_resume}%, GitHub: {weight_github}%, Code: {weight_test_code}%, LA: {weight_test_la}%")
    
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        print(f"!!! Error reading Excel file: {e}")
        tasks[task_id] = {"status": "error", "error": str(e)}
        return

    total_candidates = len(df)
    
    tasks[task_id] = {
        "status": "processing", 
        "total": total_candidates, 
        "processed": 0, 
        "current": "Initializing...",
        "results": []
    }
    
    evaluated_candidates = []
    
    for index, row in df.iterrows():
        name = row.get('name', 'Unknown')
        email = row.get('email', '')
        print(f"\n--- Processing Row {index + 1}/{total_candidates}: {name} ---")
        
        tasks[task_id]["current"] = name
        
        test_code = pd.to_numeric(row.get('test_code', 0), errors='coerce') or 0
        test_la = pd.to_numeric(row.get('test_la', 0), errors='coerce') or 0
        
        resume_text = extract_resume(row.get('resume', ''))
        github_data = fetch_github_data(row.get('github', ''))
        
        if resume_text:
            inputs = {
                "resume_text": resume_text[:5000],
                "github_data": github_data,
                "jd_text": jd_text
            }
            
            result = evaluator_app.invoke(inputs)
            
            # Dynamic calculation using frontend weights
            final_score = ((weight_test_code / 100.0) * test_code) + \
                          ((weight_github / 100.0) * result['github_score']) + \
                          ((weight_resume / 100.0) * result['resume_score']) + \
                          ((weight_test_la / 100.0) * test_la)
                          
            print(f"-> Final Score calculated: {final_score}")
            
            evaluated_candidates.append({
                "Name": name,
                "Email": email,
                "Resume_Score": result['resume_score'],
                "GitHub_Score": result['github_score'],
                "Test_Code": test_code,
                "Test_LA": test_la,
                "Final_Score": round(final_score, 2),
                "Reason": f"Resume: {result['resume_feedback']} | GitHub: {result['github_feedback']}"
            })
            
        tasks[task_id]["processed"] = index + 1
        time.sleep(2) 
        
    ranked_df = pd.DataFrame(evaluated_candidates).sort_values(by="Final_Score", ascending=False).reset_index(drop=True)
    all_results = ranked_df.to_dict(orient="records")
    
    tasks[task_id] = {"status": "completed", "results": all_results}
    if os.path.exists(file_path): os.remove(file_path)
@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    sender_email: str = Form(...),
    app_password: str = Form(...),
    jd_text: str = Form(...),
    test_link: str = Form(...),
    weight_resume: float = Form(...),
    weight_github: float = Form(...),
    weight_test_code: float = Form(...),
    weight_test_la: float = Form(...)
):
    print(f"\n========== NEW UPLOAD RECEIVED ==========")
    task_id = str(uuid.uuid4())
    file_path = f"{task_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    background_tasks.add_task(process_evaluation, task_id, file_path, jd_text, test_link, sender_email, app_password, weight_resume, weight_github, weight_test_code, weight_test_la)
    return {"task_id": task_id, "status": "processing"}

@app.get("/api/status/{task_id}")
def get_status(task_id: str):
    return tasks.get(task_id, {"status": "not_found"})

@app.post("/api/send-email")
def trigger_email(req: EmailRequest):
    print(f"\n========== MANUAL EMAIL TRIGGER ==========")
    print(f"Attempting to send email to: {req.candidate_email}")
    try:
        send_test_link(req.candidate_email, req.candidate_name, req.test_link, req.sender_email, req.app_password, req.email_message)
        print("-> Trigger complete. Success.")
        return {"status": "success"}
    except Exception as e:
        print(f"!!! Trigger complete. Failed: {e}")
        return {"status": "error", "detail": str(e)}