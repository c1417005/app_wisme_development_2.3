from .models import SearchedWord
from .utils.func_api import GeminiAsk


class WordService:
    @staticmethod
    def search_or_fetch(word: str, user=None) -> SearchedWord:
        existing = SearchedWord.objects.filter(word=word).first()
        if existing:
            meaning = existing.meaning
        else:
            meaning = GeminiAsk(word)

        # 同じユーザー・同じ単語・未紐付けのレコードが既にあれば再利用する
        instance, _ = SearchedWord.objects.get_or_create(
            word=word,
            owner=user,
            note=None,
            defaults={'meaning': meaning},
        )
        # meaning が空の場合（既存レコードが先に作られていた場合）は上書き
        if not instance.meaning:
            instance.meaning = meaning
            instance.save(update_fields=['meaning'])
        return instance
