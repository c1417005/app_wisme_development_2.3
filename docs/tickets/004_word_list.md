# 004 単語帳機能の実装

## 1. 概要

### 目的
保存済みの `SearchedWord` をユーザーが一覧で確認できる単語帳画面を実装する。  
アルファベット順・登録順のソート機能を提供し、復習に役立てる。

### 背景
- 現在は単語検索で保存された単語を一覧で見る手段がなく、活用できていない。
- 002 チケット（ユーザー認証）完了後、`SearchedWord` をユーザーに紐づけてからこのチケットを実施する。

---

## 2. 実装方針

### 2-1. `SearchedWord` へのユーザー FK 追加

```python
class SearchedWord(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
```

- 既存データとの互換性のため初期は `null=True` にする。
- `WordService.search_or_fetch()` でログインユーザーを `owner` に設定する。

### 2-2. 単語帳ビューの追加

```python
# wisme/views.py
class WordListView(LoginRequiredMixin, ListView):
    model = SearchedWord
    template_name = 'wisme/word_list.html'
    context_object_name = 'words'

    def get_queryset(self):
        qs = SearchedWord.objects.filter(owner=self.request.user)
        sort = self.request.GET.get('sort', 'created_at')
        if sort == 'alpha':
            qs = qs.order_by('word')
        else:
            qs = qs.order_by('-created_at')
        return qs
```

### 2-3. `SearchedWord` への `created_at` フィールド追加

```python
class SearchedWord(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2-4. URL の追加

```python
path('words/', WordListView.as_view(), name='word_list'),
```

### 2-5. テンプレート

- 単語と意味をテーブルまたはカード形式で表示する。
- ソートボタン（「あいうえお順」「登録が新しい順」）を設置し、`?sort=alpha` / `?sort=created_at` で切り替える。
- 紐づく読書メモのタイトルへのリンクも表示する。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/models.py` | `SearchedWord` に `owner` FK と `created_at` を追加 |
| `wisme/views.py` | `WordListView` を追加 |
| `wisme/urls.py` | `/wisme/words/` を追加 |
| `wisme/services.py` | `search_or_fetch()` で `owner` を設定 |
| `templates/wisme/` | `word_list.html` を追加 |
| `wisme/migrations/` | フィールド追加のマイグレーション |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [ ] `/wisme/words/` に単語一覧が表示される（ログイン必須）
- [ ] 登録順（デフォルト）で表示される
- [ ] アルファベット順ソートに切り替えられる
- [ ] 他のユーザーの単語が表示されない
- [ ] 単語に紐づく読書メモへのリンクが機能する
- [ ] ナビゲーションに「単語帳」リンクが追加されている
