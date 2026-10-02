import os
import base64
import mimetypes
import time

from dotenv import load_dotenv
from groq import Groq,RateLimitError
from typing_extensions import TypedDict
from database import SessionLocal
from models import DocumentChunk

from langgraph.graph import StateGraph, START, END

from main import (
    plan_research,
    search_uploaded_documents,
    perform_web_search,
)

# --------------------------------------------------
# env
# --------------------------------------------------

load_dotenv()

# --------------------------------------------------
# Groq client
# --------------------------------------------------

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# --------------------------------------------------
# aise create karte hai langraph
# --------------------------------------------------

class ResearchState(TypedDict):
    question: str
    route: str
    plan_reason: str
    image_data_url: str
    image_result: str
    document_results: list
    web_result: str
    final_answer: str
    user_id: int


# --------------------------------------------------
# aise encode karte hai image
# --------------------------------------------------

def image_to_data_url(image_path: str) -> str:
    """
    Read an image from disk and convert it into a
    base64 data URL that can be sent to the vision model.
    """
    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def analyze_image(
    question: str,
    image_data_url: str
) -> str:
    """
    Analyze an image using the vision-capable Groq model.
    The vision node focuses only on information directly
    visible in the image.
    """
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a multimodal AI assistant. "
                    "Analyze the provided image carefully. "
                    "Describe and identify only information that can be "
                    "observed directly in the image. "
                    "Do not ask for documents, files, or external information. "
                    "Do not perform comparisons with information that is not "
                    "present in the image."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Analyze this image for the following question: "
                            f"{question}\n"
                            "Focus only on what is directly visible in the image. "
                            "Do not ask for any additional files or documents."
                        ),
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

    return response.choices[0].message.content


# --------------------------------------------------
# doc available hai ki nahi
# --------------------------------------------------

def has_uploaded_documents(user_id: int) -> bool:
    """
    Check the actual database instead of asking the LLM
    whether an uploaded document exists — scoped to user_id
    so one user's uploads never affect another user's routing.
    """
    db = SessionLocal()

    try:
        return (
            db.query(DocumentChunk.id)
            .filter(DocumentChunk.user_id == user_id)
            .first()
        ) is not None
    finally:
        db.close()


# --------------------------------------------------
# pehle plannode banao
# --------------------------------------------------

def planner_node(state: ResearchState):
    """
    Decide which route should execute.

    Supported routes:
    direct
    document
    web
    both
    image
    image_document
    image_web
    image_both
    """
    has_image = bool(state.get("image_data_url"))
    question = state["question"].lower()

    documents_available = has_uploaded_documents(state["user_id"])

    

    document_keywords = [
        "cgpa",
        "resume",
        "my resume",
        "my education",
        "my skills",
        "my experience",
        "my projects",
        "uploaded document",
        "uploaded documents",
        "uploaded file",
        "pdf",
        "according to my resume",
        "according to the document",
    ]

    web_keywords = [
        "latest",
        "recent",
        "current",
        "today",
        "news",
        "web",
        "online",
        "2026",
        "latest technologies",
        "recent technologies",
        "latest ai",
        "recent ai",
        "latest rag",
        "recent rag",
        "latest developments",
        "recent developments",
    ]

    needs_document = (
        documents_available
        and any(
            keyword in question
            for keyword in document_keywords
        )
    )

    needs_web = any(
        keyword in question
        for keyword in web_keywords
    )

    # --------------------------------------------------
    # debug kra hai isse
    # --------------------------------------------------

    print("QUESTION:", question)
    print("DOCUMENTS AVAILABLE:", documents_available)
    print("NEEDS DOCUMENT:", needs_document)
    print("NEEDS WEB:", needs_web)
    print("HAS IMAGE:", has_image)

    # --------------------------------------------------
    # image ki routing
    # --------------------------------------------------

    if has_image:

        if needs_document and needs_web:
            return {
                "route": "image_both",
                "plan_reason": (
                    "Image, uploaded documents, and web research are required."
                )
            }

        if needs_document:
            return {
                "route": "image_document",
                "plan_reason": (
                    "Image analysis and uploaded document retrieval are required."
                )
            }

        if needs_web:
            return {
                "route": "image_web",
                "plan_reason": (
                    "Image analysis and web research are required."
                )
            }

        return {
            "route": "image",
            "plan_reason": "Image analysis is required."
        }

    # --------------------------------------------------
    # bina image routing
    # --------------------------------------------------

    # combined check krlo
    # Check the combined route BEFORE individual routes.
    if needs_document and needs_web:
        return {
            "route": "both",
            "plan_reason": (
                "Uploaded documents and web research are required."
            )
        }

    if needs_document:
        return {
            "route": "document",
            "plan_reason": (
                "The question can be answered using the uploaded documents."
            )
        }

    if needs_web:
        return {
            "route": "web",
            "plan_reason": (
                "Current web research is required."
            )
        }

    

    plan = plan_research(state["question"])

    return {
        "route": plan["route"],
        "plan_reason": plan["reason"]
    }


