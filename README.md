# image-ai-analyzer

## Setup Python env (optional)
python -m venv venv

$ ./venv/Scripts/activate   # on windows Git Bash

$ ./venv/bin/activate


## Installation

pip install -r requirements.txt
cd image-ai-analyzer

## Create a .env File
Edit .env file or

echo "OPENAI_API_KEY=sk-xxxx" >> .env

## Run the Server

uvicorn main:app --reload

## Test with Browser

Open http://localhost:8000/.
Upload a .jpg or .png file.
Check the JSON result (the model’s text) in your browser or browser dev tools.

## Test with Postman or cURL or test.sh


curl -X POST -F "file=@test.jpg" http://localhost:8000/analyze

test.sh tests JSON POST
