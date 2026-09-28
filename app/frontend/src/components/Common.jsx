import React from 'react';
import { motion } from 'framer-motion';
import { Target, Zap, BarChart3 } from 'lucide-react';

// --- LOADER COMPONENT ---
export const Loader = () => (
  <div className="flex items-center justify-center p-12">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

// --- SKILL BAR COMPONENT ---
export const SkillBar = ({ label, percentage, color = "bg-blue-500" }) => (
  <div className="mb-4">
    <div className="flex justify-between mb-1">
      <span className="text-sm font-medium text-gray-300">{label}</span>
      <span className="text-sm font-medium text-gray-400">{Math.round(percentage * 100)}%</span>
    </div>
    <div className="w-full bg-gray-700 rounded-full h-2.5">
      <motion.div 
        className={`${color} h-2.5 rounded-full`}
        initial={{ width: 0 }}
        animate={{ width: `${percentage * 100}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </div>
  </div>
);

// --- STAT CARD COMPONENT ---
export const StatCard = ({ icon: Icon, label, value, subValue, color = "blue" }) => (
  <motion.div 
    whileHover={{ y: -5 }}
    className="bg-gray-900 border border-gray-800 p-6 rounded-3xl"
  >
    <div className="flex items-center space-x-3 mb-4">
      <div className={`p-2 bg-${color}-500/10 rounded-xl`}>
        <Icon className={`text-${color}-400`} size={20} />
      </div>
      <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">{label}</span>
    </div>
    <div className="flex items-end space-x-2">
      <div className="text-3xl font-black text-white">{value}</div>
      {subValue && <div className="text-sm text-gray-500 mb-1">{subValue}</div>}
    </div>
  </motion.div>
);

// --- ACTIVITY FEED COMPONENT ---
export const ActivityFeed = ({ activities }) => (
  <div className="space-y-4">
    {activities.map((act, idx) => (
      <div key={idx} className="flex items-start space-x-4 p-4 hover:bg-gray-800/40 rounded-2xl transition-colors group">
        <div className={`mt-1 p-2 rounded-lg ${act.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          <Zap size={14} fill={act.success ? "currentColor" : "none"} />
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-bold text-gray-200 group-hover:text-white transition-colors">{act.message}</h4>
            <span className="text-[10px] text-gray-600 font-mono">{act.time}</span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{act.subtext}</p>
        </div>
      </div>
    ))}
  </div>
);

// --- RECOMMENDATION CARD COMPONENT ---
export const RecommendationCard = ({ topic, difficulty, confidence, reason }) => {
  const diffColors = {
    1: "text-green-400 border-green-900 bg-green-900/20",
    2: "text-yellow-400 border-yellow-900 bg-yellow-900/20",
    3: "text-red-400 border-red-900 bg-red-900/20"
  };

  const diffLabels = { 1: "Easy", 2: "Medium", 3: "Hard" };

  return (
    <motion.div 
      whileHover={{ scale: 1.02 }}
      className="bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden group"
    >
      <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
        <Target size={120} />
      </div>
      
      <div className="flex items-center space-x-3 mb-8">
        <div className="p-3 bg-blue-500/10 rounded-2xl">
          <Target className="text-blue-400" size={24} />
        </div>
        <div>
          <h3 className="text-xl font-black text-white">Next Target</h3>
          <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mt-0.5">AI Recommendation</p>
        </div>
      </div>
      
      <div className="space-y-6 relative z-10">
        <div>
          <label className="text-[10px] text-gray-500 uppercase tracking-widest font-black">Topic to Master</label>
          <p className="text-2xl text-white font-black capitalize mt-1">{topic}</p>
        </div>
        
        <div className="flex justify-between items-center pt-2">
          <div>
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-black">Difficulty</label>
            <div className={`mt-2 px-4 py-1.5 rounded-xl border text-xs font-black uppercase tracking-tighter ${diffColors[difficulty] || diffColors[2]}`}>
              {diffLabels[difficulty] || "Medium"}
            </div>
          </div>
          
          <div className="text-right">
            <label className="text-[10px] text-gray-500 uppercase tracking-widest font-black mb-2 block">Confidence</label>
            <div className="flex flex-col items-end">
               <div className="text-xl font-black text-blue-400 font-mono">
                 {Math.round(confidence * 100)}%
               </div>
               <div className="w-24 h-1 bg-gray-800 rounded-full mt-1 overflow-hidden">
                 <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${confidence * 100}%` }}
                    className="h-full bg-blue-500"
                 />
               </div>
            </div>
          </div>
        </div>

        {reason && (
          <div className="pt-4 border-t border-gray-800">
             <p className="text-xs text-gray-400 leading-relaxed italic">
               "{reason}"
             </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};
