from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from PIL import Image
import io
import os
import tempfile
from .models import Media
from .services.media_service import MediaService
from .utils import MediaValidator, MediaProcessor, MediaUtils

User = get_user_model()

class MediaModelTest(TestCase):
    def setUp(self):
        # Create a test user for content object
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Get content type for User model
        self.content_type = ContentType.objects.get_for_model(User)
        
        # Create a test image file
        self.test_image = self.create_test_image()

    def create_test_image(self):
        """Create a test image file"""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_media_creation(self):
        media = Media.objects.create(
            file=self.test_image,
            title='Test Image',
            alt_text='A test image',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(media.content_object, self.user)
        self.assertEqual(media.title, 'Test Image')
        self.assertEqual(media.alt_text, 'A test image')
        self.assertTrue(media.file)

    def test_media_str_method(self):
        media = Media.objects.create(
            file=self.test_image,
            title='Test Media',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(str(media), 'Test Media')

    def test_media_without_title_uses_filename(self):
        media = Media.objects.create(
            file=self.test_image,
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        # Should use filename when no title is provided
        self.assertIn('test_image', str(media))

class MediaValidatorTest(TestCase):
    def setUp(self):
        self.validator = MediaValidator()

    def create_test_file(self, name, size, content_type='image/jpeg'):
        """Create a test file with specified size"""
        content = b'x' * size
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type=content_type
        )

    def test_validate_valid_image(self):
        # Create a valid test image
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        test_file = SimpleUploadedFile(
            name='valid_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )
        
        file_info = self.validator.validate_file(test_file)
        
        self.assertEqual(file_info['type'], 'image')
        self.assertEqual(file_info['extension'], '.jpg')
        self.assertIn('width', file_info)
        self.assertIn('height', file_info)

    def test_validate_file_too_large(self):
        # Create a file that's too large
        large_file = self.create_test_file('large.jpg', 11 * 1024 * 1024)  # 11MB
        
        with self.assertRaises(ValueError) as context:
            self.validator.validate_file(large_file)
        
        self.assertIn('too large', str(context.exception))

    def test_validate_invalid_extension(self):
        invalid_file = self.create_test_file('test.exe', 1024)
        
        with self.assertRaises(ValueError) as context:
            self.validator.validate_file(invalid_file)
        
        self.assertIn('not allowed', str(context.exception))

    def test_validate_no_file(self):
        with self.assertRaises(ValueError) as context:
            self.validator.validate_file(None)
        
        self.assertEqual(str(context.exception), 'No file provided')

class MediaServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.content_type = 'users.user'
        
        # Create test image
        self.test_image = self.create_test_image()

    def create_test_image(self):
        image = Image.new('RGB', (100, 100), color='green')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name='service_test.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_create_media(self):
        media = MediaService.create_media(
            file=self.test_image,
            title='Service Test',
            alt_text='Test alt text',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        self.assertEqual(media.title, 'Service Test')
        self.assertEqual(media.alt_text, 'Test alt text')
        self.assertEqual(media.content_object, self.user)

    def test_get_media_for_object(self):
        # Create media for the user
        MediaService.create_media(
            file=self.test_image,
            title='User Media',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        media_files = MediaService.get_media_for_object(self.content_type, self.user.id)
        
        self.assertEqual(len(media_files), 1)
        self.assertEqual(media_files[0].title, 'User Media')

    def test_get_media_stats(self):
        # Create some test media
        MediaService.create_media(
            file=self.test_image,
            title='Stats Test',
            content_type=self.content_type,
            object_id=self.user.id
        )
        
        stats = MediaService.get_media_stats()
        
        self.assertEqual(stats['total_files'], 1)
        self.assertIn('by_type', stats)
        self.assertIn('by_content_type', stats)
        self.assertGreaterEqual(stats['total_size'], 0)

class MediaUtilsTest(TestCase):
    def test_format_file_size(self):
        self.assertEqual(MediaUtils.format_file_size(0), "0 B")
        self.assertEqual(MediaUtils.format_file_size(1024), "1.0 KB")
        self.assertEqual(MediaUtils.format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(MediaUtils.format_file_size(1024 * 1024 * 1024), "1.0 GB")

    def test_is_image_file(self):
        self.assertTrue(MediaUtils.is_image_file('test.jpg'))
        self.assertTrue(MediaUtils.is_image_file('test.png'))
        self.assertTrue(MediaUtils.is_image_file('test.gif'))
        self.assertFalse(MediaUtils.is_image_file('test.pdf'))
        self.assertFalse(MediaUtils.is_image_file('test.mp4'))

    def test_is_video_file(self):
        self.assertTrue(MediaUtils.is_video_file('test.mp4'))
        self.assertTrue(MediaUtils.is_video_file('test.avi'))
        self.assertFalse(MediaUtils.is_video_file('test.jpg'))
        self.assertFalse(MediaUtils.is_video_file('test.pdf'))

    def test_clean_filename(self):
        self.assertEqual(MediaUtils.clean_filename('test<>file.jpg'), 'test__file.jpg')
        self.assertEqual(MediaUtils.clean_filename('test|file?.jpg'), 'test_file_.jpg')
        self.assertEqual(MediaUtils.clean_filename('___test___.jpg'), 'test.jpg')

class MediaAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        
        # Create test media
        self.test_image = self.create_test_image()
        self.media = Media.objects.create(
            file=self.test_image,
            title='API Test Media',
            alt_text='Test alt text',
            content_type=self.content_type,
            object_id=self.user.id
        )

    def create_test_image(self):
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name='api_test.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_list_media(self):
        url = reverse('media-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_media_detail(self):
        url = reverse('media-detail', kwargs={'pk': self.media.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'API Test Media')
        self.assertIn('file_url', response.data)
        self.assertIn('file_size', response.data)
        self.assertIn('file_type', response.data)

    def test_filter_by_content_type(self):
        url = reverse('media-list')
        response = self.client.get(url, {'content_type': 'users.user'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_file_type(self):
        url = reverse('media-list')
        response = self.client.get(url, {'file_type': 'image'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_media(self):
        url = reverse('media-list')
        response = self.client.get(url, {'search': 'API Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_media_for_object(self):
        url = reverse('media-for-object')
        response = self.client.get(url, {
            'content_type': 'users.user',
            'object_id': self.user.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'API Test Media')

    def test_get_media_for_nonexistent_object(self):
        url = reverse('media-for-object')
        response = self.client.get(url, {
            'content_type': 'users.user',
            'object_id': 99999
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_gallery_view(self):
        url = reverse('media-gallery')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('media', response.data)
        self.assertIn('total_count', response.data)
        self.assertIn('page_count', response.data)

    def test_get_media_stats(self):
        url = reverse('media-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_files', response.data)
        self.assertIn('by_type', response.data)

    def test_get_content_types(self):
        url = reverse('media-content-types')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_upload_media_authenticated(self):
        self.client.force_authenticate(user=self.user)
        
        # Create new test image
        new_image = self.create_test_image()
        
        url = reverse('media-list')
        data = {
            'file': new_image,
            'title': 'New Upload',
            'alt_text': 'New upload alt text',
            'content_type': self.content_type.id,
            'object_id': self.user.id
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_media_unauthenticated(self):
        new_image = self.create_test_image()
        
        url = reverse('media-list')
        data = {
            'file': new_image,
            'title': 'New Upload',
            'content_type': self.content_type.id,
            'object_id': self.user.id
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_media_metadata(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('media-detail', kwargs={'pk': self.media.pk})
        data = {
            'title': 'Updated Title',
            'alt_text': 'Updated alt text'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.media.refresh_from_db()
        self.assertEqual(self.media.title, 'Updated Title')
        self.assertEqual(self.media.alt_text, 'Updated alt text')

    def test_delete_media(self):
        self.client.force_authenticate(user=self.user)
        
        url = reverse('media-detail', kwargs={'pk': self.media.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Media.objects.filter(pk=self.media.pk).exists())

    def test_get_recent_media(self):
        url = reverse('media-recent')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_validate_file_tool(self):
        url = reverse('mediatools-validate-file')
        
        # Create test file
        test_file = self.create_test_image()
        
        response = self.client.post(url, {'file': test_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertIn('file_info', response.data)

    def test_get_storage_info(self):
        url = reverse('mediatools-storage-info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Storage info might have errors in test environment, so just check it returns data
        self.assertIsInstance(response.data, dict)