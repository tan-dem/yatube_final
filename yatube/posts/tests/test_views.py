import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='Follower')
        cls.user_non_follower = User.objects.create_user(username='NoName')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test-slug',
            description='Test group description',
        )
        cls.post_with_group = Post.objects.create(
            author=cls.author,
            text='Test post text',
            id=100501,
            group=cls.group,
        )

        cls.NAMES_VS_TEMPLATES = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{cls.group.slug}'},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{cls.author.username}'},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{cls.post_with_group.id}'},
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{cls.post_with_group.id}'},
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.user_follower)
        self.authorized_non_follower = Client()
        self.authorized_non_follower.force_login(self.user_non_follower)
        cache.clear()

    def test_pages_use_correct_templates(self):
        """Проверка: при обращении к name вызывается соответствующий шаблон."""
        for reverse_name, template in self.NAMES_VS_TEMPLATES.items():
            with self.subTest(reverse_name=reverse_name, template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_index_group_list_profile_show_correct_context(self):
        """Проверка словаря контекста: шаблоны главной страницы,
        страницы с постами группы и страницы профиля."""
        pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group.slug}'}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author.username}'}
            ),
        ]
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].text,
                    self.post_with_group.text
                )
                self.assertEqual(
                    response.context['page_obj'][0].author,
                    self.post_with_group.author
                )
                self.assertEqual(
                    response.context['page_obj'][0].group,
                    self.post_with_group.group
                )

    def test_page_post_detail_shows_correct_context(self):
        """Проверка словаря контекста: страница проcмотра поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post_with_group.id}'},
            )
        )
        self.assertEqual(
            response.context['post'].text,
            self.post_with_group.text
        )
        self.assertEqual(
            response.context['post'].author,
            self.post_with_group.author
        )
        self.assertEqual(
            response.context['post'].group,
            self.post_with_group.group
        )

    def test_page_post_create_shows_correct_context(self):
        """Проверка словаря контекста: страница создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertFalse(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_page_post_edit_shows_correct_context(self):
        """Проверка словаря контекста: страница редактирования поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post_with_group.id}'},
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_with_group_is_shown_correctly(self):
        """Проверка, что созданный пост с указанием группы появляется
        на главной странице, странице этой группы и в профайле пользователя."""
        another_group = Group.objects.create(
            title='Another test group title',
            slug='another-test-slug',
        )
        post_with_another_group = Post.objects.create(
            author=self.author,
            text='Test post text',
            group=another_group,
        )
        pages_names_for_group_test = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{another_group.slug}'},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author.username}'},
            ),
        ]
        for reverse_name in pages_names_for_group_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].group,
                    post_with_another_group.group
                )

    def test_post_with_group_is_not_shown_on_other_group_page(self):
        """Проверка, что созданный пост с указанием группы не появляется
        на странице другой группы."""
        another_group = Group.objects.create(
            title='Another test group title',
            slug='another-test-slug',
        )
        post_with_another_group = Post.objects.create(
            author=self.author,
            text='Test post text',
            group=another_group,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group.slug}'}
            )
        )
        self.assertNotEqual(
            response.context['page_obj'][0].group,
            post_with_another_group.group
        )

    def test_image_added_to_post_is_shown_on_index_group_profile_pages(self):
        """Проверка, что при создании поста с картинкой изображение
        передаётся в контекст главной страницы, страницы группы
        и профайла пользователя."""
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
        post_with_image = Post.objects.create(
            author=self.author,
            text='Test post text',
            group=self.group,
            image=uploaded,
        )
        pages_names_for_image_test = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group.slug}'},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.author.username}'},
            ),
        ]
        for reverse_name in pages_names_for_image_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].image,
                    'posts/small.gif'
                )

    def test_image_added_to_post_is_shown_on_post_detail_page(self):
        """Проверка, что при создании поста с картинкой изображение
        передаётся в контекст страницы поста."""
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=test_gif,
            content_type='image/gif'
        )
        post_with_image = Post.objects.create(
            author=self.author,
            text='Test post text',
            group=self.group,
            image=uploaded,
        )
        pages_names_for_image_test = [
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{post_with_image.id}'},
            )
        ]
        for reverse_name in pages_names_for_image_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['post'].image,
                    'posts/test.gif'
                )

    def test_index_page_cache(self):
        """Проверка кэширования главной страницы."""
        post_cached = Post.objects.create(
            author=self.author,
            text='Test text for a post to be cached',
        )
        response_initial = self.guest_client.get(reverse('posts:index'))
        content_initial = response_initial.content
        post_cached.delete()
        response_new = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_new.content, content_initial)
        cache.clear()
        response_final = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_final.content, content_initial)

    def test_user_can_follow_and_unfollow_author(self):
        """Проверка, что авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        follow_count = Follow.objects.count()
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': f'{self.author.username}'},
            ),
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': f'{self.author.username}'},
            ),
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_available_for_follower(self):
        """Проверка, что новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        new_post = Post.objects.create(
            author=self.author,
            text='Some special text for a dear follower only',
        )
        Follow.objects.create(
            user=self.user_follower,
            author=self.author,
        )
        response = self.authorized_follower.get(reverse('posts:follow_index'))
        self.assertIn(new_post, response.context['page_obj'])

    def test_new_post_unavailable_for_non_follower(self):
        """Проверка, что новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        new_post = Post.objects.create(
            author=self.author,
            text='Some special text for a dear follower only',
        )
        response = self.authorized_non_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostsAuthor')
        cls.client = Client()
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test-slug',
        )
        cls.PAGES_NAMES_FOR_PAGINATOR_TEST = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{cls.group.slug}'}),
            reverse(
                'posts:profile',
                kwargs={'username': f'{cls.user.username}'},
            ),
        ]

        cls.test_posts_list = Post.objects.bulk_create([
            Post(author=cls.user, text='test-text', group=cls.group)
            for _ in range(14)
        ])

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        for reverse_name in self.PAGES_NAMES_FOR_PAGINATOR_TEST:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_four_records(self):
        """Проверка: количество постов на второй странице равно 4."""
        for reverse_name in self.PAGES_NAMES_FOR_PAGINATOR_TEST:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name, {'page': 2})
                self.assertEqual(len(response.context['page_obj']), 4)
