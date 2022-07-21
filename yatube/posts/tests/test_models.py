from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Test group title',
            slug='test-slug',
            description='Test group description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Some incredible post text for model str method testing',
        )

    def test_models_have_correct_object_names(self):
        """Проверка, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        expected_object_names = {
            post: post.text[:15],
            group: group.title,
        }
        for model_object, expected_name in expected_object_names.items():
            with self.subTest(object=model_object):
                self.assertEqual(
                    str(model_object), expected_name)