# --------------------------------------------------
# Doc node
# --------------------------------------------------

def document_node(state: ResearchState):
    results = search_uploaded_documents(
        state["question"],
        state["user_id"]
    )

    return {
        "document_results": results
    }


# --------------------------------------------------
# Web search node hai ye
# --------------------------------------------------

def web_node(state: ResearchState):
    result = perform_web_search(
        state["question"]
    )

    return {
        "web_result": result
    }

# --------------------------------------------------
# doc + web node hai
# --------------------------------------------------

def both_node(state: ResearchState):
    # Step 1: Search the user's uploaded documents
    document_results = search_uploaded_documents(
        state["question"],
        state["user_id"]
    )

    # Step 2: Prepare retrieved document context
    document_context = "\n\n".join(
        [
            (
                f"[Document Source {index}]\n"
                f"{result['content']}"
            )
            for index, result in enumerate(
                document_results,
                start=1
            )
        ]
    )

    # Step 3: Give the document findings to the web researcher
    web_question = f"""
The user's uploaded documents have already been searched.

DOCUMENT RESEARCH:
{document_context}

Original user question:
{state["question"]}

Use the document research above for information about the user's
documents/profile.

Now use current web information to research only the parts of the
question that require current or external information.

Do not invent information.
Do not claim to have direct access to the uploaded document beyond
the document research provided above.
"""

    # Step 4: Perform web research
    web_result = perform_web_search(
        web_question
    )

    return {
        "document_results": document_results,
        "web_result": web_result
    }

# --------------------------------------------------
# direct node hai ue
# --------------------------------------------------

def direct_node(state: ResearchState):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": """
You are a helpful AI assistant.

Answer clearly and concisely.
Do not invent information.
"""
            },
            {
                "role": "user",
                "content": state["question"]
            }
        ],
        temperature=0.2,
        max_completion_tokens=512,
        reasoning_effort="low",
        include_reasoning=False
    )

    return {
        "final_answer": response.choices[0].message.content
    }


# --------------------------------------------------
# Image Node hai ye
# --------------------------------------------------

def image_node(state: ResearchState):
    result = analyze_image(
        state["question"],
        state["image_data_url"]
    )

    return {
        "image_result": result
    }


# --------------------------------------------------
# Image + Document Node hai ye
# --------------------------------------------------

def image_document_node(state: ResearchState):
    image_result = analyze_image(
        state["question"],
        state["image_data_url"]
    )

    document_results = search_uploaded_documents(
        state["question"],
        state["user_id"]
    )

    return {
        "image_result": image_result,
        "document_results": document_results
    }


# --------------------------------------------------
# Image + Web Node hai ye 
# --------------------------------------------------

def image_web_node(state: ResearchState):
    # Step 1: Analyze the image using the vision model
    image_result = analyze_image(
        state["question"],
        state["image_data_url"]
    )

    # Step 2: Give the image analysis to the web researcher
    web_question = f"""
The image has already been analyzed by a vision model.

VISION ANALYSIS:
{image_result}

Original user question:
{state["question"]}

Use the vision analysis above to identify the relevant technology/topic.
Then use current web information to explain its latest developments in 2026.

Do not try to interpret the image yourself.
Research only the technology/topic identified in the vision analysis.
"""

    web_result = perform_web_search(
        web_question
    )

    return {
        "image_result": image_result,
        "web_result": web_result
    }

# --------------------------------------------------
# Image + Document + Web Node hai ye
# --------------------------------------------------

def image_both_node(state: ResearchState):
    # Step 1: Analyze the image
    image_result = analyze_image(
        state["question"],
        state["image_data_url"]
    )

    # Step 2: Search the user's uploaded documents
    document_results = search_uploaded_documents(
        state["question"],
        state["user_id"]
    )

    # Step 3: Prepare document information for web research
    document_context = "\n\n".join(
        [
            (
                f"[Document Source {index}]\n"
                f"{result['content']}"
            )
            for index, result in enumerate(
                document_results,
                start=1
            )
        ]
    )

    # Step 4: Give image + document findings to the web researcher
    web_question = f"""
