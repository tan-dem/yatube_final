from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Test post text',
            id=100500,
        )
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test-slug',
            description='Test group description',
        )

        cls.URLS_VS_TEMPLATES_GUEST = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.URLS_VS_TEMPLATES_AUTHORIZED = {
            '/create/': 'posts/create_post.html',
        }
        cls.URLS_VS_TEMPLATES_AUTHOR = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_available_for_guest(self):
        """Проверка общедоступных страниц."""
        for url in self.URLS_VS_TEMPLATES_GUEST:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_available_for_authorized(self):
        """Проверка страниц, доступных для авторизованного пользователя."""
        for url in self.URLS_VS_TEMPLATES_AUTHORIZED:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_available_for_author(self):
        """Проверка страниц, доступных для автора поста."""
        for url in self.URLS_VS_TEMPLATES_AUTHOR:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_guest(self):
        """Проверка перенаправления неавторизованного пользователя
        на страницу логина."""
        url_list = [
            *list(self.URLS_VS_TEMPLATES_AUTHORIZED),
            *list(self.URLS_VS_TEMPLATES_AUTHOR),
        ]
        url_redirect = '/auth/login/?next='
        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, url_redirect + url)

    def test_post_edit_url_redirects_not_author(self):
        """Проверка страницы /posts/<post_id>/edit/ -> перенаправляет
        не автора поста на страницу просмотра поста."""
        url_list = self.URLS_VS_TEMPLATES_AUTHOR
        url_redirect = f'/posts/{self.post.id}/'
        for url in url_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(response, url_redirect)

    def test_url_unexisting_page(self):
        """Проверка запроса к несуществующей странице."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_use_correct_templates_guest(self):
        """Проверка общедоступных страниц
        -> URL-адреса используют соответствующие шаблоны."""
        for url, template in self.URLS_VS_TEMPLATES_GUEST.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_use_correct_templates_authorized(self):
        """Проверка страниц, доступных для авторизованного пользователя
        -> URL-адреса используют соответствующие шаблоны."""
        for url, template in self.URLS_VS_TEMPLATES_AUTHORIZED.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_use_correct_templates_author(self):
        """Проверка страниц, доступных для автора поста
        -> URL-адреса используют соответствующие шаблоны."""
        for url, template in self.URLS_VS_TEMPLATES_AUTHOR.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_add_comment_authorized_and_guest(self):
        """Проверка: комментировать пост может только авторизованный
         пользователь, неавторизованный перенаправляется на страницу логина."""
        url_comment = f'/posts/{self.post.id}/comment/'
        url_post_detail = f'/posts/{self.post.id}/'
        url_redirect_guest = '/auth/login/?next='
        response_authorized = self.authorized_client.post(
            url_comment,
            follow=True
        )
        response_guest = self.guest_client.post(url_comment, follow=True)
        self.assertRedirects(response_authorized, url_post_detail)
        self.assertRedirects(response_guest, url_redirect_guest + url_comment)
