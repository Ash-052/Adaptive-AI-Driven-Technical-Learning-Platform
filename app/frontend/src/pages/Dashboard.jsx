import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Award, Play, Zap, Target, Loader2, AlertCircle, LogOut, Flame, Trophy, Clock, Search, History, PieChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import { SkillBar, RecommendationCard, StatCard, ActivityFeed } from '../components/Common';

const Dashboard = () => {
  const [profile, setProfile] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [mastery, setMastery] = useState({});
  const [isNewUser, setIsNewUser] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [profileRes, recRes, progressRes] = await Promise.all([
          api.getProfile(userId),
          api.getRecommendation(userId),
          api.getUserProgress(userId)
        ]);

        setProfile(profileRes.data);
        setRecommendation(recRes.data);
        setMastery(progressRes.data.topic_mastery);
        setIsNewUser(progressRes.data.is_new_user);
      } catch (err) {
        console.error("Dashboard Fetch Error:", err);
        setError("Failed to synchronize with backend engine.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  if (loading) {
    return (
      <div className="h-screen bg-gray-950 flex flex-col items-center justify-center text-gray-500">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
          className="mb-6 p-4 bg-blue-500/10 rounded-3xl"
        >
          <Loader2 className="text-blue-500" size={48} />
        </motion.div>
        <p className="text-lg font-black tracking-tighter text-gray-400">SYNCING NEURAL PROFILE...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-12 font-sans">
      <div className="max-w-7xl mx-auto">
        
        {/* Top Navbar */}
        <nav className="flex justify-between items-center mb-16">
          <div className="flex items-center space-x-4">
             <div className="w-12 h-12 bg-gradient-to-tr from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center font-black text-xl shadow-lg shadow-blue-500/20">
               {profile?.username?.[0].toUpperCase() || 'U'}
             </div>
             <div>
               <h3 className="font-black text-lg text-white leading-none">{profile?.username}</h3>
               <p className="text-xs text-gray-500 font-bold uppercase mt-1">{profile?.badge} Learner</p>
             </div>
          </div>

          <div className="flex items-center space-x-6">
            <Link to="/history" className="text-gray-400 hover:text-white transition-colors">
              <History size={20} />
            </Link>
            <div className="h-6 w-[1px] bg-gray-800"></div>
            <button onClick={handleLogout} className="text-gray-500 hover:text-red-400 transition-colors">
              <LogOut size={20} />
            </button>
          </div>
        </nav>

        {/* Hero Section */}
        <header className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8">
          <div className="max-w-2xl">
            <div className="flex items-center space-x-2 text-blue-500 mb-4">
              <Zap size={18} fill="currentColor" />
              <span className="text-xs font-black uppercase tracking-[0.2em]">Adaptive Intelligence Platform</span>
            </div>
            <h1 className="text-6xl md:text-7xl font-black text-white tracking-tighter leading-[0.9]">
              Level {profile?.level} <br />
              <span className="text-gray-700">Arena</span>
            </h1>
          </div>
          
          <Link to="/arena" className="group flex items-center space-x-4 bg-white text-black px-10 py-6 rounded-3xl font-black transition-all hover:scale-105 hover:bg-blue-500 hover:text-white active:scale-95 shadow-2xl shadow-white/5">
            <Play size={24} fill="currentColor" />
            <span className="text-lg">ENTER ARENA</span>
          </Link>
        </header>

        {/* Gamification Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <StatCard icon={Flame} label="Daily Streak" value={`${profile?.streak} Days`} subValue="Keep it up!" color="orange" />
          <StatCard icon={Trophy} label="Experience Points" value={profile?.xp} subValue={`${100 - (profile?.xp % 100)} to next level`} color="yellow" />
          <StatCard icon={Target} label="Problems Solved" value={profile?.total_solved} subValue={`Across ${Object.keys(mastery).length} topics`} color="green" />
          <StatCard icon={TrendingUp} label="Global Skill" value={`${(profile?.skill_score * 100).toFixed(0)}%`} subValue={profile?.badge} color="blue" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Main Content Area */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* Recommendation & Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               {recommendation && (
                 <RecommendationCard 
                   topic={recommendation.next_topic}
                   difficulty={recommendation.next_difficulty}
                   confidence={recommendation.confidence ?? 0}
                   reason={isNewUser ? "Initial assessment based on cold-start profile." : `Targeting your ${recommendation.next_topic} mastery gap.`}
                 />
               )}

               <motion.div 
                 whileHover={{ scale: 1.02 }}
                 className="bg-gray-900 border border-gray-800 rounded-3xl p-8 flex flex-col justify-between"
               >
                 <div>
                   <h3 className="text-xl font-black text-white mb-2">Smart Insights</h3>
                   <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mb-6">AI Evaluation</p>
                   
                   <div className="space-y-4">
                     <div className="flex items-center space-x-3 text-sm text-gray-300 bg-gray-800/40 p-3 rounded-2xl">
                        <Award className="text-yellow-500" size={16} />
                        <span>Your speed in {Object.keys(mastery)[0] || 'Basics'} is top 10%!</span>
                     </div>
                     <div className="flex items-center space-x-3 text-sm text-gray-300 bg-gray-800/40 p-3 rounded-2xl">
                        <TrendingUp className="text-blue-500" size={16} />
                        <span>Accuracy has improved by 12% this week.</span>
                     </div>
                   </div>
                 </div>

                 <div className="mt-8 pt-6 border-t border-gray-800 flex items-center justify-between">
                   <div className="text-[10px] text-gray-600 font-bold uppercase">Daily Goal: 3 Problems</div>
                   <div className="w-1/2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 w-2/3" />
                   </div>
                 </div>
               </motion.div>
            </div>

            {/* Mastery Visualization */}
            <div className="bg-gray-900 border border-gray-800 rounded-3xl p-10">
               <div className="flex items-center justify-between mb-12">
                 <div className="flex items-center space-x-4">
                    <div className="p-3 bg-purple-500/10 rounded-2xl">
                      <PieChart className="text-purple-400" size={28} />
                    </div>
                    <div>
                      <h2 className="text-2xl font-black text-white">Domain Mastery</h2>
                      <p className="text-sm text-gray-500">Skill distribution across technical stacks</p>
                    </div>
                 </div>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-10">
                 {Object.entries(mastery).map(([topic, level]) => (
                   <SkillBar 
                     key={topic}
                     label={topic.replace('_', ' ').toUpperCase()}
                     percentage={level}
                     color={level < 0.35 ? "bg-red-500" : (level < 0.7 ? "bg-yellow-500" : "bg-green-500")}
                   />
                 ))}
               </div>
            </div>
          </div>

          {/* Sidebar Area */}
          <div className="lg:col-span-4 space-y-8">
             <div className="bg-gray-900 border border-gray-800 rounded-3xl p-8">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="text-lg font-black text-white">Recent Activity</h3>
                  <Link to="/history" className="text-xs text-blue-500 font-bold hover:underline">View All</Link>
                </div>
                <ActivityFeed activities={[
                  { success: true, message: "Solved Array Challenge", time: "2m ago", subtext: "+20 XP | 100% Accuracy" },
                  { success: true, message: "New Skill Level: Advanced", time: "1h ago", subtext: "Mastered Recursion" },
                  { success: false, message: "Failed Graph Search", time: "4h ago", subtext: "Time Limit Exceeded" },
                ]} />
             </div>

             <div className="bg-gradient-to-br from-blue-600 to-purple-700 rounded-3xl p-8 text-white relative overflow-hidden group shadow-2xl shadow-blue-500/10">
                <div className="relative z-10">
                   <h3 className="text-2xl font-black mb-2 tracking-tight">Weekly Challenge</h3>
                   <p className="text-sm text-blue-100 opacity-80 mb-6">Solve 10 Sorting problems to unlock the 'QuickSort King' badge.</p>
                   <button className="bg-white text-blue-600 px-6 py-3 rounded-2xl font-black text-sm hover:bg-blue-50 transition-colors">START CHALLENGE</button>
                </div>
                <Trophy className="absolute bottom-[-20px] right-[-20px] opacity-10 group-hover:scale-110 transition-transform" size={160} />
             </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
