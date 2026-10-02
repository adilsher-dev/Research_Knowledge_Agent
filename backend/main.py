import json
import os
import re
import base64
import tempfile
import uuid
import numpy as np

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader
from fastembed import TextEmbedding



from sqlalchemy import select,func
from database import SessionLocal
from models import ResearchQuery, DocumentChunk, User, Document

import schemas
from auth import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)



load_dotenv()



app = FastAPI()




_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

_frontend_url = os.getenv("FRONTEND_URL")

if _frontend_url:
    _allowed_origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




MAX_PDF_BYTES = int(os.getenv("MAX_PDF_BYTES", 25 * 1024 * 1024))
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", 4 * 1024 * 1024))




client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)




class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name=model_name)

    def encode(self, texts):
        if isinstance(texts, str):
            vector = list(self.model.embed([texts]))[0]
            return np.asarray(vector)

        vectors = list(self.model.embed(texts))
        return np.asarray(vectors)


embedding_model = EmbeddingModel(
    "sentence-transformers/all-MiniLM-L6-v2"
)




class ChatRequest(BaseModel):
    message: str


class ResearchRequest(BaseModel):
    topic: str


class VectorSearchRequest(BaseModel):
    question: str


class RAGRequest(BaseModel):
    question: str


class ResearchResponse(BaseModel):
    topic: str
    summary: str
    key_points: list[str]




@app.get("/")
def home():
    return {
        "message": "AI Research Assistant API is running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}




@app.post("/auth/register", response_model=schemas.TokenResponse)
def register(data: schemas.RegisterRequest):
    db = SessionLocal()

    try:
        existing = (
            db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists."
            )

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(user.id)

        return schemas.TokenResponse(
            access_token=token,
            user=schemas.UserResponse.model_validate(user)
        )

    finally:
        db.close()


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password."
            )

        token = create_access_token(user.id)

        return schemas.TokenResponse(
            access_token=token,
            user=schemas.UserResponse.model_validate(user)
        )

    finally:
        db.close()


@app.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Access tokens are stateless JWTs, so there is nothing to
    # invalidate server-side — the frontend discards the token.
    return {"message": "Logged out."}


@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return schemas.UserResponse.model_validate(current_user)




@app.post("/chat")
def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user)
):

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. "
                    "Explain things clearly and simply."
                )
            },
            {
                "role": "user",
                "content": data.message
            }
        ],

        temperature=0.2,
        stream=True
    )

    def generate():

        for chunk in response:

            content = chunk.choices[0].delta.content

            if content:
                yield content

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )




@app.post(
    "/research",
    response_model=ResearchResponse
)
def research(
    data: ResearchRequest,
    current_user: User = Depends(get_current_user)
):

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are a research assistant.

Return the answer in JSON format with exactly these fields:
- topic
- summary
- key_points

