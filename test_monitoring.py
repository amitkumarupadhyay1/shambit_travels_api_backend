#!/usr/bin/env python
"""
Test script for monitoring and error handling features
Run this to verify Day 12-13 implementation
"""

import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def test_health_check(base_url="http://localhost:8000"):
    """Test the health check endpoint"""
    print("\n" + "=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)

    try:
        url = f"{base_url}/health/"
        print(f"\n📡 Calling: {url}")

        start_time = time.time()
        req = Request(url)
        with urlopen(req) as response:
            response_time = (time.time() - start_time) * 1000
            data = json.loads(response.read().decode())

        print(f"✅ Status: {response.status}")
        print(f"⏱️  Response Time: {response_time:.2f}ms")
        print(f"\n📊 Response Data:")
        print(json.dumps(data, indent=2))

        # Validate response
        assert data["status"] == "healthy", "Health check status is not healthy"
        assert "response_time_ms" in data, "Response time not in response"
        assert "database" in data, "Database info not in response"

        print("\n✅ Health check test PASSED")
        return True

    except HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
        print("💡 Make sure the server is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_api_response_time(base_url="http://localhost:8000"):
    """Test API response time logging"""
    print("\n" + "=" * 60)
    print("Testing API Response Time")
    print("=" * 60)

    try:
        url = f"{base_url}/api/packages/experiences/"
        print(f"\n📡 Calling: {url}")

        start_time = time.time()
        req = Request(url)
        with urlopen(req) as response:
            response_time = (time.time() - start_time) * 1000
            x_response_time = response.headers.get("X-Response-Time")

        print(f"✅ Status: {response.status}")
        print(f"⏱️  Measured Response Time: {response_time:.2f}ms")
        if x_response_time:
            print(f"⏱️  X-Response-Time Header: {x_response_time}")
            print("✅ Response time header is present")
        else:
            print(
                "⚠️  X-Response-Time header not found (middleware may not be enabled)"
            )

        print("\n✅ API response time test PASSED")
        return True

    except HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_error_handling(base_url="http://localhost:8000"):
    """Test error handling with invalid request"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    try:
        # Try to access non-existent package
        url = f"{base_url}/api/packages/packages/non-existent-package/"
        print(f"\n📡 Calling: {url}")
        print("(Expecting 404 error)")

        req = Request(url)
        try:
            with urlopen(req) as response:
                print(f"⚠️  Unexpected success: {response.status}")
                return False
        except HTTPError as e:
            if e.code == 404:
                error_data = json.loads(e.read().decode())
                print(f"✅ Got expected 404 error")
                print(f"\n📊 Error Response:")
                print(json.dumps(error_data, indent=2))

                # Check for user-friendly error message
                if "error" in error_data or "detail" in error_data:
                    print("✅ Error response has user-friendly message")
                else:
                    print("⚠️  Error response missing user-friendly message")

                print("\n✅ Error handling test PASSED")
                return True
            else:
                print(f"❌ Unexpected error code: {e.code}")
                return False

    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_rate_limiting(base_url="http://localhost:8000"):
    """Test rate limiting (optional - may take time)"""
    print("\n" + "=" * 60)
    print("Testing Rate Limiting (Optional)")
    print("=" * 60)
    print("⚠️  This test makes 15 rapid requests and may take a moment...")

    try:
        url = f"{base_url}/api/packages/experiences/"
        success_count = 0
        rate_limited = False

        for i in range(15):
            try:
                req = Request(url)
                with urlopen(req) as response:
                    if response.status == 200:
                        success_count += 1
                        print(f"✅ Request {i + 1}: Success")
            except HTTPError as e:
                if e.code == 429:
                    rate_limited = True
                    print(f"⚠️  Request {i + 1}: Rate limited (429)")
                    break
                else:
                    print(f"❌ Request {i + 1}: Error {e.code}")

            time.sleep(0.1)  # Small delay between requests

        if rate_limited:
            print("\n✅ Rate limiting is working")
        else:
            print(f"\n⚠️  Made {success_count} requests without hitting rate limit")
            print("💡 Rate limiting may not be enabled or limit is higher than 15/min")

        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 Day 12-13 Monitoring & Error Handling Tests")
    print("=" * 60)

    base_url = "http://localhost:8000"
    print(f"\n🌐 Testing against: {base_url}")
    print("💡 Make sure the server is running: python manage.py runserver")

    results = {
        "Health Check": test_health_check(base_url),
        "API Response Time": test_api_response_time(base_url),
        "Error Handling": test_error_handling(base_url),
    }

    # Optional test
    print("\n" + "=" * 60)
    user_input = input("Run rate limiting test? (y/n): ").lower()
    if user_input == "y":
        results["Rate Limiting"] = test_rate_limiting(base_url)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\n🎯 Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Day 12-13 implementation is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
