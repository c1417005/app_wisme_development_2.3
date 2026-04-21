import logging

import requests

from django.conf import settings

logger = logging.getLogger(__name__)

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


class BookThumbnailService:
    _ENDPOINT = 'https://www.googleapis.com/books/v1/volumes'

    @staticmethod
    def search(title: str, author: str = '') -> list[dict]:
        q = f'intitle:{title}'
        if author:
            q += f'+inauthor:{author}'
        params: dict = {
            'q': q,
            'maxResults': '20',
            'printType': 'books',
        }
        api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', '')
        if api_key:
            params['key'] = api_key
        try:
            res = requests.get(
                BookThumbnailService._ENDPOINT,
                params=params,
                timeout=10,
                proxies={'http': None, 'https': None},
            )
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            logger.warning('BookThumbnailService: request failed: %s', e)
            return []

        results = []
        for item in data.get('items', []):
            info = item.get('volumeInfo', {})
            images = info.get('imageLinks', {})
            thumbnail = images.get('thumbnail') or images.get('smallThumbnail', '')
            if not thumbnail:
                continue
            thumbnail = thumbnail.replace('http://', 'https://')
            results.append({
                'title': info.get('title', ''),
                'thumbnail': thumbnail,
            })
        return results
