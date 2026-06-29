import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client


load_dotenv()

ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision:11b")
cscms_root = Path(os.getenv("CSCMS_ROOT", "")).expanduser()

photos_dir = cscms_root / "Photos to Review"

image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

print(f"Ollama host: {ollama_host}")
print(f"Ollama model: {ollama_model}")
print(f"Photos folder: {photos_dir}")

client = Client(host=ollama_host)

print("\nTesting server connection...")
models = client.list()
print("Server responded.")

print("\nTesting text generation...")
text_response = client.chat(
    model=ollama_model,
    messages=[
        {
            "role": "user",
            "content": "Respond with only the word OK.",
        }
    ],
    options={"temperature": 0},
)

print("Text response:")
print(text_response["message"]["content"])

if not photos_dir.exists():
    raise FileNotFoundError(f"Photos folder not found: {photos_dir}")

images = [
    path for path in photos_dir.iterdir()
    if path.is_file() and path.suffix.lower() in image_extensions
]

if not images:
    raise FileNotFoundError(f"No test images found in: {photos_dir}")

test_image = images[0]
print(f"\nTesting vision with image: {test_image.name}")

vision_response = client.chat(
    model=ollama_model,
    messages=[
        {
            "role": "user",
            "content": "Briefly describe this image and say whether it looks useful for a CSCMS social media post.",
            "images": [str(test_image.resolve())],
        }
    ],
    options={"temperature": 0},
)

print("\nVision response:")
print(vision_response["message"]["content"])

print("\nOllama connection and vision test complete.")