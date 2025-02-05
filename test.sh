#!/bin/bash

# Check if a filename and access token are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <image_file.png> <access_token>"
    exit 1
fi

IMAGE_FILE="$1"
ACCESS_TOKEN="$2"

# Check if the file exists
if [ ! -f "$IMAGE_FILE" ]; then
    echo "Error: File '$IMAGE_FILE' not found!"
    exit 1
fi

# Convert image to Base64 and store it in a variable
BASE64_STRING=$(base64 -w 0 "$IMAGE_FILE")

# Create a temporary JSON file
# This is to avoid curl limitation on the string length
TMP_JSON=$(mktemp)
cat <<EOF > "$TMP_JSON"
{
  "images_base64": ["$BASE64_STRING"]
}
EOF

# cat "$TMP_JSON" 
# Send the request using the JSON file
curl -X POST "http://127.0.0.1:8000/analyze-json" \
     -H "Content-Type: application/json" \
     -H "x-access-token: $ACCESS_TOKEN" \
     --data @"$TMP_JSON"

# Clean up the temporary JSON file
# rm "$TMP_JSON"

# Print success message
echo ""
echo "✅ Image '$IMAGE_FILE' successfully converted and sent!"
