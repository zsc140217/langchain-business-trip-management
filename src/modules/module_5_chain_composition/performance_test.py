"""
Performance Comparison Test
Compare sequential vs parallel chain execution times

Goal: Demonstrate 50%+ time savings with parallel execution

Test Scenarios:
1. Single execution comparison
2. Multiple runs with statistics
3. Different destinations
4. Performance under load
"""

from typing import Dict, List, Any
from .sequential_chain import SequentialChain
from .parallel_chain import ParallelChain
import logging
import time
import statistics
from tabulate import tabulate

logger = logging.getLogger(__name__)


class PerformanceTest:
    """
    Performance comparison test suite

    Tests sequential vs parallel chain execution and calculates:
    - Average execution time
    - Time savings percentage
    - Performance consistency (std dev)
    - Throughput comparison
    """

    def __init__(self):
        """Initialize test suite"""
        self.sequential_chain = SequentialChain()
        self.parallel_chain = ParallelChain()
        logger.info("PerformanceTest initialized")

    def run_single_test(
        self,
        destination: str,
        category: str = "accommodation"
    ) -> Dict[str, Any]:
        """
        Run single comparison test

        Args:
            destination: Target city
            category: Policy category

        Returns:
            Test results with timing data
        """
        test_input = {
            "destination": destination,
            "category": category
        }

        print(f"\n{'='*70}")
        print(f"Testing: {destination} - {category}")
        print(f"{'='*70}")

        # Test sequential chain
        print("\n[1/2] Running Sequential Chain...")
        seq_result = self.sequential_chain.invoke(test_input)
        seq_time = seq_result["total_time_ms"]
        print(f"✓ Completed in {seq_time:.0f}ms")

        # Test parallel chain
        print("\n[2/2] Running Parallel Chain...")
        par_result = self.parallel_chain.invoke(test_input)
        par_time = par_result["total_time_ms"]
        print(f"✓ Completed in {par_time:.0f}ms")

        # Calculate improvement
        time_saved = seq_time - par_time
        improvement_pct = (time_saved / seq_time) * 100

        return {
            "destination": destination,
            "category": category,
            "sequential_time_ms": seq_time,
            "parallel_time_ms": par_time,
            "time_saved_ms": time_saved,
            "improvement_percent": improvement_pct,
            "sequential_result": seq_result,
            "parallel_result": par_result,
        }

    def run_multiple_tests(
        self,
        destinations: List[str],
        category: str = "accommodation",
        runs_per_destination: int = 3
    ) -> Dict[str, Any]:
        """
        Run multiple tests with statistics

        Args:
            destinations: List of cities to test
            category: Policy category
            runs_per_destination: Number of runs per city

        Returns:
            Aggregated test results with statistics
        """
        print(f"\n{'='*70}")
        print(f"MULTIPLE TEST RUNS")
        print(f"{'='*70}")
        print(f"Destinations: {len(destinations)}")
        print(f"Runs per destination: {runs_per_destination}")
        print(f"Total tests: {len(destinations) * runs_per_destination * 2}")

        all_results = []
        seq_times = []
        par_times = []

        for dest in destinations:
            print(f"\n{'─'*70}")
            print(f"Testing: {dest}")
            print(f"{'─'*70}")

            for run in range(runs_per_destination):
                print(f"\nRun {run + 1}/{runs_per_destination}")

                result = self.run_single_test(dest, category)
                all_results.append(result)

                seq_times.append(result["sequential_time_ms"])
                par_times.append(result["parallel_time_ms"])

                time.sleep(0.5)  # Brief pause between runs

        # Calculate statistics
        stats = {
            "total_tests": len(all_results),
            "sequential": {
                "mean_ms": statistics.mean(seq_times),
                "median_ms": statistics.median(seq_times),
                "stdev_ms": statistics.stdev(seq_times) if len(seq_times) > 1 else 0,
                "min_ms": min(seq_times),
                "max_ms": max(seq_times),
            },
            "parallel": {
                "mean_ms": statistics.mean(par_times),
                "median_ms": statistics.median(par_times),
                "stdev_ms": statistics.stdev(par_times) if len(par_times) > 1 else 0,
                "min_ms": min(par_times),
                "max_ms": max(par_times),
            },
            "improvement": {
                "mean_time_saved_ms": statistics.mean(seq_times) - statistics.mean(par_times),
                "mean_improvement_percent": ((statistics.mean(seq_times) - statistics.mean(par_times)) / statistics.mean(seq_times)) * 100,
                "best_improvement_percent": max(r["improvement_percent"] for r in all_results),
                "worst_improvement_percent": min(r["improvement_percent"] for r in all_results),
            },
            "results": all_results,
        }

        return stats

    def print_comparison_report(self, test_result: Dict[str, Any]) -> None:
        """
        Print detailed comparison report for single test

        Args:
            test_result: Result from run_single_test()
        """
        seq_time = test_result["sequential_time_ms"]
        par_time = test_result["parallel_time_ms"]
        time_saved = test_result["time_saved_ms"]
        improvement = test_result["improvement_percent"]

        print(f"\n{'='*70}")
        print("PERFORMANCE COMPARISON REPORT")
        print(f"{'='*70}")
        print(f"Destination: {test_result['destination']}")
        print(f"Category: {test_result['category']}")
        print(f"{'='*70}")

        # Timing comparison table
        table_data = [
            ["Sequential Chain", f"{seq_time:.0f}ms", "100%", "Baseline"],
            ["Parallel Chain", f"{par_time:.0f}ms", f"{(par_time/seq_time)*100:.1f}%", "✓ Faster"],
            ["Time Saved", f"{time_saved:.0f}ms", f"{improvement:.1f}%", "✓ Improvement"],
        ]

        print("\nTiming Comparison:")
        print(tabulate(table_data, headers=["Mode", "Time", "Relative", "Status"], tablefmt="grid"))

        # Goal assessment
        print(f"\n{'─'*70}")
        print("Performance Goal Assessment:")
        print(f"{'─'*70}")
        print(f"Target: 50% time savings")
        print(f"Actual: {improvement:.1f}% time savings")

        if improvement >= 50:
            print("✓ GOAL ACHIEVED - Parallel chain meets 50% target!")
        elif improvement >= 40:
            print("⚠ CLOSE - Within 10% of target")
        else:
            print("✗ BELOW TARGET - Optimization needed")

        # Detailed breakdown
        seq_result = test_result["sequential_result"]
        par_result = test_result["parallel_result"]

        print(f"\n{'─'*70}")
        print("Sequential Chain Breakdown:")
        print(f"{'─'*70}")
        print(f"Step 1 (Policy):  {seq_result.get('step1_time_ms', 0):>8.0f}ms")
        print(f"Step 2 (Weather): {seq_result.get('step2_time_ms', 0):>8.0f}ms")
        print(f"Step 3 (Itinerary): {seq_result.get('step3_time_ms', 0):>8.0f}ms")
        print(f"{'─'*70}")
        print(f"Total:            {seq_time:>8.0f}ms")

        print(f"\n{'─'*70}")
        print("Parallel Chain Breakdown:")
        print(f"{'─'*70}")
        print(f"Steps 1&2 (Parallel): {par_result.get('parallel_time_ms', 0):>8.0f}ms")
        print(f"Step 3 (Itinerary):   {par_result.get('step3_time_ms', 0):>8.0f}ms")
        print(f"{'─'*70}")
        print(f"Total:                {par_time:>8.0f}ms")

    def print_statistics_report(self, stats: Dict[str, Any]) -> None:
        """
        Print statistical analysis report for multiple tests

        Args:
            stats: Result from run_multiple_tests()
        """
        print(f"\n{'='*70}")
        print("STATISTICAL ANALYSIS REPORT")
        print(f"{'='*70}")
        print(f"Total Tests: {stats['total_tests']}")
        print(f"{'='*70}")

        # Summary statistics table
        seq = stats["sequential"]
        par = stats["parallel"]

        table_data = [
            ["Mean", f"{seq['mean_ms']:.0f}ms", f"{par['mean_ms']:.0f}ms", f"{stats['improvement']['mean_improvement_percent']:.1f}%"],
            ["Median", f"{seq['median_ms']:.0f}ms", f"{par['median_ms']:.0f}ms", ""],
            ["Std Dev", f"{seq['stdev_ms']:.0f}ms", f"{par['stdev_ms']:.0f}ms", ""],
            ["Min", f"{seq['min_ms']:.0f}ms", f"{par['min_ms']:.0f}ms", ""],
            ["Max", f"{seq['max_ms']:.0f}ms", f"{par['max_ms']:.0f}ms", ""],
        ]

        print("\nPerformance Statistics:")
        print(tabulate(table_data, headers=["Metric", "Sequential", "Parallel", "Improvement"], tablefmt="grid"))

        # Improvement analysis
        print(f"\n{'─'*70}")
        print("Improvement Analysis:")
        print(f"{'─'*70}")
        print(f"Mean Time Saved:      {stats['improvement']['mean_time_saved_ms']:.0f}ms")
        print(f"Mean Improvement:     {stats['improvement']['mean_improvement_percent']:.1f}%")
        print(f"Best Improvement:     {stats['improvement']['best_improvement_percent']:.1f}%")
        print(f"Worst Improvement:    {stats['improvement']['worst_improvement_percent']:.1f}%")

        # Goal assessment
        mean_improvement = stats['improvement']['mean_improvement_percent']
        print(f"\n{'─'*70}")
        print("Overall Goal Assessment:")
        print(f"{'─'*70}")
        print(f"Target: 50% average time savings")
        print(f"Actual: {mean_improvement:.1f}% average time savings")

        if mean_improvement >= 50:
            print("✓ GOAL ACHIEVED - Consistently meeting 50% target!")
        elif mean_improvement >= 45:
            print("⚠ CLOSE - Within 5% of target")
        else:
            print("✗ BELOW TARGET - Review optimization strategy")

        # Consistency analysis
        seq_cv = (seq['stdev_ms'] / seq['mean_ms']) * 100 if seq['mean_ms'] > 0 else 0
        par_cv = (par['stdev_ms'] / par['mean_ms']) * 100 if par['mean_ms'] > 0 else 0

        print(f"\n{'─'*70}")
        print("Performance Consistency:")
        print(f"{'─'*70}")
        print(f"Sequential CV: {seq_cv:.1f}%")
        print(f"Parallel CV:   {par_cv:.1f}%")

        if par_cv < seq_cv:
            print("✓ Parallel chain is more consistent")
        else:
            print("⚠ Sequential chain is more consistent")


