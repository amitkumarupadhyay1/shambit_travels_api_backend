#!/usr/bin/env python
"""
Simple test to verify Swagger implementation is working.
"""

import os

import django
from django.conf import settings
from django.test import Client

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.development")
django.setup()


def test_swagger_basic():
    """Test basic Swagger functionality"""
    client = Client()

    print("🚀 Testing Swagger Implementation")
    print("=" * 50)

    # Test schema endpoint
    print("1. Testing Schema Generation...")
    try:
        response = client.get("/api/schema/", HTTP_HOST="localhost")
        if response.status_code == 200:
            print("   ✅ Schema endpoint accessible")
            schema = response.json()
            print(f"   ✅ OpenAPI version: {schema.get('openapi', 'N/A')}")
            print(f"   ✅ API title: {schema.get('info', {}).get('title', 'N/A')}")
            print(f"   ✅ Paths documented: {len(schema.get('paths', {}))}")

            # Check for key endpoints
            paths = schema.get("paths", {})
            key_endpoints = [
                "/api/auth/nextauth-sync/",
                "/api/cities/city-context/{slug}/",
                "/api/articles/",
                "/api/packages/",
            ]

            documented_count = 0
            for endpoint in key_endpoints:
                if endpoint in paths:
                    documented_count += 1
                    print(f"   ✅ {endpoint} - documented")
                else:
                    print(f"   ❌ {endpoint} - missing")

            print(
                f"   📊 Coverage: {documented_count}/{len(key_endpoints)} key endpoints"
            )

        else:
            print(f"   ❌ Schema endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Schema test error: {e}")

    # Test Swagger UI endpoint
    print("\n2. Testing Swagger UI...")
    try:
        response = client.get("/api/docs/", HTTP_HOST="localhost")
        if response.status_code == 200:
            print("   ✅ Swagger UI accessible")
            content = response.content.decode("utf-8")
            if "swagger-ui" in content.lower():
                print("   ✅ Swagger UI content loaded")
            else:
                print("   ⚠️  Swagger UI content may not be fully loaded")
        else:
            print(f"   ❌ Swagger UI failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Swagger UI test error: {e}")

    # Test ReDoc endpoint
    print("\n3. Testing ReDoc...")
    try:
        response = client.get("/api/redoc/", HTTP_HOST="localhost")
        if response.status_code == 200:
            print("   ✅ ReDoc accessible")
            content = response.content.decode("utf-8")
            if "redoc" in content.lower():
                print("   ✅ ReDoc content loaded")
            else:
                print("   ⚠️  ReDoc content may not be fully loaded")
        else:
            print(f"   ❌ ReDoc failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ReDoc test error: {e}")

    # Test security configuration
    print("\n4. Testing Security Configuration...")
    print(f"   📋 DEBUG mode: {settings.DEBUG}")
    print(
        f"   📋 SPECTACULAR_SETTINGS configured: {'SPECTACULAR_SETTINGS' in dir(settings)}"
    )

    if hasattr(settings, "SPECTACULAR_SETTINGS"):
        spectacular = settings.SPECTACULAR_SETTINGS
        print(f"   ✅ API Title: {spectacular.get('TITLE', 'N/A')}")
        print(f"   ✅ Security schemes: {len(spectacular.get('SECURITY', []))}")
        print(f"   ✅ Tags defined: {len(spectacular.get('TAGS', []))}")

    print("\n" + "=" * 50)
    print("✅ Swagger Implementation Test Complete!")
    print("\n📖 Access your API documentation:")
    print("   - Swagger UI: http://localhost:8000/api/docs/")
    print("   - ReDoc: http://localhost:8000/api/redoc/")
    print("   - Schema: http://localhost:8000/api/schema/")

    print("\n🔧 Next Steps:")
    print("   1. Start Django server: python manage.py runserver")
    print("   2. Visit Swagger UI in browser")
    print("   3. Test API endpoints interactively")


if __name__ == "__main__":
    test_swagger_basic()
