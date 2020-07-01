from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth.decorators import login_required

from django.contrib.auth import get_user_model

from django.core.paginator import Paginator

from .models import Post, Group, Comment, Follow

from .forms import PostForm, CommentForm


User = get_user_model()


def get_subscriptions(user, author):
    if user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    else:
        following = False
    return {
        "following": following,
        "subscribers_count": Follow.objects.filter(author=author).count(),
        "authors_count": Follow.objects.filter(user=author).count()
    }


def create_paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return (paginator, page)


# Замечание: Кэширование потерял - @cache_page(20, key_prefix='index_page')
# Ответ: Кэширование настроено в самом шаблоне "index.html" - {% cache 20 index_page %}
def index(request):
    post_list = Post.objects.all()
    paginator, page = create_paginator(request, post_list)
    return render(request, "index.html", {
        "page": page,
        "paginator": paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator, page = create_paginator(request, post_list)
    return render(request, "group.html", {
        "group": group,
        "page": page,
        "paginator": paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new_post.html", {
        "form": form,
        "title": "Добавить запись",
        "button": "Добавить"
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator, page = create_paginator(request, post_list)
    subscriptions = get_subscriptions(user=request.user, author=author)
    return render(request, "profile.html", {
        "author": author,
        "page": page,
        "paginator": paginator,
        "author_posts_count": author.posts.count(),
        "subscriptions": subscriptions
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    subscriptions = get_subscriptions(user=request.user, author=author)
    return render(request, "post.html", {
        "author": author,
        "post": post,
        "form": form,
        "author_posts_count": author.posts.count(),
        "subscriptions": subscriptions
    })


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect("post", username=username, post_id=post_id)

    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)

    return render(request, "new_post.html", {
        "form": form,
        "post": post,
        "title": "Редактировать запись",
        "button": "Сохранить"
    })


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        post = get_object_or_404(Post, pk=post_id, author__username=username)
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("post", username=username, post_id=post_id)


@login_required
def follow_index(request):
    subscriptions = Follow.objects.filter(user=request.user)
    authors = [sub.author for sub in subscriptions]
    posts = Post.objects.filter(author__in=authors)
    paginator, page = create_paginator(request, posts)
    return render(request, "follow.html", {
        "page": page,
        "paginator": paginator
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    try:
        Follow.objects.get(user=request.user, author=author).delete()
    except Follow.DoesNotExist:
        pass
    return redirect("profile", username=username)
