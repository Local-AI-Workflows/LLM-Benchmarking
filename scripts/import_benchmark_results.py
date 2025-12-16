"""Script to import existing benchmark results from JSON files into MongoDB."""

import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import Database
from database.repository import BenchmarkRepository
from database.models import BenchmarkDocument, BenchmarkStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_metadata_from_result(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract benchmark metadata from result data."""
    metadata = result_data.get('metadata', {})
    
    # Extract model name
    model_name = metadata.get('model_name', 'unknown')
    
    # Extract dataset name
    dataset_name = metadata.get('dataset_name', 'Unknown Dataset')
    
    # Extract metrics
    metrics = metadata.get('metrics', [])
    if not metrics:
        # Try to extract from prompt_evaluations
        metrics = set()
        for pe in result_data.get('prompt_evaluations', []):
            for evaluation in pe.get('evaluations', []):
                metric_name = evaluation.get('metric_name')
                if metric_name:
                    metrics.add(metric_name)
        metrics = list(metrics)
    
    # Extract evaluator models
    evaluator_models = metadata.get('evaluator_models', [])
    if not evaluator_models:
        # Try to extract from evaluations
        evaluator_models = set()
        for pe in result_data.get('prompt_evaluations', []):
            for evaluation in pe.get('evaluations', []):
                for ir in evaluation.get('individual_responses', []):
                    model = ir.get('model_name')
                    if model and model != 'multi-evaluator':
                        evaluator_models.add(model)
        evaluator_models = list(evaluator_models)
    
    # Determine metric type based on metric names
    metric_type = None
    mcp_metrics = ['tool_usage_accuracy', 'information_retrieval_quality', 
                   'contextual_awareness', 'tool_selection_efficiency']
    if any(m in metrics for m in mcp_metrics):
        metric_type = 'mcp'
    else:
        metric_type = 'standard'
    
    # Try to extract timestamp from filename
    created_at = None
    
    return {
        'model_name': model_name,
        'dataset_name': dataset_name,
        'metrics': metrics,
        'metric_type': metric_type,
        'evaluator_models': evaluator_models,
        'created_at': created_at
    }


def parse_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """Try to extract timestamp from filename like benchmark_results_20250629_215947.json."""
    try:
        # Look for pattern: YYYYMMDD_HHMMSS in filename
        # Examples: benchmark_results_20250629_215947.json
        #          weather_mcp_mistral_latest_20251026_184250.json
        stem = Path(filename).stem
        parts = stem.split('_')
        
        # Look for consecutive parts that form YYYYMMDD_HHMMSS
        for i in range(len(parts) - 1):
            date_part = parts[i]
            time_part = parts[i + 1]
            
            # Check if date_part is 8 digits (YYYYMMDD) and time_part is 6 digits (HHMMSS)
            if len(date_part) == 8 and date_part.isdigit() and \
               len(time_part) == 6 and time_part.isdigit():
                timestamp_str = f"{date_part}_{time_part}"
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    except Exception as e:
        logger.debug(f"Could not parse timestamp from filename {filename}: {e}")
    return None


async def import_result_file(
    file_path: Path,
    repository: BenchmarkRepository,
    dry_run: bool = False
) -> Optional[str]:
    """Import a single result file into the database."""
    try:
        logger.info(f"Processing: {file_path}")
        
        # Load JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Validate structure
        if 'prompt_evaluations' not in result_data:
            logger.warning(f"Skipping {file_path}: Missing 'prompt_evaluations'")
            return None
        
        if 'metadata' not in result_data:
            logger.warning(f"Skipping {file_path}: Missing 'metadata'")
            return None
        
        # Extract metadata
        extracted = extract_metadata_from_result(result_data)
        
        # Try to get timestamp from filename
        timestamp = parse_timestamp_from_filename(file_path.name)
        if timestamp:
            extracted['created_at'] = timestamp
        
        # Create benchmark document
        benchmark = BenchmarkDocument(
            status=BenchmarkStatus.COMPLETED,
            model_name=extracted['model_name'],
            dataset_name=extracted['dataset_name'],
            metrics=extracted['metrics'],
            metric_type=extracted['metric_type'],
            evaluator_models=extracted['evaluator_models'],
            result_data=result_data,
            created_at=extracted['created_at'] or datetime.utcnow(),
            completed_at=extracted['created_at'] or datetime.utcnow(),
            started_at=extracted['created_at'] or datetime.utcnow()
        )
        
        if dry_run:
            logger.info(f"[DRY RUN] Would import: {file_path.name}")
            logger.info(f"  Model: {benchmark.model_name}")
            logger.info(f"  Dataset: {benchmark.dataset_name}")
            logger.info(f"  Metrics: {', '.join(benchmark.metrics)}")
            logger.info(f"  Type: {benchmark.metric_type}")
            logger.info(f"  Evaluators: {', '.join(benchmark.evaluator_models)}")
            return None
        
        # Check if benchmark with same characteristics already exists
        # (optional: you might want to skip duplicates)
        benchmark_id = await repository.create(benchmark)
        logger.info(f"✓ Imported {file_path.name} as benchmark {benchmark_id}")
        return benchmark_id
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to import {file_path}: {e}", exc_info=True)
        return None


async def find_result_files(results_dir: Path) -> List[Path]:
    """Find all JSON result files in the results directory."""
    result_files = []
    
    # Find JSON files in root results directory
    for json_file in results_dir.glob("*.json"):
        # Skip non-benchmark files (like dashboard HTML exports)
        if json_file.name.startswith("benchmark_results") or \
           json_file.name.startswith("demo_benchmark") or \
           json_file.name.startswith("weather_mcp") or \
           json_file.name.startswith("mcp_benchmark"):
            result_files.append(json_file)
    
    # Find JSON files in subdirectories
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            for json_file in subdir.glob("*.json"):
                result_files.append(json_file)
    
    return sorted(result_files)


async def main():
    """Main function to import benchmark results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import benchmark results from JSON files")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory containing benchmark result JSON files (default: results)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that appear to already be imported (by checking model/dataset/metrics)"
    )
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        return 1
    
    logger.info(f"Scanning for benchmark results in: {results_dir}")
    
    # Find all result files
    result_files = await find_result_files(results_dir)
    
    if not result_files:
        logger.warning(f"No benchmark result files found in {results_dir}")
        return 1
    
    logger.info(f"Found {len(result_files)} result file(s)")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be imported")
    
    # Connect to database
    await Database.connect()
    try:
        repository = BenchmarkRepository()
        
        imported = 0
        skipped = 0
        failed = 0
        
        for result_file in result_files:
            benchmark_id = await import_result_file(
                result_file,
                repository,
                dry_run=args.dry_run
            )
            
            if benchmark_id:
                imported += 1
            elif args.dry_run:
                imported += 1  # Count as imported in dry run
            else:
                failed += 1
        
        logger.info("\n" + "="*60)
        logger.info("IMPORT SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files: {len(result_files)}")
        if args.dry_run:
            logger.info(f"Would import: {imported}")
        else:
            logger.info(f"Imported: {imported}")
            logger.info(f"Failed: {failed}")
        logger.info("="*60)
        
        return 0 if failed == 0 else 1
        
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

