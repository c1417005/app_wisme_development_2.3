from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from pathlib import Path
from encrypted_model_fields.fields import EncryptedCharField
import uuid


class CustomUser(AbstractUser):
    display_name = EncryptedCharField(max_length=100, blank=True, verbose_name="表示名")
    profile_image = models.ImageField(
        upload_to='media/profile/', blank=True, null=True, verbose_name="プロフィール画像"
    )

    def save(self, *args, **kwargs):
        try:
            old = CustomUser.objects.get(pk=self.pk)
            if old.profile_image and old.profile_image != self.profile_image:
                Path(old.profile_image.path).unlink(missing_ok=True)
        except CustomUser.DoesNotExist:
            pass
        super().save(*args, **kwargs)

class Page(models.Model):
    id = models.UUIDField(primary_key=True,
                          default = uuid.uuid4,editable=False,verbose_name="Id")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="オーナー",
    )
    
    title = models.CharField(max_length=100,verbose_name="タイトル")

    #input_word = models.TextField(max_length=1000,verbose_name="意味を知りたい単語")

    #return_mean = models.CharField(max_length=100,verbose_name="その単語の意味",null = True)

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


class Chapter(models.Model):
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name='所属メモ',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='並び順')
    title = models.CharField(max_length=100, blank=True, verbose_name='章タイトル')
    content = models.TextField(blank=True, verbose_name='章の内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title or f'第{self.order + 1}章'


class SearchedWord(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="オーナー",
    )
    note = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='words',
        null = True,
        blank = True,
        verbose_name = "関連メモ"
    )
    word = models.CharField(max_length=100, db_index=True, verbose_name="意味を知りたい単語")
    meaning = models.TextField(verbose_name="意味")
    created_at = models.DateTimeField(auto_now_add = True,verbose_name="検索日時")


    def __str__(self):
        return self.word