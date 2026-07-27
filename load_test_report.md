# Load Test Performance Report

**Generated:** 2026-07-26 09:55:22

---

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Concurrency | 10 |
| Duration | 1.09s |
| Total Requests | 50 |
| Use Real LLM | False |

## Overall Metrics

| Metric | Value |
|--------|-------|
| Total Requests | 50 |
| Successful | 50 |
| Failed | 0 |
| Success Rate | 100.0% |
| Overall QPS | 45.8 |
| Peak QPS | 50 |

## Latency Distribution (ms)

| Percentile | Latency (ms) |
|------------|--------------|
| Min | 15.01 |
| Mean | 15.8 |
| Median (P50) | 15.58 |
| P95 | 17.0 |
| P99 | 17.0 |
| Max | 17.0 |
| Std Dev | 0.69 |

## Performance by Category

| Category | Requests | Success Rate | Avg Latency | P95 | P99 |
|----------|----------|--------------|-------------|-----|-----|
| chitchat | 18 | 100.0% | 15.85ms | 17.0ms | 17.0ms |
| complex | 2 | 100.0% | 15.5ms | 15.58ms | 15.58ms |
| intent | 18 | 100.0% | 16.05ms | 17.0ms | 17.0ms |
| medium | 2 | 100.0% | 15.5ms | 15.58ms | 15.58ms |
| simple | 10 | 100.0% | 15.4ms | 15.58ms | 15.58ms |

## QPS Time Series (First 10 seconds)

| Second | QPS | Success | Avg Latency (ms) |
|--------|-----|---------|------------------|
| 0 | 50 | 50 | 15.8 |

## Performance Assessment

**Success Rate:** Excellent (100.0%)

**P95 Latency:** Excellent (17.0ms)

**Throughput (QPS):** Acceptable (45.8)
