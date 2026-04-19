from google import genai
from django.conf import settings


def GeminiAsk(Text = ""):
    client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{Text} の意味を一言で説明してください。語数はなるべく少なく。辞書の説明のような簡潔で分かりやすい説明にしてください。"
    )
    return response.text

