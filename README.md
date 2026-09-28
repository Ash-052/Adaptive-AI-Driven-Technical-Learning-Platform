# Adaptive-AI-Driven-Technical-Learning-Platform
AI-powered adaptive programming tutor that personalizes coding practice using machine learning, FastAPI, React, and Supabase.
An intelligent adaptive learning platform that personalizes programming practice using Artificial Intelligence and Machine Learning.

The system analyzes a student's coding performance and dynamically recommends programming problems based on their skill level, helping learners improve efficiently.

---

## Features

- Adaptive programming question recommendations
- AI-powered personalized learning
- User authentication
- Student progress tracking
- Difficulty prediction using Machine Learning
- Programming practice dashboard
- Performance analytics
- FastAPI REST APIs
- Responsive React frontend
- Supabase database integration
- Supabase database integration with local SQLite fallback
- Topic mastery that starts at 0% and grows with problem-solving accuracy
- Function-based coding challenges with examples, constraints, and test cases
- Python, JavaScript, C, C++, Java, Go, Rust, and C# editor templates

---

## Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- JavaScript

### Backend

- FastAPI
- Python

### Machine Learning

- PyTorch
- Scikit-learn
- Pandas
- NumPy

### Database

- Supabase

### Authentication

- JWT Authentication

### AI Integration

- OpenAI API

---

## Project Structure

```
Adaptive/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── ml/
│
├── data/
├── requirements.txt
├── main.py
└── README.md
```

---

## Installation

### Clone Repository
```bash
git clone https://github.com/Ash-052/Adaptive-AI-Driven-Technical-Learning-Platform.git
cd Adaptive-AI-Driven-Technical-Learning-Platform
```

### Backend

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file for Supabase and OpenAI credentials, or use the local SQLite fallback where supported.

Run the backend from the repository root:

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server prints the local URL when it starts.

## Deploy on Render

The repository includes a `render.yaml` Blueprint that builds the React frontend and serves it with FastAPI from one web service.

1. Open [Render Blueprints](https://dashboard.render.com/blueprints) and create a Blueprint from this repository.
2. Apply the Blueprint and wait for the service health check to pass. Render will show the public URL.

Submissions are sent to Judge0 CE for sandboxed execution with CPU, wall-time, and memory limits and network access disabled. Judge0's public endpoint may enforce rate limits; set `JUDGE0_API_URL` to a managed Judge0 endpoint if needed. The free Render service may sleep while idle, and its local SQLite filesystem is temporary; add `SUPABASE_URL` and `SUPABASE_KEY` for persistent accounts and progress. Add `OPENAI_API_KEY` to enable AI tutor features.

## Deploy Frontend to Vercel

The Vercel project root is `frontend`. Set the Production environment variable `VITE_API_BASE_URL` to `https://adaptive-learning-platform-omt2.onrender.com/api/v1`, then redeploy. The `frontend/vercel.json` rewrite serves React routes such as `/register` directly.

---

## Environment Variables

Create a `.env` file in the root directory.

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

---
