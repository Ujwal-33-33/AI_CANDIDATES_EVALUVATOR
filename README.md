# AI Candidate Evaluator

An automated, AI-powered hiring pipeline that evaluates candidate resumes and GitHub profiles, ranks them based on custom weights, and automatically schedules Google Meet interviews while sending customized assessment emails.

## 🚀 Features
- **Automated Resume Parsing:** Downloads and extracts text from PDF resumes via Google Drive links.
- **GitHub Profiling:** Fetches and analyzes recent public repositories for code quality and language matching.
- **LLM Evaluation:** Uses Groq (Llama-3.3-70b) via LangGraph to evaluate candidates against a specific Job Description.
- **Customizable Scoring:** Dynamically adjust the weight of Resumes, GitHub, Coding Tests, and Logical Ability (LA) tests.
- **Automated Interview Scheduling:** Integrates with Google Calendar API via a Service Account to generate Google Meet links.
- **Automated Emailing:** Uses SMTP to send candidates their assessment links and interview invitations.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following:
1. **Python 3.10+** installed.
2. **Node.js & npm** installed.
3. **Groq API Key** (Get one at [console.groq.com](https://console.groq.com)).
4. **GitHub Personal Access Token** (Classic token to read public repos).
5. **Google App Password** (For sending SMTP emails from your Gmail account).
6. **Google Cloud Service Account** (For Google Calendar API).

---

## ⚙️ Setup & Installation

### 1. Backend Setup
1. Open a terminal in the root directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
