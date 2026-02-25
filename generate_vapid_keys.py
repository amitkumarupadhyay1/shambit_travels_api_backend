#!/usr/bin/env python
"""
Generate VAPID keys for Web Push Notifications
Run this script to generate public and private keys for push notifications.
"""

try:
    from py_vapid import Vapid

    print("Generating VAPID keys...")
    print("-" * 60)

    vapid = Vapid()
    vapid.generate_keys()

    # Save to PEM format and read back
    vapid.save_key("vapid_private.pem")
    vapid.save_public_key("vapid_public.pem")

    # Read the keys
    with open("vapid_private.pem", "r") as f:
        private_key = f.read().strip()

    with open("vapid_public.pem", "r") as f:
        public_key = f.read().strip()

    print("\n✅ VAPID Keys Generated Successfully!\n")
    print("=" * 60)
    print("Copy these keys to your backend/backend/settings.py file:")
    print("=" * 60)
    print()
    print("# Push Notifications Configuration")
    print(f"VAPID_PUBLIC_KEY = '{public_key}'")
    print(f"VAPID_PRIVATE_KEY = '{private_key}'")
    print("VAPID_CLAIMS = {")
    print('    "sub": "mailto:your-email@shambit.com"  # Replace with your email')
    print("}")
    print()
    print("=" * 60)
    print("\n⚠️  IMPORTANT:")
    print("1. Keep the PRIVATE_KEY secret - never commit it to git")
    print("2. Add VAPID_PRIVATE_KEY to .env file")
    print("3. Replace the email in VAPID_CLAIMS with your actual email")
    print("4. Restart your Django server after adding these keys")
    print("5. Delete vapid_private.pem and vapid_public.pem files after copying keys")
    print()

    # Cleanup
    import os

    try:
        os.remove("vapid_private.pem")
        os.remove("vapid_public.pem")
        print("✅ Temporary key files cleaned up")
    except OSError:
        pass

except ImportError:
    print("❌ Error: py-vapid is not installed")
    print("\nInstall it using:")
    print("  pip install py-vapid")
    print("\nOr if using requirements.txt:")
    print("  pip install -r requirements.txt")
