from django.db import models
from pathlib import Path
import uuid

class Page(models.Model):
    id = models.UUIDField(primary_key=True,
                          default = uuid.uuid4,editable=False,verbose_name="Id")
    
    title = models.CharField(max_length=100,verbose_name="タイトル")

    input_word = models.TextField(max_length=1000,verbose_name="意味を知りたい単語")

    return_mean = models.CharField(max_length=100,verbose_name="その単語の意味",null = True)

    thoughts = models.TextField(max_length=1000,blank=True,verbose_name="このドキュメントを読んだ感想(空欄可)")

    page_date = models.DateField(verbose_name="日付")

    picture = models.ImageField(upload_to="wisme/picture/",blank = True,null = True,verbose_name="写真")

    created_at = models.DateTimeField(auto_now_add = True,verbose_name="作成日時")#このデータが初めて作成されたその時の日時を保存

    update_at = models.DateTimeField(auto_now = True,verbose_name="更新日時")#更新されたら日時を保存



    def __str__(self):
        return self.title
    
    def delete(self, *args,**kwargs):
        picture = self.picture
        super().delete(*args,**kwargs)
        if picture:
            Path(picture.path).unlink(missing_ok=True)


