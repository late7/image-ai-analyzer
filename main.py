import os
import base64

from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from typing import Any, Dict, Optional

# For environment variable loading
from dotenv import load_dotenv

# Import the OpenAI library
from openai import OpenAI

# 1. Load environment variables from .env
load_dotenv()

# 2. Read the API key and access token from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
access_token = os.getenv("ACCESS_TOKEN")

# 3. Initialize the OpenAI client with the API key
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

def verify_access_token(token: Optional[str]):
    if token != access_token:
        raise HTTPException(status_code=401, detail="Invalid or missing access token")

@app.get("/", response_class=HTMLResponse)
def get_upload_form(request: Request, x_access_token: Optional[str] = Header(None)):
    """
    Returns a simple HTML form for manual image upload.
    """
    verify_access_token(x_access_token)
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
          <title>GPT-4 Vision Demo</title>
      </head>
      <body>
          <h1>Upload an Image for GPT-4 Vision Analysis</h1>
          <form action="/analyze" method="post" enctype="multipart/form-data">
              <input type="file" name="file" accept="image/*" />
              <button type="submit">Analyze Image</button>
          </form>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), x_access_token: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Receives an image via form-data,
    encodes it in Base64, then calls the GPT-4 Vision endpoint.
    """
    verify_access_token(x_access_token)
    
    # 1. Read and Base64-encode the image
    image_bytes = await file.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # 2. Build messages array with "text" and "image_url" blocks
    messages = [
        {
          "role": "system",
          "content": [
            {
              "type": "text",
              "text": "You are professional analyser that analyses profile picture for an App. You are given images one by one. Answer either OK or not-OK. For not-OK result give a short reasoning that advice end user to select proper photo.\nOK: Profile picture should clearly contain human face in front or standing or sitting face facing the camera. Clothing, if visible, should be business or business casual as the App is meant for professional use.\nNot-OK: Detect and report as not-OK any unappropriate images and parts of images. Especially:  offensive or containing NSFW content. Detect also if the image is manipulated for face change or similar discontinuity on pixel level."
            }
          ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
            ],
        }
    ]

    # 3. Call the GPT-4 Vision endpoint
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use the correct model name
            messages=messages,
            max_tokens=2000,  # Adjust as needed
        )
    except Exception as e:
        return {"error": str(e)}

    # 4. Return response from GPT-4 Vision
    return {
        "response": response.choices[0].message.content  # Extract the content from the response
    }

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)