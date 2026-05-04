import time
import statistics
from src.app import query, QueryRequest
import asyncio

async def measure():
    print("Measuring performance (20 iterations)...")
    latencies = []
    
    req = QueryRequest(
        query="tell me about my portfolio",
        user={"country": "US", "positions": []},
        session_id="perf_test"
    )

    for i in range(20):
        start = time.perf_counter()
        
        # Simulate a full request going through the event generator
        response = await query(req)
        
        # Iterate through the SSE events
        async for _ in response.body_iterator:
            pass
            
        end = time.perf_counter()
        latencies.append((end - start) * 1000) # Convert to ms
        
    avg_latency = statistics.mean(latencies)
    
    # Calculate p95
    sorted_latencies = sorted(latencies)
    p95_idx = int(0.95 * len(sorted_latencies))
    p95_latency = sorted_latencies[p95_idx]
    
    print(f"Average latency: {avg_latency:.2f} ms")
    print(f"p95 latency:     {p95_latency:.2f} ms")

if __name__ == "__main__":
    asyncio.run(measure())
