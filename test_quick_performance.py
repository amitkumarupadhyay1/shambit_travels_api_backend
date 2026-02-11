#!/usr/bin/env python
"""
Quick performance test - non-interactive
"""

import json
import statistics
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def test_endpoint(url: str, name: str, iterations: int = 3):
    """Test an endpoint multiple times"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")

    times = []
    for i in range(iterations):
        try:
            start = time.time()
            req = Request(url)
            with urlopen(req) as response:
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                status = response.status
                print(f"  Request {i+1}: {elapsed:.2f}ms (Status: {status})")
        except Exception as e:
            print(f"  Request {i+1}: Error - {e}")
            continue

        time.sleep(0.2)

    if times:
        print(f"\n  📊 Statistics:")
        print(f"     Min: {min(times):.2f}ms")
        print(f"     Max: {max(times):.2f}ms")
        print(f"     Avg: {statistics.mean(times):.2f}ms")

        # Check cache effectiveness
        if len(times) > 1:
            improvement = ((times[0] - min(times[1:])) / times[0]) * 100
            if improvement > 10:
                print(f"     Cache Improvement: {improvement:.1f}%")
                print(f"     ✅ Caching is working!")
            else:
                print(f"     ⚠️  Cache improvement: {improvement:.1f}%")

        # Performance rating
        avg = statistics.mean(times)
        if avg < 500:
            print(f"     ✅ Performance: Excellent (<500ms)")
        elif avg < 1000:
            print(f"     ⚠️  Performance: Good (<1000ms)")
        else:
            print(f"     ❌ Performance: Needs improvement (>1000ms)")

    return times


def main():
    print("\n" + "=" * 60)
    print("🚀 Quick Performance Test")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Test health check
    test_endpoint(f"{base_url}/health/", "Health Check", 2)

    # Test experiences
    test_endpoint(f"{base_url}/api/packages/experiences/", "Experiences List", 3)

    # Test packages
    test_endpoint(f"{base_url}/api/packages/packages/", "Packages List", 3)

    print("\n" + "=" * 60)
    print("✅ Performance Test Complete!")
    print("=" * 60)
    print("\n💡 Notes:")
    print("  - First request is always slower (cache miss)")
    print("  - Subsequent requests should be faster (cache hit)")
    print("  - Response times >1000ms may indicate database issues")
    print("\n")


if __name__ == "__main__":
    main()
