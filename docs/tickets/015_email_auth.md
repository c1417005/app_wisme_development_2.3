# 015 メール認証基盤の実装（django-allauth + Resend）

## 1. 概要

### 目的

django-allauth を用いたメールアドレス確認・パスワードリセット機能を実装し、
メール送信には外部サービス **Resend** の SMTP リレーを利用する。

### 背景

- チケット 002 ではユーザー認証の基本機能（ログイン・ログアウト）を実装済みだが、
  メールアドレス確認およびパスワードリセットのメール送信基盤が未整備である。
- 本番環境（Heroku）で実際にメールが届く状態にするため、外部メール送信サービスとの
  連携が必要となった。
- ヒアリングの結果、以下の条件に最も合致する **Resend** を採用する。
  - 無料枠：3,000通/月・100通/日（確認メール＋パスワードリセットのみの用途に十分）
  - Django への設定が `settings.py` への数行追加で完結する
  - Heroku Config Vars との相性が良く、CLAUDE.md の環境変数管理方針に沿っている

---

## 2. 実装方針

### 基本方針

- **メール送信バックエンド:** Django 標準の SMTP バックエンドを使用し、Resend の SMTP リレー経由で送信する。専用 SDK（`resend` パッケージ）は使用しない。
- **認証フロー:** django-allauth の標準フローを採用し、カスタムビューは最小限にとどめる。
- **環境変数管理:** `RESEND_API_KEY` を `django-environ` 経由で読み込む。ローカルは `.env`、本番は Heroku Config Vars で管理する。
- **ローカル開発:** `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` を使い、メールをターミナルに出力して確認する。本番のみ Resend SMTP に切り替える。

---

## 3. 設定変更

### 3-1. 環境変数の追加

`.env` および `.env.example` に以下を追加する。

```
# .env.example
RESEND_API_KEY=           # Resend ダッシュボードで発行した API キー
DEFAULT_FROM_EMAIL=       # 送信元メールアドレス（例: noreply@yourdomain.com）
```

### 3-2. settings.py の変更

```python
# settings.py

# --- メール送信バックエンド ---
# ローカル開発時はコンソール出力、本番は Resend SMTP を使用
if env.bool('DEBUG', default=True):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.resend.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'resend'
    EMAIL_HOST_PASSWORD = env('RESEND_API_KEY')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# --- django-allauth 設定 ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

INSTALLED_APPS = [
    # ... 既存アプリ ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',        # Google OAuth 対応のため追加（本チケットでは未使用）
]

SITE_ID = 1

# allauth 動作設定
ACCOUNT_LOGIN_METHODS = {'email'}           # メールアドレスでログイン
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'    # 確認メール必須
ACCOUNT_EMAIL_REQUIRED = True
LOGIN_REDIRECT_URL = '/wisme/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
```

### 3-3. urls.py の変更

```python
# myproject/urls.py
urlpatterns = [
    # ...
    path('accounts/', include('allauth.urls')),
    path('wisme/', include('wisme.urls')),
]
```

---

## 4. 実装フローとロジック

### 4-1. メールアドレス確認フロー

1. ユーザーが `/accounts/signup/` でメールアドレス・パスワードを入力して登録。
2. django-allauth が確認メールを自動送信（Resend SMTP 経由）。
3. ユーザーがメール内のリンクをクリックして認証完了。
4. `LOGIN_REDIRECT_URL` へリダイレクト。

### 4-2. パスワードリセットフロー

1. ユーザーが `/accounts/password/reset/` でメールアドレスを入力。
2. django-allauth がリセットメールを自動送信（Resend SMTP 経由）。
3. ユーザーがメール内のリンクをクリックして新しいパスワードを設定。

### 4-3. Heroku デプロイ時の環境変数設定

```bash
heroku config:set RESEND_API_KEY=re_xxxxxxxxxxxx
heroku config:set DEFAULT_FROM_EMAIL=noreply@yourdomain.com
heroku config:set DEBUG=False
```

---

## 5. カスタムテンプレート

django-allauth のデフォルトテンプレートを上書きし、アプリのデザインに合わせる。
対象ファイルは `templates/account/` 以下に配置する。

| テンプレートファイル | 用途 |
|---|---|
| `account/login.html` | ログインページ |
| `account/signup.html` | 新規登録ページ |
| `account/email_confirm.html` | メールアドレス確認完了ページ |
| `account/password_reset.html` | パスワードリセット申請ページ |
| `account/password_reset_done.html` | リセットメール送信完了ページ |
| `account/password_reset_from_key.html` | 新パスワード入力ページ |
| `email/email_confirmation_message.txt` | 確認メール本文（テキスト） |
| `email/password_reset_key_message.txt` | リセットメール本文（テキスト） |

---

## 6. テスト項目（DoD: Definition of Done）

### 動作確認

- [ ] ローカルで新規登録すると、確認メールの内容がコンソールに出力される。
- [ ] 確認メール内のリンクをクリックすると、メールアドレスが確認済み状態になる。
- [ ] 未確認状態のユーザーがログインしようとすると、確認を促すメッセージが表示される。
- [ ] パスワードリセット申請後、リセットメールの内容がコンソールに出力される。
- [ ] リセットメール内のリンクから新しいパスワードを設定できる。
- [ ] Heroku 本番環境で実際にメールが届く（手動確認・自動テスト対象外）。

### 自動テスト

- [x] 新規登録後、`EmailAddress` オブジェクトが未確認状態で作成される。
- [x] 確認リンクへの GET リクエストにより、`EmailAddress.verified` が `True` になる。
- [x] パスワードリセット申請後、対象ユーザーにリセットトークンが発行される。
- [x] 未確認ユーザーが保護ページ（`LoginRequiredMixin`）にアクセスすると、ログインページにリダイレクトされる。

### 安全性・品質確認

- [ ] `RESEND_API_KEY` が `.env` で管理され、公開リポジトリに含まれない設定になっている。
- [ ] `DEBUG=False` の本番環境で SMTP バックエンドが有効になっている。
- [ ] `DEFAULT_FROM_EMAIL` が Heroku Config Vars で設定されている。