key_points must be an array of strings.
Do not add any extra fields.
"""
            },
            {
                "role": "user",
                "content": (
                    f"Research the following topic: {data.topic}"
                )
            }
        ],

        temperature=0.2,

        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content

    result = json.loads(content)

    # Save research result in PostgreSQL
    db = SessionLocal()

    try:

        new_research = ResearchQuery(
            user_id=current_user.id,
            topic=result["topic"],
            question=(
                f"Research the following topic: {data.topic}"
            ),
            answer=result["summary"],
            key_points="\n".join(
                f"- {point}"
                for point in result["key_points"]
            )
        )

        db.add(new_research)
        db.commit()

    finally:
        db.close()

    return result

@app.post("/agentic-research-multimodal")
async def agentic_research_multimodal(
    question: str = Form(...),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user)
):
    from agent_workflow import research_graph

    image_data_url = ""

    # Handle optional image
    if file:
        if not file.content_type:
            return {
                "error": "Could not determine file type."
            }

        if not file.content_type.startswith("image/"):
            return {
                "error": "Only image files are allowed here."
            }

        image_bytes = await file.read(MAX_IMAGE_BYTES + 1)

        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Image is too large. Maximum size is {MAX_IMAGE_BYTES // (1024 * 1024)} MB."
            )

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        image_data_url = (
            f"data:{file.content_type};base64,{base64_image}"
        )

    # Run LangGraph. user_id travels through the graph state so
    # document_node / both_node / image_document_node /
    # image_both_node only ever retrieve THIS user's chunks.
    result = research_graph.invoke({
        "question": question,
        "route": "",
        "plan_reason": "",
        "image_data_url": image_data_url,
        "image_result": "",
        "document_results": [],
        "web_result": "",
        "final_answer": "",
        "user_id": current_user.id
    })

    # Return useful frontend data
    document_sources = []

    for item in result.get("document_results", []):
        document_sources.append({
        "filename": item.get("filename"),
        "chunk_index": item.get("chunk_index"),
        "similarity": item.get("vector_similarity"),
        "matched_by": item.get("matched_by", []),
        "content_preview": item.get("content", "")[:200]
    })

    # Persist to this user's research history. The earlier version
    # of this endpoint didn't save anything, so History had nothing
    # to show — every completed research run is now recorded.
    db = SessionLocal()

    try:
        db.add(ResearchQuery(
            user_id=current_user.id,
            topic=question[:255],
            question=question,
            answer=result["final_answer"],
            route=result["route"]
        ))
        db.commit()

    finally:
        db.close()

    return {
        "question": question,
        "route": result["route"],
        "plan_reason": result["plan_reason"],
        "answer": result["final_answer"],
        "document_sources": document_sources,
        "has_web_result": bool(result.get("web_result")),
        "has_image_result": bool(result.get("image_result"))
    }




@app.get("/documents", response_model=list[schemas.DocumentResponse])
def list_documents(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        return (
            db.query(Document)
            .filter(Document.user_id == current_user.id)
            .order_by(Document.upload_date.desc())
            .all()
        )

    finally:
        db.close()


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        # Delete the chunks first (belt-and-suspenders alongside the
        # ON DELETE CASCADE foreign key), scoped to this user too.
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.user_id == current_user.id
        ).delete()

        db.delete(document)
        db.commit()

        return {"message": "Document deleted."}

    finally:
        db.close()



@app.get("/research-history", response_model=list[schemas.ResearchHistoryItem])
def list_research_history(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        return (
            db.query(ResearchQuery)
            .filter(ResearchQuery.user_id == current_user.id)
            .order_by(ResearchQuery.created_at.desc())
            .all()
        )

    finally:
        db.close()


@app.get("/research-history/{item_id}", response_model=schemas.ResearchHistoryItem)
def get_research_history_item(
    item_id: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        item = (
            db.query(ResearchQuery)
            .filter(
                ResearchQuery.id == item_id,
                ResearchQuery.user_id == current_user.id
            )
            .first()
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Research record not found."
            )

        return item

    finally:
        db.close()




@app.get("/research")
def get_research(current_user: User = Depends(get_current_user)):

    db = SessionLocal()

    try:

        research_list = db.execute(
            select(ResearchQuery)
            .where(ResearchQuery.user_id == current_user.id)
            .order_by(
                ResearchQuery.id.desc()
            )
        ).scalars().all()

        return research_list

    finally:
        db.close()



def clean_text(text: str) -> str:

    # Replace multiple spaces/tabs with one space
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text
    )

    # Remove spaces at beginning and end
    text = text.strip()

    return text




def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    # Split text into natural blocks.
    # Blank lines are treated as paragraph boundaries.
    paragraphs = re.split(
        r"\n\s*\n+",
        text
    )

    paragraphs = [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # If the current chunk can safely contain this paragraph
        candidate = (
            f"{current_chunk}\n\n{paragraph}"
            if current_chunk
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        # Save the current chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Start the next chunk with the current paragraph
        current_chunk = paragraph

        # Handle a single paragraph larger than chunk_size
        if len(current_chunk) > chunk_size:

            start = 0

            while start < len(current_chunk):

                end = start + chunk_size

                piece = current_chunk[start:end].strip()

                if piece:
                    chunks.append(piece)

                start += chunk_size - overlap

            current_chunk = ""

    # Add the final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks



@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    # Check file type
    if file.content_type != "application/pdf":
        return {
            "error": "Only PDF files are allowed."
        }

    # Read with a server-side limit. Client-side validation alone is not
    # sufficient for a public API.
    contents = await file.read(MAX_PDF_BYTES + 1)

    if len(contents) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"PDF is too large. Maximum size is {MAX_PDF_BYTES // (1024 * 1024)} MB."
        )

    # Basic PDF signature check in addition to the browser-supplied MIME type.
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF."
        )

    # Temporary file path.
    # IMPORTANT: never build this path from the client-supplied
    # filename (e.g. f"temp_{file.filename}") — a crafted filename
    # like "../../something" would let an upload write outside the
    # intended directory. Use a random name instead, and always
    # delete it once we're done with it.
    file_path = os.path.join(
        tempfile.gettempdir(),
        f"upload_{uuid.uuid4().hex}.pdf"
    )

    db = SessionLocal()

    try:
        # Save PDF temporarily
        with open(file_path, "wb") as f:
            f.write(contents)

        # Read PDF
        reader = PdfReader(file_path)

        text = ""

        # Extract text from every page
        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        # Clean text
        text = clean_text(text)

        # Make chunks
        chunks = chunk_text(
            text,
            chunk_size=1000,
            overlap=200
        )

        # Handle empty PDF
        if not chunks:
            return {
                "error": "No readable text was found in the PDF."
            }

       

        embeddings = embedding_model.encode(
            chunks
        ).tolist()

        

        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            content_type=file.content_type,
            status="processing",
            chunk_count=0
        )

        db.add(document)
        db.flush()  # assigns document.id before we insert chunks

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            document_chunk = DocumentChunk(
                user_id=current_user.id,
                document_id=document.id,
                filename=file.filename,
                chunk_index=index,
                content=chunk,
                embedding=embedding
            )

            db.add(document_chunk)

        document.status = "ready"
        document.chunk_count = len(chunks)

        db.commit()

        return {
            "document_id": document.id,
            "filename": file.filename,
            "pages": len(reader.pages),
            "chunk_count": len(chunks),
            "embedding_dimensions": len(embeddings[0]),
            "message": (
                "PDF processed and stored successfully."
            )
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="PDF upload failed."
        )

    finally:
        db.close()

        if os.path.exists(file_path):
            os.remove(file_path)




@app.post("/vector-search")
def vector_search(
    data: VectorSearchRequest,
    current_user: User = Depends(get_current_user)
):

    # Convert question into embedding
    question_embedding = embedding_model.encode(
        data.question
    ).tolist()

    db = SessionLocal()

    try:

        results = (
            db.query(
                DocumentChunk,
                (
                    1
                    - DocumentChunk.embedding.cosine_distance(
                        question_embedding
                    )
                ).label("similarity")
            )
            .filter(DocumentChunk.user_id == current_user.id)
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    question_embedding
                )
            )
            .limit(3)
            .all()
        )

        return [
            {
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity": float(similarity)
            }
            for chunk, similarity in results
        ]

    finally:
        db.close()



def hybrid_retrieve(
    question: str,
    user_id: int,
    top_k: int = 5
):
    """
    Retrieve relevant document chunks using:

    1. Semantic search with pgvector
    2. Keyword search with PostgreSQL Full-Text Search
    3. Reciprocal Rank Fusion (RRF)

    Always scoped to user_id — a user's question must only ever
    be able to retrieve that same user's own uploaded chunks.
    """

    

    question_embedding = embedding_model.encode(
        question
    ).tolist()

    db = SessionLocal()

    try:

        

        vector_results = (
            db.query(
                DocumentChunk,
                (
                    1
                    - DocumentChunk.embedding.cosine_distance(
                        question_embedding
                    )
                ).label("similarity")
            )
            .filter(DocumentChunk.user_id == user_id)
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    question_embedding
                )
            )
            .limit(top_k)
            .all()
        )

        

        words = re.findall(
            r"[A-Za-z0-9]+",
            question.lower()
        )

        stop_words = {
            "what",
            "is",
            "are",
            "the",
            "a",
            "an",
            "in",
            "on",
            "of",
            "to",
            "for",
            "and",
            "or",
            "with",
            "from",
            "this",
            "that",
            "mentioned",
            "used"
        }

        keywords = [
            word
            for word in words
            if word not in stop_words
        ]

        keyword_results = []

        if keywords:

            # Build an OR query
            tsquery_text = " | ".join(
                keywords
            )

            document_vector = func.to_tsvector(
                "english",
                DocumentChunk.content
            )

            keyword_query = func.to_tsquery(
                "english",
                tsquery_text
            )

            keyword_results = (
                db.query(
                    DocumentChunk,
                    func.ts_rank_cd(
                        document_vector,
                        keyword_query
                    ).label("keyword_score")
                )
                .filter(
                    document_vector.op("@@")(
                        keyword_query
                    )
                )
                .filter(DocumentChunk.user_id == user_id)
                .order_by(
                    func.ts_rank_cd(
                        document_vector,
                        keyword_query
                    ).desc()
                )
                .limit(top_k)
                .all()
            )

        

        combined_results = {}

        

        for rank, (chunk, similarity) in enumerate(
            vector_results,
            start=1
        ):

            combined_results[chunk.id] = {
                "chunk": chunk,
                "vector_similarity": float(
                    similarity
                ),
                "keyword_score": 0.0,
                "rrf_score": 1 / (60 + rank),
                "matched_by": [
                    "semantic"
                ]
            }

        

        for rank, (chunk, keyword_score) in enumerate(
            keyword_results,
            start=1
        ):

            if chunk.id in combined_results:

                combined_results[
                    chunk.id
                ]["keyword_score"] = float(
                    keyword_score
                )

                combined_results[
                    chunk.id
                ]["rrf_score"] += (
                    1 / (60 + rank)
                )

                combined_results[
                    chunk.id
                ]["matched_by"].append(
                    "keyword"
                )

            else:

                combined_results[chunk.id] = {
                    "chunk": chunk,
                    "vector_similarity": 0.0,
                    "keyword_score": float(
                        keyword_score
                    ),
                    "rrf_score": (
                        1 / (60 + rank)
                    ),
                    "matched_by": [
                        "keyword"
                    ]
                }

        
        final_results = sorted(
            combined_results.values(),
            key=lambda item: item["rrf_score"],
            reverse=True
        )

        return final_results[:top_k]

    finally:
        db.close()



@app.post("/hybrid-search")
def hybrid_search(
    data: VectorSearchRequest,
    current_user: User = Depends(get_current_user)
):

    results = hybrid_retrieve(
        data.question,
        current_user.id,
        top_k=5
    )

    return [
        {
            "filename": item["chunk"].filename,
            "chunk_index": item["chunk"].chunk_index,
            "content": item["chunk"].content,
            "vector_similarity": item["vector_similarity"],
            "keyword_score": item["keyword_score"],
            "rrf_score": item["rrf_score"],
            "matched_by": item["matched_by"]
        }
        for item in results
    ]

def search_uploaded_documents(
    question: str,
    user_id: int,
    top_k: int = 5
):
    """
    Search uploaded documents using
    hybrid retrieval, scoped to user_id.
    """

    results = hybrid_retrieve(
        question,
        user_id,
        top_k=top_k
    )

    tool_results = []

    for item in results:

        chunk = item["chunk"]

        tool_results.append(
            {
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "vector_similarity": (
                    item["vector_similarity"]
                ),
                "keyword_score": (
                    item["keyword_score"]
                ),
                "rrf_score": (
                    item["rrf_score"]
                ),
                "matched_by": (
                    item["matched_by"]
                )
            }
        )

    return tool_results



document_search_tool = {
    "type": "function",
    "function": {
        "name": "search_uploaded_documents",
        "description": (
            "Search the user's uploaded documents "
            "for information relevant to a question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "The question to search "
                        "for in the uploaded documents."
                    )
                }
            },
            "required": [
                "question"
            ]
        }
    }
}

browser_search_tool = {
    "type": "browser_search"
}

available_tools = [
    document_search_tool,
    browser_search_tool
]



@app.post("/agent")
def agent(
    data: RAGRequest,
    current_user: User = Depends(get_current_user)
):

    question = data.question.lower()

    web_keywords = [
        "latest",
        "recent",
        "today",
        "current",
        "news",
        "2026",
        "this week",
        "this month",
        "recent developments",
        "latest developments"
    ]

    needs_web = any(
        keyword in question
        for keyword in web_keywords
    )

   

    if needs_web:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": """
