import base64

from django.conf import settings
from django.test import SimpleTestCase

from py_vapid import Vapid

from .services.push_service import PushNotificationService


class PushNotificationServiceKeyFormatTests(SimpleTestCase):
    def test_private_key_conversion_from_pem_is_vapid_compatible(self):
        converted = PushNotificationService._private_key_to_webpush_format(
            settings.VAPID_PRIVATE_KEY
        )

        self.assertNotIn("BEGIN PRIVATE KEY", converted)
        self.assertNotIn("\n", converted)
        # Should be accepted by py_vapid (same parser used by pywebpush)
        Vapid.from_string(converted)

    def test_private_key_conversion_supports_escaped_newlines(self):
        escaped_private_key = settings.VAPID_PRIVATE_KEY.replace("\n", "\\n")
        converted = PushNotificationService._private_key_to_webpush_format(
            escaped_private_key
        )

        self.assertNotIn("BEGIN PRIVATE KEY", converted)
        Vapid.from_string(converted)

    def test_public_key_conversion_from_pem_is_browser_compatible(self):
        converted = PushNotificationService._public_key_to_browser_format(
            settings.VAPID_PUBLIC_KEY
        )

        padding = "=" * ((4 - len(converted) % 4) % 4)
        decoded = base64.urlsafe_b64decode(converted + padding)
        self.assertEqual(len(decoded), 65)
        self.assertEqual(decoded[0], 0x04)

    def test_get_vapid_keys_returns_normalized_formats(self):
        keys = PushNotificationService.get_vapid_keys()

        self.assertIn("public_key", keys)
        self.assertIn("private_key", keys)

        # public key should be browser-compatible X9.62 uncompressed point
        public_padding = "=" * ((4 - len(keys["public_key"]) % 4) % 4)
        public_bytes = base64.urlsafe_b64decode(keys["public_key"] + public_padding)
        self.assertEqual(len(public_bytes), 65)
        self.assertEqual(public_bytes[0], 0x04)

        # private key should be accepted by py_vapid
        Vapid.from_string(keys["private_key"])
