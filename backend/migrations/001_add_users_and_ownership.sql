
----------------------------------
--tables banalo isse
------------------------------------
BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    upload_date TIMESTAMP NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS research_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    route VARCHAR(50),
    key_points TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);



ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE;

ALTER TABLE research_queries
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE research_queries
    ADD COLUMN IF NOT EXISTS route VARCHAR(50);



CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id ON document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_research_queries_user_id ON research_queries(user_id);

COMMIT;


