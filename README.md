# BlogSphere — Multi-Author Blogging Platform

A Django 5.2 project built as a beginner-to-advanced learning project. It includes author accounts, profiles, article publishing, categories, tags, search, pagination, comments/replies, likes, bookmarks, a dashboard, moderation through Django Admin, tests, and deployment configuration.

## Features

- Registration, login, logout, password validation, and user profiles.
- Author-only create/edit/delete permissions; staff can moderate content.
- Draft and published posts, unique slugs, cover images, categories, and tags.
- Search across titles, article content, categories, and tags; six posts per page.
- Article detail pages, threaded one-level replies, likes, and bookmarks.
- Author dashboard, public author profiles, and saved reading list.
- Django Admin management for posts, categories, tags, profiles, likes, bookmarks, and comment approval.
- Responsive interface, CSRF protection, secure POST actions, and automated tests.
- SQLite for local development; optional PostgreSQL via `DATABASE_URL`.

## Requirements

- Python 3.11+
- pip
- (Optional) PostgreSQL for production

## Windows PowerShell setup

Open PowerShell in the folder containing `manage.py`:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

If PowerShell blocks activation, allow it for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Open http://127.0.0.1:8000/.

Create an administrator account:

```powershell
python manage.py createsuperuser
```

Admin panel: http://127.0.0.1:8000/admin/.

## Existing database and migration

This package includes the database supplied with the learner's original project. Back it up before changing anything. The new `0002` migration adds profiles, authorship, slugs, categories, tags, comments, likes, bookmarks, status, and image fields. It also creates slugs and category records for legacy posts so earlier articles remain available.

For a fresh installation, `python manage.py migrate` creates all tables. For an existing database, the same command applies only the pending migration.

## Important routes

| Route | Purpose |
|---|---|
| `/` | Homepage, search, category filters, pagination |
| `/register/` | Create an account |
| `/login/` / `/logout/` | Authentication |
| `/dashboard/` | Your posts and draft/published counts |
| `/create/` | Create a post (login required) |
| `/post/<slug>/` | Read an article |
| `/post/<id>/edit/` | Edit your own article |
| `/post/<id>/delete/` | Confirm and delete your own article |
| `/authors/<username>/` | Public author profile |
| `/profile/edit/` | Edit your profile |
| `/bookmarks/` | Saved articles |
| `/category/<slug>/` | Category archive |
| `/tag/<slug>/` | Tag archive |
| `/admin/` | Staff moderation and management |

## Run tests

```powershell
python manage.py test blogs
```

The test suite covers public pages, registration/profile creation, permissions, post lifecycle, drafts, likes, bookmarks, comments, categories, tags, and author profiles.

## PostgreSQL configuration

Install requirements, create a PostgreSQL database, and set environment variables before starting Django. Example PowerShell session:

```powershell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DBNAME"
$env:DJANGO_DEBUG = "False"
$env:DJANGO_SECRET_KEY = "a-long-random-production-secret"
$env:DJANGO_ALLOWED_HOSTS = "your-domain.com"
python manage.py migrate
python manage.py collectstatic --noinput
```

`psycopg` is included in requirements. If `DATABASE_URL` is not set, the app uses SQLite.

## Deployment checklist

1. Create a PostgreSQL database with your hosting provider.
2. Configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, and `DATABASE_URL` in the host's environment settings.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run `python manage.py migrate` and `python manage.py collectstatic --noinput` as release/build commands.
5. Start the service with `gunicorn config.wsgi:application` (Procfile included).
6. Configure persistent media storage for uploaded avatars and cover images. The local `media/` folder is suitable for development, not ephemeral production containers.
7. Test HTTPS, login, image upload, static files, and admin access on the deployed domain.

## Security notes

- Never commit `.env`, production secrets, uploaded media, or a live user database to a public repository.
- Keep `DEBUG=False` in production and set a unique secret key and exact allowed hosts.
- All state-changing actions (logout, like, bookmark, comment, delete) use POST and CSRF tokens.
- Post owners can edit/delete their own posts; staff can moderate all posts. Users cannot set the featured flag from the public form.
- Configure a production media storage service before accepting public uploads at scale.

## Suggested 40-step learning map

1. Environment setup; 2. MVT; 3. App creation; 4. Homepage; 5. Static CSS; 6. Template inheritance; 7. Dynamic template data; 8. Conditions/loops; 9. Post model; 10. Migrations; 11. Admin; 12. Database-backed homepage; 13. Detail page; 14. 404 handling; 15. Create posts; 16. Edit posts; 17. Delete posts; 18. Registration; 19. Login/logout; 20. Access control; 21. Author profiles; 22. Profile editing/avatar; 23. Categories; 24. Tags; 25. Search; 26. Pagination; 27. Comments; 28. Replies; 29. Likes; 30. Bookmarks; 31. Draft/publish; 32. Dashboard; 33. Admin moderation; 34. Responsive UI; 35. Validation/security; 36. Automated tests; 37. PostgreSQL; 38. Git/GitHub; 39. Production configuration; 40. Deployment.

This project is the integrated implementation of the roadmap; use the numbered map as a study checklist and complete the tests as you learn each feature.

## Git and GitHub workflow

Create a private or public GitHub repository, then from the project folder:

```powershell
git init
git add .
git status
git commit -m "Build BlogSphere multi-author blogging platform"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Before pushing to a public repository, remove `db.sqlite3` if it contains real accounts or personal data, and verify that `.env` and uploaded media are not staged. Never publish production credentials.

## Learning checkpoints

The application is supplied as an integrated implementation, but the recommended way to learn it is still incremental: study one feature, run the related page, inspect its view/model/template, then run `python manage.py test blogs`. The 40-step map above is a suggested learning order, not a claim that every hosting-provider account or production credential has already been configured for you.
