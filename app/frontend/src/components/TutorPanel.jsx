import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, HelpCircle, Code2, Info, Loader2 } from 'lucide-react';
import { api } from '../api/api';

const TutorPanel = ({ problemId, userCode, topic, difficulty }) => {
  const [loading, setLoading] = useState(null);
  const [response, setResponse] = useState(null);

  const handleAction = async (actionType) => {
    setLoading(actionType);
    setResponse(null);
    
    try {
      const payload = {
        problem_id: problemId,
        user_code: userCode,
        topic: topic,
        difficulty: difficulty
      };

      let res;
      if (actionType === 'hint') res = await api.getHint(payload);
      else if (actionType === 'analyze') res = await api.analyzeCode(payload);
      else if (actionType === 'explain') res = await api.explainCode({ ...payload, solution_code: userCode });
      
      setResponse(res.data);
    } catch (err) {
      setResponse({ response: "Error connecting to AI Tutor. Please try again.", type: "error" });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-gray-800 border-l border-gray-700 h-full p-4 flex flex-col">
      <div className="flex items-center space-x-2 mb-6 border-b border-gray-700 pb-4">
        <Sparkles className="text-purple-400" size={20} />
        <h2 className="text-lg font-bold text-white">AI Tutor</h2>
      </div>

      <div className="grid grid-cols-1 gap-3 mb-6">
        <TutorButton 
          icon={<HelpCircle size={18} />}
          label="Get Hint"
          onClick={() => handleAction('hint')}
          isLoading={loading === 'hint'}
          color="hover:bg-blue-600/20 text-blue-400 border-blue-900/50"
        />
        <TutorButton 
          icon={<Code2 size={18} />}
          label="Analyze Code"
          onClick={() => handleAction('analyze')}
          isLoading={loading === 'analyze'}
          color="hover:bg-green-600/20 text-green-400 border-green-900/50"
        />
        <TutorButton 
          icon={<Info size={18} />}
          label="Explain Logic"
          onClick={() => handleAction('explain')}
          isLoading={loading === 'explain'}
          color="hover:bg-purple-600/20 text-purple-400 border-purple-900/50"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {response && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`p-4 rounded-xl border ${
                response.type === 'error' ? 'bg-red-900/20 border-red-900 text-red-200' : 'bg-gray-900/50 border-gray-700 text-gray-300'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{response.response}</p>
            </motion.div>
          )}
        </AnimatePresence>
        
        {!response && !loading && (
          <div className="text-center text-gray-500 mt-12">
            <Sparkles size={40} className="mx-auto mb-4 opacity-20" />
            <p className="text-sm">Select an action to get AI assistance</p>
          </div>
        )}
      </div>
    </div>
  );
};

const TutorButton = ({ icon, label, onClick, isLoading, color }) => (
  <button
    onClick={onClick}
    disabled={isLoading}
    className={`flex items-center space-x-3 w-full p-3 rounded-xl border transition-all duration-200 ${color} disabled:opacity-50`}
  >
    {isLoading ? <Loader2 className="animate-spin" size={18} /> : icon}
    <span className="font-semibold text-sm">{label}</span>
  </button>
);

export default TutorPanel;
