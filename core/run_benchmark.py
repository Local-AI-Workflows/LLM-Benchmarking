import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from models.ollama_model import OllamaModel
from metrics.relevance import RelevanceMetric

class BenchmarkRunner:
    """Main class for running LLM benchmarks."""
    
    def __init__(self, model_name: str = "llama2", output_dir: str = "data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.model = OllamaModel(model_name=model_name)
        self.evaluator = OllamaModel(model_name="deepseek-r1:1.5b")
        self.metrics = [RelevanceMetric()]
    
    async def run_benchmark(self, prompts: List[str], **kwargs) -> Dict[str, Any]:
        """
        Run a benchmark on a list of prompts.
        
        Args:
            prompts: List of prompts to evaluate
            **kwargs: Additional arguments for model generation
            
        Returns:
            Dictionary containing benchmark results
        """
        results = []
        
        for prompt in prompts:
            # Generate response
            response = await self.model.generate(prompt, **kwargs)
            
            # Evaluate metrics
            metric_results = {}
            for metric in self.metrics:
                metric_result = await metric.evaluate(
                    prompt, 
                    response.text,
                    evaluator_model=self.evaluator
                )
                metric_results[metric.name] = metric_result.dict()
            
            # Store results
            result = {
                "prompt": prompt,
                "response": response.text,
                "metadata": response.metadata,
                "metrics": metric_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            results.append(result)
        
        # Save results
        output_file = self.output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        return {
            "results": results,
            "output_file": str(output_file)
        }

async def main():
    """Example usage of the benchmark runner."""
    runner = BenchmarkRunner(model_name="llama2")
    
    # Example prompts
    prompts = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms."
    ]
    
    results = await runner.run_benchmark(prompts)
    print(f"Benchmark completed. Results saved to: {results['output_file']}")

if __name__ == "__main__":
    asyncio.run(main()) 