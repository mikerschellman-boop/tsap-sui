import json
from datetime import date

data = {
    "updated": str(date.today()),
    "sections": {
        "complexity": [
            {
                "source": "Santa Fe Institute",
                "title": "Automated Tsap Sui test",
                "url": "https://www.santafe.edu/",
                "date": str(date.today()),
                "archive": False
            }
        ]
    }
}

with open("tsapsui.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("tsapsui.json updated")
