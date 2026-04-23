# 010 Heroku へのデプロイと PostgreSQL 移行

## 1. 概要

### 目的
開発環境の SQLite から本番用 PostgreSQL に移行し、Heroku に Web アプリをデプロイする。

### 背景
- 現在はローカルの SQLite で動作しており、本番デプロイが行われていない。
- GitHub Student Developer Pack の Heroku クレジット（$13/月）を活用する。
- `django-environ` による環境変数管理（CLAUDE.md 記載）を本番でも活用する。

### 使用リソースと費用
| リソース | プラン | 月額 |
|---|---|---|
| Dyno | Eco | $5 |
| PostgreSQL | Essential-0（25MB） | $5 |
| **合計** | | **$10/月** |

> GitHub Student Developer Pack の $13 クレジット内に収まる。

---

## 2. 実装方針

### 2-1. 依存パッケージの追加

```bash
pip install gunicorn dj-database-url whitenoise psycopg2-binary
pip freeze > requirements.txt
```

| パッケージ | 用途 |
|---|---|
| `gunicorn` | Heroku の WSGI サーバー |
| `whitenoise` | 静的ファイルの配信 |
| `psycopg2-binary` | PostgreSQL ドライバ |

> `dj-database-url` は `django-environ` の `env.db()` で代替できるため、既に `django-environ` が導入済みであれば不要。

### 2-2. `Procfile` の作成

プロジェクトルート（`manage.py` と同階層）に作成する：

```
web: gunicorn myproject.wsgi --log-file -
```

### 2-3. `runtime.txt` の作成

プロジェクトルートに作成し、使用する Python バージョンを明記する：

```
python-3.12.x
```

> `python --version` で確認した実際のバージョンを記載する。

### 2-4. `settings.py` の本番設定

```python
import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# デバッグ設定
DEBUG = env.bool('DEBUG', default=False)

# ホスト設定
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# 静的ファイル
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# WhiteNoise ミドルウェア（SecurityMiddleware の直後に追加）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 追加
    ...
]

# DB 設定（DATABASE_URL 環境変数から読み込む）
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}
```

- ローカルでは `DATABASE_URL` を未設定にして SQLite を使用。
- 本番では Heroku が PostgreSQL 追加時に `DATABASE_URL` を自動設定する。

### 2-5. メディアファイルの扱い

**Heroku の Ephemeral Filesystem について：**  
Heroku の Dyno はデプロイのたびにファイルシステムがリセットされる。そのため、ユーザーがアップロードしたメディアファイルは Dyno 再起動・デプロイのたびに消滅する。

**今チケットのスコープ：**  
- メディアファイルのクラウドストレージ対応（`django-storages` + S3）は **このチケットのスコープに含まない**。
- 将来的には `django-storages` + AWS S3 への移行を推奨する。

```python
# settings.py — 現状維持（ローカル開発用）
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

### 2-6. Heroku デプロイ手順

```bash
# 1. Heroku CLI でログイン
heroku login

# 2. アプリ作成
heroku create <app-name>

# 3. PostgreSQL Essential-0 アドオンを追加
heroku addons:create heroku-postgresql:essential-0

# 4. Config Vars の設定
heroku config:set SECRET_KEY='<your-secret-key>'
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS='<app-name>.herokuapp.com'
heroku config:set GOOGLE_GEMINI_API_KEY='<your-key>'
heroku config:set GOOGLE_BOOKS_API_KEY='<your-key>'
# DATABASE_URL は PostgreSQL アドオン追加時に自動設定される

# 5. デプロイ
git push heroku main

# 6. マイグレーション適用
heroku run python manage.py migrate

# 7. 静的ファイルの収集
heroku run python manage.py collectstatic --noinput
```

### 2-7. 設定が必要な Config Vars 一覧

| 変数名 | 設定方法 |
|---|---|
| `SECRET_KEY` | 手動設定 |
| `DEBUG` | `False` を手動設定 |
| `ALLOWED_HOSTS` | `<app-name>.herokuapp.com` を手動設定 |
| `DATABASE_URL` | PostgreSQL アドオン追加時に **自動設定** |
| `GOOGLE_GEMINI_API_KEY` | 手動設定 |
| `GOOGLE_BOOKS_API_KEY` | 手動設定 |

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | `gunicorn`, `whitenoise`, `psycopg2-binary` を追加 |
| `Procfile` | 新規作成 |
| `runtime.txt` | 新規作成 |
| `myproject/settings.py` | `DEBUG`, `ALLOWED_HOSTS`, `STATIC_ROOT`, WhiteNoise ミドルウェアの変更 |
| `.env.example` | `ALLOWED_HOSTS` を追加 |

---

## 4. テスト項目（完了定義 / DoD）

### デプロイ確認
- [ ] Heroku 上でアプリが正常に起動する
- [ ] PostgreSQL（Essential-0）に接続できる
- [ ] `heroku run python manage.py migrate` がエラーなく完了する
- [ ] 静的ファイル（CSS・JS）が WhiteNoise 経由で正しく配信される
- [ ] 全 Config Vars が Heroku ダッシュボードに設定されている
- [ ] `python manage.py test` が通過している

### セキュリティ確認
- [ ] 本番環境で `DEBUG=False` になっている
- [ ] `SECRET_KEY` が Config Vars から読み込まれている
- [ ] HTTPS でアクセスできる（Heroku は標準で HTTPS 提供）
