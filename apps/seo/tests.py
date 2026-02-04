from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import SEOData
from .services.seo_service import SEOService
from .utils import SEOAnalyzer, StructuredDataGenerator

User = get_user_model()


class SEODataModelTest(TestCase):
    def setUp(self):
        # Create a test user for content object
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        # Get content type for User model
        self.content_type = ContentType.objects.get_for_model(User)

    def test_seo_data_creation(self):
        seo_data = SEOData.objects.create(
            content_type=self.content_type,
            object_id=self.user.id,
            title="Test SEO Title",
            description="Test SEO description for testing purposes",
            keywords="test, seo, keywords",
        )

        self.assertEqual(seo_data.content_object, self.user)
        self.assertEqual(seo_data.title, "Test SEO Title")
        self.assertEqual(
            seo_data.description, "Test SEO description for testing purposes"
        )
        self.assertEqual(seo_data.keywords, "test, seo, keywords")

    def test_seo_data_str_method(self):
        seo_data = SEOData.objects.create(
            content_type=self.content_type,
            object_id=self.user.id,
            title="Test Title",
            description="Test description",
        )

        expected_str = f"SEO for {self.user}"
        self.assertEqual(str(seo_data), expected_str)


class SEOServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.content_type = "users.user"

    def test_create_seo_data(self):
        seo_data_dict = {
            "title": "Test Title",
            "description": "Test description",
            "keywords": "test, keywords",
        }

        seo_data = SEOService.create_seo_data(
            content_type=self.content_type,
            object_id=self.user.id,
            seo_data=seo_data_dict,
        )

        self.assertEqual(seo_data.title, "Test Title")
        self.assertEqual(seo_data.content_object, self.user)

    def test_create_duplicate_seo_data_raises_error(self):
        seo_data_dict = {"title": "Test Title", "description": "Test description"}

        # Create first SEO data
        SEOService.create_seo_data(
            content_type=self.content_type,
            object_id=self.user.id,
            seo_data=seo_data_dict,
        )

        # Try to create duplicate - should raise error
        with self.assertRaises(ValueError):
            SEOService.create_seo_data(
                content_type=self.content_type,
                object_id=self.user.id,
                seo_data=seo_data_dict,
            )

    def test_get_or_create_seo_data(self):
        defaults = {"title": "Default Title", "description": "Default description"}

        # First call should create
        seo_data, created = SEOService.get_or_create_seo_data(
            content_type=self.content_type, object_id=self.user.id, defaults=defaults
        )

        self.assertTrue(created)
        self.assertEqual(seo_data.title, "Default Title")

        # Second call should get existing
        seo_data2, created2 = SEOService.get_or_create_seo_data(
            content_type=self.content_type,
            object_id=self.user.id,
            defaults={"title": "Different Title"},
        )

        self.assertFalse(created2)
        self.assertEqual(seo_data.id, seo_data2.id)
        self.assertEqual(seo_data2.title, "Default Title")  # Should keep original

    def test_bulk_create_seo_data(self):
        # Create additional users
        user2 = User.objects.create_user(email="test2@example.com", password="pass")
        user3 = User.objects.create_user(email="test3@example.com", password="pass")

        object_ids = [self.user.id, user2.id, user3.id]
        seo_data = {"title": "Bulk Title", "description": "Bulk description"}

        result = SEOService.bulk_create_seo_data(
            content_type=self.content_type, object_ids=object_ids, seo_data=seo_data
        )

        self.assertEqual(result["created_count"], 3)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(SEOData.objects.count(), 3)

    def test_get_seo_stats(self):
        # Create some test SEO data
        SEOService.create_seo_data(
            self.content_type,
            self.user.id,
            {"title": "Title", "description": "Desc", "keywords": "key"},
        )

        stats = SEOService.get_seo_stats()

        self.assertEqual(stats["total_seo_data"], 1)
        self.assertIn("by_content_type", stats)
        self.assertIn("completeness", stats)


class SEOAnalyzerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.content_type = ContentType.objects.get_for_model(User)

        self.analyzer = SEOAnalyzer()

    def test_analyze_good_seo_data(self):
        seo_data = SEOData.objects.create(
            content_type=self.content_type,
            object_id=self.user.id,
            title="This is a good SEO title with proper length",
            description="This is a good meta description that falls within the recommended character limit for search engines and provides useful information.",
            keywords="seo, test, good, keywords, optimization",
            og_title="Good OG Title",
            og_description="Good OG description",
        )

        analysis = self.analyzer.analyze_seo_data(seo_data)

        self.assertEqual(analysis["title_score"], "good")
        self.assertEqual(analysis["description_score"], "good")
        self.assertEqual(analysis["keywords_score"], "good")
        self.assertGreater(analysis["og_completeness"], 0.5)
        self.assertIn(analysis["overall_score"], ["good", "excellent"])

    def test_analyze_poor_seo_data(self):
        seo_data = SEOData.objects.create(
            content_type=self.content_type,
            object_id=self.user.id,
            title="Short",  # Too short
            description="Short desc",  # Too short
            keywords="",  # Missing
        )

        analysis = self.analyzer.analyze_seo_data(seo_data)

        self.assertEqual(analysis["title_score"], "too_short")
        self.assertEqual(analysis["description_score"], "too_short")
        self.assertEqual(analysis["keywords_score"], "missing")
        self.assertEqual(analysis["og_completeness"], 0.0)
        self.assertEqual(analysis["overall_score"], "poor")
        self.assertGreater(len(analysis["recommendations"]), 0)


class StructuredDataGeneratorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.generator = StructuredDataGenerator()

    def test_generate_generic_schema(self):
        schema = self.generator.generate_for_object(self.user)

        self.assertEqual(schema["@context"], "https://schema.org")
        self.assertEqual(schema["@type"], "Thing")
        self.assertIn("name", schema)
        self.assertIn("url", schema)


class SEOAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.content_type = ContentType.objects.get_for_model(User)

        # Create test SEO data
        self.seo_data = SEOData.objects.create(
            content_type=self.content_type,
            object_id=self.user.id,
            title="Test SEO Title",
            description="Test SEO description",
            keywords="test, seo",
        )

    def test_list_seo_data(self):
        url = reverse("seodata-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_seo_data_detail(self):
        url = reverse("seodata-detail", kwargs={"pk": self.seo_data.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test SEO Title")

    def test_filter_by_content_type(self):
        url = reverse("seodata-list")
        response = self.client.get(url, {"content_type": "users.user"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_seo_data(self):
        url = reverse("seodata-list")
        response = self.client.get(url, {"search": "Test SEO"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_seo_for_object(self):
        url = reverse("seodata-for-object")
        response = self.client.get(
            url, {"content_type": "users.user", "object_id": self.user.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test SEO Title")

    def test_get_seo_for_nonexistent_object(self):
        url = reverse("seodata-for-object")
        response = self.client.get(
            url, {"content_type": "users.user", "object_id": 99999}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_generate_meta_tags(self):
        url = reverse("seodata-meta-tags", kwargs={"pk": self.seo_data.pk})
        response = self.client.get(url, {"canonical_url": "https://example.com/test"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta_tags", response.data)
        self.assertIn("meta_tags_html", response.data)

    def test_analyze_seo_data(self):
        url = reverse("seodata-analyze", kwargs={"pk": self.seo_data.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("overall_score", response.data)
        self.assertIn("recommendations", response.data)

    def test_get_seo_stats(self):
        url = reverse("seodata-stats")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_seo_data", response.data)
        self.assertIn("completeness", response.data)

    def test_get_content_types(self):
        url = reverse("seodata-content-types")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_create_seo_data_authenticated(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("seodata-list")
        data = {
            "content_type": self.content_type.id,
            "object_id": self.user.id + 1,  # Different object
            "title": "New SEO Title",
            "description": "New SEO description",
        }

        # This will fail because object doesn't exist, but tests authentication
        response = self.client.post(url, data)
        self.assertIn(
            response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED]
        )

    def test_create_seo_data_unauthenticated(self):
        url = reverse("seodata-list")
        data = {
            "content_type": self.content_type.id,
            "object_id": 999,
            "title": "New SEO Title",
            "description": "New SEO description",
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_seo_health_check(self):
        url = reverse("seotools-seo-health-check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_checked", response.data)
        self.assertIn("health_percentage", response.data)

    def test_validate_structured_data(self):
        url = reverse("seotools-validate-structured-data")
        data = {
            "schema_type": "Article",
            "data": {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Test Article",
            },
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])

    def test_validate_invalid_structured_data(self):
        url = reverse("seotools-validate-structured-data")
        data = {"schema_type": "InvalidType", "data": {}}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
