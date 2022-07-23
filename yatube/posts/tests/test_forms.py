import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Test post text',
            id=100501,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """При отправке валидной формы со страницы создания поста
        в базе данных создаётся новый пост."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'texty text',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author.username}'}
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(Post.objects.first().text, form_data['text'])
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_edit_post(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Some updated post text',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.last().text, form_data['text'])
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Test post text',
            id=100503,
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_add_comment(self):
        """После успешной отправки формы в базе данных создан комментарий."""
        post = self.post
        comments_count = post.comments.count()
        form_data = {
            'text': 'little test comment',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(post.comments.count(), comments_count + 1)
