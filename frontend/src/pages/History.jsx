import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronLeft, Clock3, CheckCircle2, XCircle, Loader2, BrainCircuit, Trophy } from 'lucide-react';
import { api } from '../api/api';

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const userId = localStorage.getItem('user_id');

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);

      try {
        if (!userId) {
          setError('Please log in again to view your activity.');
          setLoading(false);
          return;
        }

        const response = await api.getHistory(userId);
        const payload = Array.isArray(response?.data)
          ? response.data
          : Array.isArray(response?.data?.history)
            ? response.data.history
            : [];

        setHistory(payload);
      } catch (err) {
        console.error('History fetch error:', err);
        setError('Could not load your recent activity.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-10">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <ChevronLeft size={18} />
            <span className="font-medium">Dashboard</span>
          </Link>
          <h1 className="text-3xl font-black tracking-tight">Recent Activity</h1>
        </div>

        {loading ? (
          <div className="bg-gray-900 border border-gray-800 rounded-3xl p-10 text-center text-gray-400">
            <Loader2 className="animate-spin mx-auto mb-4 text-blue-500" size={36} />
            <p>Loading your history...</p>
          </div>
        ) : error ? (
          <div className="bg-gray-900 border border-red-900/50 rounded-3xl p-8 text-center text-red-400">
            {error}
          </div>
        ) : history.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-3xl p-10 text-center text-gray-400">
            No activity yet. Start solving problems to build your record.
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((entry, index) => {
              const status = entry?.accuracy === 1 || entry?.passed === true || entry?.status === 'Accepted';
              const problemTitle = entry?.problems?.title || entry?.problem_title || entry?.title || `Attempt ${index + 1}`;
              const topic = entry?.topic || entry?.problem?.topic || 'General';
              const difficulty = entry?.difficulty || entry?.problem?.difficulty || 'Medium';
              const createdAt = entry?.created_at || entry?.submitted_at || null;

              return (
                <motion.div
                  key={`${problemTitle}-${index}`}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gray-900 border border-gray-800 rounded-3xl p-6"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-2xl ${status ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {status ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                      </div>
                      <div>
                        <h2 className="text-xl font-black text-white">{problemTitle}</h2>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mt-1">
                          <span className="flex items-center gap-1"><BrainCircuit size={12} /> {topic}</span>
                          <span className="flex items-center gap-1"><Trophy size={12} /> {difficulty}</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right text-sm text-gray-400">
                      <div className="flex items-center justify-end gap-2">
                        <Clock3 size={14} />
                        <span>{createdAt ? new Date(createdAt).toLocaleString() : 'Recent'}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        Accuracy: {Math.round((entry?.accuracy ?? entry?.score ?? 0) * 100) || 0}%
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
