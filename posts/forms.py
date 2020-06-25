from django.forms import ModelForm

from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", 'image']
        labels = {
            "text": _("Текст поста"),
            "group": _("Группа"),
            "image": _("Изображение"),
        }
        help_texts = {
            "text": _("Введите текст поста"),
            "group": _("Выберите группу, к которой относится пост"),
            "image": _("Выберите изображение"),
        }
        error_messages = {
            "text": {
                "required": _("Вы не добавили текст поста"),
            },
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {
            "text": _("Текст комментария")
        }
        help_texts = {
            "text": _("Введите текст комментария"),
        }
        error_messages = {
            "text": {
                "required": _("Вы не добавили текст комментария"),
            },
        }
