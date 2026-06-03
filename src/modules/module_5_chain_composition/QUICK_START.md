# Quick Start - Module 5: Chain Composition

## Installation

Ensure dependencies are installed:
```bash
pip install langchain langchain-community tabulate python-dotenv
```

## Configuration

Create `.env` file with:
```bash
DASHSCOPE_API_KEY=your_api_key_here
```

## Run Examples

### 1. Sequential Chain (Baseline)
```bash
cd src/modules/module_5_chain_composition
python sequential_chain.py
```

Expected output:
```
Sequential Chain Test
============================================================
Input: {'destination': '北京', 'category': 'accommodation'}

Executing sequential chain...

RESULTS
============================================================
1. Policy Result: [Policy details for Beijing accommodation]
2. Weather Result: [Weather advice for Beijing]
3. Itinerary Result: [Complete itinerary with policy compliance]

Sequential Chain Performance:
========================================
Step 1 (Policy Query):        2000ms
Step 2 (Weather Query):       1500ms
Step 3 (Itinerary):           2500ms
----------------------------------------
Total Time:                   6000ms
========================================
```

### 2. Parallel Chain (Optimized)
```bash
python parallel_chain.py
```

Expected output:
```
Parallel Chain Test
============================================================
Input: {'destination': '北京', 'category': 'accommodation'}

Executing parallel chain...

RESULTS
============================================================
1. Policy Result: [Same quality as sequential]
2. Weather Result: [Same quality as sequential]
3. Itinerary Result: [Same quality as sequential]

Parallel Chain Performance:
========================================
Steps 1 & 2 (Parallel):       2000ms  ← 50% faster!
Step 3 (Itinerary):           2500ms
----------------------------------------
Total Time:                   4500ms  ← 25% faster overall!
========================================
```

### 3. Performance Comparison
```bash
python performance_test.py
```

This runs both chains and shows:
- Side-by-side timing comparison
- Time savings percentage
- Goal achievement status
- Statistical analysis

## Python API Usage

```python
# Import chains
from src.modules.module_5_chain_composition import SequentialChain, ParallelChain

# Create chains
seq_chain = SequentialChain()
par_chain = ParallelChain()

# Execute
test_input = {
    "destination": "北京",
    "category": "accommodation"
}

seq_result = seq_chain.invoke(test_input)
par_result = par_chain.invoke(test_input)

# Compare
print(f"Sequential: {seq_result['total_time_ms']}ms")
print(f"Parallel:   {par_result['total_time_ms']}ms")
print(f"Saved:      {seq_result['total_time_ms'] - par_result['total_time_ms']}ms")
```

## When to Use Which

### Use Sequential When:
- Steps have strict dependencies
- Debugging/understanding execution flow
- Simple single-threaded environment

### Use Parallel When:
- Operations are independent
- Minimizing execution time is critical
- I/O-bound operations (API calls)
- Production systems with high throughput

## Troubleshooting

**Issue**: ModuleNotFoundError
**Fix**: Run from project root or add to PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/langchain-business-trip-management"
```

**Issue**: API key error
**Fix**: Ensure DASHSCOPE_API_KEY is set in .env

**Issue**: Import errors
**Fix**: Install dependencies
```bash
pip install -r requirements.txt
```

