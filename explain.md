3. Frontend Setup
Open a new terminal and navigate to the frontend folder:

Bash
cd frontend
npm install
🏃‍♂️ Running the Application
Start the Backend:

Bash
uvicorn backend:app --reload
The backend will run on http://localhost:8000

Start the Frontend:

Bash
cd frontend
npm run dev
The frontend will run on http://localhost:5173

📖 Tutorial: How to Use the Evaluator
Prepare your Data: Create an Excel file (.xlsx) containing your candidates. The sheet must have the following column headers exactly:

name: Candidate's full name.

email: Candidate's email address.

test_code: Score from previous coding test (0-100).

test_la: Score from previous logical ability test (0-100).

resume: Publicly accessible Google Drive link to their PDF resume.

github: Link to their GitHub profile.

Configure the App: Open the frontend UI and fill in your sender email, your 16-digit Google App Password, the Job Description, and the Assessment Link.

Set Weights: Adjust the sliders/inputs for how much weight the Resume, GitHub, Code Test, and LA test should carry in the final score.

Upload & Evaluate: Upload the Excel file and click Start Evaluation. Wait for the AI to process all candidates.

Schedule & Send: Once ranked, pick a date/time from the calendar picker for top candidates and click Send. The app will create a Google Calendar event, generate a Meet link, and email the candidate.

🧠 How the Code Works
The Backend (backend.py)
The backend is built with FastAPI and uses an asynchronous architecture to prevent long LLM calls from blocking the server.

Upload Phase (/api/upload): When the Excel file is uploaded, the backend saves it temporarily, generates a unique task_id, and pushes the evaluation process into FastAPI's BackgroundTasks.

Data Extraction: - extract_resume(url): Uses gdown to download the PDF from Drive and PyPDF2 to extract the raw text.

fetch_github_data(url): Calls the GitHub API to fetch the candidate's top 5 most recently updated public repositories, extracting the repo name, language, and description.

AI Evaluation (LangGraph & Groq): - The app uses ChatGroq bound to Pydantic's EvaluationOutput for structured JSON output.

The data is passed to a LangGraph node evaluate_candidate, which prompts the LLM to compare the Resume and GitHub data against the provided Job Description. It returns a score (0-100) and brief feedback for both.

Scoring: The final score is calculated dynamically based on the weights provided from the frontend.

Interview Scheduling (/api/send-email): - Uses the google-api-python-client. It authenticates silently using credentials.json (Service Account).

It formats the frontend's datetime string into ISO 8601, creates an event payload with conferenceDataVersion=1 to generate a Google Meet link, and inserts it into your calendar.

Finally, it uses smtplib to replace placeholders ({name}, {link}) in your email template and fires off the email.

The Frontend (frontend/src/App.jsx)
The frontend is a lightweight React (Vite) application styled with Tailwind CSS.

State Management: Uses React useState to manage form inputs, weights, file data, and polling status.

Polling Mechanism: Because AI evaluation takes time, the frontend uses a useEffect interval to ping the backend's /api/status/{task_id} endpoint every 3 seconds. This updates the progress bar and current candidate name in real-time.

Dynamic Results: Once the backend status turns to completed, the polling stops, and the ranked data is mapped into a dynamic table.

Action Handling: The "Send" button reads the local state of the datetime-local input and sends it to the backend to trigger the calendar/email flow, updating the button state to "Sent" to prevent duplicate emails.
