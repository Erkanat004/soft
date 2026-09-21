import sys
import os

sys.path.append(os.path.dirname(__file__))

from app.services.image_gen import ImageGenerationService

if __name__ == "__main__":
    print("Testing free online AI image generation (Pollinations.ai)...")
    res = ImageGenerationService.generate_image("Cosmic astronaut floating in space with colorful nebula")
    print("Result:", res)
    if os.path.exists(res["image_path"]):
        size = os.path.getsize(res["image_path"])
        print(f"Image successfully generated and saved! Size: {size} bytes")
    else:
        print("Error: image file not found")
