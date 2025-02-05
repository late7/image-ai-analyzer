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

print(f"OPENAI_API_KEY: {openai_api_key}")
print(f"ACCESS_TOKEN: {access_token}")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

def verify_access_token(token: Optional[str]):
    """Check if the provided token matches the stored access token."""
    if token != access_token:
        raise HTTPException(status_code=401, detail="Invalid or missing access token")

def call_gpt4_vision(base64_images: List[str]) -> Dict[str, Any]:
    """
    Calls GPT-4 Vision API with the given list of base64-encoded images.
    Returns the API response.
    """
    prompt = (
        'You are a professional analyzer that evaluates profile pictures for an App. '
        'You are given images one by one. Answer either "true" or "false". '
        'For false: provide a short reasoning advising the user on how to select a proper photo. '
        'True: Profile picture should clearly contain a human face in front-facing view, standing or sitting, '
        'wearing business or business casual attire, and free from offensive or NSFW content. '
        'False: Detect and report any inappropriate images, such as offensive, manipulated, or AI-generated faces.'
    )

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": prompt}]
        }
    ]

    # Append all images to the request
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={
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
            },
            temperature=0.5,
            max_completion_tokens=1142,
            top_p=0.79,
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

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
      </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), x_access_token: Optional[str] = Form(None)) -> Dict[str, Any]:
    """Handles file upload and analysis via GPT-4 Vision."""
    verify_access_token(x_access_token)
    
    # Read and encode image
    image_bytes = await file.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Call GPT-4 Vision API
    return call_gpt4_vision([base64_image])

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

    # Extract base64 images
    base64_images = payload.get("images_base64", [])
    if not base64_images:
        raise HTTPException(status_code=400, detail="Missing images_base64 in request body")

    # Call GPT-4 Vision API
    return call_gpt4_vision(base64_images)

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
