from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):

    def setUp(self):
        super().setUp()
        self.guest_client = Client()

    URLS_VS_TEMPLATES = {
        '/about/author/': 'about/author.html',
        '/about/tech/': 'about/tech.html',
    }

    def test_urls_available(self):
        """Проверка общедоступных страниц."""
        for url in self.URLS_VS_TEMPLATES:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_templates(self):
        """Проверка общедоступных страниц
        -> URL-адреса используют соответствующие шаблоны."""
        for url, template in self.URLS_VS_TEMPLATES.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
