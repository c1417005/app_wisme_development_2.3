# 011 UI/UX 実装（デザインシステム・画面別フロントエンド）

## 1. 概要

### 目的
「読書体験を拡張し、自分の書いたメモを振り返る」ためのアプリとして、全画面に統一されたデザインとインタラクションを実装する。  
バックエンドロジック（Django ビュー・モデル）は既存のものを活用し、**見た目とフロントエンドの挙動**に特化する。

### デザインコンセプト
- **視覚的主役は「本の表紙」。** 自分の書斎を眺めているような感覚。
- **ベースカラー:** オフホワイト・紙の質感を意識した落ち着いた色調（例: `#FAF8F4`）。
- **トーン:** 読書のリズムを崩さない。単語検索はシームレスに行えること。

### 前提チケット
- 001（CustomUser）・002（認証）・004（単語帳）・006（単語検索 UX）・007（推薦図書）が完了していること。

---

## 2. 実装方針

### 2-1. ベーステンプレートの刷新（`templates/base/wisme_base.html`）

以下を CDN で読み込む：

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>
<!-- Vue.js 3 -->
<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
<!-- Lucide Icons -->
<script src="https://unpkg.com/lucide@latest"></script>
```

- ベースの `<body>` 背景色: `bg-[#FAF8F4]`
- ナビゲーション: Lucide Icons を使用したシンプルなトップバー。
- 既存の Bootstrap 依存があれば段階的に Tailwind へ移行する。

### 2-2. ダッシュボード（ホーム画面）

**対象テンプレート:** `templates/wisme/index.html`

#### 初回ログイン時
- アカウント作成後の初回アクセス（セッションフラグまたは `Page` 件数 = 0 で判定）に「このアプリでできること」の説明 UI を表示。
- モーダルまたはウェルカムセクションで実装。

#### 通常時
- 中央に「いま、何を読んでいますか？」という問いかけと、直近のメモへの **再開ボタン**（`Page.objects.filter(owner=user).order_by('-updated_at').first()` で取得）を配置。
- 推薦図書カルーセルは画面下部（2-5 参照）。

#### 振り返りポップアップ
- `Page.updated_at` が現在時刻から **7 日以上**経過している場合、「久しぶりに自分の書いたメモを振り返ってみませんか？」というポップアップを表示。
- クリックで `wisme:page_list`（メモ一覧）へ遷移。クイズ・学習画面へは飛ばない。
- 表示制御は JavaScript で行い、`localStorage` にフラグを保存してセッション内で1回のみ表示。
- `Page.updated_at` の値は Django テンプレートの `data-*` 属性でフロントエンドへ渡す。

```html
<!-- index.html の <body> 内 -->
<div data-last-updated="{{ last_page_updated_at|date:'c' }}" id="review-popup-trigger"></div>
```

### 2-3. 動的エディタ（メモ作成・編集画面）

**対象テンプレート:** `templates/wisme/page_form.html`, `page_update.html`

#### 章（Chapter）エディタ
- バックエンド側のデータモデル・formset・ビュー拡張は **チケット 012（章単位メモ機能）** で定義。本チケットでは UI 面のみを担当する。
- 実装は **Django `inlineformset_factory` + バニラ JS** で行う（Vue.js は導入しない）。
- 「章を追加」ボタン押下で、formset の `empty_form` を複製して DOM に挿入し、`TOTAL_FORMS` をインクリメントする。ページ遷移は発生させない。
- フォーム送信は通常の Django formset として POST される（hidden JSON input は不要）。

#### 感想と章の視覚分離
- 「本全体の感想」（`Page.thoughts`）と「章ごと」（`Chapter`）のセクションを視覚的に明確に分離する：
  - 感想セクション: アクセント色の左ボーダー or 薄背景 + 見出し「本全体の感想」。
  - 章セクション: 白カード + 章番号バッジ。章間にセパレータ。
- 要件書 `requirements/UI_requirements.md` セクション B「本全体の感想文入力欄と、章ごとの入力欄を明確に分ける」に対応。

#### 自動紐付けの視覚化
- 単語検索が完了し自動紐付けが成功した際、検索結果エリアに控えめなインジケーター（例: 緑のチェックアイコン + 「このメモに保存されました」テキスト）を 3 秒表示する。

### 2-4. 単語検索サイドバー（メモ作成・編集画面）

詳細は 006 チケットを参照。このチケットではレイアウト面のみ規定する：

- PC: メモ入力エリア右横に固定幅のサイドバーとして常駐。
- スマホ: 画面下部に折りたたんだパネルとして配置し、スワイプアップで展開。
- スケルトン UI・エラーメッセージの実装は 006 チケットと共有。

### 2-5. 推薦図書カルーセル（ダッシュボード下部）

**対象テンプレート:** `templates/wisme/index.html`

- 本の表紙画像（縦長、比率 2:3）を横スクロールで並べるカルーセルを実装。
- スクロール量は CSS `overflow-x: scroll` + `scroll-snap` で実装（JS ライブラリ不要）。
- 表紙画像がない場合はタイトル文字のプレースホルダーカードを表示。
- データは Django ビューから `recommendations` コンテキストとして渡す（007 チケット参照）。

```html
<div class="flex gap-4 overflow-x-scroll snap-x snap-mandatory pb-4">
  {% for book in recommendations %}
  <div class="snap-start shrink-0 w-32">
    <img src="{{ book.cover_url }}" class="w-full aspect-[2/3] object-cover rounded shadow" alt="{{ book.title }}">
    <p class="text-xs mt-1 truncate">{{ book.title }}</p>
  </div>
  {% endfor %}
</div>
```

### 2-6. フラッシュカード（単語帳・クイズ画面）

詳細は 005 チケットを参照。CSS 実装のみここで規定する：

```css
/* 3D フリップカード */
.card-container { perspective: 1000px; }
.card { transform-style: preserve-3d; transition: transform 0.5s; }
.card.flipped { transform: rotateY(180deg); }
.card-front, .card-back { backface-visibility: hidden; }
.card-back { transform: rotateY(180deg); }
```

- Tailwind のユーティリティクラスで同等の効果を実現する場合は `[transform-style:preserve-3d]` 等の任意値クラスを使用。

### 2-7. トースト通知

- 保存ボタン押下後、Django のレスポンスを受けて「保存しました ✓」トースト通知を Vue.js で表示。
- 表示時間: 3 秒。画面右下に絶対配置。

```javascript
// Vue component
const app = Vue.createApp({
  data() { return { toast: null } },
  methods: {
    showToast(msg) {
      this.toast = msg;
      setTimeout(() => this.toast = null, 3000);
    }
  }
});
```

### 2-8. 表紙画像の表示ルール（一覧画面）

- `templates/wisme/page_list.html`（メモ一覧）では、テキスト情報よりも本の表紙画像を優先して表示。
- カードレイアウト: 縦長（比率 3:4 または 2:3）で整列。タイトルは画像下部に小さく表示。
- 表紙がない場合: グレーの `<div>` にタイトル文字を中央表示するプレースホルダーを使用。

---

## 3. レスポンシブ設計

| 画面幅 | 対応内容 |
|---|---|
| PC（768px 以上）| 2カラム（メモエディタ + 検索サイドバー）、カルーセル表示 |
| スマホ（767px 以下）| 1カラム、検索パネルはスワイプアップで展開、カルーセルは横スクロール |

- Tailwind のブレークポイント（`md:`, `lg:`）を基準にする。

---

## 4. 影響範囲

| ファイル | 変更内容 |
|---|---|
| `templates/base/wisme_base.html` | Tailwind・Vue.js・Lucide を読み込み、ナビゲーションを更新 |
| `templates/wisme/index.html` | ダッシュボード全面刷新（再開ボタン・振り返りポップアップ・カルーセル） |
| `templates/wisme/page_list.html` | 表紙画像優先のカードレイアウトに変更 |
| `templates/wisme/page_form.html` | 感想/章セクションの視覚分離、章 formset の動的追加 UI（012 連携）、自動紐付けインジケーター、サイドバー |
| `templates/wisme/page_update.html` | 同上 |
| `static/wisme/js/chapter_formset.js` | 「章を追加」のバニラ JS（012 連携） |
| `static/wisme/css/style.css` | フリップカード CSS、トースト CSS、スケルトン CSS を追加 |
| `wisme/views.py` | `IndexView` に `last_page_updated_at` コンテキストを追加 |

---

## 5. テスト項目（完了定義 / DoD）

### ダッシュボード
- [ ] 初回ログイン時（Page 0 件）にウェルカム UI が表示される
- [ ] 直近のメモへの再開ボタンが機能する
- [ ] 7 日以上更新がない場合、振り返りポップアップが表示される
- [ ] ポップアップクリックでメモ一覧へ遷移する（クイズ画面ではない）
- [ ] 同一セッション内でポップアップが2回表示されない

### 動的エディタ（UI 面のみ。データ保存側は 012 チケット）
- [ ] 「章を追加」ボタンで入力欄が増える（ページ遷移なし）
- [ ] 「本全体の感想」と「章ごと」が視覚的に明確に分離されて表示される
- [ ] 自動紐付け成功時にインジケーターが3秒表示される

### デザイン・レスポンシブ
- [ ] PC 表示でサイドバーがメモ横に常駐する
- [ ] スマホ表示でサイドバーが下部パネル形式になる
- [ ] メモ一覧で表紙画像が縦長カードで表示される
- [ ] 表紙がないメモでプレースホルダーが表示される
- [ ] 推薦図書カルーセルが横スクロールする

### インタラクション
- [ ] 保存時にトースト通知「保存しました ✓」が3秒表示される
- [ ] フラッシュカードをクリックすると3Dアニメーションで裏返る
