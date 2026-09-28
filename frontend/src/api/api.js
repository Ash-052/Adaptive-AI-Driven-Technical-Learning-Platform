import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Auth
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),

  // Recommendations
  getRecommendation: (userId) => apiClient.get(`/recommendation/${userId}`),
  
  // Problems
  getNextProblem: (userId) => apiClient.get(`/problem/next/${userId}`),
  getProblemDetails: (problemId) => apiClient.get(`/problem/${problemId}`),
  
  // Tutor
  getHint: (data) => apiClient.post('/tutor/hint', data),
  analyzeCode: (data) => apiClient.post('/tutor/analyze', data),
  explainCode: (data) => apiClient.post('/tutor/explain', data),
  
  // Mastery
  getUserMastery: (userId) => apiClient.get(`/mastery/${userId}`),
  // User Progress & Profile
  getUserProgress: (userId) => apiClient.get(`/user/${userId}/progress`),
  getProfile: (userId) => apiClient.get(`/user/${userId}/profile`),
  getHistory: (userId) => apiClient.get(`/user/${userId}/history`),
  getAnalytics: (userId) => apiClient.get(`/user/${userId}/analytics`),
  
  // Submissions
  submitResult: (data) => apiClient.post('/submission/', data),
};