You are a web research assistant.

Use browser search to answer questions requiring
current, recent, or external information.

Rules:
- Search the web for current information.
- Prefer recent and reliable sources.
- Do not invent facts.
- Cite important factual claims using
  the citations provided by the browser search.
- Keep the answer clear and concise.
"""
                },
                {
                    "role": "user",
                    "content": data.question
                }
            ],

            tools=[
                {
                    "type": "browser_search"
                }
            ],

            tool_choice="required",

            temperature=1,

            max_completion_tokens=2048,

            reasoning_effort="low"
        )

        return {
            "question": data.question,
            "route": "web_search",
            "answer": response.choices[0].message.content
        }

    # --------------------------------------------------
    # DOCUMENT RESEARCH
    # --------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": """
You are a document research assistant.

Use the uploaded-document search tool when answering
questions about the user's uploaded documents.

Do not invent information.

Use document source citations such as:
[Source 1], [Source 2].
"""
        },
        {
            "role": "user",
            "content": data.question
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=messages,

        tools=[
            document_search_tool
        ],

        tool_choice="auto",

        temperature=0.2,

        max_completion_tokens=1024,

        reasoning_effort="low",

        include_reasoning=False
    )

    message = response.choices[0].message

    # --------------------------------------------------
    # Local document tool
    # --------------------------------------------------

    if message.tool_calls:

        messages.append(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": (
                                tool_call.function.arguments
                            )
                        }
                    }
                    for tool_call in message.tool_calls
                ]
            }
        )

        for tool_call in message.tool_calls:

            if (
                tool_call.function.name
                == "search_uploaded_documents"
            ):

                arguments = json.loads(
                    tool_call.function.arguments
                )

                tool_result = search_uploaded_documents(
                    arguments["question"],
                    current_user.id
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": (
                            tool_call.function.name
                        ),
                        "content": json.dumps(
                            tool_result
                        )
                    }
                )

        final_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.2,
            max_completion_tokens=1024,
            reasoning_effort="low",
            include_reasoning=False
        )

        return {
            "question": data.question,
            "route": "document_search",
            "answer": (
                final_response
                .choices[0]
                .message
                .content
            ),
            "tool_used": True
        }

    return {
        "question": data.question,
        "route": "direct",
        "answer": message.content,
        "tool_used": False
    }
@app.post("/web-research")
def web_research(
    data: RAGRequest,
    current_user: User = Depends(get_current_user)
):

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are a web research assistant.

Research the user's question using the browser search tool.

Rules:
1. Prefer recent sources relevant to the question.
2. Prefer primary sources such as research papers,
   official project pages, documentation, and author pages.
3. Do not invent papers, systems, dates, or claims.
4. Distinguish established information from emerging research.
5. Include dates when discussing recent developments.
6. Cite important factual claims using the web citations
   provided by the browser search.
7. If evidence is weak or conflicting, say so.
8. Give a concise but useful answer.
"""
            },
            {
                "role": "user",
                "content": data.question
            }
            
        ],

        tools=[
            {
                "type": "browser_search"
            }
        ],

        tool_choice="required",

        temperature=1,
        max_completion_tokens=2048,
        reasoning_effort="low"
    )

    return {
        "question": data.question,
        "answer": response.choices[0].message.content
    }
