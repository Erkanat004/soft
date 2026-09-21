import urllib.request
import urllib.parse

prompts = [
    "cat",
    "a beautiful sunset over mountains",
    "futuristic city night"
]

for p in prompts:
    enc = urllib.parse.quote(p)
    # Test standard Pollinations URL format
    url = f"https://image.pollinations.ai/prompt/{enc}?width=1280&height=720&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            print(f"SUCCESS for '{p}': status {resp.status}, size {len(data)} bytes")
    except Exception as e:
        print(f"FAILED for '{p}': {e}")
