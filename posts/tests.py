from django.test import TestCase

from django.test import Client

from django.contrib.auth import get_user_model

from django.urls import reverse

from .models import Post, Group


User = get_user_model()


class PostTest(TestCase):
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

        self.auth_client.force_login(self.user)

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

    def return_post_from_context(self, response):
        if "paginator" in response.context:
            return response.context["page"][0]
        else:
            return response.context["post"]

    def add_post(self, c, text, group):
        response = c.post(
            reverse("new_post"),
            data={
                "text": text,
                "group": group.pk},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        return self.user.posts.get(text=text)

    def edit_post(self, c, text, post, group):
        response = c.post(
            reverse("post_edit", kwargs={
                "username": self.user.username,
                "post_id": post.pk}),
            data={'text': text, "group": group.pk},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        return self.user.posts.get(text=text)

    def check_post(self, c, post, group):
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
            self.assertEqual(Post.objects.count(), 1)

    def test_post_auth_user(self):
        c = self.auth_client

        group = self.groups[0]
        text = self.texts[0]
        post = self.add_post(c, text, group)
        self.check_post(c, post, group)

        group = self.groups[1]
        text = self.texts[1]
        post = self.edit_post(c, text, post, group)
        self.assertEqual(post.text, text)
        self.check_post(c, post, group)

    def test_post_unauth_user(self):
        response = self.unauth_client.post(
            reverse("new_post"),
            data={"text": "test"}
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next=/new/",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True
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
