from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='blogs/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password/change/', auth_views.PasswordChangeView.as_view(template_name='blogs/password_change.html', success_url='/password/change/done/'), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='blogs/password_change_done.html'), name='password_change_done'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('authors/<str:username>/', views.author_profile, name='author_profile'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail_legacy, name='post_detail_legacy'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
]
