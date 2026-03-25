// namespace std;
import React, { useState, useEffect } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [senderEmail, setSenderEmail] = useState('');
  const [appPassword, setAppPassword] = useState('');
  const [jdText, setJdText] = useState('');
  const [testLink, setTestLink] = useState('');
  const [emailMessage, setEmailMessage] = useState('Hello {name},\n\nYou have been shortlisted for the next round. Please complete your assessment here:\n{link}\n\nRegards,\nVisl AI Labs');
  
  const [weightResume, setWeightResume] = useState(30);
  const [weightGithub, setWeightGithub] = useState(20);
  const [weightTestCode, setWeightTestCode] = useState(40);
  const [weightTestLa, setWeightTestLa] = useState(10);
  
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [results, setResults] = useState([]);
  const [sentEmails, setSentEmails] = useState({});
  const [progress, setProgress] = useState(0);
  const [currentCandidate, setCurrentCandidate] = useState('');

  const onFileChange = (e) => setFile(e.target.files[0]);

  const uploadFile = async () => {
    if (!file || !senderEmail || !appPassword || !jdText || !testLink || !emailMessage) return;
    setStatus('uploading');
    setProgress(0);
    setCurrentCandidate('');
    setSentEmails({});
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sender_email", senderEmail);
    formData.append("app_password", appPassword);
    formData.append("jd_text", jdText);
    formData.append("test_link", testLink);
    formData.append("weight_resume", weightResume);
    formData.append("weight_github", weightGithub);
    formData.append("weight_test_code", weightTestCode);
    formData.append("weight_test_la", weightTestLa);

    try {
      const response = await fetch("https://ai-candidates-evaluvator.onrender.com/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setTaskId(data.task_id);
      setStatus('processing');
    } catch (err) {
      setStatus('error');
    }
  };

  const handleSendEmail = async (candidate, index) => {
    setSentEmails(prev => ({ ...prev, [index]: 'sending' }));
    try {
      await fetch("https://ai-candidates-evaluvator.onrender.com/api/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_email: candidate.Email,
          candidate_name: candidate.Name,
          test_link: testLink,
          sender_email: senderEmail,
          app_password: appPassword,
          email_message: emailMessage
        })
      });
      setSentEmails(prev => ({ ...prev, [index]: 'sent' }));
    } catch (error) {
      setSentEmails(prev => ({ ...prev, [index]: 'error' }));
    }
  };

  useEffect(() => {
    let interval;
    if (status === 'processing' && taskId) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`https://ai-candidates-evaluvator.onrender.com/api/status/${taskId}`);
          const data = await res.json();

          if (data.status === 'processing') {
            const percent = Math.round((data.processed / data.total) * 100) || 0;
            setProgress(percent);
            setCurrentCandidate(data.current);
          } else if (data.status === 'completed') {
            setResults(data.results);
            setStatus('completed');
            clearInterval(interval);
          }
        } catch (err) {
          setStatus('error');
          clearInterval(interval);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [status, taskId]);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-10 font-sans">
      <div className="max-w-[95%] mx-auto">
        <h1 className="text-3xl font-bold mb-6 border-b border-slate-700 pb-2">AI Candidate Evaluator</h1>
        
        <div className="bg-slate-800 p-6 rounded-lg shadow-xl mb-8 space-y-4 max-w-4xl mx-auto">
          <input type="text" placeholder="Sender Email" value={senderEmail} onChange={e => setSenderEmail(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
          <input type="password" placeholder="16 Digit App Password" value={appPassword} onChange={e => setAppPassword(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
          <textarea placeholder="Job Description" value={jdText} onChange={e => setJdText(e.target.value)} className="w-full p-2 bg-slate-700 rounded h-24" />
          <input type="text" placeholder="Assessment Link" value={testLink} onChange={e => setTestLink(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
          
          <div>
            <label className="block text-xs mb-1 text-slate-400">Email Template (Use {"{name}"} and {"{link}"} as placeholders)</label>
            <textarea value={emailMessage} onChange={e => setEmailMessage(e.target.value)} className="w-full p-2 bg-slate-700 rounded h-32" />
          </div>
          
          <div className="grid grid-cols-4 gap-4 bg-slate-900 p-4 rounded border border-slate-700">
            <div>
              <label className="block text-xs mb-1 text-slate-400">Resume Weight (%)</label>
              <input type="number" value={weightResume} onChange={e => setWeightResume(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
            </div>
            <div>
              <label className="block text-xs mb-1 text-slate-400">GitHub Weight (%)</label>
              <input type="number" value={weightGithub} onChange={e => setWeightGithub(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
            </div>
            <div>
              <label className="block text-xs mb-1 text-slate-400">Code Test Weight (%)</label>
              <input type="number" value={weightTestCode} onChange={e => setWeightTestCode(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
            </div>
            <div>
              <label className="block text-xs mb-1 text-slate-400">LA Test Weight (%)</label>
              <input type="number" value={weightTestLa} onChange={e => setWeightTestLa(e.target.value)} className="w-full p-2 bg-slate-700 rounded" />
            </div>
          </div>

          <input type="file" onChange={onFileChange} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white" />
          
          <button onClick={uploadFile} disabled={status === 'processing' || status === 'uploading'} className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 font-bold py-2 rounded">
            {status === 'processing' ? 'Processing...' : 'Start Evaluation'}
          </button>
        </div>

        {status === 'processing' && (
          <div className="bg-slate-800 p-6 rounded-lg shadow-xl mb-8 max-w-4xl mx-auto">
            <p className="text-blue-400 font-medium mb-2">
              Processing: <span className="text-white">{currentCandidate}</span> ({progress}%)
            </p>
            <div className="w-full bg-slate-700 rounded-full h-4">
              <div className="bg-blue-600 h-4 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}
        
        {status === 'completed' && (
          <div className="bg-slate-800 rounded-lg overflow-x-auto shadow-2xl">
            <table className="w-full text-left whitespace-nowrap">
              <thead className="bg-slate-700">
                <tr>
                  <th className="p-4">Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Test Code</th>
                  <th className="p-4">Test LA</th>
                  <th className="p-4">Resume Score</th>
                  <th className="p-4">GitHub Score</th>
                  <th className="p-4">Final Score</th>
                  <th className="p-4 max-w-xs">Reason</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {results.map((c, i) => (
                  <tr key={i} className={`border-t border-slate-700 hover:bg-slate-700/50 ${i < 5 ? 'bg-slate-700/30' : ''}`}>
                    <td className="p-4">{c.Name}</td>
                    <td className="p-4">{c.Email}</td>
                    <td className="p-4">{c.Test_Code}</td>
                    <td className="p-4">{c.Test_LA}</td>
                    <td className="p-4">{c.Resume_Score}</td>
                    <td className="p-4">{c.GitHub_Score}</td>
                    <td className="p-4 font-bold text-green-400">{c.Final_Score}</td>
                    <td className="p-4 max-w-xs truncate" title={c.Reason}>{c.Reason}</td>
                    <td className="p-4">
                      <button 
                        onClick={() => handleSendEmail(c, i)}
                        disabled={sentEmails[i] === 'sent' || sentEmails[i] === 'sending'}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-500 text-white px-3 py-1 rounded text-sm"
                      >
                        {sentEmails[i] === 'sending' ? 'Sending...' : sentEmails[i] === 'sent' ? 'Sent' : 'Send Email'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {status === 'error' && <p className="text-red-500 text-center">Error connecting to backend.</p>}
      </div>
    </div>
  );
}