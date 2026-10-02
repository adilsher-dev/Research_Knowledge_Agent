# AI Research Agent

AI Research Agent is a web application that helps users research a topic using different sources.

A user can ask a normal question, search the web, ask questions from uploaded PDFs, or combine documents, web research, and images in the same request.

I built this project to understand how RAG, vector search, multimodal AI, and agentic workflows can work together in one application.

## Live Project

Frontend:  
https://research-knowledge-agent.vercel.app

Backend:  
https://ai-research-agent-backend-enoo.onrender.com

API Documentation:  
https://ai-research-agent-backend-enoo.onrender.com/docs

## What the application can do

- Ask normal research questions
- Upload PDF documents and ask questions about them
- Search the web for current information
- Analyze images
- Combine information from documents and the web
- Combine image information with uploaded documents
- Combine image analysis with web research
- Combine image, document, and web research in one request
- Save research history
- Manage uploaded documents
- Keep documents and research history separated between users

## How the agent works

The application uses a planner to decide what sources are needed for a question.

The main routes are:

1. Direct
2. Document
3. Web
4. Document + Web
5. Image
6. Image + Document
7. Image + Web
8. Image + Document + Web

The selected route is handled by a LangGraph workflow.

For example, a document + web request works like this:

User Question
→ Document Retrieval
→ Web Research
→ Final Synthesis
→ Answer

For an image + document + web request:

User Question + Image + Uploaded PDF
→ Image Analysis
→ Document Retrieval
→ Web Research
→ Final Synthesis
→ Answer

## RAG pipeline

For uploaded PDFs, the application follows a basic RAG pipeline:

PDF
→ Text extraction
→ Chunking
→ Embeddings
→ Vector storage
→ Similarity search
→ Retrieved context
→ LLM response

The application uses:

- FastEmbed for embeddings
- `sentence-transformers/all-MiniLM-L6-v2` through FastEmbed
- 384-dimensional vectors
- PostgreSQL with pgvector for vector storage and search

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- LangGraph
- SQLAlchemy
- pypdf

### AI

- Groq API
- LLM-based final synthesis
- Vision model for image analysis
- FastEmbed for text embeddings

### Database

- PostgreSQL
- pgvector

### Deployment

- Vercel for frontend
- Render for backend
- Neon PostgreSQL for production database

## Authentication

The application uses JWT-based authentication.

Users can:

- Register
- Login
- Logout
- Access their own documents
- Access their own research history

Documents and research data are associated with the logged-in user so that one user cannot access another user's data.

## Project Structure

```text
AI_Research_Agent/
│
├── backend/
│   ├── main.py
│   ├── agent_workflow.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   │
│   └── migrations/
│       └── 001_add_users_and_ownership.sql
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   └── package-lock.json
│
├── .env.example
├── DEPLOYMENT.md
├── README.md
└── .gitignore