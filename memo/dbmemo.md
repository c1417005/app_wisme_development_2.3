❯ これから私の質問に答えてください。実装はしないでください。データベースはす    べてのユーザで共有される設計になっていますか？個々人それぞれに作られるわけ    ではないのですね                                                            
                                                                              
● はい、全ユーザーで1つのDBを共有する設計です。                               

  各テーブルのレコードに owner フィールド（ForeignKey to                        CustomUser）があり、クエリ時に filter(owner=request.user)
  でそのユーザーのデータだけを取り出す仕組みです。                            
  
  DB（db.sqlite3）
  ├── wisme_customuser   ← ユーザー一覧
  ├── wisme_page         ← 全ユーザーの全メモ（owner列で区別）
  ├── wisme_chapter      ← 全ユーザーの全章（page経由で帰属）
  └── wisme_searchedword ← 全ユーザーの全単語（owner列で区別）

  unique=True の話との関係でいうと、SearchedWord.word にそれを付けると「apple 
  というレコードはDB全体で1件しか存在できない」になるため、2人目のユーザーが  
  apple を調べた瞬間に制約違反になります。それがマルチユーザー設計と相容れない
  理由です。

❯ 質問に答えてください。実装はしないでください。では現状、すべてのデータベー    スは前ユーザで共通だが、owner列でその個人のものを特定しているということです   ね。つまり、誰かが調べた単語に高速でアクセスできる設計になっているという認    識であっていますか？                                                        
                                                                              
● その認識でほぼ合っていますが、正確には少し補足があります。                  

  意味（meaning）の取得はユーザー横断で共有されています。services.py            の処理を見ると：
                                                                              
  existing = SearchedWord.objects.filter(word=word).first()  # 
  誰かが調べた履歴を全員から検索
  if existing:
      meaning = existing.meaning  # DBから即返す（Gemini API呼ばない）        
  else:
      meaning = GeminiAsk(word)   # 誰も調べたことがない単語だけAPIを呼ぶ     

  つまり「ユーザーAがappleを調べた後、ユーザーBがappleを調べると、Gemini      
  APIを呼ばずDBから返る」という設計です。

  ただし、単語のレコード自体は owner
  ごとに別々に作られます。ユーザーAとBそれぞれに apple のレコードが存在し、単 
  語帳やフラッシュカードは自分のレコードのみ表示されます。

  まとめると：
  - 意味の取得コスト → 全ユーザーで共有（誰かが一度調べれば以降は高速）       
  - 単語帳・フラッシュカードの表示 → 個人ごとに分離