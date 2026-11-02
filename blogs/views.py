from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .forms import CommentForm, PostForm, ProfileForm, RegisterForm
from .models import Bookmark, Category, Comment, Like, Post, Profile, Tag


def _get_or_create_category(name):
    clean_name = name.strip()
    base_slug = slugify(clean_name)[:100] or 'category'
    category = Category.objects.filter(slug=base_slug).first()
    if category:
        return category
    candidate, counter = base_slug, 2
    while Category.objects.filter(slug=candidate).exists():
        candidate = f'{base_slug[:90]}-{counter}'
        counter += 1
    return Category.objects.create(name=clean_name, slug=candidate)


def _get_or_create_tag(name):
    base_slug = slugify(name)[:50] or 'tag'
    tag = Tag.objects.filter(slug=base_slug).first()
    if tag:
        return tag
    candidate, counter = base_slug, 2
    while Tag.objects.filter(slug=candidate).exists():
        candidate = f'{base_slug[:40]}-{counter}'
        counter += 1
    return Tag.objects.create(name=name, slug=candidate)


def _save_post_tags_and_category(form, post):
    if post.category_ref:
        post.category = post.category_ref.name
        post.save(update_fields=['category'])
    elif post.category:
        category = _get_or_create_category(post.category)
        post.category_ref = category
        post.save(update_fields=['category_ref'])
    tag_names = [name.strip().lower() for name in form.cleaned_data.get('tag_names', '').split(',') if name.strip()]
    post.tags.set([_get_or_create_tag(name) for name in tag_names])


def _visible_posts(user):
    posts = Post.objects.select_related('author', 'category_ref').prefetch_related('tags', 'likes')
    if user.is_authenticated:
        return posts.filter(Q(status=Post.PUBLISHED) | Q(author=user) | Q(author__isnull=True, status=Post.PUBLISHED)).distinct()
    return posts.filter(status=Post.PUBLISHED)


def home(request):
    posts = _visible_posts(request.user)
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    tag_slug = request.GET.get('tag', '').strip()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(category__icontains=query) | Q(tags__name__icontains=query)).distinct()
    if category_slug:
        posts = posts.filter(Q(category_ref__slug=category_slug) | Q(category__iexact=category_slug.replace('-', ' ')))
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)
    paginator = Paginator(posts, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blogs/home.html', {
        'page_obj': page_obj, 'posts': page_obj.object_list, 'page_title': 'Discover Stories',
        'query': query, 'categories': Category.objects.all(), 'active_category': category_slug,
        'featured_posts': _visible_posts(request.user).filter(is_featured=True)[:3],
    })


def post_detail_legacy(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return redirect(post.get_absolute_url())


def post_detail(request, slug):
    post = get_object_or_404(_visible_posts(request.user), slug=slug)
    comments = post.comments.filter(is_approved=True, parent__isnull=True).select_related('author').prefetch_related('replies__author')
    comment_form = CommentForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.info(request, 'Please log in to comment.')
            return redirect('login')
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, pk=parent_id, post=post, parent__isnull=True)
            comment.save()
            messages.success(request, 'Your comment has been added.')
            return redirect(post.get_absolute_url())
    liked = request.user.is_authenticated and post.likes.filter(user=request.user).exists()
    bookmarked = request.user.is_authenticated and post.bookmarks.filter(user=request.user).exists()
    return render(request, 'blogs/post_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form, 'liked': liked, 'bookmarked': bookmarked})


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        form.save_m2m()
        _save_post_tags_and_category(form, post)
        messages.success(request, 'Your post has been saved.')
        return redirect(post.get_absolute_url())
    return render(request, 'blogs/post_form.html', {'form': form, 'page_heading': 'Create a new post', 'button_label': 'Save post'})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author_id != request.user.id and not request.user.is_staff:
        messages.error(request, 'You can only edit your own posts.')
        return redirect(post.get_absolute_url())
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated.save()
        form.save_m2m()
        _save_post_tags_and_category(form, updated)
        messages.success(request, 'Your post has been updated.')
        return redirect(updated.get_absolute_url())
    return render(request, 'blogs/post_form.html', {'form': form, 'page_heading': 'Edit post', 'button_label': 'Update post'})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author_id != request.user.id and not request.user.is_staff:
        messages.error(request, 'You can only delete your own posts.')
        return redirect(post.get_absolute_url())
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'The post was deleted.')
        return redirect('dashboard')
    return render(request, 'blogs/delete_post.html', {'post': post})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to BlogSphere! Your account is ready.')
        return redirect('home')
    return render(request, 'blogs/register.html', {'form': form})


@login_required
def dashboard(request):
    posts = Post.objects.filter(author=request.user).order_by('-updated_at')
    return render(request, 'blogs/dashboard.html', {'posts': posts, 'draft_count': posts.filter(status=Post.DRAFT).count(), 'published_count': posts.filter(status=Post.PUBLISHED).count()})


def author_profile(request, username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    author = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=author)
    posts = Post.objects.filter(author=author, status=Post.PUBLISHED).order_by('-published_at')
    return render(request, 'blogs/profile.html', {'author': author, 'profile': profile, 'posts': posts})


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('author_profile', username=request.user.username)
    return render(request, 'blogs/profile_form.html', {'form': form})


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status=Post.PUBLISHED)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return redirect(post.get_absolute_url())


@login_required
@require_POST
def toggle_bookmark(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status=Post.PUBLISHED)
    bookmark, created = Bookmark.objects.get_or_create(post=post, user=request.user)
    if not created:
        bookmark.delete()
    return redirect(post.get_absolute_url())


@login_required
def bookmarks(request):
    saved = Post.objects.filter(bookmarks__user=request.user, status=Post.PUBLISHED).select_related('author')
    return render(request, 'blogs/bookmarks.html', {'posts': saved})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(status=Post.PUBLISHED, category_ref=category).select_related('author')
    return render(request, 'blogs/listing.html', {'page_title': category.name, 'posts': posts, 'description': category.description})


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(status=Post.PUBLISHED, tags=tag).select_related('author')
    return render(request, 'blogs/listing.html', {'page_title': f'#{tag.name}', 'posts': posts})
