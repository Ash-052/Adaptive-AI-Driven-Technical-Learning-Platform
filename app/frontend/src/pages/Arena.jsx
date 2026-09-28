import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, ChevronLeft, Terminal, CheckCircle2, AlertCircle, Loader2, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import TutorPanel from '../components/TutorPanel';
import ExecutionModal from '../components/ExecutionModal';

const Arena = () => {
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [execResult, setExecResult] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  // Dynamic User ID from session
  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    fetchProblem();
  }, []);

  const fetchProblem = async () => {
    setLoading(true);
    setError(null);
    setSubmitSuccess(false);
    try {
      const response = await api.getNextProblem(userId);
      console.log("Problem API:", response.data);
      
      const problemData = response.data.problem;
      setProblem(problemData);
      
      // Load starter code or default
      setCode(problemData.starter_code || "# Write your solution here\n");
    } catch (err) {
      console.error("API Error:", err);
      setError("Failed to load problem from database. Please ensure backend is running and seeded.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        user_id: userId,
        problem_id: problem.id,
        code: code,
        topic: problem.topic,
        difficulty: problem.difficulty,
        time_taken: 60,
        attempts: 1
      };
      
      const res = await api.submitResult(payload);
      console.log("Submission Result:", res.data);
      
      setExecResult(res.data.execution);
      setShowModal(true);
      
      if (res.data.execution.status === 'Accepted') {
        setSubmitSuccess(true);
        // Don't auto-fetch next problem immediately so they can see results
      }
    } catch (err) {
      console.error("Submission Error:", err);
      setError("Failed to execute code. Check your connection.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-screen bg-gray-900 flex flex-col items-center justify-center text-gray-400">
        <Loader2 className="animate-spin mb-4 text-blue-500" size={48} />
        <p className="text-lg font-medium">Loading real-time problem from database...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen bg-gray-900 flex flex-col items-center justify-center text-gray-400 p-4 text-center">
        <AlertCircle className="mb-4 text-red-500" size={48} />
        <p className="text-xl font-bold text-white mb-2">Data Flow Error</p>
        <p className="max-w-md">{error}</p>
        <button 
          onClick={fetchProblem}
          className="mt-6 bg-gray-800 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-all"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
      {/* Top Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 p-4 flex justify-between items-center px-6">
        <div className="flex items-center space-x-6">
          <Link to="/" className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors">
            <ChevronLeft size={20} />
            <span className="font-semibold">Dashboard</span>
          </Link>
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-2 text-gray-500 hover:text-red-400 transition-colors text-sm font-medium"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
        
        <div className="flex items-center space-x-4">
           <span className="px-3 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-bold border border-blue-900 uppercase tracking-widest">
             {problem.topic}
           </span>
           <span className="px-3 py-1 rounded bg-gray-700 text-gray-300 text-xs font-bold uppercase">
             Level {problem.difficulty}
           </span>
        </div>

        <button 
          onClick={handleSubmit}
          disabled={submitting || submitSuccess}
          className={`flex items-center space-x-2 px-6 py-2 rounded-lg font-bold transition-all shadow-lg ${
            submitSuccess ? 'bg-green-600 cursor-default' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-900/20'
          } disabled:opacity-50`}
        >
          {submitting ? <Loader2 className="animate-spin" size={18} /> : (submitSuccess ? <CheckCircle2 size={18} /> : <Send size={18} />)}
          <span>{submitSuccess ? 'Accepted!' : 'Submit Solution'}</span>
        </button>
      </nav>

      {/* Workspace Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Problem Details */}
        <div className="w-1/3 bg-gray-950 p-6 overflow-y-auto border-r border-gray-800 scrollbar-thin">
          <h1 className="text-3xl font-extrabold text-white mb-6 tracking-tight">{problem.title}</h1>
          
          <div className="space-y-8">
            <section>
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap text-base">
                {problem.description}
              </p>
            </section>

            <section className="bg-gray-900/50 rounded-xl p-5 border border-gray-800">
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center">
                <Terminal size={16} className="mr-2" />
                Example Case
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-blue-400 font-bold uppercase mb-1 block">Input</label>
                  <pre className="bg-black/40 p-3 rounded font-mono text-sm text-gray-300 border border-gray-800">{problem.sample_input}</pre>
                </div>
                <div>
                  <label className="text-xs text-green-400 font-bold uppercase mb-1 block">Output</label>
                  <pre className="bg-black/40 p-3 rounded font-mono text-sm text-gray-300 border border-gray-800">{problem.sample_output}</pre>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-3">Constraints</h3>
              <div className="bg-gray-800/30 p-4 rounded-lg border border-gray-800 text-sm text-gray-400 italic">
                {problem.constraints}
              </div>
            </section>
          </div>
        </div>

        {/* Center: Monaco Editor */}
        <div className="flex-1 bg-[#1e1e1e] border-r border-gray-800 relative">
          <div className="absolute top-0 right-0 p-2 z-10 opacity-30 text-[10px] font-mono text-gray-500 pointer-events-none">
            PYTHON 3.12 ENGINE
          </div>
          <Editor
            height="100%"
            defaultLanguage="python"
            theme="vs-dark"
            value={code}
            onChange={(val) => setCode(val)}
            options={{
              fontSize: 15,
              fontFamily: "'Fira Code', 'JetBrains Mono', monospace",
              minimap: { enabled: false },
              padding: { top: 24 },
              scrollBeyondLastLine: false,
              cursorBlinking: "smooth",
              lineNumbersMinChars: 3,
              smoothScrolling: true,
              contextmenu: false
            }}
          />
        </div>

        {/* Right: AI Tutor Integration */}
        <div className="w-1/4">
          <TutorPanel 
            problemId={problem.id} 
            userCode={code} 
            topic={problem.topic} 
            difficulty={problem.difficulty} 
          />
        </div>
      </div>

      <ExecutionModal 
        isOpen={showModal} 
        onClose={() => {
          setShowModal(false);
          if (submitSuccess) fetchProblem();
        }} 
        result={execResult}
        feedback={execResult?.status === 'Accepted' ? "Perfect! Your skill score is increasing." : "Not quite. Check the test cases below."}
      />
    </div>
  );
};

export default Arena;
