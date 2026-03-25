# AI Candidate Evaluator

An automated, AI-powered hiring pipeline that evaluates candidate resumes and GitHub profiles, ranks them based on custom weights, and sends customized assessment emails to shortlisted candidates.

## 🚀 Features
- **Automated Resume Parsing:** Downloads and extracts text from PDF resumes via Google Drive links.
- **GitHub Profiling:** Fetches and analyzes recent public repositories for code quality and language matching.
- **LLM Evaluation:** Uses Groq (default: Llama-3.3-70b-versatile) via LangGraph to evaluate candidates against a specific Job Description.
- **Customizable Scoring:** Dynamically adjust the weight of Resumes, GitHub, Coding Tests, and Logical Ability (LA) tests.
- **Automated Emailing:** Uses SMTP to send shortlisted candidates their assessment links and invitations.

---

## 🛠️ Prerequisites

Ensure you have the following before starting:
1. **Python 3.10+** and **Node.js & npm** installed.
2. **Groq API Key** (Get one at [console.groq.com](https://console.groq.com)).
3. **GitHub Personal Access Token** (Classic token to read public repos).
4. **Google App Password** (For sending SMTP emails from your Gmail account).

---

## ⚙️ Local Setup & Installation
### 1. Backend Setup
1. Open a terminal in the root directory.
2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file in the root directory with the following content:
```plaintext
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token
GROQ_MODEL=llama-3.3-70b-versatile
```
### 2. Frontend Setup
Open a new terminal and navigate to the frontend folder:
```bash
dd frontend
npm install
```
### 3. Running Locally
Start Backend: `uvicorn backend:app --reload` (Runs on port 8000)
Start Frontend: `npm run dev` (Runs on port 5173)

☁️ Cloud Deployment
### Backend (Render)
push the repository to GitHub.
Create a new Web Service on Render connected to that repo.
build Command: `pip install -r requirements.txt`
start Command: `uvicorn backend:app --host 0.0.0.0 --port $PORT`
and add GROQ_API_KEY, GITHUB_TOKEN, and GROQ_MODEL to the Render Environment Variables.
### Frontend (Vercel)
in `frontend/src/App.jsx`, replace all `http://localhost:8000` instances with your live Render backend URL.
push the changes to GitHub.
import the repository into Vercel.
sSet the Root Directory to `frontend`.
deploy.

📖 How to Use the Evaluator
Create an Excel file (.xlsx) with exactly these headers:
| Header | Description |
|---------|--------------|
| name | Full name |
| email | Email address |
| test_code | Coding test score (0-100) |
| test_la | Logical ability test score (0-100) |
| resume | Public Google Drive link to PDF resume |
to configure UI:
oen the deployed frontend,
fll in your sender email, 16-digit App Password,
jobs description,
and assessment link.
tAdjust scoring weights as needed,
upload your Excel file,
and click "Start Evaluation".
the system will rank candidates based on your criteria,
and allow you to send assessment invites automatically.
