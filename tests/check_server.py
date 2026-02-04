#!/usr/bin/env python
import requests
import sys

def check_server_status():
    try:
        response = requests.get("http://127.0.0.1:8000/admin/", timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running successfully!")
            print("🌐 Server URL: http://127.0.0.1:8000")
            print("🔧 Admin URL: http://127.0.0.1:8000/admin/")
            print("📡 API Base URL: http://127.0.0.1:8000/api/")
            return True
        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server")
        print("💡 Make sure the server is running with: python manage.py runserver 8000")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == '__main__':
    if check_server_status():
        sys.exit(0)
    else:
        sys.exit(1)