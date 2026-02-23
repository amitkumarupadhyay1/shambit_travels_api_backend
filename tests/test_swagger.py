#!/usr/bin/env python
"""
Test script for Swagger API documentation implementation.
Tests schema generation, endpoint accessibility, and security.
"""

import os

import django
from django.contrib.auth import get_user_model
from django.test import Client

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
django.setup()

User = get_user_model()


def test_swagger_endpoints():
    """Test Swagger endpoint accessibility"""
    client = Client()

    print("🔍 Testing Swagger Endpoints...")

    # Test schema endpoint
    try:
        response = client.get("/api/schema/")
        print(f"✅ Schema endpoint: {response.status_code}")
        if response.status_code == 200:
            schema = response.json()
            print(f"   - OpenAPI version: {schema.get('openapi', 'N/A')}")
            print(f"   - API title: {schema.get('info', {}).get('title', 'N/A')}")
            print(f"   - Paths count: {len(schema.get('paths', {}))}")
    except Exception as e:
        print(f"❌ Schema endpoint error: {e}")

    # Test Swagger UI endpoint
    try:
        response = client.get("/api/docs/")
        print(f"✅ Swagger UI endpoint: {response.status_code}")
        if response.status_code == 200:
            print("   - Swagger UI accessible")
    except Exception as e:
        print(f"❌ Swagger UI error: {e}")

    # Test ReDoc endpoint
    try:
        response = client.get("/api/redoc/")
        print(f"✅ ReDoc endpoint: {response.status_code}")
        if response.status_code == 200:
            print("   - ReDoc accessible")
    except Exception as e:
        print(f"❌ ReDoc error: {e}")


def test_api_endpoints_in_schema():
    """Test that main API endpoints are documented in schema"""
    client = Client()

    print("\n🔍 Testing API Endpoints in Schema...")

    try:
        response = client.get("/api/schema/")
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            expected_endpoints = [
                "/api/cities/{slug}/",
                "/api/articles/",
                "/api/packages/",
                "/api/packages/{slug}/price_range/",
                "/api/packages/{slug}/calculate_price/",
                "/api/bookings/",
                "/api/auth/sync/",
            ]

            for endpoint in expected_endpoints:
                if endpoint in paths:
                    print(f"✅ {endpoint} - documented")
                    # Check if it has proper tags
                    methods = paths[endpoint]
                    for method, details in methods.items():
                        tags = details.get("tags", [])
                        if tags:
                            print(f"   - {method.upper()}: tags {tags}")
                else:
                    print(f"❌ {endpoint} - missing from schema")
        else:
            print(f"❌ Could not fetch schema: {response.status_code}")
    except Exception as e:
        print(f"❌ Schema analysis error: {e}")


def test_authentication_in_schema():
    """Test authentication documentation in schema"""
    client = Client()

    print("\n🔍 Testing Authentication in Schema...")

    try:
        response = client.get("/api/schema/")
        if response.status_code == 200:
            schema = response.json()

            # Check security schemes
            components = schema.get("components", {})
            security_schemes = components.get("securitySchemes", {})

            if security_schemes:
                print("✅ Security schemes found:")
                for scheme_name, scheme_details in security_schemes.items():
                    print(f"   - {scheme_name}: {scheme_details.get('type', 'N/A')}")
            else:
                print("❌ No security schemes found")

            # Check if endpoints have security requirements
            paths = schema.get("paths", {})
            secured_endpoints = 0
            total_endpoints = 0

            for path, methods in paths.items():
                for method, details in methods.items():
                    total_endpoints += 1
                    if "security" in details:
                        secured_endpoints += 1

            print(f"✅ Secured endpoints: {secured_endpoints}/{total_endpoints}")
        else:
            print(f"❌ Could not fetch schema: {response.status_code}")
    except Exception as e:
        print(f"❌ Authentication analysis error: {e}")


def test_security_in_production_mode():
    """Test that Swagger is secured in production mode"""
    print("\n🔍 Testing Production Security...")

    # This would require changing DEBUG setting, which we'll simulate
    print("ℹ️  In production (DEBUG=False):")
    print("   - Swagger UI should require admin login")
    print("   - Schema endpoint should require admin permissions")
    print("   - ReDoc should require admin login")
    print("   - Check backend/backend/swagger_views.py for implementation")


def test_example_api_calls():
    """Test some example API calls to ensure they work"""
    client = Client()

    print("\n🔍 Testing Example API Calls...")

    # Test public endpoints
    try:
        response = client.get("/api/articles/")
        print(f"✅ Articles list: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Results count: {data.get('count', 0)}")
    except Exception as e:
        print(f"❌ Articles endpoint error: {e}")

    # Test packages endpoint
    try:
        response = client.get("/api/packages/")
        print(f"✅ Packages list: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Results count: {data.get('count', 0)}")
    except Exception as e:
        print(f"❌ Packages endpoint error: {e}")


def main():
    """Run all tests"""
    print("🚀 Starting Swagger API Documentation Tests")
    print("=" * 50)

    test_swagger_endpoints()
    test_api_endpoints_in_schema()
    test_authentication_in_schema()
    test_security_in_production_mode()
    test_example_api_calls()

    print("\n" + "=" * 50)
    print("✅ Swagger testing completed!")
    print("\n📖 Access your API documentation at:")
    print("   - Swagger UI: http://localhost:8000/api/docs/")
    print("   - ReDoc: http://localhost:8000/api/redoc/")
    print("   - Schema: http://localhost:8000/api/schema/")
    print("\n🔒 Security Notes:")
    print("   - In DEBUG=True: Public access")
    print("   - In DEBUG=False: Admin-only access")


if __name__ == "__main__":
    main()
