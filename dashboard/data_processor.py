"""
Data processor for preparing benchmark results for dashboard visualization.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from metrics.responses import BenchmarkResult
from datetime import datetime
import json


class DashboardDataProcessor:
    """Processes benchmark results for dashboard visualization."""
    
    def __init__(self, benchmark_result: BenchmarkResult):
        """
        Initialize the data processor.
        
        Args:
            benchmark_result: The benchmark result to process
        """
        self.benchmark_result = benchmark_result
        self.processed_data = {}
        self._process_all_data()
    
    def _process_all_data(self):
        """Process all data needed for the dashboard."""
        self.processed_data = {
            'overview': self._get_overview_data(),
            'metrics': self._get_metrics_data(),
            'questions': self._get_questions_data(),
            'evaluators': self._get_evaluators_data(),
            'correlations': self._get_correlation_data(),
            'raw_scores': self._get_raw_scores_data(),
            'metadata': self._get_metadata()
        }
    
    def _get_overview_data(self) -> Dict[str, Any]:
        """Get overview statistics for the dashboard."""
        avg_scores = self.benchmark_result.get_average_scores_by_metric()
        summary = self.benchmark_result.get_summary_statistics()
        
        return {
            'overall_score': summary['overall_average'],
            'num_questions': summary['num_prompts'],
            'num_metrics': summary['num_metrics'],
            'num_evaluators': len(summary['evaluator_models']),
            'model_name': summary['model_name'],
            'metrics_scores': avg_scores,
            'score_distribution': summary.get('score_distribution', {}),
            'evaluator_models': summary['evaluator_models']
        }
    
    def _get_metrics_data(self) -> List[Dict[str, Any]]:
        """Get detailed metrics data."""
        metrics_data = []
        avg_scores = self.benchmark_result.get_average_scores_by_metric()
        
        for metric_name, avg_score in avg_scores.items():
            # Get all scores for this metric
            all_scores = []
            for evaluation in self.benchmark_result.prompt_evaluations:
                for eval_result in evaluation.evaluations:
                    if eval_result.metric_name == metric_name:
                        all_scores.append(eval_result.score)
            
            metrics_data.append({
                'name': metric_name,
                'average_score': avg_score,
                'min_score': min(all_scores) if all_scores else 0,
                'max_score': max(all_scores) if all_scores else 0,
                'std_dev': np.std(all_scores) if all_scores else 0,
                'count': len(all_scores)
            })
        
        return metrics_data
    
    def _get_questions_data(self) -> List[Dict[str, Any]]:
        """Get question-level analysis data."""
        questions_data = []
        
        for i, evaluation in enumerate(self.benchmark_result.prompt_evaluations):
            # Calculate average score for this question across all metrics
            all_scores = []
            metric_scores = {}
            
            for eval_result in evaluation.evaluations:
                all_scores.append(eval_result.score)
                metric_scores[eval_result.metric_name] = eval_result.score
            
            avg_score = np.mean(all_scores) if all_scores else 0
            
            # Determine difficulty level
            if avg_score >= 8:
                difficulty = "Easy"
            elif avg_score >= 6:
                difficulty = "Medium"
            elif avg_score >= 4:
                difficulty = "Hard"
            else:
                difficulty = "Very Hard"
            
            questions_data.append({
                'id': i + 1,
                'text': evaluation.prompt[:100] + ("..." if len(evaluation.prompt) > 100 else ""),
                'full_text': evaluation.prompt,
                'response': evaluation.response[:200] + ("..." if len(evaluation.response) > 200 else ""),
                'full_response': evaluation.response,
                'average_score': avg_score,
                'difficulty': difficulty,
                'metric_scores': metric_scores,
                'num_metrics': len(metric_scores)
            })
        
        # Sort by difficulty (hardest first)
        questions_data.sort(key=lambda x: x['average_score'])
        
        return questions_data
    
    def _get_evaluators_data(self) -> List[Dict[str, Any]]:
        """Get evaluator-level analysis data."""
        evaluators_data = []
        evaluator_models = self.benchmark_result.metadata.get("evaluator_models", [])
        
        # If no evaluator models in metadata, try to extract from individual responses
        if not evaluator_models:
            evaluator_set = set()
            for evaluation in self.benchmark_result.prompt_evaluations:
                for eval_result in evaluation.evaluations:
                    for individual in eval_result.individual_responses:
                        evaluator_set.add(individual.model_name)
            evaluator_models = list(evaluator_set)
        
        for evaluator_name in evaluator_models:
            # Get all scores from this evaluator
            evaluator_scores = []
            metric_scores = {}
            
            for evaluation in self.benchmark_result.prompt_evaluations:
                for eval_result in evaluation.evaluations:
                    for individual in eval_result.individual_responses:
                        if individual.model_name == evaluator_name:
                            evaluator_scores.append(individual.score)
                            
                            if eval_result.metric_name not in metric_scores:
                                metric_scores[eval_result.metric_name] = []
                            metric_scores[eval_result.metric_name].append(individual.score)
            
            # Only add evaluator if we found scores
            if evaluator_scores:
                # Calculate statistics
                avg_score = np.mean(evaluator_scores)
                
                # Calculate per-metric averages
                metric_averages = {}
                for metric, scores in metric_scores.items():
                    metric_averages[metric] = np.mean(scores) if scores else 0
                
                evaluators_data.append({
                    'name': evaluator_name,
                    'average_score': avg_score,
                    'total_evaluations': len(evaluator_scores),
                    'std_dev': np.std(evaluator_scores),
                    'min_score': min(evaluator_scores),
                    'max_score': max(evaluator_scores),
                    'metric_averages': metric_averages
                })
        
        return evaluators_data
    
    def _get_correlation_data(self) -> Dict[str, Any]:
        """Get metric correlation data."""
        from scipy.stats import pearsonr
        
        metrics = self.benchmark_result.metadata["metrics"]
        metric_scores = {}
        
        # Collect all scores for each metric
        for metric in metrics:
            scores = []
            for evaluation in self.benchmark_result.prompt_evaluations:
                for eval_result in evaluation.evaluations:
                    if eval_result.metric_name == metric:
                        scores.append(eval_result.score)
            metric_scores[metric] = scores
        
        # Calculate correlation matrix
        correlation_matrix = {}
        for metric1 in metrics:
            correlation_matrix[metric1] = {}
            for metric2 in metrics:
                if metric1 == metric2:
                    correlation_matrix[metric1][metric2] = 1.0
                else:
                    scores1 = metric_scores[metric1]
                    scores2 = metric_scores[metric2]
                    if len(scores1) == len(scores2) and len(scores1) > 1:
                        corr, p_value = pearsonr(scores1, scores2)
                        correlation_matrix[metric1][metric2] = {
                            'correlation': corr,
                            'p_value': p_value,
                            'significant': p_value < 0.05
                        }
                    else:
                        correlation_matrix[metric1][metric2] = {
                            'correlation': 0.0,
                            'p_value': 1.0,
                            'significant': False
                        }
        
        return {
            'matrix': correlation_matrix,
            'metrics': metrics
        }
    
    def _get_raw_scores_data(self) -> List[Dict[str, Any]]:
        """Get raw scores data for detailed analysis."""
        raw_data = []
        
        for i, evaluation in enumerate(self.benchmark_result.prompt_evaluations):
            for eval_result in evaluation.evaluations:
                for individual in eval_result.individual_responses:
                    raw_data.append({
                        'question_id': i + 1,
                        'question_text': evaluation.prompt,
                        'metric': eval_result.metric_name,
                        'evaluator': individual.model_name,
                        'score': individual.score,
                        'rationale': individual.rationale
                    })
        
        return raw_data
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the benchmark."""
        metadata = self.benchmark_result.metadata.copy()
        
        # Add processing timestamp
        metadata['processed_at'] = datetime.now().isoformat()
        
        # Add data statistics
        metadata['data_stats'] = {
            'total_evaluations': len(self._get_raw_scores_data()),
            'unique_questions': len(self.benchmark_result.prompt_evaluations),
            'unique_metrics': len(set(self.benchmark_result.metadata.get("metrics", []))),
            'unique_evaluators': len(set(self.benchmark_result.metadata.get("evaluator_models", [])))
        }
        
        return metadata
    
    def get_question_detail(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific question."""
        if question_id < 1 or question_id > len(self.benchmark_result.prompt_evaluations):
            return None
        
        evaluation = self.benchmark_result.prompt_evaluations[question_id - 1]
        
        # Get all scores and rationales for this question
        scores_by_metric = {}
        evaluator_details = {}
        
        for eval_result in evaluation.evaluations:
            metric_name = eval_result.metric_name
            scores_by_metric[metric_name] = {
                'average_score': eval_result.score,
                'rationale': eval_result.rationale,
                'individual_scores': []
            }
            
            for individual in eval_result.individual_responses:
                scores_by_metric[metric_name]['individual_scores'].append({
                    'evaluator': individual.model_name,
                    'score': individual.score,
                    'rationale': individual.rationale
                })
                
                if individual.model_name not in evaluator_details:
                    evaluator_details[individual.model_name] = {}
                evaluator_details[individual.model_name][metric_name] = {
                    'score': individual.score,
                    'rationale': individual.rationale
                }
        
        return {
            'id': question_id,
            'prompt': evaluation.prompt,
            'response': evaluation.response,
            'scores_by_metric': scores_by_metric,
            'evaluator_details': evaluator_details,
            'overall_average': np.mean([eval_result.score for eval_result in evaluation.evaluations])
        }
    
    def get_metric_detail(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific metric."""
        if metric_name not in self.benchmark_result.metadata.get("metrics", []):
            return None
        
        # Get all scores for this metric
        all_scores = []
        question_scores = []
        evaluator_scores = {}
        
        for i, evaluation in enumerate(self.benchmark_result.prompt_evaluations):
            for eval_result in evaluation.evaluations:
                if eval_result.metric_name == metric_name:
                    all_scores.append(eval_result.score)
                    question_scores.append({
                        'question_id': i + 1,
                        'question_text': evaluation.prompt[:50] + "...",
                        'score': eval_result.score,
                        'rationale': eval_result.rationale[:100] + ("..." if len(eval_result.rationale) > 100 else "")
                    })
                    
                    for individual in eval_result.individual_responses:
                        evaluator_name = individual.model_name
                        if evaluator_name not in evaluator_scores:
                            evaluator_scores[evaluator_name] = []
                        evaluator_scores[evaluator_name].append(individual.score)
        
        # Calculate statistics
        return {
            'name': metric_name,
            'average_score': np.mean(all_scores) if all_scores else 0,
            'std_dev': np.std(all_scores) if all_scores else 0,
            'min_score': min(all_scores) if all_scores else 0,
            'max_score': max(all_scores) if all_scores else 0,
            'total_evaluations': len(all_scores),
            'question_scores': question_scores,
            'evaluator_averages': {
                evaluator: np.mean(scores) for evaluator, scores in evaluator_scores.items()
            },
            'score_distribution': {
                'excellent': len([s for s in all_scores if s >= 9]),
                'good': len([s for s in all_scores if 7 <= s < 9]),
                'fair': len([s for s in all_scores if 5 <= s < 7]),
                'poor': len([s for s in all_scores if s < 5])
            }
        }
    
    def to_json(self) -> str:
        """Convert processed data to JSON string."""
        return json.dumps(self.processed_data, indent=2, default=str) 