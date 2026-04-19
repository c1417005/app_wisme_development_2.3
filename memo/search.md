● 章単位入力の導入 — 影響調査サマリ

  前提方針

  要件B「本全体の感想文入力欄と、章ごとの入力欄を明確に分ける」に従い、既存の 
  Page.thoughts は「本全体の感想」として残し、Chapter
  モデルを新規追加する加算的変更とするのが安全。

  影響を受ける箇所

  分類: モデル
  ファイル: wisme/models.py
  影響: 加算
  変更内容: 新モデル Chapter(page FK, order, title?, content) を追加。Page    
    は無変更で thoughts も保持。
  ────────────────────────────────────────
  分類: マイグレーション
  ファイル: wisme/migrations/
  影響: 加算
  変更内容: 新規 0005_chapter.py の追加のみ。既存データ移行不要。
  ────────────────────────────────────────
  分類: フォーム
  ファイル: wisme/forms.py
  影響: 拡張
  変更内容: inlineformset_factory(Page, Chapter, ...) で ChapterFormSet       
    を定義。PageForm 自体は無変更。
  ────────────────────────────────────────
  分類: ビュー
  ファイル: wisme/views.py
  影響: 変更
  変更内容: PageCreateView.post / PageUpdateView.post で formset の is_valid()

    と save() を追加。PageDetailView.get に chapters = page.chapters.all()    
    を追加。PageDeleteView は FK の CASCADE で自動処理されるため無変更。      
  ────────────────────────────────────────
  分類: テンプレート
  ファイル: page_form.html / page_update.html
  影響: 変更
  変更内容: 「本全体の感想」と「章ごと」セクションを視覚分離。formset
    各行レンダリング + {{ formset.management_form }} + empty_form
    テンプレート（JS 複製用）を追加。
  ────────────────────────────────────────
  分類: テンプレート
  ファイル: page_detail.html
  影響: 変更
  変更内容: chapters を order 順に iterate して章単位表示。thoughts
    との表示上の区分けも必要。
  ────────────────────────────────────────
  分類: JS
  ファイル: 新規 or search.js と別ファイル
  影響: 加算
  変更内容: 「章を追加」ボタンで empty_form を複製し TOTAL_FORMS
    をインクリメント（ページ遷移なし）。要件「章の追加:
    JavaScriptを用いて、ページ遷移なしで章の入力欄を追加可能」を満たす。      
  ────────────────────────────────────────
  分類: admin
  ファイル: wisme/admin.py
  影響: 任意
  変更内容: ChapterInline を PageAdmin
    に追加するとメンテしやすい。必須ではない。
  ────────────────────────────────────────
  分類: テスト
  ファイル: wisme/tests.py
  影響: 互換
  変更内容: make_page() は thoughts=""
    のままで壊れない。章作成のテスト追加は任意。
  ────────────────────────────────────────
  分類: SearchedWord
  ファイル: models.py / services.py / views.py
  影響: 無変更可
  変更内容: note FK は Page
    単位のままで要件「そのメモへ紐づく」を満たす。章単位に紐付けたい場合のみ  
  FK
     追加だが今回スコープ外として OK。

  破壊的影響の有無

  - データ破壊なし: thoughts カラムは残る。既存 Page データは全て有効。       
  - URL/リダイレクト無変更: ルーティングに影響なし。
  - 既存テスト全通過見込み: 章参照を追加しなければ既存テストは無関係。        
  - CASCADE 削除: Page 削除時に章も自動削除される（page_confirm_delete.html   
  の文言「紐づいた単語も削除されます」は自然に「紐づいた章・単語」へ拡張可）。

  実装上の留意点

  1. 順序管理: Chapter.order = IntegerField。保存時にフォーム順で 0,1,2,...   
  を振り直すのが簡単。後でドラッグ並替を入れる余地を残す。
  2. formset 動的追加の定番: Django の {{ formset.empty_form|crispy }} 相当を 
  __prefix__ 付きで出力し、JS で __prefix__ を現 TOTAL_FORMS に置換 →
  TOTAL_FORMS を +1。
  3. 既存の自動紐付けロジック
  (SearchedWord.objects.filter(note__isnull=True).update(note=new_page)) は   
  Page 単位なので無影響。ただし副作用として、複数ユーザー環境では他人の未紐付 
  けワードを拾う潜在バグあり（本件とは独立。別途修正推奨）。
  4. モバイル UI: 章が増えるとスクロール量が増える。目次ジャンプや折りたたみは
  将来検討可。現在のスコープ外でも要件は満たせる。
  5. サイドバー検索との共存: 単語検索パネルの挙動（search.js）は影響ゼロ。    

  結論

  変更可能。既存コードとは非破壊的に共存する加算的リファクタで実装可能。影響範
  囲は models/forms/views/templates に局所化され、データマイグレーションや既存
  テスト修正は不要。主要工数は「formset + JS の動的追加 UI」と「page_detail   
  表示調整」の2点。