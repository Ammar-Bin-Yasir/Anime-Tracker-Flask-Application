import requests
import re

try:
    response = requests.get('http://127.0.0.1:5000/')
    content = response.text
    
    # regex to find hero title
    match = re.search(r'<h1 class="hero-title">(.*?)</h1>', content)
    if match:
        print(f"FOUND TITLE: {match.group(1)}")
    else:
        print("NO TITLE FOUND")
        # Print snippet for debugging
        print(content[:500])
except Exception as e:
    print(f"ERROR: {e}")
