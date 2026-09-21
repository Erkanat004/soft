import urllib.request
import urllib.parse
import time

def generate_free_image(prompt: str, width: int = 1280, height: int = 720) -> bytes:
    encoded = urllib.parse.quote(prompt.strip())
    
    # Try 1: Pollinations with flux model
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&model=flux",
        f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true",
        f"https://picsum.photos/{width}/{height}?random=1" # High quality real stock photo fallback
    ]

    for idx, url in enumerate(urls):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 2000:
                        print(f"Success on attempt {idx+1} ({url[:40]}...): size {len(data)}")
                        return data
        except Exception as e:
            print(f"Attempt {idx+1} failed ({url[:40]}...): {e}")
            time.sleep(1)

    raise RuntimeError("All free image providers failed")

if __name__ == "__main__":
    for p in ["futuristic city night", "cyberpunk street", "sleeping kitten"]:
        img_bytes = generate_free_image(p)
        print(f"Done for '{p}': {len(img_bytes)} bytes")
