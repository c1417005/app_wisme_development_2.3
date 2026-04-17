# 007 推奨図書機能の実装

## 1. 概要

### 目的
ユーザーの読書履歴・好みに基づいて、類似書籍や人気書籍を推薦する機能を実装する。  
Gemini API を活用してジャンル・著者・評価から推薦候補を生成する。

### 背景
- ユーザーが次に読む本を探す手助けができる。
- 002（ユーザー認証）・001（CustomUser）完了後に実施する。
- 評価機能が前提となるため、`Page` モデルへの評価フィールド追加も含む。

---

## 2. 実装方針

### 2-1. `Page` モデルへの評価フィールド追加

```python
class Page(models.Model):
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
    )
    genre = models.CharField(max_length=50, blank=True)
    author = models.CharField(max_length=100, blank=True)
```

### 2-2. 推薦ロジック（`wisme/services.py`）

```python
class BookRecommendationService:
    @staticmethod
    def get_recommendations(user) -> list[dict]:
        """
        ユーザーの読書履歴から Gemini API に推薦を依頼する。
        返却形式: [{'title': '...', 'author': '...', 'reason': '...'}, ...]
        """
        pages = Page.objects.filter(owner=user).exclude(genre='')
        prompt = BookRecommendationService._build_prompt(pages)
        return GeminiAsk(prompt)  # 既存の Gemini クライアントを再利用
```

プロンプト設計：
- ユーザーが読んだ本のタイトル・著者・ジャンル・評価を含める。
- 「これらの本を読んだユーザーにおすすめの本を 5 冊、タイトル・著者・推薦理由を JSON 形式で返してください」と指示。

### 2-3. 推薦ビューの追加

```python
class BookRecommendationView(LoginRequiredMixin, View):
    def get(self, request):
        recommendations = BookRecommendationService.get_recommendations(request.user)
        return render(request, 'wisme/book_recommendations.html', {
            'recommendations': recommendations
        })
```

### 2-4. 人気図書の推薦

- 全ユーザーで高評価（rating >= 4）の `Page` タイトルをランキング表示する。
- 同一タイトルの集計は `Page.objects.values('title').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')` で行う。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/models.py` | `Page` に `rating`, `genre`, `author` フィールドを追加 |
| `wisme/views.py` | `BookRecommendationView` を追加 |
| `wisme/services.py` | `BookRecommendationService` を追加 |
| `wisme/urls.py` | `/wisme/books/recommend/` を追加 |
| `templates/wisme/` | `book_recommendations.html`, ページ作成/編集フォームへのフィールド追加 |
| `wisme/migrations/` | `Page` フィールド追加のマイグレーション |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [ ] 読書メモ作成・編集フォームでジャンル・著者・評価を入力できる
- [ ] `/wisme/books/recommend/` でおすすめ本が表示される
- [ ] 読書履歴が 0 件のとき、適切なメッセージが表示される（API は呼ばない）
- [ ] 人気図書ランキングが表示される
- [ ] 未ログイン状態でアクセスするとログイン画面にリダイレクトされる

### API 確認
- [ ] Gemini API のレスポンスが JSON 形式で正しくパースされる
- [ ] API エラー時にユーザーにフレンドリーなメッセージが表示される
