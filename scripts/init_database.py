"""Script to initialize the database with current metrics and datasets."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import Database
from database.metric_repository import MetricRepository
from database.dataset_repository import DatasetRepository
from database.models import MetricDocument, DatasetDocument, MetricType
from metrics import get_all_metrics, get_metric_by_name
from metrics.metric_factory import MetricFactory
from dataset import DatasetLoader, Dataset
from dataset.question import Question
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Metric registry mapping
METRIC_REGISTRY = {
    # Standard metrics
    'relevance': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.relevance.RelevanceMetric',
        'description': 'Measures how well the response addresses the prompt\'s requirements and stays on topic'
    },
    'hallucinations': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.hallucinations.HallucinationsMetric',
        'description': 'Measures the extent to which the response contains fabricated or incorrect information'
    },
    'fairness': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.fairness.FairnessMetric',
        'description': 'Measures fairness and lack of bias in the response'
    },
    'robustness': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.robustness.RobustnessMetric',
        'description': 'Measures the robustness and consistency of the response'
    },
    'bias': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.bias.BiasMetric',
        'description': 'Measures the presence of bias in the response'
    },
    'toxicity': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.general.toxicity.ToxicityMetric',
        'description': 'Measures the presence of toxic or harmful content'
    },
    'email_professionalism': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.email.email_professionalism.EmailProfessionalismMetric',
        'description': 'Measures professionalism in email responses'
    },
    'email_responsiveness': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.email.email_responsiveness.EmailResponsivenessMetric',
        'description': 'Measures responsiveness and appropriateness in email responses'
    },
    'email_clarity': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.email.email_clarity.EmailClarityMetric',
        'description': 'Measures clarity and readability in email responses'
    },
    'email_empathy': {
        'type': MetricType.STANDARD,
        'class_path': 'metrics.email.email_empathy.EmailEmpathyMetric',
        'description': 'Measures empathy and emotional intelligence in email responses'
    },
    # MCP metrics
    'tool_usage_accuracy': {
        'type': MetricType.MCP,
        'class_path': 'metrics.mcp.tool_usage_accuracy.ToolUsageAccuracyMetric',
        'description': 'Measures how accurately and appropriately models use available tools'
    },
    'information_retrieval_quality': {
        'type': MetricType.MCP,
        'class_path': 'metrics.mcp.information_retrieval_quality.InformationRetrievalQualityMetric',
        'description': 'Measures the quality of information retrieved through tool usage'
    },
    'contextual_awareness': {
        'type': MetricType.MCP,
        'class_path': 'metrics.mcp.contextual_awareness.ContextualAwarenessMetric',
        'description': 'Measures contextual awareness in tool usage scenarios'
    },
    'tool_selection_efficiency': {
        'type': MetricType.MCP,
        'class_path': 'metrics.mcp.tool_selection_efficiency.ToolSelectionEfficiencyMetric',
        'description': 'Measures efficiency and appropriateness of tool selection strategy'
    }
}


async def init_metrics():
    """Initialize metrics in the database."""
    logger.info("Initializing metrics...")
    repo = MetricRepository()
    
    # Get all available metrics from code
    available_metrics = get_all_metrics()
    
    count = 0
    for metric_name in available_metrics:
        metric_doc = None
        
        if metric_name in METRIC_REGISTRY:
            metric_info = METRIC_REGISTRY[metric_name]
            # Create metric instance to extract configuration
            try:
                metric_instance = MetricFactory.create_metric(metric_name)
                # Extract configuration from instance
                evaluation_instructions = getattr(metric_instance, 'evaluation_instructions', '')
                scale_min = getattr(metric_instance, 'scale_min', 0)
                scale_max = getattr(metric_instance, 'scale_max', 10)
                custom_format = getattr(metric_instance, 'custom_format', None)
                additional_context = getattr(metric_instance, 'additional_context', None)
                
                metric_doc = MetricDocument(
                    name=metric_name,
                    type=metric_info['type'],
                    description=metric_info['description'],
                    class_path=metric_info['class_path'],
                    enabled=True,
                    evaluation_instructions=evaluation_instructions,
                    scale_min=scale_min,
                    scale_max=scale_max,
                    custom_format=custom_format,
                    additional_context=additional_context
                )
            except Exception as e:
                logger.warning(f"Failed to extract config for {metric_name}: {e}, using defaults")
                metric_doc = MetricDocument(
                    name=metric_name,
                    type=metric_info['type'],
                    description=metric_info['description'],
                    class_path=metric_info['class_path'],
                    enabled=True
                )
        else:
            # Try to get from registry
            metric_class = get_metric_by_name(metric_name)
            if metric_class:
                # Determine type based on module path
                module_path = metric_class.__module__
                metric_type = MetricType.MCP if 'mcp' in module_path else MetricType.STANDARD
                
                # Create instance to extract configuration
                try:
                    metric_instance = MetricFactory.create_metric(metric_name)
                    evaluation_instructions = getattr(metric_instance, 'evaluation_instructions', '')
                    scale_min = getattr(metric_instance, 'scale_min', 0)
                    scale_max = getattr(metric_instance, 'scale_max', 10)
                    custom_format = getattr(metric_instance, 'custom_format', None)
                    additional_context = getattr(metric_instance, 'additional_context', None)
                    
                    metric_doc = MetricDocument(
                        name=metric_name,
                        type=metric_type,
                        description=getattr(metric_class, 'description', ''),
                        class_path=f"{module_path}.{metric_class.__name__}",
                        enabled=True,
                        evaluation_instructions=evaluation_instructions,
                        scale_min=scale_min,
                        scale_max=scale_max,
                        custom_format=custom_format,
                        additional_context=additional_context
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract config for {metric_name}: {e}, using defaults")
                    metric_doc = MetricDocument(
                        name=metric_name,
                        type=metric_type,
                        description=getattr(metric_class, 'description', ''),
                        class_path=f"{module_path}.{metric_class.__name__}",
                        enabled=True
                    )
        
        if metric_doc:
            await repo.upsert_by_name(metric_doc)
            count += 1
            logger.info(f"  ✓ {metric_name} ({metric_doc.type})")
    
    logger.info(f"Initialized {count} metrics")
    return count


async def init_datasets():
    """Initialize default datasets in the database."""
    logger.info("Initializing datasets...")
    repo = DatasetRepository()
    
    # Create default dataset
    default_questions = [
        Question.from_string("What is the capital of France?"),
        Question.from_string("Explain the concept of quantum computing in simple terms."),
        Question.from_string("Write a short poem about artificial intelligence."),
        Question.from_string("If a train travels at 60 mph for 2.5 hours, how far does it go?"),
        Question.from_string("Write a Python function to calculate the Fibonacci sequence.")
    ]
    
    default_dataset = Dataset(
        questions=default_questions,
        name="Default Benchmark Dataset",
        description="Standard test questions for LLM evaluation"
    )
    
    dataset_doc = DatasetDocument(
        name=default_dataset.name,
        description=default_dataset.description,
        questions=[q.to_dict() for q in default_dataset.questions],
        enabled=True,
        metadata=default_dataset.metadata
    )
    
    await repo.upsert_by_name(dataset_doc)
    logger.info(f"  ✓ {default_dataset.name}")
    
    # Try to load weather MCP dataset if it exists
    weather_dataset_path = Path(__file__).parent.parent / "weather_mcp_test_dataset.json"
    if weather_dataset_path.exists():
        try:
            weather_dataset = DatasetLoader.load_from_file(str(weather_dataset_path))
            weather_doc = DatasetDocument(
                name=weather_dataset.name or "Weather MCP Test Dataset",
                description=weather_dataset.description or "Weather-related questions for MCP testing",
                questions=[q.to_dict() for q in weather_dataset.questions],
                enabled=True,
                metadata=weather_dataset.metadata
            )
            await repo.upsert_by_name(weather_doc)
            logger.info(f"  ✓ {weather_doc.name}")
        except Exception as e:
            logger.warning(f"  ✗ Failed to load weather dataset: {e}")
    
    count = await repo.count()
    logger.info(f"Initialized {count} datasets")
    return count


async def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    # Connect to database
    await Database.connect()
    
    try:
        # Initialize metrics
        metric_count = await init_metrics()
        
        # Initialize datasets
        dataset_count = await init_datasets()
        
        logger.info(f"\n✓ Initialization complete!")
        logger.info(f"  - Metrics: {metric_count}")
        logger.info(f"  - Datasets: {dataset_count}")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

