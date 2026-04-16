import io
from PIL import Image
import pytesseract


def read_text_from_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image)
    return text.strip()


def explain_text(text: str) -> str:
    if not text:
        return "I couldn't find any text in that image. Please try again with a clearer picture."
    return f"Here is what I found in the image: {text}"
