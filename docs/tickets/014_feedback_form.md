# 014 フィードバックフォームの実装

## 1. 概要

### 目的

index.html のページ下部に、ユーザーがアプリへのフィードバック（意見・要望・不具合報告など）を送信できるフォームを設置する。

### 背景

- ユーザーの声を継続的に収集し、今後の機能改善や優先度付けに活用する。
- ログイン済みユーザーと未ログインユーザーの両方から投稿を受け付ける。
- 001（CustomUser）および 002（ユーザー認証）完了後のタスク。

---

## 2. 実装方針

### 基本方針

- **シンプルなフォーム設計:** メッセージ本文のみを必須とし、ユーザーの送信ハードルを下げる。
- **ログイン不要:** 未ログインでも送信可能とする（`owner` は nullable FK）。
- **送信後リダイレクト:** PRG（Post/Redirect/Get）パターンで二重送信を防止し、成功メッセージを表示。
- **Service 層に集約:** ビジネスロジックは `services.py` に置き、View は薄く保つ（Thin View / Fat Service）。

---

## 3. データ構造の変更 (Models)

`Feedback` モデルを `wisme/models.py` に新規追加する。

```python
# wisme/models.py
class Feedback(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("送信者"),
    )
    message = models.TextField(max_length=2000, verbose_name=_("メッセージ"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("送信日時"))

    def __str__(self):
        return self.message[:30]
```

※ フィールド追加後はマイグレーションが必要。

---

## 4. 実装フローとロジック

### 4-1. ユーザー操作の流れ

1. ユーザーが index.html 下部のフィードバックセクションを見つける。
2. テキストエリアにメッセージを入力し「送信」ボタンをクリック。
3. POST リクエストが `feedback/submit/` へ送信される。
4. バリデーション通過後、`Feedback` レコードを保存。
5. `index` へリダイレクトし、成功メッセージをページ上部に表示。

### 4-2. フォームクラス (Forms)

```python
# wisme/forms.py
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['message']
```

### 4-3. ビュー (Views)

```python
# wisme/views.py
def feedback_submit(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.owner = request.user
            feedback.save()
            messages.success(request, _("フィードバックを送信しました。ありがとうございます！"))
            return redirect('wisme:index')
    return redirect('wisme:index')
```

---

## 5. UI/UX 仕様

- **配置:** index.html の `{% endblock %}` 直前（`{% endif %}` の後）に独立したセクションとして設置。
- **スタイリング:** 既存の Tailwind CSS クラスに合わせ、白背景・角丸・ボーダーを基調としたカード形式。
- **テキストエリア:** 3〜4 行程度の高さ（`rows="4"`）、最大文字数 2000 を `maxlength` で制限。
- **送信ボタン:** 既存の `bg-stone-800` ボタンと同じスタイルを踏襲。
- **成功メッセージ:** Django の `messages` フレームワークを利用し、ベーステンプレートで表示（既存の実装があれば流用）。
- **CSRF:** Django デフォルトの `{% csrf_token %}` をフォームタグ内に必ず含める。

---

## 6. テスト項目 (DoD: Definition of Done)

### 動作確認

- [x] ログイン済みユーザーがフォームを送信すると、`Feedback` レコードに `owner` が紐づいて保存される。
- [ ] 未ログインユーザーがフォームを送信すると、`owner=None` で `Feedback` レコードが保存される。（実装上 `LoginRequiredMixin` によりログイン画面へリダイレクト。index 自体もログイン必須のため実質影響なし）
- [x] 空のメッセージを送信した場合、バリデーションエラーが表示される（またはリダイレクト前にはじかれる）。
- [x] 送信成功後、index ページへリダイレクトされ成功メッセージが表示される。
- [×] ブラウザのリロードによる二重送信が発生しない（PRG パターン）。（手動確認済み・自動テスト対象外）

### 安全性・品質確認

- [x] CSRF トークンがフォームに含まれている。
- [x] `message` フィールドの入力値は Django フォームでバリデーションされる。
- [x] メッセージの最大文字数（2000 字）を超えた入力を受け付けない。
