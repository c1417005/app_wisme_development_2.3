# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 1. 開発コマンド

すべて `myproject/` ディレクトリで実行：

```bash
# 開発サーバー起動
python manage.py runserver

# マイグレーション適用
python manage.py migrate

# モデル変更後にマイグレーション生成
python manage.py makemigrations

# テスト実行
python manage.py test
```

---

## 2. 環境セットアップ

`myproject/` に `.env` ファイルを作成し、以下を記載する：

```
GOOGLE_API_KEY=<your Gemini API key>
SECRET_KEY=<Django secret key>
DATABASE_URL=<DB接続文字列（本番はPostgreSQL）>
DEBUG=True
```

- 環境変数の読み込みには **`django-environ`** を使用する（`python-dotenv` から移行予定）。
- `.env` はバージョン管理に含めない（`.gitignore` に追記済み）。
- 設定値のハードコードは禁止。`env()` 経由で必ず読み込む。

---

## 3. アーキテクチャ概要

**Single Django app:** `wisme` — 日本語の読書メモ管理アプリ。単語検索時に Gemini API で意味を自動取得する。

### データモデル (`wisme/models.py`)

- **CustomUser** — `AbstractUser` を継承したカスタムユーザーモデル。将来の拡張（プロフィール画像・暗号化フィールド等）に対応するため、プロジェクト初期から導入する。`AUTH_USER_MODEL = 'wisme.CustomUser'` を `settings.py` に設定。
- **Page** — 読書メモ。UUID PK、タイトル、感想、日付、任意の画像を持つ。`delete()` をオーバーライドし、削除時に画像ファイルをディスクから削除。
- **SearchedWord** — 単語と意味のペア。`Page` への nullable FK を持つ。単語検索時に即座に作成され（フォーム送信前）、Page 保存時に紐づけられる。`word` フィールドには一意インデックスを設定し、DB キャッシュとして機能させる。

### リクエストフロー

1. ユーザーがフォームで単語入力 → JS が `wisme/search/mean/` へ AJAX POST → `PageSendWordReturnMean` ビューが `WordService.search_or_fetch()` を呼ぶ → DB にヒットすれば API 呼び出しをスキップ、なければ `GeminiAsk()` → `SearchedWord`（`note=None`）として保存 → 意味をレスポンス返却。
2. ユーザーが Page フォームを送信 → `PageCreateView`/`PageUpdateView` が Page を保存 → `note=None` の `SearchedWord` を全件取得して新規 Page に紐づける。

> ビジネスロジック（API呼び出し・単語の重複チェック・紐づけ処理）は View に書かず、`wisme/services.py` の Service 層に集約する（**Thin View / Fat Service** 原則）。

### URL 構成

| URL | View |
|-----|------|
| `wisme/` | IndexView |
| `wisme/page/create/` | PageCreateView |
| `wisme/page/list/` | PageListView |
| `wisme/page/<uuid:id>/` | PageDetailView |
| `wisme/page/<uuid:id>/update/` | PageUpdateView |
| `wisme/page/<uuid:id>/delete/` | PageDeleteView |
| `wisme/search/mean/` | PageSendWordReturnMean (AJAX) |

### テンプレート

- ベースレイアウト: `templates/base/wisme_base.html`
- アプリテンプレート: `templates/wisme/*.html`
- 静的 CSS: `static/wisme/css/style.css`

### 主要設定

- DB: SQLite3（`db.sqlite3`、gitignore済み）→ 本番は PostgreSQL
- 言語: `ja`、タイムゾーン: `Asia/Tokyo`
- メディアアップロード先: `media/wisme/picture/`
- URL 設定: `myproject/myproject/urls.py` でアプリを `/wisme/` にマウント、DEBUG モード時にメディアを配信

---

## 4. 計画中の機能（要件）

### 近期
- **ユーザー認証** — メール/パスワード登録 + Google OAuth。`django-allauth` を使用。ログイン必須画面には `LoginRequiredMixin` を適用。認証基盤は `CustomUser`（`AbstractUser`継承）で構築済みであること。
- **単語帳** — 保存済み `SearchedWord` の一覧・ソート（アルファベット順/登録順）。
- **クイズ機能** — Page と SearchedWord を組み合わせた復習クイズ。出題・解答判定・結果記録。