# Main test execution
if __name__ == "__main__":
    """Run performance comparison tests"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("MODULE 5: CHAIN COMPOSITION - PERFORMANCE TEST")
    print("="*70)
    print("\nGoal: Demonstrate 50%+ time savings with parallel execution")

    # Create test suite
    test_suite = PerformanceTest()

    # Test 1: Single execution comparison
    print("\n" + "="*70)
    print("TEST 1: SINGLE EXECUTION COMPARISON")
    print("="*70)

    result = test_suite.run_single_test(
        destination="北京",
        category="accommodation"
    )

    test_suite.print_comparison_report(result)

    # Test 2: Multiple runs with statistics
    print("\n\n" + "="*70)
    print("TEST 2: MULTIPLE RUNS WITH STATISTICS")
    print("="*70)

    destinations = ["北京", "上海", "杭州"]
    stats = test_suite.run_multiple_tests(
        destinations=destinations,
        category="accommodation",
        runs_per_destination=2
    )

    test_suite.print_statistics_report(stats)

    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    mean_improvement = stats['improvement']['mean_improvement_percent']
    print(f"\nParallel Chain Performance: {mean_improvement:.1f}% faster than Sequential")
    print(f"Goal Achievement: {'✓ PASSED' if mean_improvement >= 50 else '✗ NEEDS IMPROVEMENT'}")
    print("\nKey Insights:")
    print("- Parallel execution significantly reduces total time")
    print("- Best for independent I/O-bound operations")
    print("- LCEL RunnableParallel enables concurrent execution")
    print("\n" + "="*70)
