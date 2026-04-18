# 003 ユーザープロフィール管理機能の実装

## 1. 概要

### 目的
ユーザーが名前・メールアドレス・プロフィール画像を設定・変更できるプロフィール管理画面を実装する。  
個人情報（氏名・メールアドレス）は AES-256 で暗号化してデータベースに保存する。

### 背景
- 002 チケット（ユーザー認証）完了後に実施する。
- 個人情報を平文で保存するとセキュリティリスクがあるため、暗号化が必要。
- `django-encrypted-model-fields` を使用することで、フィールドレベルの暗号化を透過的に実現できる。

---

## 2. 実装方針

### 2-1. `django-encrypted-model-fields` のインストール

```bash
pip install django-encrypted-model-fields
```

`settings.py` に暗号化キーを追加：

```python
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')
```

`.env` に追加：

```
FIELD_ENCRYPTION_KEY=<32バイトの Base64 エンコードキー>
```

### 2-2. `CustomUser` モデルへのフィールド追加

```python
from encrypted_model_fields.fields import EncryptedCharField, EncryptedEmailField
from django.db import models

class CustomUser(AbstractUser):
    display_name = EncryptedCharField(max_length=100, blank=True)
    profile_image = models.ImageField(
        upload_to='media/profile/', blank=True, null=True
    )
    # email は AbstractUser に既存。暗号化フィールドで上書きする場合は別途検討。
```

> `email` フィールドの暗号化は `AbstractUser` の既存フィールドを置き換える必要があり複雑なため、まず `display_name` の暗号化から着手し、メール暗号化は別チケットで検討する。

### 2-3. プロフィール編集ビューとフォーム

```python
# wisme/views.py
class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    fields = ['display_name', 'profile_image']
    template_name = 'wisme/profile_update.html'
    success_url = reverse_lazy('wisme:profile')

    def get_object(self):
        return self.request.user
```

### 2-4. URL の追加

```python
path('profile/', UserProfileView.as_view(), name='profile'),
path('profile/update/', UserProfileUpdateView.as_view(), name='profile_update'),
```

### 2-5. プロフィール画像削除処理

`CustomUser` の `save()` をオーバーライドし、画像更新時に古いファイルをディスクから削除する（`Page` モデルの `delete()` と同様の方針）。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | `django-encrypted-model-fields`, `Pillow` を追加 |
| `myproject/settings.py` | `FIELD_ENCRYPTION_KEY` を追加 |
| `wisme/models.py` | `CustomUser` にフィールドを追加 |
| `wisme/views.py` | `UserProfileView`, `UserProfileUpdateView` を追加 |
| `wisme/urls.py` | プロフィール URL を追加 |
| `templates/wisme/` | `profile.html`, `profile_update.html` を追加 |
| `wisme/migrations/` | `CustomUser` フィールド追加のマイグレーション |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [x] プロフィール画面にアクセスできる（ログイン必須）
- [x] 表示名を変更して保存できる
- [ ] プロフィール画像をアップロードできる
- [ ] 画像を変更したとき、古い画像ファイルがディスクから削除される
- [x] 未ログイン状態でプロフィール画面にアクセスするとログイン画面にリダイレクトされる

### セキュリティ確認
- [ ] DB の `display_name` カラムが暗号化されている（SQLite ブラウザ等で確認）
- [x] 他ユーザーのプロフィールを直接 URL から編集できない
