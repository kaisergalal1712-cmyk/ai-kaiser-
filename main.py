from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import pytesseract
import io
import openai
from googleapiclient.discovery import build

openai.api_key = "YOUR_OPENAI_API_KEY"
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def search_youtube(query, max_results=3):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    videos = []
    for item in response['items']:
        videos.append({
            "title": item['snippet']['title'],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return videos

@app.post("/solve")
async def solve_question(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    question_text = pytesseract.image_to_string(image, lang='ara+eng')

    prompt = f"Please solve this question step by step and explain clearly:\n{question_text}"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    prompt_keywords = f"Generate 3-5 keywords to search YouTube for explaining this question:\n{question_text}"
    keywords_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_keywords}]
    )
    keywords_list = [kw.strip() for kw in keywords_response.choices[0].message.content.split(',')]

    videos = []
    for kw in keywords_list:
        videos += search_youtube(kw, max_results=1)

    return {"question": question_text, "solution": answer, "videos": videos}