The image and uploaded documents have already been analyzed.

VISION ANALYSIS:
{image_result}

DOCUMENT RESEARCH:
{document_context}

Original user question:
{state["question"]}

Use the vision analysis and document research above to understand
the technology/topic and the user's relevant skills.

Then use current web information to explain its latest developments
in 2026.

Do not try to interpret the image yourself.
Do not assume information that is not present in the supplied
vision analysis or document research.
Research the relevant technology/topic using current web sources.
"""

    # Step 5: Perform web research
    web_result = perform_web_search(
        web_question
    )

    return {
        "image_result": image_result,
        "document_results": document_results,
        "web_result": web_result
    }

# --------------------------------------------------
# yahan par result synthesis hoga
# --------------------------------------------------

def synthesis_node(state: ResearchState):
    document_context = ""

    if state.get("document_results"):
        document_context = "\n\n".join(
            [
                (
                    f"[Document Source {index}]\n"
                    f"{result['content']}"
                )
                for index, result in enumerate(
                    state["document_results"],
                    start=1
                )
            ]
        )

    web_context = state.get(
        "web_result",
        ""
    )

    image_context = state.get(
        "image_result",
        ""
    )

    research_context = f"""
IMAGE ANALYSIS:
{image_context}

DOCUMENT RESEARCH:
{document_context}

WEB RESEARCH:
{web_context}
"""

    messages = [
        {
            "role": "system",
            "content": """
You are the final synthesis component of an AI research assistant.

Use only the research information provided to you.

Rules:
1. Do not invent facts.
2. Use image analysis for visual claims.
3. Use document sources for document claims.
4. Preserve web citations when present.
5. If information is missing, say so clearly.
6. Keep the answer clear and concise.
"""
        },
        {
            "role": "user",
            "content": f"""
Question:

{state["question"]}

Research:

{research_context}

Give the final answer.
"""
        }
    ]

    # agar groq ki limit aayegi to ushe try catch se handle kr rhe hai bina limit error diye
    response = None

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                temperature=0.2,
                max_completion_tokens=1024,
                reasoning_effort="low",
                include_reasoning=False
            )

            break

        except RateLimitError as error:
            if attempt == 2:
                print("Groq rate limit persisted after 3 attempts.")
                raise error

            wait_seconds = 3 * (2 ** attempt)

            print(
                f"Groq rate limit reached. "
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)

    return {
        "final_answer": response.choices[0].message.content
    }

# --------------------------------------------------
# Route banao after planner
# --------------------------------------------------

def route_after_planner(state: ResearchState):
    route = state["route"]

    if route == "document":
        return "document"

    if route == "web":
        return "web"

    if route == "both":
        return "both"

    if route == "image":
        return "image"

    if route == "image_document":
        return "image_document"

    if route == "image_web":
        return "image_web"

    if route == "image_both":
        return "image_both"

    return "direct"


# --------------------------------------------------
# graph banao aise
# --------------------------------------------------

builder = StateGraph(ResearchState)

# Nodes
builder.add_node(
    "planner",
    planner_node
)

builder.add_node(
    "document",
    document_node
)

builder.add_node(
    "web",
    web_node
)

builder.add_node(
    "both",
    both_node
)

builder.add_node(
    "direct",
    direct_node
)

builder.add_node(
    "image",
    image_node
)

builder.add_node(
    "image_document",
    image_document_node
)

builder.add_node(
    "image_web",
    image_web_node
)

builder.add_node(
    "image_both",
    image_both_node
)

builder.add_node(
    "synthesis",
    synthesis_node
)


# --------------------------------------------------
# usme edges daalo
# --------------------------------------------------

builder.add_edge(
    START,
    "planner"
)

builder.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "document": "document",
        "web": "web",
        "both": "both",
        "image": "image",
        "image_document": "image_document",
        "image_web": "image_web",
        "image_both": "image_both",
        "direct": "direct"
    }
)

builder.add_edge(
    "document",
    "synthesis"
)

builder.add_edge(
    "web",
    "synthesis"
)

builder.add_edge(
    "both",
    "synthesis"
)

builder.add_edge(
    "image",
    "synthesis"
)

builder.add_edge(
    "image_document",
    "synthesis"
)

builder.add_edge(
    "image_web",
    "synthesis"
)

builder.add_edge(
    "image_both",
    "synthesis"
)

builder.add_edge(
    "direct",
    END
)

builder.add_edge(
    "synthesis",
    END
)


# --------------------------------------------------
# graph ko compile karo taaki inbuilt methods support ho sakein
# --------------------------------------------------

research_graph = builder.compile()