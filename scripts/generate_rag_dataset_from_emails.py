#!/usr/bin/env python3
"""
Generate RAG test dataset from dummy emails using Qdrant for context retrieval.

This script:
1. Reads dummy_emails.json
2. For each email, queries Qdrant to retrieve relevant context
3. Generates a RAG test dataset with real context from the knowledge base
"""

import json
import asyncio
import sys
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
except ImportError:
    print("Please install qdrant-client: pip install qdrant-client")
    sys.exit(1)


# Qdrant Configuration
QDRANT_HOST = "ollama.ios.htwg-konstanz.de"
QDRANT_PORT = 6333
COLLECTION_NAME = "htwg_knowledge_base"

# Ollama Configuration (for embeddings)
OLLAMA_BASE_URL = "http://ollama.ios.htwg-konstanz.de:11434"
EMBEDDING_MODEL = "mxbai-embed-large"

# Output settings
OUTPUT_FILE = "rag_email_dataset.json"
TOP_K = 5  # Number of context chunks to retrieve per email (increased from 3)


def connect_to_qdrant():
    """Connect to the Qdrant vector database."""
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Verify connection by checking collection
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"Connected! Collection '{COLLECTION_NAME}' has {collection_info.points_count} points")
        return client
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        raise


def get_embedding(text: str) -> list:
    """Get embedding for text using Ollama's mxbai-embed-large model."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text
        }
    )
    response.raise_for_status()
    return response.json()["embedding"]


def get_email_query(email: dict) -> str:
    """
    Extract the main question/query from an email.
    Combines subject and body for better context retrieval.
    """
    subject = email.get("subject", "")
    body = email.get("body", "")
    return f"{subject}\n\n{body}"


def get_focused_queries(email: dict) -> list:
    """
    Generate multiple focused queries from an email to improve retrieval.
    Returns a list of queries that target different aspects of the email.
    """
    subject = email.get("subject", "")
    body = email.get("body", "")
    category = email.get("expected_category", "")
    
    queries = []
    
    # Full email query
    queries.append(f"{subject}\n\n{body}")
    
    # Subject only (often contains key topic)
    if subject:
        queries.append(subject)
    
    # Category-specific queries for better retrieval
    category_queries = {
        "contract_submission": [
            "Praktikumsvertrag einreichen Unterlagen Dokumente",
            "Antrag Zulassung praktisches Studiensemester PSS",
            "Praktikumsvertrag persönlich abgeben Sekretariat"
        ],
        "international_office_question": [
            "Praxissemester Ausland internationale Praktikum",
            "Auslandspraktikum Anerkennung Versicherung",
            "Praktikum im Ausland Regeln Voraussetzungen"
        ],
        "internship_postponement": [
            "Praxissemester verschieben Antrag Verschiebung",
            "Praktikum verschieben Formular Gründe",
            "PSS Verschiebung Prüfungsausschuss"
        ]
    }
    
    if category in category_queries:
        queries.extend(category_queries[category])
    
    return queries


def retrieve_context(client: QdrantClient, query: str, top_k: int = TOP_K) -> str:
    """
    Query Qdrant to retrieve relevant context for the given query.
    Returns concatenated context from top-k results.
    """
    # Embed the query using Ollama
    query_vector = get_embedding(query)
    
    # Search Qdrant using query_points
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True
    )
    
    # Extract and concatenate context
    contexts = []
    # query_points returns a QueryResponse with .points attribute
    points = results.points if hasattr(results, 'points') else results
    for result in points:
        # The payload structure may vary - adjust based on your actual data
        payload = result.payload
        if payload:
            # Common payload fields to check
            text = payload.get("text") or payload.get("content") or payload.get("chunk") or str(payload)
            if text:
                contexts.append(text)
    
    return contexts  # Return list instead of joined string


def retrieve_multi_query_context(client: QdrantClient, queries: list, max_chunks: int = 8) -> str:
    """
    Retrieve context using multiple queries and deduplicate results.
    This improves recall by using different phrasings of the question.
    """
    all_contexts = []
    seen_texts = set()
    
    for query in queries:
        contexts = retrieve_context(client, query)
        for ctx in contexts:
            # Deduplicate based on first 100 chars
            ctx_key = ctx[:100] if len(ctx) > 100 else ctx
            if ctx_key not in seen_texts:
                seen_texts.add(ctx_key)
                all_contexts.append(ctx)
        
        # Stop if we have enough unique contexts
        if len(all_contexts) >= max_chunks:
            break
    
    # Take only the top chunks (limited to max_chunks)
    return "\n\n---\n\n".join(all_contexts[:max_chunks]) if all_contexts else ""


def generate_expected_answer_hint(email: dict) -> str:
    """
    Generate a hint for expected answer based on email category.
    The actual evaluation will be done by the LLM evaluator.
    """
    category = email.get("expected_category", "uncategorized")
    
    hints = {
        "contract_submission": "Der Praktikumsvertrag wurde eingereicht und wird bearbeitet. Informationen zu Fristen und nächsten Schritten.",
        "international_office_question": "Informationen zu Auslandspraktika, internationalen Anforderungen und Anerkennungsverfahren.",
        "internship_postponement": "Hinweise zur Verschiebung des Praktikums, notwendige Schritte und Fristen.",
        "uncategorized": "Allgemeine Informationen basierend auf dem Kontext der Wissensdatenbank."
    }
    
    return hints.get(category, hints["uncategorized"])


def process_emails(emails: list, client: QdrantClient) -> list:
    """
    Process all emails and generate RAG test questions.
    Uses multi-query retrieval for better context coverage.
    """
    questions = []
    
    for i, email in enumerate(emails):
        print(f"Processing email {i+1}/{len(emails)}: {email.get('id', 'unknown')}...")
        
        # Get multiple queries from email for better retrieval
        queries = get_focused_queries(email)
        print(f"  Using {len(queries)} queries for retrieval...")
        
        # Retrieve context from Qdrant using multiple queries
        context = retrieve_multi_query_context(client, queries, max_chunks=8)
        
        if not context:
            print(f"  Warning: No context found for email {email.get('id')}")
            # Still create the question but with empty context marker
            context = "[Kein relevanter Kontext in der Wissensdatenbank gefunden]"
        else:
            chunk_count = context.count("---") + 1
            print(f"  Retrieved {chunk_count} context chunks")
        
        # Get the main query (subject + body) for the question text
        query = get_email_query(email)
        
        # Create RAG question
        question = {
            "id": f"rag_{email.get('id', f'email_{i+1}')}",
            "text": query,
            "context": context,
            "expected_answer": generate_expected_answer_hint(email),
            "metadata": {
                "source_email_id": email.get("id"),
                "category": email.get("expected_category", "uncategorized"),
                "subject": email.get("subject", ""),
                "sender": email.get("sender", ""),
                "has_attachment": email.get("has_attachment", False),
                "difficulty": email.get("metadata", {}).get("difficulty", "medium"),
                "keywords": email.get("metadata", {}).get("keywords", [])
            }
        }
        
        questions.append(question)
    
    return questions


def main():
    """Main function to generate RAG dataset."""
    # Load dummy emails
    emails_path = Path(__file__).parent.parent / "dummy_emails.json"
    print(f"Loading emails from {emails_path}...")
    
    with open(emails_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    emails = data.get("emails", [])
    print(f"Loaded {len(emails)} emails")
    
    # Connect to Qdrant
    client = connect_to_qdrant()
    
    # Test embedding model connection
    print(f"Using embedding model: {EMBEDDING_MODEL} via Ollama at {OLLAMA_BASE_URL}")
    
    # Process emails
    questions = process_emails(emails, client)
    
    # Create dataset
    dataset = {
        "name": "HTWG Email RAG Dataset",
        "description": "RAG benchmark dataset generated from internship office emails with context from HTWG knowledge base",
        "metadata": {
            "domain": "university_internship_office",
            "language": "de",
            "created_for": "rag_benchmark",
            "source": "dummy_emails.json",
            "qdrant_collection": COLLECTION_NAME,
            "generated_at": datetime.now().isoformat(),
            "total_questions": len(questions),
            "categories": {
                "contract_submission": sum(1 for q in questions if q["metadata"]["category"] == "contract_submission"),
                "international_office_question": sum(1 for q in questions if q["metadata"]["category"] == "international_office_question"),
                "internship_postponement": sum(1 for q in questions if q["metadata"]["category"] == "internship_postponement"),
                "uncategorized": sum(1 for q in questions if q["metadata"]["category"] == "uncategorized"),
            }
        },
        "questions": questions
    }
    
    # Save dataset
    output_path = Path(__file__).parent.parent / OUTPUT_FILE
    print(f"\nSaving dataset to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("RAG Dataset Generation Complete")
    print(f"{'='*60}")
    print(f"  Total questions: {len(questions)}")
    print(f"  Output file: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
