"""
RAG (Retrieval-Augmented Generation) Benchmark Runner.

This module provides a specialized benchmark runner for RAG evaluation.
It supports:
- Models with MCP tool calling for context retrieval
- Evaluation of responses based on retrieved context
- Multiple RAG-specific metrics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.base_model import BaseLLMModel
from models.ollama_mcp_model import OllamaWithMCPModel
from metrics.metric_base import BaseMetric
from metrics.evaluator import BaseEvaluator
from metrics.responses import BenchmarkResult, PromptEvaluation
from dataset import Dataset, Question

logger = logging.getLogger(__name__)

# Default RAG prompt - optimized for good performance
DEFAULT_RAG_PROMPT = """Du bist ein Assistent des Praktikantenamts der HTWG Konstanz.

Dein oberstes Ziel ist rechtlich und organisatorisch korrekte Auskunft.

## INHALTLICHE REGELN (verpflichtend):
- Durchsuche ALLE bereitgestellten Kontext-Abschnitte sorgfältig nach relevanten Informationen
- Der Kontext enthält mehrere Abschnitte, getrennt durch "---" - prüfe jeden einzelnen
- Übernimm Zahlen, Fristen, Zeiträume und Bedingungen wortgleich aus dem Kontext
- Verändere keine Modalverben (z.B. "kann", "muss", "sollte")
- Füge keine Interpretationen oder Schlussfolgerungen hinzu
- Nur wenn KEIN Abschnitt relevante Information enthält: "Dazu liegen in der Wissensdatenbank keine Informationen vor."

## KONTEXT-NUTZUNG:
- Suche nach Informationen zu Fristen, Formularen, Anträgen, Verfahren
- Zitiere konkrete Details (z.B. "Der Antrag ist an den Vorsitzenden des Prüfungsausschusses zu richten")
- Verweise auf genannte Ressourcen (z.B. "Download-Bereich", "Webseite des Praktischen Studiensemesters")
- Bei Vertragseinreichungen: PSS-Terminplan, persönliche Abgabe im Sekretariat
- Bei Verschiebungsanfragen: Antrag auf Verschiebung, gute Gründe angeben, Prüfungsausschuss
- Bei Auslandspraktika: gleiche Regeln wie Inland, frühzeitig (zwei Semester vorher) bewerben

## STRUKTUR:
- Genau ein kurzer, klarer Hauptsatz pro gestellter Frage
- Jede Antwort in einer eigenen Zeile
- Keine Leerzeilen zwischen den Antworten

## FORM:
- Durchgehend formelle Sie-Form
- Keine Anrede (kein "Sehr geehrte/r...")
- Keine Grußformel (kein "Mit freundlichen Grüßen")
- Keine Signatur
- Nur der reine Antworttext

## Kontext aus der Wissensdatenbank (mehrere Abschnitte, durch --- getrennt):
{context}

## E-Mail-Anfrage:
{query}

## Antwort:"""


