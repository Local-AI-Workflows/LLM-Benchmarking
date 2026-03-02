#!/usr/bin/env python3
"""
Script to initialize RAG metrics in the database.

This script creates the default RAG evaluation metrics in MongoDB
so they can be selected in the frontend for RAG benchmarks.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import Database
from database.metric_repository import MetricRepository
from database.models import MetricDocument, MetricType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# RAG Metric definitions
RAG_METRICS = [
    {
        "name": "faithfulness",
        "type": MetricType.RAG,
        "description": "Measures if the response stays true to the retrieved context without hallucination",
        "evaluation_instructions": """
Evaluate the FAITHFULNESS of the response. Faithfulness measures whether the response:
- Only uses information from the provided context
- Does NOT hallucinate or make up facts not present in the context
- Correctly represents information from the context without distortion

Scoring guide:
- 5: Completely faithful - all claims are supported by the context
- 4: Mostly faithful - minor unsupported claims that don't affect accuracy
- 3: Partially faithful - some unsupported claims but core information is correct
- 2: Mostly unfaithful - significant unsupported or contradicting claims
- 1: Completely unfaithful - response contradicts context or is entirely fabricated
""",
        "scale_min": 1,
        "scale_max": 5,
        "enabled": True,
        "metadata": {"category": "rag", "icon": "mdi-shield-check"}
    },
    {
        "name": "relevance",
        "type": MetricType.RAG,
        "description": "Measures if the response directly answers the user's question",
        "evaluation_instructions": """
Evaluate the RELEVANCE of the response. Relevance measures whether the response:
- Directly addresses the user's query
- Provides information that is useful for answering the question
- Stays on topic without unnecessary tangents

Scoring guide:
- 5: Highly relevant - directly and completely answers the question
- 4: Mostly relevant - answers the question with minor off-topic content
- 3: Partially relevant - partially addresses the question
- 2: Mostly irrelevant - only tangentially related to the question
- 1: Completely irrelevant - does not address the question at all
""",
        "scale_min": 1,
        "scale_max": 5,
        "enabled": True,
        "metadata": {"category": "rag", "icon": "mdi-target"}
    },
    {
        "name": "language_quality",
        "type": MetricType.RAG,
        "description": "Measures clarity, structure, and professionalism of the response",
        "evaluation_instructions": """
Evaluate the LANGUAGE QUALITY of the response. Language quality measures:
- Clarity: Is the response easy to understand?
- Structure: Is the response well-organized?
- Professionalism: Is the tone appropriate and professional?
- Readability: Can the reader easily follow the response?

Scoring guide:
- 5: Excellent - clear, well-structured, highly professional
- 4: Good - mostly clear and professional with minor issues
- 3: Adequate - understandable but could be improved
- 2: Poor - confusing, poorly structured, or unprofessional
- 1: Very poor - incomprehensible or highly unprofessional
""",
        "scale_min": 1,
        "scale_max": 5,
        "enabled": True,
        "metadata": {"category": "rag", "icon": "mdi-text-box-check"}
    },
    {
        "name": "grammatical_correctness",
        "type": MetricType.RAG,
        "description": "Measures grammatical correctness, spelling, and ease of understanding",
        "evaluation_instructions": """
Evaluate the GRAMMATICAL CORRECTNESS of the response. This includes:
- Grammar: Are there grammatical errors?
- Spelling: Are words spelled correctly?
- Punctuation: Is punctuation used correctly?
- Simplicity: Is the language clear and easy to understand?
- Sentence structure: Are sentences well-formed and not overly complex?

Scoring guide:
- 5: Perfect - no errors, clear and simple language
- 4: Very good - minor errors that don't affect understanding
- 3: Acceptable - some errors but still understandable
- 2: Poor - multiple errors that make reading difficult
- 1: Very poor - many errors, hard to understand
""",
        "scale_min": 1,
        "scale_max": 5,
        "enabled": True,
        "metadata": {"category": "rag", "icon": "mdi-spellcheck"}
    },
    {
        "name": "overall_rag_score",
        "type": MetricType.RAG,
        "description": "Overall evaluation combining faithfulness, relevance, and language quality",
        "evaluation_instructions": """
Provide an OVERALL evaluation of the RAG response quality considering:
1. Faithfulness: Does the response stay true to the context?
2. Relevance: Does the response answer the question?
3. Language Quality: Is the response well-written and clear?
4. Grammar: Is the response grammatically correct and easy to understand?

Give a holistic score considering all these factors.

Scoring guide:
- 5: Excellent - outstanding on all dimensions
- 4: Good - strong on most dimensions with minor weaknesses
- 3: Adequate - acceptable but with room for improvement
- 2: Below average - significant issues in multiple dimensions
- 1: Poor - fails on most or all dimensions
""",
        "scale_min": 1,
        "scale_max": 5,
        "enabled": True,
        "metadata": {"category": "rag", "icon": "mdi-star"}
    }
]


async def init_rag_metrics():
    """Initialize RAG metrics in the database."""
    logger.info("Connecting to database...")
    await Database.connect()
    
    repo = MetricRepository()
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for metric_data in RAG_METRICS:
        metric_name = metric_data["name"]
        
        # Check if metric already exists
        existing = await repo.get_by_name(metric_name)
        
        if existing:
            # Check if it's the same type
            if existing.type == MetricType.RAG:
                logger.info(f"RAG metric '{metric_name}' already exists, updating...")
                # Update the metric
                await repo.update(str(existing.id), {
                    "description": metric_data["description"],
                    "evaluation_instructions": metric_data["evaluation_instructions"],
                    "scale_min": metric_data["scale_min"],
                    "scale_max": metric_data["scale_max"],
                    "metadata": metric_data["metadata"],
                    "updated_at": datetime.utcnow()
                })
                updated_count += 1
            else:
                logger.warning(
                    f"Metric '{metric_name}' exists but with different type "
                    f"({existing.type} instead of {MetricType.RAG}). Skipping."
                )
                skipped_count += 1
        else:
            # Create new metric
            logger.info(f"Creating RAG metric '{metric_name}'...")
            metric_doc = MetricDocument(**metric_data)
            await repo.create(metric_doc)
            created_count += 1
    
    await Database.disconnect()
    
    logger.info(f"\n{'='*50}")
    logger.info(f"RAG Metrics Initialization Complete")
    logger.info(f"{'='*50}")
    logger.info(f"  Created: {created_count}")
    logger.info(f"  Updated: {updated_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info(f"{'='*50}\n")


async def list_rag_metrics():
    """List all RAG metrics in the database."""
    await Database.connect()
    repo = MetricRepository()
    
    metrics = await repo.get_all(metric_type=MetricType.RAG)
    
    print(f"\nRAG Metrics in Database ({len(metrics)} total):")
    print("-" * 50)
    for metric in metrics:
        status = "✓ enabled" if metric.enabled else "✗ disabled"
        print(f"  {metric.name:30} [{status}]")
    print("-" * 50)
    
    await Database.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_rag_metrics())
    else:
        asyncio.run(init_rag_metrics())
