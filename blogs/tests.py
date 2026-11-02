from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Bookmark, Category, Comment, Like, Post, Profile, Tag


class BlogSphereTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='writer', password='StrongPass123!')
        self.reader = User.objects.create_user(username='reader', password='StrongPass123!')
        self.category = Category.objects.create(name='Technology', slug='technology')
        self.tag = Tag.objects.create(name='Django', slug='django')
        self.post = Post.objects.create(
            author=self.author, title='Test story', content='A useful Django article.',
            category='Technology', category_ref=self.category, status=Post.PUBLISHED,
        )
        self.post.tags.add(self.tag)

    def test_homepage_displays_published_post(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_detail_page_displays_article(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A useful Django article.')

    def test_legacy_numeric_url_redirects_to_slug(self):
        response = self.client.get(reverse('post_detail_legacy', args=[self.post.pk]))
        self.assertRedirects(response, self.post.get_absolute_url())

    def test_registration_creates_user_and_profile(self):
        response = self.client.post(reverse('register'), {
            'username': 'newwriter', 'email': 'new@example.com',
            'password1': 'SafePassword456!', 'password2': 'SafePassword456!',
        })
        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(username='newwriter')
        self.assertTrue(user.check_password('SafePassword456!'))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_create_post_requires_login(self):
        response = self.client.get(reverse('create_post'))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("create_post")}')

    def test_author_can_create_post(self):
        self.client.login(username='writer', password='StrongPass123!')
        response = self.client.post(reverse('create_post'), {
            'title': 'Created from website', 'content': 'Post body', 'category': 'Technology',
            'status': Post.PUBLISHED, 'tag_names': 'python, django',
        })
        post = Post.objects.get(title='Created from website')
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.tags.count(), 2)

    def test_author_can_edit_own_post(self):
        self.client.login(username='writer', password='StrongPass123!')
        response = self.client.post(reverse('edit_post', args=[self.post.pk]), {
            'title': 'Updated story', 'content': 'Updated body', 'category': 'Technology',
            'status': Post.PUBLISHED, 'tag_names': 'django',
        })
        self.post.refresh_from_db()
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(self.post.title, 'Updated story')

    def test_other_user_cannot_edit_post(self):
        self.client.login(username='reader', password='StrongPass123!')
        response = self.client.get(reverse('edit_post', args=[self.post.pk]))
        self.assertRedirects(response, self.post.get_absolute_url())
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Test story')

    def test_author_can_delete_own_post_with_post_request(self):
        self.client.login(username='writer', password='StrongPass123!')
        response = self.client.post(reverse('delete_post', args=[self.post.pk]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_drafts_are_not_public(self):
        draft = Post.objects.create(author=self.author, title='Private draft', content='Not public', status=Post.DRAFT)
        response = self.client.get(draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        self.client.login(username='writer', password='StrongPass123!')
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 200)

    def test_like_and_bookmark_are_post_only(self):
        self.client.login(username='reader', password='StrongPass123!')
        like_url = reverse('toggle_like', args=[self.post.pk])
        bookmark_url = reverse('toggle_bookmark', args=[self.post.pk])
        self.assertEqual(self.client.get(like_url).status_code, 405)
        self.client.post(like_url)
        self.client.post(bookmark_url)
        self.assertTrue(Like.objects.filter(post=self.post, user=self.reader).exists())
        self.assertTrue(Bookmark.objects.filter(post=self.post, user=self.reader).exists())

    def test_comment_is_saved_for_logged_in_user(self):
        self.client.login(username='reader', password='StrongPass123!')
        response = self.client.post(self.post.get_absolute_url(), {'body': 'Great article!'})
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertTrue(Comment.objects.filter(post=self.post, author=self.reader, body='Great article!').exists())

    def test_category_listing(self):
        response = self.client.get(reverse('category_detail', args=['technology']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_tag_listing(self):
        response = self.client.get(reverse('tag_detail', args=['django']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_author_profile(self):
        response = self.client.get(reverse('author_profile', args=['writer']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_search_finds_article_by_content(self):
        response = self.client.get(reverse('home'), {'q': 'useful Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_comment_reply_is_attached_to_parent(self):
        root = Comment.objects.create(post=self.post, author=self.author, body='Parent comment')
        self.client.login(username='reader', password='StrongPass123!')
        response = self.client.post(self.post.get_absolute_url(), {'body': 'A reply', 'parent_id': root.pk})
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertTrue(Comment.objects.filter(parent=root, body='A reply').exists())

    def test_bookmarks_page_lists_saved_post(self):
        Bookmark.objects.create(post=self.post, user=self.reader)
        self.client.login(username='reader', password='StrongPass123!')
        response = self.client.get(reverse('bookmarks'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test story')

    def test_password_change_requires_login(self):
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 302)
        self.client.login(username='reader', password='StrongPass123!')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