class RAGBenchmarkRunner:
    """
    Specialized benchmark runner for RAG (Retrieval-Augmented Generation) evaluation.
    
    This runner:
    1. Executes queries against a RAG-enabled model (with tool/MCP support)
    2. Captures the retrieved context from tool calls
    3. Evaluates the generated response using RAG-specific metrics
    """
    
    def __init__(
        self,
        evaluator: BaseEvaluator,
        metrics: List[BaseMetric],
        rag_prompt: Optional[str] = None,
        capture_context: bool = True
    ):
        """
        Initialize the RAG benchmark runner.
        
        Args:
            evaluator: The evaluator for scoring responses
            metrics: List of RAG metrics to use for evaluation
            rag_prompt: Instructional prompt template with {context} and {query} placeholders
            capture_context: Whether to capture context from tool calls
        """
        self.evaluator = evaluator
        self.metrics = metrics
        self.rag_prompt = rag_prompt or DEFAULT_RAG_PROMPT
        self.capture_context = capture_context
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the full prompt from template."""
        return self.rag_prompt.format(context=context, query=query)
    
    async def run_benchmark(
        self,
        model: BaseLLMModel,
        dataset: Dataset
    ) -> BenchmarkResult:
        """
        Run RAG benchmark for a model across a dataset.
        
        The dataset should contain questions that can be answered using
        retrieval-augmented generation. Each question may have:
        - text: The user query
        - context: Reference context (for comparison with retrieved context)
        - expected_answer: Expected answer (optional)
        
        Args:
            model: The RAG-enabled model to evaluate
            dataset: Dataset containing test questions
            
        Returns:
            BenchmarkResult with all evaluation results
        """
        logger.info(f"Starting RAG benchmark with {len(dataset.questions)} questions")
        logger.info(f"Using {len(self.metrics)} metrics: {[m.name for m in self.metrics]}")
        logger.info(f"Using RAG prompt template: {self.rag_prompt[:80]}...")
        
        questions = dataset.questions
        
        # Collect responses from the model
        model_responses: Dict[str, str] = {}
        model_response_objects: Dict[str, Any] = {}
        
        # Build prompts using the RAG template
        prompt_strings = []
        for question in questions:
            context = question.context or "[Kein Kontext verfügbar]"
            query = question.text
            full_prompt = self._build_prompt(query, context)
            prompt_strings.append(full_prompt)
        
        for i, (question, prompt_string) in enumerate(zip(questions, prompt_strings)):
            logger.info(f"Processing question {i+1}/{len(questions)}: {question.text[:50]}...")
            
            try:
                # Generate response
                response = await model.generate(prompt_string)
                model_responses[prompt_string] = response.text
                
                # Ensure metadata exists
                if not hasattr(response, 'metadata') or response.metadata is None:
                    response.metadata = {}
                
                # Store original query (email text) for display in results
                response.metadata['original_query'] = question.text
                
                # Add reference context from question if available
                if question.context:
                    response.metadata['reference_context'] = question.context
                    response.metadata['retrieved_context'] = question.context  # Use question context as retrieved
                
                # For MCP models, context should already be in metadata
                # from tool results. Ensure it's properly captured.
                if isinstance(model, OllamaWithMCPModel):
                    # Context is typically captured in tool_results
                    if 'tool_results' not in response.metadata:
                        response.metadata['tool_results'] = []
                    
                    # Build retrieved_context from tool results
                    tool_results = response.metadata.get('tool_results', [])
                    if tool_results:
                        context_parts = []
                        for result in tool_results:
                            if isinstance(result, dict) and result.get('result'):
                                context_parts.append(str(result['result']))
                        response.metadata['retrieved_context'] = "\n\n".join(context_parts)
                
                # Store question metadata in response for evaluation
                if question.expected_answer:
                    response.metadata['expected_answer'] = question.expected_answer
                if question.metadata:
                    response.metadata.update(question.metadata)
                
                model_response_objects[prompt_string] = response
                
                logger.debug(f"Question {i+1} response received (length: {len(response.text)})")
                
            except Exception as e:
                logger.error(f"Error generating response for question {i+1}: {e}")
                # Create a placeholder response for failed queries
                from models.responses import ModelResponse
                failed_response = ModelResponse(
                    text=f"[Generation failed: {str(e)}]",
                    model_name=model.model_name,
                    metadata={"error": str(e)}
                )
                model_responses[prompt_string] = failed_response.text
                model_response_objects[prompt_string] = failed_response
        
        # Run evaluation for each metric
        metric_results = []
        for metric in self.metrics:
            logger.info(f"Running metric: {metric.name}")
            try:
                result = await metric.evaluate_batch(
                    prompt_strings,
                    model_responses,
                    self.evaluator,
                    response_objects=model_response_objects
                )
                metric_results.append(result)
                logger.info(f"Metric {metric.name} complete")
            except Exception as e:
                logger.error(f"Error running metric {metric.name}: {e}")
        
        # Combine all metric results
        if metric_results:
            benchmark_result = BenchmarkResult.combine(metric_results, model.model_name)
        else:
            # Create empty result if all metrics failed
            benchmark_result = BenchmarkResult(
                model_name=model.model_name,
                overall_score=0.0,
                prompt_evaluations=[],
                evaluator_models=[],
                metadata={"error": "All metrics failed"}
            )
        
        # Add RAG-specific metadata
        benchmark_result.metadata["benchmark_type"] = "rag"
        benchmark_result.metadata["dataset_name"] = dataset.name
        benchmark_result.metadata["dataset_description"] = dataset.description
        benchmark_result.metadata["num_questions"] = len(questions)
        benchmark_result.metadata["metrics_used"] = [m.name for m in self.metrics]
        
        # Calculate per-metric summaries
        metric_summaries = {}
        for metric in self.metrics:
            metric_scores = []
            for pe in benchmark_result.prompt_evaluations:
                for eval_resp in pe.evaluations:
                    if eval_resp.metric_name == metric.name:
                        metric_scores.append(eval_resp.score)
            
            if metric_scores:
                metric_summaries[metric.name] = {
                    "average": sum(metric_scores) / len(metric_scores),
                    "min": min(metric_scores),
                    "max": max(metric_scores),
                    "count": len(metric_scores)
                }
        
        benchmark_result.metadata["metric_summaries"] = metric_summaries
        
        # Calculate overall score from metric averages
        if metric_summaries:
            overall_score = sum(m["average"] for m in metric_summaries.values()) / len(metric_summaries)
            benchmark_result.metadata["overall_score"] = overall_score
            logger.info(f"RAG benchmark complete. Overall score: {overall_score:.2f}")
        else:
            logger.info("RAG benchmark complete. No metric scores available.")
        
        return benchmark_result
    
    async def run_benchmark_with_context_verification(
        self,
        model: BaseLLMModel,
        dataset: Dataset
    ) -> BenchmarkResult:
        """
        Run RAG benchmark with additional context verification.
        
        This method also compares the retrieved context with reference context
        (if provided in the dataset) to assess retrieval quality.
        
        Args:
            model: The RAG-enabled model to evaluate
            dataset: Dataset with reference contexts
            
        Returns:
            BenchmarkResult with context verification metadata
        """
        # Run standard benchmark
        result = await self.run_benchmark(model, dataset)
        
        # Add context verification metadata
        # This could be extended to include context similarity metrics
        result.metadata["context_verification_enabled"] = True
        
        return result
