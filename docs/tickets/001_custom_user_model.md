# 001 CustomUser モデルへの移行

## 1. 概要

### 目的
現在のプロジェクトは Django デフォルトの `auth.User` をそのまま使用しており、ユーザーモデルが存在しない状態で開発が進んでいる。  
`AbstractUser` を継承した `CustomUser` モデルをプロジェクト初期に導入し、将来の拡張（プロフィール画像・暗号化フィールド・認証拡張等）に対応できる基盤を整える。

### 背景
- Django の公式ドキュメントおよびベストプラクティスでは、**プロジェクト開始時にカスタムユーザーモデルを導入することを強く推奨**している。
- 既存データが少ない現段階で移行しないと、後から変更する際にマイグレーションのリセットが必要になる。
- 近期機能として予定している「ユーザー認証（`django-allauth`）」「ユーザープロフィール管理」を安全に実装するための前提条件である。

---

## 2. 実装方針

### 2-1. `CustomUser` モデルの追加（`wisme/models.py`）

```python
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    pass  # 将来の拡張のために定義のみ先に行う
```

- フィールドの追加はこのチケットのスコープ外とする。
- プロフィール画像・暗号化フィールドは「ユーザープロフィール機能」チケットで追加する。

### 2-2. `settings.py` の変更

```python
AUTH_USER_MODEL = 'wisme.CustomUser'
```

- この設定を追加することで、Django 全体が `CustomUser` を認証ユーザーとして使用する。

### 2-3. マイグレーションのリセット

現時点では本番 DB にユーザーデータが存在しないため、以下の手順でマイグレーションをリセットする。

```bash
# ローカル環境での手順
rm db.sqlite3
find . -path "*/migrations/0*.py" -not -path "*/wisme/migrations/0001_initial.py" -delete

python manage.py makemigrations wisme
python manage.py migrate
```

> 注意: 既存の `wisme` アプリのマイグレーションファイルが存在する場合、`CustomUser` を含む新しい初期マイグレーションを作り直す。

### 2-4. 管理画面の設定（`wisme/admin.py`）

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)
```

### 2-5. 既存モデルの FK 確認

`Page` および `SearchedWord` は現時点でユーザーへの FK を持たないため、このチケットでの変更は不要。  
ユーザー認証導入時に `Page.owner = ForeignKey(CustomUser, ...)` を追加するチケットを別途作成すること。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/models.py` | `CustomUser` クラスを追加 |
| `myproject/settings.py` | `AUTH_USER_MODEL = 'wisme.CustomUser'` を追加 |
| `wisme/admin.py` | `CustomUser` を管理画面に登録 |
| `db.sqlite3` | ローカル DB を削除・再作成 |
| `wisme/migrations/` | マイグレーションファイルを再生成 |

**影響なし（変更不要）**
- `wisme/views.py` — 現時点でユーザー認証に依存した処理なし
- `templates/` — 同上
- `wisme/utils/` — 同上

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [ ] `python manage.py makemigrations` がエラーなく完了する
- [ ] `python manage.py migrate` がエラーなく完了する
- [ ] `python manage.py runserver` が起動する
- [ ] `python manage.py createsuperuser` でスーパーユーザーが作成できる
- [ ] Django 管理画面（`/admin/`）に `CustomUser` が表示される
- [ ] 管理画面からユーザーの作成・編集・削除ができる

### 既存機能のリグレッション確認
- [ ] 読書メモの新規作成（`wisme/page/create/`）が正常に動作する
- [ ] 単語検索 AJAX（`wisme/search/mean/`）が正常にレスポンスを返す
- [ ] 読書メモの一覧・詳細・更新・削除が正常に動作する

### コード確認
- [ ] `settings.py` に `AUTH_USER_MODEL = 'wisme.CustomUser'` が設定されている
- [ ] `models.py` の `CustomUser` が `AbstractUser` を継承している
- [ ] デフォルトの `auth.User` を直接参照している箇所がない（`grep -r "auth.User"` で確認）