### 単語検索パフォーマンス
- 検索前に DB を引き、ヒットすれば Gemini API を呼ばない。`SearchedWord.word` に `db_index=True` + `unique=True` を設定してキャッシュとして機能させる。
- 検索中はスケルトン UI またはプログレスバーを表示（フロントエンド）。

### ユーザープロフィール
- 名前・メールアドレス・プロフィール画像の管理。個人情報は AES-256 等で暗号化して保存。`CustomUser` モデルへフィールドを追加する形で実装。

### 多言語対応 (i18n)
- 日本語・英語の切り替え。`django.middleware.locale.LocaleMiddleware` + `gettext` を使用。

### おすすめ書籍
- ユーザーの読書履歴・評価から類似書籍を推薦。Gemini API を活用予定。

### 将来・要調査
- バーコードスキャンによる書籍情報自動取得（OpenBD API）
- Web Speech API による音声入力

---

## 5. インフラとデプロイ

- **PythonAnywhere** — 無料プランで開発スタート。DB は PostgreSQL。
- 将来的に AWS/GCP への移行を視野に入れたスケーラブルな設計を意識する。

### 環境変数管理
- `django-environ` を使い、`SECRET_KEY`・`DATABASE_URL`・`GOOGLE_API_KEY` 等をすべて `.env` から読み込む。
- 本番サーバーでは `.env` ではなく OS 環境変数（PythonAnywhere の Web タブで設定）を使用する。
- `.env.example` をリポジトリに含め、必要なキーを明示する（値は空欄）。

### メディア・静的ファイル
- `MEDIA_ROOT` / `MEDIA_URL` を `settings.py` で明示的に設定する。
- 本番環境では Django からメディアを直接配信せず、PythonAnywhere の Static Files マッピングか、将来的には S3 等のオブジェクトストレージを利用する。
- `django-storages` + `boto3` を使い、ストレージバックエンドを差し替え可能な設計にしておく。

---

## 6. セキュリティ方針

- `SECRET_KEY` は `.env` で管理し、コードにハードコードしない。
- `DEBUG=False` を本番では必ず設定し、`ALLOWED_HOSTS` を明示する。
- ユーザー入力は Django フォームまたは DRF シリアライザでバリデーション後に処理する。
- 個人情報（メール・プロフィール等）は AES-256 等で暗号化して保存する（`django-encrypted-model-fields` 等を検討）。
- CSRF トークンを全フォームに適用する（Django デフォルト）。AJAX POST は `X-CSRFToken` ヘッダを付与する。

---

## 10. 開発ガイドライン（技術スタックと設計原則）

### カスタムユーザーモデル
- **`AbstractUser` を継承した `CustomUser` をプロジェクト開始時から使用する。**
- `AUTH_USER_MODEL = 'wisme.CustomUser'` を設定し、デフォルトの `auth.User` は使わない。
- これにより、将来のフィールド追加（プロフィール画像・暗号化フィールド等）がマイグレーションのやり直しなしに可能になる。

### Service 層による責務分離（Thin View / Fat Service）
- ビジネスロジックは View に書かず、`wisme/services.py` に集約する。
- View は「リクエスト受け取り → Service 呼び出し → レスポンス返却」のみを担う。
- 例：`WordService.search_or_fetch(word: str) -> SearchedWord`、`PageService.link_orphan_words(page: Page) -> None`

### 環境変数管理（django-environ）
- `python-dotenv` の代わりに `django-environ` を使用する。
- `env = environ.Env()` を `settings.py` 冒頭で定義し、`env('KEY')` で値を取得する。
- すべての機密情報・環境依存値は `.env` に記載し、コードへのハードコードを禁止する。

### DB インデックス設計
- `SearchedWord.word` には `unique=True`（暗黙的にインデックス生成）を設定する。
- 検索・フィルタリング頻度の高いフィールドには `db_index=True` を付与する。
- N+1 クエリを防ぐため、関連オブジェクトを取得する際は `select_related` / `prefetch_related` を使用する。

### メディア・静的ファイル設計
- `settings.py` に `MEDIA_ROOT = BASE_DIR / 'media'`、`MEDIA_URL = '/media/'` を明示的に設定する。
- 本番ではストレージバックエンドを `django-storages`（S3 等）に差し替えられるよう、`DEFAULT_FILE_STORAGE` を環境変数で切り替え可能にする。
- 静的ファイルは `collectstatic` で `STATIC_ROOT` に集約し、本番サーバーから直接配信する。
