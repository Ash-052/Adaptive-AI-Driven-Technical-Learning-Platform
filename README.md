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
git clone https://github.com/yourusername/AI-Tutor-Adaptive-Programming-Practice.git
```

### Backend

```bash
pip install -r requirements.txt
```

Run backend

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Create a `.env` file in the root directory.

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

---
