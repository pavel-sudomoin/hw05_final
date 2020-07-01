import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from shutil import rmtree
from PIL import Image

from .models import Post, Group, Comment, Follow

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp()
DISABLE_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


@override_settings(CACHES=DISABLE_CACHE)
@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostTest(TestCase):
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

        self.users = (
            User.objects.create_user(
                username="test_user_1",
                email="test_1@test.com",
                password="12345"
            ),
            User.objects.create_user(
                username="test_user_2",
                email="test_2@test.com",
                password="12345"
            ),
        )

        self.groups = (
            Group.objects.create(
                title="test_title_1",
                slug="test_slug_1"
            ),
            Group.objects.create(
                title="test_title_2",
                slug="test_slug_2"
            )
        )
        self.texts = (
            "Lorem ipsum dolor sit amet",
            "consectetur adipiscing elit"
        )
        self.files = {
            "img": (self._create_image(),
                    self._create_image()),
            "txt": (self._create_txt(),)
        }
        self.form_error_messages = {
            "image_wrong_file": "Загрузите правильное изображение. "
            f"Файл, который вы загрузили, поврежден "
            f"или не является изображением."
        }

        self.comment_text = "comment_test_text"

        self.force_login(self.users[0])

    def tearDown(self):
        # добавил закрытие всех файлов после прохождения всех тестов
        for files_collection in self.files.values():
            for open_file in files_collection:
                open_file.close()
        rmtree(MEDIA_ROOT, ignore_errors=True)

    def force_login(self, user):
        self.user = user
        self.auth_client.force_login(self.user)

    def create_url_list_for_check_post(self, post, group):
        return (
            {
                "nameview": "index",
                "kwargs": {},
                "display_comments": False
            },
            {
                "nameview": "group_posts",
                "kwargs": {"slug": group.slug},
                "display_comments": False
            },
            {
                "nameview": "profile",
                "kwargs": {"username": self.user.username},
                "display_comments": False
            },
            {
                "nameview": "post",
                "kwargs": {"username": self.user.username,
                           "post_id": post.pk},
                "display_comments": True
            }
        )

    def create_post_data(self, var, filetype="img"):
        return {
            "text": self.texts[var],
            "group": self.groups[var],
            "image": self.files[filetype][var]
        }

    def create_comment_data(self):
        return {"text": self.comment_text}

    def post_data_wrapper(self, data):
        return {
            "text": data["text"],
            "group": data["group"].pk,
            "image": SimpleUploadedFile("img.png", data["image"].read(), content_type='image/gif')
        }

    def post_response_handler(self, response, data):
        self.assertEqual(response.status_code, 200)
        return self.user.posts.get(text=data["text"])

    def comment_response_handler(self, response, data):
        self.assertEqual(response.status_code, 200)
        return Comment.objects.get(text=data["text"])

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

    def add_comment(self, c, post, data):
        return c.post(
            reverse("add_comment", kwargs={
                "username": self.user.username,
                "post_id": post.pk}),
            data=data,
            follow=True
        )

    def subscribe(self, c, author):
        return c.post(
            reverse("profile_follow",
                    kwargs={"username": author.username}),
            follow=True
        )

    def add_post_handler(self, c, num):
        data = self.create_post_data(num)
        response = self.add_post(c, data)
        post = self.post_response_handler(response, data)
        return (data, post)

    def edit_post_handler(self, c, num, post):
        data = self.create_post_data(num)
        response = self.edit_post(c, post, data)
        post = self.post_response_handler(response, data)
        return (data, post)

    def check_login_redirect(self, response, url):
        self.assertRedirects(
            response,
            url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True
        )

    def check_post(self, c, post, data):
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

    def check_comment(self, c, post, comment, post_data, comment_data):
        group = post_data["group"]
        url_list = self.create_url_list_for_check_post(post, group)

        for url in url_list:
            response = c.post(
                reverse(url["nameview"], kwargs=url["kwargs"]),
                follow=True
            )
            if url["display_comments"]:
                self.assertContains(
                    response,
                    comment.text,
                    count=1,
                    status_code=200,
                    html=False
                )
            post_from_context = self.return_post_from_context(response)
            comments_from_context = post_from_context.comments.all()
            self.assertEqual(comments_from_context.count(), 1)
            comment_from_context = comments_from_context[0]
            self.assertEqual(
                comment_from_context.author.username,
                self.user.username
            )
            self.assertEqual(comment_from_context.text, comment.text)

        self.assertEqual(Comment.objects.count(), 1)

    def check_subscriptions(self, c, subscriber, author, author_post):
        response = c.post(reverse("follow_index"), follow=True)
        self.assertContains(
            response,
            author_post.text,
            count=1,
            status_code=200,
            html=False
        )

        response = c.post(
            reverse("profile", kwargs={"username": subscriber.username}),
            follow=True
        )
        subs_from_context = response.context["subscriptions"]
        self.assertEqual(subs_from_context["subscribers_count"], 0)
        self.assertEqual(subs_from_context["authors_count"], 1)

        response = c.post(
            reverse("profile", kwargs={"username": author.username}),
            follow=True
        )
        subs_from_context = response.context["subscriptions"]
        self.assertEqual(subs_from_context["subscribers_count"], 1)
        self.assertEqual(subs_from_context["authors_count"], 0)

        self.assertEqual(Follow.objects.count(), 1)
        follow_instance = Follow.objects.first()
        self.assertEqual(follow_instance.user, subscriber)
        self.assertEqual(follow_instance.author, author)

    def test_post_auth_user(self):
        c = self.auth_client

        data, post = self.add_post_handler(c, num=0)
        self.check_post(c, post=post, data=data)

        data, post = self.edit_post_handler(c, num=1, post=post)
        self.check_post(c, post=post, data=data)

    def test_follow_auth_user(self):
        c = self.auth_client

        author = self.users[0]
        subscriber = self.users[1]
        _, author_post = self.add_post_handler(c, num=0)

        self.force_login(subscriber)

        self.subscribe(c, author=author)

        self.check_subscriptions(
            c,
            subscriber=subscriber,
            author=author,
            author_post=author_post
        )

        self.force_login(author)
        response = c.post(reverse("follow_index"), follow=True)
        self.assertEqual(len(response.context["page"]), 0)

    def test_comment_auth_user(self):
        c = self.auth_client

        post_data, post = self.add_post_handler(c, num=0)

        comment_data = self.create_comment_data()
        comment_response = self.add_comment(c, post, comment_data)
        comment = self.comment_response_handler(comment_response, comment_data)
        self.check_comment(
            c,
            comment=comment,
            post=post,
            comment_data=comment_data,
            post_data=post_data
        )

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

    def test_post_unauth_user(self):
        c = self.unauth_client

        data = self.create_post_data(0)
        response = self.add_post(c, data)

        self.check_login_redirect(
            response,
            f"{reverse('login')}?next=/new/"
        )

        self.assertEqual(Post.objects.count(), 0)

    def test_follow_unauth_user(self):
        c = self.auth_client
        self.add_post_handler(c, num=0)

        c = self.unauth_client
        response = self.subscribe(c, author=self.user)

        self.check_login_redirect(
            response,
            f"{reverse('login')}?next=/{self.user.username}/follow/"
        )

        self.assertEqual(Follow.objects.count(), 0)

    def test_comment_unauth_user(self):
        auth_client = self.auth_client
        unauth_client = self.unauth_client

        _, post = self.add_post_handler(auth_client, num=0)

        data = self.create_comment_data()
        response = self.add_comment(unauth_client, post, data)

        self.check_login_redirect(
            response,
            f"{reverse('login')}?next=/{self.user.username}/{post.pk}/comment"
        )

        self.assertEqual(Comment.objects.count(), 0)

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


class CacheTest(TestCase):
    CACHE_TIME = 21

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="test_user",
            email="test@test.com",
            password="12345"
        )

        self.texts = (
            "Lorem ipsum dolor sit amet",
            "consectetur adipiscing elit"
        )

        self.client.force_login(self.user)

    def add_post(self, c, num):
        data = {"text": self.texts[num]}
        response = c.post(
            reverse("new_post"),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post = self.user.posts.get(text=data["text"])
        return post.text

    def test_cache(self):
        c = self.client

        self.add_post(c, num=0)
        text = self.add_post(c, num=1)

        self.assertNotContains(
            c.post(reverse("index"), follow=True),
            text,
            status_code=200,
            html=False
        )

        cache.clear()

        self.assertContains(
            c.post(reverse("index"), follow=True),
            text,
            status_code=200,
            html=False
        )
