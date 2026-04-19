# 005 クイズ機能の実装（フラッシュカード形式）

## 1. 概要

### 目的
ユーザーが保存した単語（`SearchedWord`）を使ったフラッシュカード形式の復習機能を実装する。  
メモを読み返した「ついで」にやる**おまけ要素**として位置づけ、気軽に使えるようにする。

### 背景
- 単語帳（004）で保存した単語を実際に復習できる仕組みが必要。
- UI 要件定義に基づき、**フラッシュカード形式**（自由記述・正誤判定なし）を採用する。
- カード裏面には「どの本のメモで調べたか」を表示し、当時の文脈を思い出させる設計にする。
- 004 チケット（単語帳機能）完了後に実施する。

---

## 2. 実装方針

### 2-1. フラッシュカードのフロー

正誤判定・結果記録は行わない。シンプルな閲覧・めくり体験に特化する：

1. `/wisme/quiz/` — 単語帳画面（フラッシュカード一覧）
2. ソート切り替え（アルファベット順 / 登録順）
3. カードをクリック → 3D アニメーションで裏返る

### 2-2. カードの表裏

| 面 | 表示内容 |
|---|---|
| 表（front）| 単語（`SearchedWord.word`） |
| 裏（back）| 意味（`SearchedWord.mean`）＋ 紐づくメモの本タイトル・表紙画像（`SearchedWord.note.title`, `note.picture`）|

- `SearchedWord.note` が `None`（メモ未紐づけ）の場合、裏面は意味のみ表示。

### 2-3. ビュー

```python
# wisme/views.py
class FlashcardView(LoginRequiredMixin, ListView):
    model = SearchedWord
    template_name = 'wisme/flashcard.html'
    context_object_name = 'words'

    def get_queryset(self):
        qs = SearchedWord.objects.filter(owner=self.request.user).select_related('note')
        sort = self.request.GET.get('sort', 'created_at')
        if sort == 'alpha':
            qs = qs.order_by('word')
        else:
            qs = qs.order_by('-created_at')
        return qs
```

### 2-4. URL の追加

```python
path('quiz/', FlashcardView.as_view(), name='flashcard'),
```

### 2-5. 3D フリップアニメーション（CSS）

```css
.card-container { perspective: 1000px; cursor: pointer; }
.card { transform-style: preserve-3d; transition: transform 0.5s; }
.card.flipped { transform: rotateY(180deg); }
.card-front, .card-back {
  backface-visibility: hidden;
  position: absolute; inset: 0;
}
.card-back { transform: rotateY(180deg); }
```

JavaScript でカードクリック時に `.flipped` クラスを付け替える。

### 2-6. ソート UI

単語帳（004）の `/wisme/words/` と同じソートパラメータ（`?sort=alpha` / `?sort=created_at`）を使用。

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/views.py` | `FlashcardView` を追加 |
| `wisme/urls.py` | `/wisme/quiz/` を追加 |
| `templates/wisme/` | `flashcard.html` を追加 |
| `static/wisme/css/style.css` | 3D フリップ CSS を追加（011 チケットと共有） |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [x] `/wisme/quiz/` にフラッシュカードが表示される（ログイン必須）
- [ ] カードをクリックすると3Dアニメーションで裏返る
- [ ] 裏面に意味が表示される
- [ ] 裏面に紐づくメモの本タイトル・表紙画像が表示される
- [ ] `note=None` の単語は裏面に意味のみ表示される
- [x] アルファベット順 / 登録順のソートが切り替えられる
- [x] 単語が 0 件の場合、わかりやすいメッセージが表示される
- [x] 未ログイン状態でアクセスするとログイン画面にリダイレクトされる