# --------------------------------------------------
# RAG
# --------------------------------------------------

@app.post("/rag")
def rag(
    data: RAGRequest,
    current_user: User = Depends(get_current_user)
):

   
    results = hybrid_retrieve(
        data.question,
        current_user.id,
        top_k=5
    )

    

    if not results:

        return {
            "question": data.question,
            "answer": (
                "The uploaded documents do not contain "
                "enough relevant information to answer "
                "this question."
            ),
            "sources": []
        }

    
    context_parts = []

    for source_id, item in enumerate(
        results,
        start=1
    ):

        chunk = item["chunk"]

        context_parts.append(
            f"""
[Source {source_id}]

Filename:
{chunk.filename}

Chunk:
{chunk.chunk_index}

Content:
{chunk.content}
"""
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are a document question-answering assistant.

Answer ONLY from the provided document sources.

Rules:

1. Do not use outside knowledge.
2. Do not guess or invent information.
3. Every factual statement must be supported
   by the provided sources.
4. Cite factual claims using:
   [Source 1], [Source 2], etc.
5. Ignore irrelevant sources.
6. If multiple sources support a statement,
   cite all relevant sources.
7. If the answer is not present in the sources,
   say exactly:

"The uploaded document does not contain enough
information to answer this question."

8. Keep the answer clear and concise.
"""
            },
            {
                "role": "user",
                "content": f"""
Document sources:

{context}

Question:

{data.question}

Answer using only the provided sources.
Include source citations.
"""
            }
        ],

        temperature=0.2,

        max_completion_tokens=1024,

        reasoning_effort="low",

        include_reasoning=False
    )

    
    answer = response.choices[0].message.content

    print(
        "LLM CONTENT:",
        answer
    )

    print(
        "FINISH REASON:",
        response.choices[0].finish_reason
    )

    

    sources = []

    for source_id, item in enumerate(
        results,
        start=1
    ):

        chunk = item["chunk"]

        sources.append(
            {
                "source_id": source_id,
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "vector_similarity": (
                    item["vector_similarity"]
                ),
                "keyword_score": (
                    item["keyword_score"]
                ),
                "rrf_score": (
                    item["rrf_score"]
                ),
                "matched_by": (
                    item["matched_by"]
                ),
                "content_preview": (
                    chunk.content[:300]
                )
            }
        )

    
    return {
        "question": data.question,
        "answer": answer,
        "sources": sources
    }


def plan_research(question: str, has_image: bool = False) -> dict:

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are the planning component of an AI research agent.

Choose the best route for answering the user's question.

Return JSON with exactly these fields:

{
  "route": "document" | "web" | "both" | "direct",
  "reason": "short explanation"
}

Routing rules:

- If an image is provided and the question requires understanding,
  reading, identifying, or analyzing the image, choose "image".
- If no image is provided, never choose "image".
- Otherwise choose among "document", "web", "both", or "direct"
  according to the existing rules.

If an image is provided:

- Choose "image" when only the image is needed.
- Choose "image_document" when both the image and uploaded documents are needed.
- Choose "image_web" when both the image and web research are needed.
- Choose "image_both" when the image, uploaded documents, and web research are all needed.

If no image is provided:

- Choose "document", "web", "both", or "direct" using the existing rules.

Never choose an image route when no image is provided.

Valid routes:
document
web
both
direct
image

Use these rules:

- document:
  Use when the answer depends on the user's uploaded
  documents or resume.

- web:
  Use when the answer requires current, recent,
  external, or web information.

- both:
  Use when the answer requires information from the
  uploaded documents AND current/external web information.

- direct:
  Use for general questions that do not require the
  uploaded documents or current web information.

Do not add any other fields.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],

        temperature=0,

        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content

    return json.loads(content)




def perform_web_search(question: str) -> str:

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are a web research assistant.

Use browser search to answer the question.

Rules:
- Use current web information.
- Prefer reliable and recent sources.
- Do not invent facts.
- Preserve the web citations returned by the browser search.
- Give a concise research summary.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],

        tools=[
            {
                "type": "browser_search"
            }
        ],

        tool_choice="required",

        temperature=1,

        max_completion_tokens=2048,

        reasoning_effort="low"
    )

    return response.choices[0].message.content



@app.post("/agentic-research")
def agentic_research(
    data: RAGRequest,
    current_user: User = Depends(get_current_user)
):
    from agent_workflow import research_graph

    

    plan = plan_research(
        data.question
    )

    print("PLAN:", plan)

    route = plan["route"]

    

    document_results = []
    web_result = None

    
    if route in {"document", "both"}:

        document_results = (
            search_uploaded_documents(
                data.question,
                current_user.id
            )
        )
        
    print("DOCUMENT RESULTS:", len(document_results))

    

    if route in {"web", "both"}:

        web_result = perform_web_search(
            data.question
        )

    print("WEB RESULT RECEIVED:", web_result is not None)

    
    if route == "direct":

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": """
You are a helpful AI research assistant.

Answer clearly and concisely.
Do not invent information.
"""
                },
                {
                    "role": "user",
                    "content": data.question
                }
            ],

            temperature=0.2,

            max_completion_tokens=1024,

            reasoning_effort="low",

            include_reasoning=False
        )

        return {
            "question": data.question,
            "route": route,
            "plan_reason": plan["reason"],
            "answer": response.choices[0].message.content
        }

    # --------------------------------------------------
    # 5. BUILD FINAL RESEARCH CONTEXT
    # --------------------------------------------------

    research_context = ""

    # Document results
    if document_results:

        research_context += """

===== DOCUMENT RESEARCH =====

"""

        for source_id, result in enumerate(
            document_results,
            start=1
        ):

            research_context += f"""
[Document Source {source_id}]

Filename:
{result["filename"]}

Chunk:
{result["chunk_index"]}

Similarity:
{result["rrf_score"]}

Content:
{result["content"]}

"""
    
    # Web result
    if web_result:

        research_context += """

===== WEB RESEARCH =====

"""

        research_context += web_result

    

    print("FINAL SYNTHESIS STARTING")

    final_response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": """
You are the final synthesis component of an AI research agent.

Answer the user's question using only the research
results provided below.

Rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. Clearly distinguish document information from web information.
4. For document facts, use citations like:
   [Document Source 1]
5. Preserve web citations exactly as provided by the
   web research.
6. If the available research is insufficient, say so.
7. Keep the final answer clear and concise.
"""
            },
            {
                "role": "user",
                "content": f"""
User question:

{data.question}

Research results:

{research_context}

Now produce the final answer.
"""
            }
        ],

        temperature=0.2,

        max_completion_tokens=2048,

        reasoning_effort="low",

        include_reasoning=False
    )

    

    return {
        "question": data.question,
        "route": route,
        "plan_reason": plan["reason"],
        "answer": final_response.choices[0].message.content
    }

@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    question: str = "What is shown in this image?",
    current_user: User = Depends(get_current_user)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"error": "Please upload an image file."}

    image_bytes = await file.read()

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    image_data_url = (
        f"data:{file.content_type};base64,{base64_image}"
    )

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful multimodal AI assistant. "
                    "Analyze the image carefully and answer the user's question "
                    "based only on what can be observed from the image."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        },
                    },
                ],
            },
        ],
        temperature=0.7,
        max_completion_tokens=1024,
    )

    answer = response.choices[0].message.content

    return {
        "filename": file.filename,
        "question": question,
        "answer": answer,
    }
