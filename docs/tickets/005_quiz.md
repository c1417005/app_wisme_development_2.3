# 005 クイズ機能の実装

## 1. 概要

### 目的
ユーザーが保存した単語（`SearchedWord`）を使った復習クイズを実装する。  
単語を見て意味を答える形式で出題し、正誤判定とクイズ結果の記録を行う。

### 背景
- 単語帳（004）で保存した単語を実際に復習できる仕組みが必要。
- クイズ結果を記録することで、苦手な単語を把握できるようにする。
- 004 チケット（単語帳機能）完了後に実施する。

---

## 2. 実装方針

### 2-1. クイズ結果モデルの追加

```python
class QuizResult(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    word = models.ForeignKey(
        SearchedWord,
        on_delete=models.CASCADE,
    )
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
```

### 2-2. クイズのフロー設計

1. `/wisme/quiz/start/` — クイズ開始（対象の単語をランダムで N 件セッションに格納）
2. `/wisme/quiz/question/` — 1 問ずつ出題（単語を表示、意味を選択肢または入力で回答）
3. `/wisme/quiz/result/` — 全問終了後に正答数・正答率を表示し `QuizResult` を保存

> 初期実装は **単語 → 意味** の自由記述形式とし、意味の一致判定はサーバー側で行う。選択肢形式は拡張として後回し。

### 2-3. クイズビューの追加

```python
# wisme/views.py
class QuizStartView(LoginRequiredMixin, View):
    """クイズ対象の単語をセッションに格納してリダイレクト"""

class QuizQuestionView(LoginRequiredMixin, View):
    """セッションから1問ずつ取り出して出題"""

class QuizResultView(LoginRequiredMixin, View):
    """結果を表示し QuizResult を一括保存"""
```

### 2-4. 回答判定ロジック（`wisme/services.py`）

```python
class QuizService:
    @staticmethod
    def judge(user_answer: str, correct_answer: str) -> bool:
        # 空白・大文字小文字を正規化して比較
        return user_answer.strip().lower() == correct_answer.strip().lower()
```

### 2-5. URL の追加

```python
path('quiz/start/', QuizStartView.as_view(), name='quiz_start'),
path('quiz/question/', QuizQuestionView.as_view(), name='quiz_question'),
path('quiz/result/', QuizResultView.as_view(), name='quiz_result'),
```

---

## 3. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `wisme/models.py` | `QuizResult` モデルを追加 |
| `wisme/views.py` | Quiz 系ビューを追加 |
| `wisme/services.py` | `QuizService.judge()` を追加 |
| `wisme/urls.py` | クイズ URL を追加 |
| `templates/wisme/` | `quiz_start.html`, `quiz_question.html`, `quiz_result.html` を追加 |
| `wisme/migrations/` | `QuizResult` のマイグレーションを追加 |

---

## 4. テスト項目（完了定義 / DoD）

### 動作確認
- [ ] クイズ開始画面から問題が出題される
- [ ] 正解・不正解が判定され次の問題に進む
- [ ] 全問終了後に正答数と正答率が表示される
- [ ] クイズ結果が DB に保存される
- [ ] 単語が 0 件の場合、クイズ開始時にわかりやすいメッセージが表示される
- [ ] 未ログイン状態でクイズ画面にアクセスするとログイン画面にリダイレクトされる

### ロジック確認
- [ ] 大文字小文字の違いは無視して判定される
- [ ] 前後の空白は無視して判定される
