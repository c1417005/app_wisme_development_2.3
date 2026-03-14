from google import genai
from dotenv import load_dotenv

# client = genai.Client()

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="How does AI work?"
# )
# print(response.text)

load_dotenv()


def GeminiAsk(Text = ""):
    client = genai.Client()
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents = f"{Text} の意味を一言で説明してください。語数はなるべく少なく。辞書の説明のような簡潔で分かりやすい説明にしてください。"
    )

    return response.text
    
