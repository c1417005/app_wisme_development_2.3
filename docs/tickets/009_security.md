# 009 セキュリティ強化

## 1. 概要

### 目的
Django の標準セキュリティ機能を有効化し、本番環境に向けたセキュリティ設定を整える。  
個人情報の暗号化・アクセス制御・セキュリティヘッダの設定を行う。

### 背景
- 現在は開発用設定（`DEBUG=True`、`SECRET_KEY` 露出リスク等）のままである。
- ユーザー認証（002）導入後、個人情報を扱うため暗号化が必要。
- 003（ユーザープロフィール）チケットと並行して進める。

---

## 2. 実装方針

### 2-1. `settings.py` のセキュリティ設定

```python
# 本番環境では必ず False
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# セキュリティミドルウェア（デフォルトで有効だが明示的に確認）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    ...
]

# HTTPS 関連（本番のみ有効化）
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

`.env.example` にコメントを追加して本番時の変更点を明示する。

### 2-2. 個人情報の暗号化（003 と連携）

- 003 チケットで導入した `django-encrypted-model-fields` を使用。
- `FIELD_ENCRYPTION_KEY` は本番では OS 環境変数として設定する（PythonAnywhere の Web タブ）。
- 暗号化対象フィールド：`CustomUser.display_name`（初期）

### 2-3. ログイン必須ページのアクセス制御

- 全 View クラスに `LoginRequiredMixin` を適用済みであること（002 チケット）。
- `settings.py` でデフォルトのリダイレクト先を設定：

```python
LOGIN_URL = '/accounts/login/'
```

### 2-4. CSRF 対策の確認

- 全フォームに `{% csrf_token %}` が存在することを確認する。
- AJAX POST リクエストに `X-CSRFToken` ヘッダが付与されていることを確認する（単語検索 AJAX）。

### 2-5. `SECRET_KEY` の安全な管理

- `SECRET_KEY` が `.env` から読み込まれており、コードにハードコードされていないことを確認する。
- `.env.example` に `SECRET_KEY=` を空欄で追加する。

### 2-6. パスワードバリデーションの確認

```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

Django デフォルトのバリデーターが設定されていることを確認する。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `myproject/settings.py` | セキュリティ設定を追加・確認 |
| `.env.example` | 本番用セキュリティ設定のキーを追加 |
| `templates/**/*.html` | `{% csrf_token %}` の存在確認 |
| `static/wisme/js/` | AJAX POST の `X-CSRFToken` ヘッダ付与確認 |

---

## 4. テスト項目（完了定義 / DoD）

### セキュリティ確認
- [ ] `SECRET_KEY` がコードにハードコードされていない（`grep -r "SECRET_KEY" --include="*.py"` で確認）
- [ ] `DEBUG=False` の状態でサーバーが起動する
- [ ] 全フォームに `{% csrf_token %}` が含まれている
- [ ] AJAX POST に `X-CSRFToken` ヘッダが付与されている
- [ ] `python manage.py check --deploy` で重大な警告がない
- [ ] 他ユーザーのリソースに直接 URL でアクセスできない

### 暗号化確認
- [ ] DB の暗号化フィールドが平文で保存されていない
- [ ] `FIELD_ENCRYPTION_KEY` が `.env` で管理されている
