# image-ai-analyzer



## Installation

pip install -r requirements.txt

## Create a .env File
Edit .env file or
echo "OPENAI_API_KEY=sk-xxxx" >> .env

## Run the Server

uvicorn main:app --reload

## Test with Browser

Open http://localhost:8000/.
Upload a .jpg or .png file.
Check the JSON result (the model’s text) in your browser or browser dev tools.

## Test with Postman or cURL


curl -X POST -F "file=@test.jpg" http://localhost:8000/analyze
