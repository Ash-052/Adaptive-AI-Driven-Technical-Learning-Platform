import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, Clock, Terminal, AlertTriangle } from 'lucide-react';

const ExecutionModal = ({ isOpen, onClose, result, feedback }) => {
  if (!isOpen || !result) return null;

  const isAccepted = result.status === 'Accepted';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-gray-900 border border-gray-700 w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className={`p-6 flex items-center justify-between ${isAccepted ? 'bg-green-600/10' : 'bg-red-600/10'}`}>
          <div className="flex items-center space-x-3">
            {isAccepted ? <CheckCircle2 className="text-green-500" size={32} /> : <XCircle className="text-red-500" size={32} />}
            <div>
              <h2 className="text-2xl font-black text-white">{result.status}</h2>
              <p className="text-sm text-gray-400">{feedback}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <XCircle size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-8 max-h-[60vh] overflow-y-auto custom-scrollbar">
          <div className="grid grid-cols-3 gap-4 mb-8">
            <StatCard icon={<Terminal size={16}/>} label="Passed" value={`${result.passed}/${result.total}`} />
            <StatCard icon={<Clock size={16}/>} label="Time" value={`${Math.max(...result.results.map(r => r.time || 0))}s`} />
            <StatCard icon={<CheckCircle2 size={16}/>} label="Accuracy" value={`${Math.round((result.passed/result.total)*100)}%`} />
          </div>

          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">Test Case Details</h3>
          <div className="space-y-4">
            {result.results.map((res, idx) => (
              <div key={idx} className="bg-gray-950 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-gray-500">Case {idx + 1}</span>
                  {res.passed ? 
                    <span className="text-xs font-bold text-green-400 bg-green-400/10 px-2 py-0.5 rounded">PASSED</span> : 
                    <span className="text-xs font-bold text-red-400 bg-red-400/10 px-2 py-0.5 rounded">FAILED</span>
                  }
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] text-gray-600 uppercase font-bold">Input</label>
                    <pre className="text-xs text-blue-300 bg-black/30 p-2 rounded mt-1 truncate">{res.input}</pre>
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 uppercase font-bold">Expected</label>
                    <pre className="text-xs text-gray-400 bg-black/30 p-2 rounded mt-1 truncate">{res.expected}</pre>
                  </div>
                </div>

                {!res.passed && (
                  <div className="mt-4 pt-3 border-t border-gray-800">
                    <label className="text-[10px] text-red-400 uppercase font-bold">Actual Output</label>
                    <pre className="text-xs text-red-200 bg-red-900/10 p-2 rounded mt-1 whitespace-pre-wrap">
                      {res.actual || (res.error ? res.error : "No output")}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-950 border-t border-gray-800 flex justify-end">
          <button 
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-8 py-3 rounded-xl transition-all"
          >
            Got it
          </button>
        </div>
      </motion.div>
    </div>
  );
};

const StatCard = ({ icon, label, value }) => (
  <div className="bg-gray-800/50 border border-gray-800 p-4 rounded-2xl">
    <div className="flex items-center space-x-2 text-gray-500 mb-1">
      {icon}
      <span className="text-[10px] font-bold uppercase">{label}</span>
    </div>
    <div className="text-lg font-black text-white">{value}</div>
  </div>
);

export default ExecutionModal;
