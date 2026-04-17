# 006 単語検索 UX 改善（スケルトン UI・パフォーマンス）

## 1. 概要

### 目的
Gemini API による単語検索中のローディング表示（スケルトン UI またはプログレスバー）を追加し、  
DB キャッシュを活用した検索高速化を完全に機能させる。

### 背景
- 現在の `WordService.search_or_fetch()` は DB ヒット時に API を呼ばない設計だが、  
  `SearchedWord.word` の `unique=True` と `db_index=True` が設定されているか確認が必要。
- API 呼び出し中に UI が固まるとユーザー体験が悪い。
- CLAUDE.md に「検索中はスケルトン UI またはプログレスバーを表示」と明記されている。

---

## 2. 実装方針

### 2-1. DB インデックスの確認・修正

`SearchedWord.word` フィールドを確認し、以下が設定されていることを確認する：

```python
class SearchedWord(models.Model):
    word = models.CharField(max_length=100, unique=True, db_index=True)
```

`unique=True` は暗黙的にインデックスを生成するが、明示的に `db_index=True` も付与しておく。

### 2-2. スケルトン UI の実装（フロントエンド）

`templates/wisme/page_create.html` および `page_update.html` の単語検索フォームに追加：

```html
<!-- 検索中に表示するスケルトン -->
<div id="skeleton-loader" class="skeleton" style="display:none;">
  <div class="skeleton-line"></div>
  <div class="skeleton-line short"></div>
</div>
<div id="search-result"></div>
```

```javascript
// 既存の AJAX 処理に追加
async function searchWord(word) {
  document.getElementById('skeleton-loader').style.display = 'block';
  document.getElementById('search-result').textContent = '';
  try {
    const res = await fetch('/wisme/search/mean/', { ... });
    const data = await res.json();
    document.getElementById('search-result').textContent = data.mean;
  } finally {
    document.getElementById('skeleton-loader').style.display = 'none';
  }
}
```

### 2-3. スケルトン CSS の追加

`static/wisme/css/style.css` に追加：

```css
.skeleton {
  background: #e0e0e0;
  border-radius: 4px;
  padding: 12px;
  animation: pulse 1.5s infinite;
}
.skeleton-line {
  height: 14px;
  background: #c0c0c0;
  border-radius: 4px;
  margin-bottom: 8px;
}
.skeleton-line.short { width: 60%; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 2-4. エラー時の表示

API エラーや通信エラー発生時にユーザーにわかりやすいメッセージを表示する：

```javascript
} catch (e) {
  document.getElementById('search-result').textContent = '検索に失敗しました。再度お試しください。';
}
```

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/models.py` | `SearchedWord.word` の `db_index=True` を確認・追加 |
| `static/wisme/css/style.css` | スケルトン CSS を追加 |
| `templates/wisme/page_create.html` | スケルトン UI と JS を追加 |
| `templates/wisme/page_update.html` | 同上 |
| `wisme/migrations/` | インデックス変更がある場合のみ |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [ ] 単語を入力して検索ボタンを押すと、スケルトン UI が表示される
- [ ] 検索結果が返ってくるとスケルトンが消えて意味が表示される
- [ ] 2 回目以降に同じ単語を検索すると DB から即座に返る（API を呼ばない）
- [ ] ネットワークエラー時にエラーメッセージが表示される
- [ ] スマートフォン表示でもスケルトン UI が崩れない

### パフォーマンス確認
- [ ] `SearchedWord.word` に `unique=True` が設定されている
- [ ] Django shell で `SearchedWord.objects.filter(word='...')` が高速に返る
