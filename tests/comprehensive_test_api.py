import json
import os
import time

import requests

BASE_URL = "http://localhost:8000"
ENDPOINTS_FILE = "all_endpoints.json"
REPORT_FILE = "test_report.md"

import subprocess


def get_token():
    cmd = "python manage.py shell -c \"from django.contrib.auth import get_user_model; from rest_framework_simplejwt.tokens import RefreshToken; User = get_user_model(); user = User.objects.get(username='admin'); refresh = RefreshToken.for_user(user); print(f'---TOKEN_START---{str(refresh.access_token)}---TOKEN_END---')\""
    try:
        output = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT
        ).decode()
        if "---TOKEN_START---" in output:
            token = (
                output.split("---TOKEN_START---")[1].split("---TOKEN_END---")[0].strip()
            )
            return token
    except Exception as e:
        print(f"Error generating token: {e}")
    return None


def test_endpoint(path, method, token, path_params=None):
    if path_params:
        for key, value in path_params.items():
            path = path.replace(f"{{{key}}}", str(value))

    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    print(f"Headers: {headers}")

    print(f"Testing {method.upper()} {path}...", end=" ", flush=True)
    try:
        start_time = time.time()
        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        elif method.lower() == "post":
            # For POST, we try a minimal empty body or generic data if needed
            # but sticking to GET mostly as per plan to avoid side effects
            response = requests.post(url, headers=headers, json={})
        else:
            print("SKIPPED (Method not GET/POST)")
            return None

        duration = time.time() - start_time
        status = response.status_code
        print(f"{status} ({duration:.2f}s)")

        return {
            "path": path,
            "method": method.upper(),
            "status": status,
            "duration": duration,
            "response": (
                response.json()
                if status == 200
                and "application/json" in response.headers.get("Content-Type", "")
                else None
            ),
        }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "path": path,
            "method": method.upper(),
            "status": "ERROR",
            "duration": 0,
            "error": str(e),
        }


def run_comprehensive_test():
    token = get_token()
    if not token:
        print("Falling back to unauthenticated testing (some endpoints may fail)")

    with open(ENDPOINTS_FILE, "r") as f:
        endpoints = json.load(f)

    results = []

    # Discovery phase for slugs/ids
    discovery_data = {"slug": "mumbai", "id": 1}  # Defaults

    # Try to find actual slugs from cities/packages
    print("\n--- Discovery Phase ---")
    city_res = test_endpoint("/api/cities/city-context/mumbai/", "get", token)
    if city_res and city_res["status"] == 200:
        # We have mumbai
        pass
    else:
        # Try generic list
        pass

    package_res = test_endpoint("/api/packages/packages/", "get", token)
    if package_res and package_res["status"] == 200 and package_res["response"]:
        results_list = package_res["response"].get("results", [])
        if results_list:
            discovery_data["slug"] = results_list[0].get("slug", discovery_data["slug"])
            print(f"Found dynamic slug: {discovery_data['slug']}")

    print("\n--- Testing Phase ---")
    for path, methods in endpoints.items():
        if "get" in methods:
            res = test_endpoint(path, "get", token, discovery_data)
            results.append(res)
        elif "post" in methods:
            # Only test specific POST endpoints that are safe
            safe_posts = [
                "/api/packages/packages/{slug}/calculate_price/",
                "/api/pricing/rules/test_pricing/",
            ]
            if path in safe_posts:
                # We'll need specific data for these, might skip or use dummy
                res = test_endpoint(path, "post", token, discovery_data)
                results.append(res)

    generate_report(results)


def generate_report(results):
    print(f"\nGenerating report to {REPORT_FILE}...")
    with open(REPORT_FILE, "w") as f:
        f.write("# API Test Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Path | Method | Status | Duration (s) |\n")
        f.write("|------|--------|--------|--------------|\n")

        success_count = 0
        fail_count = 0

        for r in results:
            if not r:
                continue
            status_str = f"{r['status']}"
            if r["status"] == 200 or r["status"] == 201:
                status_str = f"✅ {r['status']}"
                success_count += 1
            else:
                status_str = f"❌ {r['status']}"
                fail_count += 1

            f.write(
                f"| {r['path']} | {r['method']} | {status_str} | {r['duration']:.2f} |\n"
            )

        f.write(f"\n## Summary\n")
        f.write(f"- Total Tested: {len(results)}\n")
        f.write(f"- Success: {success_count}\n")
        f.write(f"- Failures/Errors: {fail_count}\n")


if __name__ == "__main__":
    run_comprehensive_test()
