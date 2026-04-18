# 002 ユーザー認証機能の実装

## 1. 概要

### 目的
メールアドレス/パスワードによる登録・ログイン・ログアウトと、Google OAuth によるソーシャルログインを実装する。  
ログインが必要な全画面に `LoginRequiredMixin` を適用し、未認証ユーザーのアクセスを制限する。

### 背景
- 現在はユーザー認証が存在せず、誰でも全データにアクセスできる状態である。
- `CustomUser` モデルは 001 チケットで導入済みであり、認証基盤として利用できる。
- `django-allauth` を使用することで、メール認証と OAuth を統一的に管理できる。

---

## 2. 実装方針

### 2-1. `django-allauth` のインストールと設定

```bash
pip install django-allauth
```

`settings.py` に以下を追加：

```python
INSTALLED_APPS += [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth 設定
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
LOGIN_REDIRECT_URL = '/wisme/'
LOGOUT_REDIRECT_URL = '/wisme/'
```

### 2-2. URL 設定

`myproject/urls.py` に追加：

```python
path('accounts/', include('allauth.urls')),
```

### 2-3. Google OAuth の設定

- Django 管理画面で `Social Application` を作成し、Google の Client ID / Secret を登録する。
- `.env` に `GOOGLE_CLIENT_ID` と `GOOGLE_CLIENT_SECRET` を追加する。

### 2-4. 既存ビューへの `LoginRequiredMixin` 適用

`wisme/views.py` の全 View クラスに `LoginRequiredMixin` を追加：

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class PageListView(LoginRequiredMixin, ListView):
    ...
```

### 2-5. Page モデルへのオーナーフィールド追加

```python
class Page(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
```

- 既存データとの互換性のため初期は `null=True` にする。
- `PageListView` / `PageDetailView` 等で `owner=request.user` によるフィルタリングを適用する。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | `django-allauth` を追加 |
| `myproject/settings.py` | allauth 設定を追加 |
| `myproject/urls.py` | `allauth.urls` をインクルード |
| `wisme/models.py` | `Page` に `owner` FK を追加 |
| `wisme/views.py` | 全 View に `LoginRequiredMixin` を適用 |
| `wisme/migrations/` | `Page.owner` のマイグレーションを追加 |
| `templates/` | ナビゲーションにログイン/ログアウトリンクを追加 |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [✕] メールアドレスとパスワードで新規登録できる
- [✕] 登録後、確認メールが送信される（開発環境ではコンソール出力でよい）
- [✕] メールアドレスとパスワードでログインできる
- [✕] ログアウトできる
- [ ] Google アカウントでログインできる（外部サービス依存のため自動テスト対象外・手動確認済み）
- [✕] 未ログイン状態で `/wisme/page/list/` にアクセスするとログイン画面にリダイレクトされる
- [✕] ログイン後は自分のメモのみ一覧に表示される

### セキュリティ確認
- [✕] 他ユーザーの Page UUID を直接指定してもアクセスできない（403 または 404）
- [✕] CSRF トークンがログインフォームに含まれている
