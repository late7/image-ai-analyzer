import os
import base64
from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Header, Form, Body
from fastapi.responses import HTMLResponse
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
access_token = os.getenv("ACCESS_TOKEN")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

def verify_access_token(token: Optional[str]):
    """Check if the provided token matches the stored access token."""
    if token != access_token:
        raise HTTPException(status_code=401, detail="Invalid or missing access token")

def create_completion(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calls the GPT-4 API using the provided messages.
    The lengthy response_format is defined within this function.
    Returns the API response or an error message.
    """
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "content_compliance",
            "schema": {
                "type": "object",
                "required": ["status", "violation_reason"],
                "properties": {
                    "status": {
                        "type": "boolean",
                        "description": "Indicates whether the content is appropriate."
                    },
                    "violation_reason": {
                        "type": "string",
                        "description": "Explanation of why the content violates policies and suggestions for correction."
                    }
                },
                "additionalProperties": False
            },
            "strict": True
        }
    }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format=response_format,
            temperature=0.5,
            max_completion_tokens=1142,
            top_p=0.79,
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

def call_gpt4_vision(base64_images: List[str]) -> Dict[str, Any]:
    """
    Calls GPT-4 Vision API with the given list of base64-encoded images.
    Returns the API response.
    """
    prompt = (
        'Check if the profile picture meets these requirements: real photo (not AI generated), one clear face, good quality, '
        'no logos/copyrighted material, no impersonation, no NSFW/NSFL content, no overlays, appropriate clothing (shirt/pants), '
        'facing camera, professional pose, non-distracting background. Respond "true" if all met; otherwise, '
        '"false" with a brief reason. Ignore stock watermarks.'
    )

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": prompt}]
        }
    ]

    # Append all images as user messages.
    for base64_image in base64_images:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ],
        })

    return create_completion(messages)

@app.get("/", response_class=HTMLResponse)
def get_upload_form(request: Request):
    """Returns an HTML form for manual image upload."""
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
              <input type="text" name="x_access_token" placeholder="Enter Access Token" />
              <button type="submit">Analyze Image</button>
          </form>
    
          <h1>Analyze Text</h1>
          <form action="/analyze_text" method="post" enctype="multipart/form-data">
              <textarea name="text" rows="4" cols="50" placeholder="Enter text to analyze"></textarea>
              <input type="text" name="x_access_token" placeholder="Enter Access Token" />
              <button type="submit">Analyze Text</button>
          </form>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

# The /analyze endpoint accepts a single image file upload.
@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), x_access_token: Optional[str] = Form(None)) -> Dict[str, Any]:
    """Handles file upload and analysis via GPT-4 Vision."""
    verify_access_token(x_access_token)
    
    # Read and encode image.
    image_bytes = await file.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    return call_gpt4_vision([base64_image])

# The /analyze-json endpoint accepts a JSON payload with one or more base64-encoded images.
@app.post("/analyze-json")
async def analyze_image_json(
    request: Request,
    x_access_token: Optional[str] = Header(None),
    payload: Dict[str, Any] = Body(...)
):
    """
    Receives one or more images in a JSON payload:
    {
      "images_base64": ["<base64_string1>", "<base64_string2>"]
    }
    """
    verify_access_token(x_access_token)

    base64_images = payload.get("images_base64", [])
    if not base64_images:
        raise HTTPException(status_code=400, detail="Missing images_base64 in request body")

    return call_gpt4_vision(base64_images)

# /analyze_text endpoint accepts a form-data payload with a text prompt.
@app.post("/analyze_text")
async def analyze_text(text: str = Form(...), x_access_token: Optional[str] = Form(None)) -> Dict[str, Any]:
    """
    Receives text via form-data and sends it to the GPT-4 API for analysis.
    """
    verify_access_token(x_access_token)

    prompt = (
        'The attached text is a "reason for calling" in an application. Check if the text meets these requirements: '
        'is appropriate for business, family, or friend interactions; does not contain inappropriate, offensive, '
        'harassing, threatening, or explicit content; can be any language and use respectful slang. '
        'Respond OK if all met; otherwise, Not OK with a brief reason.'
    )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]

    return create_completion(messages)

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
