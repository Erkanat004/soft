import os
import urllib.parse

path_with_cyrillic = r"C:\Users\shugy\OneDrive\Изображения\Desktop\project 3\cache\audio\test.mp3"

# Standard normalization for FCPXML file:// URL
normalized = os.path.abspath(path_with_cyrillic).replace("\\", "/")
encoded_uri = f"file:///{urllib.parse.quote(normalized, safe='/:')}"

print("Original Path:", path_with_cyrillic)
print("Normalized Path:", normalized)
print("Valid FCPXML URI:", encoded_uri)
