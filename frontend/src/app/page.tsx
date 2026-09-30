"use client";
import Link from "next/link";
import { Icon } from "@/components/Icon";
import { useAuth } from "@/lib/providers";

const FEATURES = [
  ["Private knowledge base", "Upload PDFs. They are chunked, embedded (all-MiniLM-L6-v2) and stored in PostgreSQL + pgvector, scoped to your account."],
  ["Hybrid retrieval", "Semantic search and PostgreSQL full-text search are merged with Reciprocal Rank Fusion."],
  ["LangGraph routing", "A planner picks direct, document, web, both, or image routes for each question."],
  ["Multimodal", "Add an image and combine vision analysis with your documents and web research."],
] as const;

export default function Landing() {
  const { user, loading } = useAuth();
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand"><span className="brand-icon"><Icon name="book" size={26} /></span>
          <div><div className="brand-name">Research Agent</div><div className="brand-sub">AI Powered • RAG • LangGraph</div></div></div>
        <div className="landing-actions">
          {!loading && user ? <Link className="btn btn-primary" href="/home">Open workspace</Link> : (
            <><Link className="btn btn-ghost" href="/login">Sign in</Link><Link className="btn btn-primary" href="/register">Create account</Link></>
          )}
        </div>
      </header>
      <section className="landing-hero">
        <h1>Better questions.<br />Deeper knowledge.</h1>
        <p>An AI research agent that searches your own documents and the web, then shows you exactly which route it took and what it found.</p>
        <Link className="btn btn-primary btn-lg" href={user ? "/home" : "/register"}>Start researching <Icon name="arrow" size={16} /></Link>
      </section>
      <section className="feature-grid">
        {FEATURES.map(([t, d]) => <div className="panel" key={t}><h2>{t}</h2><p className="muted">{d}</p></div>)}
      </section>
    </div>
  );
}
