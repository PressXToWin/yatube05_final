from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_page_obj

POSTS_COUNT = 10


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    """Рендер для главной страницы."""
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = get_page_obj(post_list, POSTS_COUNT, request)
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Рендер для страницы групп."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_page_obj(post_list, POSTS_COUNT, request)
    context = {
        'title': f'Записи сообщества {group}',
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    post_list = Post.objects.filter(author=author)
    page_obj = get_page_obj(post_list, POSTS_COUNT, request)
    following = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(user=request.user, author=author)
        if follow:
            following = True
    context = {
        'author': author,
        'post_list': post_list,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    comment_list = Comment.objects.filter(post=post.id)
    form = CommentForm()
    context = {
        'post': post,
        'comments': comment_list,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not request.method == 'POST' or not form.is_valid():
        context = {'form': form}
        return render(request, 'posts/create_post.html', context)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        username = request.user.get_username()
        return redirect('posts:profile', username=username)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id=post_id)
    if not request.method == 'POST' or not form.is_valid():
        context = {
            'form': form,
            'post_id': post_id,
            'is_edit': True
        }
        return render(request, 'posts/create_post.html', context)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(post_list, POSTS_COUNT, request)
    context = {
        'title': 'Лента подписок',
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = User.objects.get(username=username)
    is_following = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not is_following:
        follow = Follow(user=request.user, author=author)
        follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    follow = Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username))
    follow.delete()
    return redirect('posts:profile', username=username)
