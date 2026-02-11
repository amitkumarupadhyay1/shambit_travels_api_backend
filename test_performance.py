#!/usr/bin/env python
"""
Performance testing script for Day 14 implementation
Tests caching, response times, and database query optimization
"""

import json
import statistics
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def measure_response_time(url: str, iterations: int = 5) -> dict:
    """
    Measure response time for multiple requests
    Returns statistics about response times
    """
    times = []
    cache_hits = 0

    print(f"\n📊 Testing: {url}")
    print(f"Running {iterations} iterations...")

    for i in range(iterations):
        try:
            start_time = time.time()
            req = Request(url)
            with urlopen(req) as response:
                response_time = (time.time() - start_time) * 1000  # ms
                times.append(response_time)

                # Check for cache header
                x_response_time = response.headers.get("X-Response-Time")
                if x_response_time:
                    print(
                        f"  Request {i+1}: {response_time:.2f}ms (Server: {x_response_time})"
                    )
                else:
                    print(f"  Request {i+1}: {response_time:.2f}ms")

                # First request is cache miss, subsequent should be hits
                if i > 0 and response_time < times[0] * 0.5:
                    cache_hits += 1

        except (HTTPError, URLError) as e:
            print(f"  Request {i+1}: Error - {e}")
            continue

        # Small delay between requests
        if i < iterations - 1:
            time.sleep(0.1)

    if not times:
        return {"error": "All requests failed"}

    return {
        "min": min(times),
        "max": max(times),
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "cache_hits": cache_hits,
        "cache_hit_rate": (
            (cache_hits / (iterations - 1)) * 100 if iterations > 1 else 0
        ),
    }


def test_caching_effectiveness(base_url="http://localhost:8000"):
    """
    Test caching effectiveness by comparing first vs subsequent requests
    """
    print("\n" + "=" * 60)
    print("Testing Caching Effectiveness")
    print("=" * 60)

    endpoints = [
        "/api/packages/experiences/",
        "/api/packages/packages/",
    ]

    results = {}

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        stats = measure_response_time(url, iterations=5)

        if "error" not in stats:
            improvement = ((stats["max"] - stats["min"]) / stats["max"]) * 100
            print(f"\n  📈 Statistics:")
            print(f"     Min: {stats['min']:.2f}ms")
            print(f"     Max: {stats['max']:.2f}ms")
            print(f"     Avg: {stats['avg']:.2f}ms")
            print(f"     Median: {stats['median']:.2f}ms")
            print(f"     Cache Hits: {stats['cache_hits']}/4")
            print(f"     Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
            print(f"     Performance Improvement: {improvement:.1f}%")

            results[endpoint] = stats
        else:
            print(f"\n  ❌ {stats['error']}")
            results[endpoint] = stats

    return results


def test_query_optimization(base_url="http://localhost:8000"):
    """
    Test database query optimization by checking response times
    """
    print("\n" + "=" * 60)
    print("Testing Query Optimization")
    print("=" * 60)

    # Test endpoints that should have optimized queries
    endpoints = {
        "Experiences List": "/api/packages/experiences/",
        "Packages List": "/api/packages/packages/",
        "Experiences with Filters": "/api/packages/experiences/?category=CULTURAL&min_price=1000",
    }

    for name, endpoint in endpoints.items():
        url = f"{base_url}{endpoint}"
        print(f"\n📊 Testing: {name}")

        try:
            start_time = time.time()
            req = Request(url)
            with urlopen(req) as response:
                response_time = (time.time() - start_time) * 1000
                data = json.loads(response.read().decode())

                # Count results
                if isinstance(data, dict) and "results" in data:
                    count = len(data["results"])
                elif isinstance(data, list):
                    count = len(data)
                else:
                    count = 1

                print(f"  ✅ Response Time: {response_time:.2f}ms")
                print(f"  📦 Results: {count} items")

                # Check if response time is acceptable
                if response_time < 500:
                    print(f"  ✅ Performance: Excellent (<500ms)")
                elif response_time < 1000:
                    print(f"  ⚠️  Performance: Good (<1000ms)")
                else:
                    print(f"  ❌ Performance: Needs improvement (>1000ms)")

        except (HTTPError, URLError) as e:
            print(f"  ❌ Error: {e}")


def test_cache_headers(base_url="http://localhost:8000"):
    """
    Test that cache headers are present
    """
    print("\n" + "=" * 60)
    print("Testing Cache Headers")
    print("=" * 60)

    url = f"{base_url}/api/packages/experiences/"

    try:
        req = Request(url)
        with urlopen(req) as response:
            headers = dict(response.headers)

            print(f"\n📋 Response Headers:")

            # Check for performance-related headers
            important_headers = [
                "X-Response-Time",
                "Cache-Control",
                "ETag",
                "Last-Modified",
            ]

            for header in important_headers:
                value = headers.get(header)
                if value:
                    print(f"  ✅ {header}: {value}")
                else:
                    print(f"  ⚠️  {header}: Not present")

    except (HTTPError, URLError) as e:
        print(f"  ❌ Error: {e}")


def test_concurrent_requests(base_url="http://localhost:8000", concurrent=10):
    """
    Test performance under concurrent load
    """
    print("\n" + "=" * 60)
    print(f"Testing Concurrent Requests ({concurrent} simultaneous)")
    print("=" * 60)

    import concurrent.futures

    url = f"{base_url}/api/packages/experiences/"

    def make_request():
        try:
            start_time = time.time()
            req = Request(url)
            with urlopen(req) as response:
                response_time = (time.time() - start_time) * 1000
                return {"success": True, "time": response_time}
        except Exception as e:
            return {"success": False, "error": str(e)}

    print(f"\n🚀 Making {concurrent} concurrent requests...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
        start_time = time.time()
        futures = [executor.submit(make_request) for _ in range(concurrent)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        total_time = (time.time() - start_time) * 1000

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"\n📊 Results:")
    print(f"  Total Time: {total_time:.2f}ms")
    print(f"  Successful: {len(successful)}/{concurrent}")
    print(f"  Failed: {len(failed)}/{concurrent}")

    if successful:
        times = [r["time"] for r in successful]
        print(f"\n  Response Times:")
        print(f"    Min: {min(times):.2f}ms")
        print(f"    Max: {max(times):.2f}ms")
        print(f"    Avg: {statistics.mean(times):.2f}ms")
        print(f"    Median: {statistics.median(times):.2f}ms")

        # Calculate requests per second
        rps = (len(successful) / total_time) * 1000
        print(f"\n  Throughput: {rps:.2f} requests/second")


def main():
    """Run all performance tests"""
    print("\n" + "=" * 60)
    print("🧪 Day 14 Performance Testing")
    print("=" * 60)

    base_url = "http://localhost:8000"
    print(f"\n🌐 Testing against: {base_url}")
    print("💡 Make sure the server is running: python manage.py runserver")

    # Run tests
    test_caching_effectiveness(base_url)
    test_query_optimization(base_url)
    test_cache_headers(base_url)

    # Optional concurrent test
    print("\n" + "=" * 60)
    user_input = input("Run concurrent load test? (y/n): ").lower()
    if user_input == "y":
        test_concurrent_requests(base_url, concurrent=10)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Performance Test Summary")
    print("=" * 60)
    print("\n✅ Tests completed!")
    print("\n💡 Performance Goals:")
    print("  - Experience list: <500ms")
    print("  - Package detail: <800ms")
    print("  - Cache hit rate: >80%")
    print("  - Concurrent handling: 10+ req/s")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
