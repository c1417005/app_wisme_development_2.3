# 010 PythonAnywhere へのデプロイと PostgreSQL 移行

## 1. 概要

### 目的
開発環境の SQLite から本番用 PostgreSQL に移行し、PythonAnywhere に Web アプリをデプロイする。  
将来の AWS/GCP 移行を見越したスケーラブルな設定を整える。

### 背景
- 現在はローカルの SQLite で動作しており、本番デプロイが行われていない。
- PythonAnywhere の無料プランで PostgreSQL を使用できる。
- `django-environ` による環境変数管理（CLAUDE.md 記載）を本番でも活用する。

---

## 2. 実装方針

### 2-1. `django-environ` と `psycopg2` のインストール

```bash
pip install django-environ psycopg2-binary
pip freeze > requirements.txt
```

### 2-2. `settings.py` の DB 設定変更

```python
import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}
```

- ローカルでは `DATABASE_URL` を未設定にして SQLite を使用。
- 本番では `DATABASE_URL=postgres://user:pass@host/dbname` を OS 環境変数に設定。

### 2-3. 静的ファイルの設定

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

```bash
python manage.py collectstatic --noinput
```

PythonAnywhere の Static Files タブで `/static/` → `staticfiles/` へのマッピングを設定する。

### 2-4. メディアファイルの設定

```python
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

PythonAnywhere の Static Files タブで `/media/` → `media/` へのマッピングを設定する。  
将来的には `django-storages` + S3 に移行できる設計を維持する。

### 2-5. PythonAnywhere デプロイ手順

1. PythonAnywhere にサインアップし、Bash コンソールを開く。
2. リポジトリをクローン：`git clone <repo_url>`
3. 仮想環境を作成：`python -m venv venv && source venv/bin/activate`
4. 依存関係をインストール：`pip install -r requirements.txt`
5. OS 環境変数（Web タブ）に `SECRET_KEY`, `DATABASE_URL`, `GOOGLE_API_KEY`, `FIELD_ENCRYPTION_KEY` を設定。
6. `python manage.py migrate` を実行。
7. `python manage.py collectstatic` を実行。
8. Web タブで WSGI ファイルのパスを設定する。

### 2-6. WSGI 設定ファイル

PythonAnywhere の WSGI 設定ファイル（`/var/www/<username>_pythonanywhere_com_wsgi.py`）：

```python
import os
import sys

path = '/home/<username>/app_development_2.3/myproject'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 2-7. `ALLOWED_HOSTS` の設定

```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
```

本番では `ALLOWED_HOSTS=<username>.pythonanywhere.com` を OS 環境変数に設定する。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | `psycopg2-binary`, `django-environ` を追加 |
| `myproject/settings.py` | `DATABASE_URL` による DB 設定、`STATIC_ROOT`、`ALLOWED_HOSTS` の変更 |
| `.env.example` | `DATABASE_URL` を追加 |

---

## 4. テスト項目（完了定義 / DoD）

### デプロイ確認
- [ ] PythonAnywhere で `python manage.py migrate` がエラーなく完了する
- [ ] `python manage.py check --deploy` で重大な警告がない
- [ ] `https://<username>.pythonanywhere.com/wisme/` にアクセスできる
- [ ] ログイン・読書メモ作成・単語検索が本番環境で動作する
- [ ] 静的ファイル（CSS・JS）が正しく配信される
- [ ] メディアファイル（画像）がアップロードおよび表示できる

### セキュリティ確認
- [ ] 本番環境で `DEBUG=False` になっている
- [ ] `SECRET_KEY` が OS 環境変数から読み込まれている
- [ ] HTTPS でアクセスできる（PythonAnywhere は標準で HTTPS 提供）
