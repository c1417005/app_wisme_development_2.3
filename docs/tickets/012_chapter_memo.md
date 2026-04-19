# 012 章単位メモ機能（Chapter モデル・動的フォーム）

## 1. 概要

### 目的
読書メモを「本全体の感想」と「章ごとのメモ」に分離し、**ブログ記事のような一つの長い文章を章ごとに書いていくスタイル**を実現する。要件書 `requirements/UI_requirements.md` セクション B の未実装項目（章構成・章エディタ・章の動的追加・章と感想の視覚分離）を一括でカバーする。

### 前提チケット
- 既存の Page / SearchedWord モデル（001・004 等）が稼働していること。
- 011（UI/UX）の動的エディタ節は本チケットに準拠する形で読み替える（Vue.js ではなく Django formset + バニラ JS で実装）。

### 非破壊方針
既存の `Page.thoughts`（本全体の感想）フィールドは **保持したまま**、新モデル `Chapter` を加算的に追加する。既存データ・既存テスト・既存 URL への破壊的変更は行わない。

---

## 2. 実装方針

### 2-1. データモデル

`wisme/models.py` に `Chapter` モデルを追加：

```python
class Chapter(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='chapters', verbose_name='所属メモ')
    order = models.PositiveIntegerField(default=0, verbose_name='並び順')
    title = models.CharField(max_length=100, blank=True, verbose_name='章タイトル')
    content = models.TextField(blank=True, verbose_name='章の内容')
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
```

- `Page.thoughts` は「本全体の感想」として残す。
- `Page` 削除時は CASCADE で章も自動削除。
- マイグレーション `0005_chapter.py` を新規作成（データ移行は不要）。

### 2-2. フォーム

`wisme/forms.py` に `ChapterFormSet` を追加：

```python
from django.forms import inlineformset_factory

ChapterFormSet = inlineformset_factory(
    Page, Chapter,
    fields=['title', 'content', 'order'],
    extra=1, can_delete=True,
)
```

- `PageForm` 自体は変更しない（title / thoughts / page_date / picture を維持）。
- ビュー側で `PageForm` と `ChapterFormSet` を組み合わせて扱う。

### 2-3. ビュー

`wisme/views.py` の以下を変更：

- **PageCreateView.post** — `PageForm` と `ChapterFormSet` の両方を `is_valid()` 判定し、Page 保存後に formset の `instance = new_page` を設定して保存。
- **PageUpdateView.get/post** — 同様に formset を `instance=page` でバインドし、保存時は formset.save() を呼ぶ。
- **PageDetailView.get** — コンテキストに `chapters = page.chapters.all()` を追加。
- **PageDeleteView** — CASCADE で自動削除されるため変更不要（ただし確認ページ文言の調整は任意）。

### 2-4. テンプレート

| テンプレート | 変更内容 |
|---|---|
| `templates/wisme/page_form.html` | 「本全体の感想」セクションと「章ごと」セクションを視覚的に分離。章セクションは formset の各行をループ表示し、`{{ formset.management_form }}` と `empty_form` を出力。「章を追加」ボタンを配置。 |
| `templates/wisme/page_update.html` | 同上（既存章は既存フォームとして表示、追加可能）。 |
| `templates/wisme/page_detail.html` | `thoughts` 表示の後に `chapters` を `order` 順で繰り返し表示。章タイトルと本文を明確に区別。 |
| `templates/wisme/page_confirm_delete.html` | 削除警告文言に「章」を追記（任意）。 |

### 2-5. JavaScript（章の動的追加）

新規 or 既存 `static/wisme/js/` 配下に追加：

- 「章を追加」ボタン押下で `empty_form` の HTML を複製し、`__prefix__` を `TOTAL_FORMS` の現在値に置換 → DOM に挿入 → `TOTAL_FORMS` を +1。
- 「章を削除」はチェックボックス or 非表示クラスで対応（formset の `can_delete=True` に対応）。
- バニラ JS で実装（Vue.js は導入しない）。

### 2-6. 視覚分離の指針（要件 B 対応）

- 「本全体の感想」セクション: 薄いアクセント色背景、左アクセントボーダー、見出し「本全体の感想」。
- 「章ごと」セクション: 白背景カード + 章番号バッジ。章間にセパレータ。
- 要件書 UI_requirements.md の「本全体の感想文入力欄と、章ごとの入力欄を明確に分ける」を満たす。

### 2-7. SearchedWord との関係

- `SearchedWord.note` は `Page` FK のまま変更しない（要件「そのメモへ紐づく」は Page 単位で満たされる）。
- 将来的に章単位紐付けが必要になった場合は別チケットで `chapter` FK を追加する。

### 2-8. 管理画面（任意）

`wisme/admin.py` に `ChapterInline(admin.TabularInline)` を追加し、`PageAdmin.inlines = [ChapterInline]` を設定すると運用が楽になる。必須ではない。

---

## 3. 影響範囲

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `wisme/models.py` | 追加 | `Chapter` モデル追加 |
| `wisme/migrations/0005_chapter.py` | 新規 | 追加マイグレーション（データ移行なし） |
| `wisme/forms.py` | 追加 | `ChapterFormSet` 定義 |
| `wisme/views.py` | 変更 | `PageCreateView` / `PageUpdateView` / `PageDetailView` に formset 対応追加 |
| `wisme/admin.py` | 任意追加 | `ChapterInline` |
| `templates/wisme/page_form.html` | 変更 | 感想セクションと章セクションの視覚分離、formset レンダリング |
| `templates/wisme/page_update.html` | 変更 | 同上 |
| `templates/wisme/page_detail.html` | 変更 | 章の表示追加 |
| `static/wisme/js/chapter_formset.js` | 新規 | 「章を追加」JS（empty_form 複製 + TOTAL_FORMS 管理） |
| `wisme/tests.py` | 追加 | 章作成/更新/削除と formset バリデーションのテスト |

### 破壊的影響
- **なし**。既存 `Page.thoughts` データは保持、既存テスト（`make_page` 等）は無変更で通過、URL・View 署名は維持。

---

## 4. テスト項目（完了定義 / DoD）

### モデル・マイグレーション
- [x] `Chapter` モデルが作成され、`Page` との FK 関係・`related_name='chapters'` が機能する
- [x] `Page` を削除すると紐づく `Chapter` も CASCADE で削除される
- [x] `Chapter.Meta.ordering` により `order` 順で取得できる

### フォーム・ビュー
- [x] 新規作成時、`PageForm` と `ChapterFormSet` の両方を保存できる
- [x] 編集時、既存章を更新・削除・新規章を追加できる
- [ ] formset バリデーションエラー時はテンプレートが再表示される

### 画面
- [×] `page_form.html` / `page_update.html` で「本全体の感想」と「章ごと」が視覚的に分離されている（手動確認）
- [×] 「章を追加」ボタンでページ遷移なしに入力欄が増える（手動確認）
- [x] `page_detail.html` で章が `order` 順に表示される

### 既存機能の非破壊
- [x] 既存の `make_page` ベースのテストがすべて通過する
- [x] 既存の SearchedWord 自動紐付けロジックが引き続き動作する
