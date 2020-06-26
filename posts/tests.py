from django.test import TestCase, Client, override_settings

from django.contrib.auth import get_user_model

from django.urls import reverse

from .models import Post, Group

from shutil import rmtree

from PIL import Image

import tempfile

import time


User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()
print(MEDIA_ROOT)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostTest(TestCase):
    CACHE_TIME = 21


    def _create_image(self):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            image = Image.new('RGB', (200, 200), 'white')
            image.save(f, 'PNG')
        return open(f.name, mode='rb')

    def _create_txt(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Hello world!')
        return open(f.name, mode='rb')

    def setUp(self):
        self.unauth_client = Client()
        self.auth_client = Client()

        self.user = User.objects.create_user(
            username="test_user",
            email="test@test.com",
            password="12345"
        )
        self.groups = [
            Group.objects.create(
                title="test_title_1",
                slug="test_slug_1"
            ),
            Group.objects.create(
                title="test_title_2",
                slug="test_slug_2"
            )
        ]
        self.texts = [
            "Lorem ipsum dolor sit amet",
            "consectetur adipiscing elit"
        ]
        self.files = {
            "img": [self._create_image(),
                    self._create_image()],
            "txt": [self._create_txt()]
        }
        self.form_error_messages = {
            "image_wrong_file": "Загрузите правильное изображение. "
            f"Файл, который вы загрузили, поврежден "
            f"или не является изображением."
        }

        self.auth_client.force_login(self.user)

    def tearDown(self):
        rmtree(MEDIA_ROOT, ignore_errors=True)

    def create_url_list_for_check_post(self, post, group):
        return [
            {
                "nameview": "index",
                "kwargs": {}
            },
            {
                "nameview": "group_posts",
                "kwargs": {"slug": group.slug}
            },
            {
                "nameview": "profile",
                "kwargs": {"username": self.user.username}
            },
            {
                "nameview": "post",
                "kwargs": {"username": self.user.username,
                           "post_id": post.pk}
            }
        ]

    def create_post_data(self, var, filetype="img"):
        return {
            "text": self.texts[var],
            "group": self.groups[var],
            "image": self.files[filetype][var]
        }

    def post_data_wrapper(self, data):
        return {
            "text": data["text"],
            "group": data["group"].pk,
            "image": data["image"]
        }

    def post_response_handler(self, response, data):
        self.assertEqual(response.status_code, 200)
        return self.user.posts.get(text=data["text"])

    def return_post_from_context(self, response):
        if "paginator" in response.context:
            return response.context["page"][0]
        else:
            return response.context["post"]

    def add_post(self, c, data):
        return c.post(
            reverse("new_post"),
            data=self.post_data_wrapper(data),
            follow=True
        )

    def edit_post(self, c, post, data):
        return c.post(
            reverse("post_edit", kwargs={
                "username": self.user.username,
                "post_id": post.pk}),
            data=self.post_data_wrapper(data),
            follow=True
        )

    def check_post(self, c, post, data):
        time.sleep(self.CACHE_TIME)

        group = data["group"]
        url_list = self.create_url_list_for_check_post(post, group)

        for url in url_list:
            response = c.post(
                reverse(url["nameview"], kwargs=url["kwargs"]),
                follow=True
            )
            self.assertContains(
                response,
                post.text,
                count=1,
                status_code=200,
                html=False
            )
            post_from_context = self.return_post_from_context(response)
            self.assertEqual(
                post_from_context.author.username,
                self.user.username
            )
            self.assertEqual(post_from_context.group, group)
            self.assertEqual(post_from_context.text, post.text)
            self.assertContains(
                response,
                "<img",
                count=1,
                html=False
            )

        self.assertEqual(Post.objects.count(), 1)

    def check_cache_main_page(self, c, post):
        response = c.post(reverse("index"), follow=True)
        self.assertNotContains(
            response,
            post.text,
            status_code=200,
            html=False
        )

    def test_post_auth_user(self):
        c = self.auth_client

        data = self.create_post_data(0)
        response = self.add_post(c, data)
        post = self.post_response_handler(response, data)
        self.check_post(c, post, data)

        data = self.create_post_data(1)
        response = self.edit_post(c, post, data)
        post = self.post_response_handler(response, data)
        self.check_cache_main_page(c, post)
        self.check_post(c, post, data)

    def test_cache(self):
        c = self.auth_client

        data = self.create_post_data(0)
        self.add_post(c, data)

        data = self.create_post_data(1)
        response = self.add_post(c, data)
        post = self.post_response_handler(response, data)

        self.check_cache_main_page(c, post)

    def test_post_unauth_user(self):
        c = self.unauth_client

        data = self.create_post_data(0)
        response = self.add_post(c, data)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next=/new/",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_wrong_image(self):
        c = self.auth_client

        data = self.create_post_data(0, filetype="txt")
        response = self.add_post(c, data)

        self.assertFormError(
            response,
            "form",
            "image",
            self.form_error_messages["image_wrong_file"]
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_profile(self):
        response = self.auth_client.post(
            reverse("profile", kwargs={"username": self.user.username}),
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(
            response.context["author"].username,
            self.user.username)

        self.assertIsInstance(response.context["user"], User)
        self.assertEqual(response.context["user"].username, self.user.username)

    def test_404_response(self):
        response = self.auth_client.get("/some-wrong-test-url/")
        self.assertEqual(response.status_code, 404)
