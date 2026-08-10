"""
ERDIS Evaluation CLI Entrypoint.
Usage:
    python -m app.eval.run --mock
    python -m app.eval.run --live
"""

import sys
import argparse
from app.eval.runner import BenchmarkRunner


def main():
    parser = argparse.ArgumentParser(description="ERDIS Evaluation & Benchmarking CLI")
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Run benchmark in safe, deterministic mock mode (default, no LLM API keys required).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Run benchmark in live API execution mode (requires OpenAI / external credentials).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory where JSON, CSV, and Markdown report artifacts will be saved.",
    )

    args = parser.parse_args()

    is_mock = not args.live

    runner = BenchmarkRunner(output_dir=args.output_dir)
    results = runner.run_benchmark(is_mock=is_mock)

    print("\n" + "=" * 70)
    print(f"BENCHMARK COMPLETED SUCCESSFULLY ({results['mode']} MODE)")
    print(f"Total Cases Evaluated: {results['total_cases']}")
    print(f"Task Success Rate:    {results['task_success_rate'] * 100:.1f}%")
    print(f"Mean Groundedness:    {results['mean_groundedness'] * 100:.1f}%")
    print(f"Mean Citation Cov:    {results['mean_citation_coverage'] * 100:.1f}%")
    print(f"Mean Latency:         {results['mean_latency_ms']} ms")
    print(f"Total Tokens Used:    {results['total_tokens']:,}")
    print(f"Estimated Cost USD:   ${results['total_estimated_cost_usd']:.4f}")
    print("=" * 70)
    print(f"Artifacts exported to: {args.output_dir}/")
    print("  - benchmark_results.json")
    print("  - benchmark_results.csv")
    print("  - benchmark_report.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
