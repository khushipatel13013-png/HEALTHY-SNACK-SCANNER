from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)

load_dotenv()
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODELS = [
    {"name": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
    {"name": "gemini-2.5-flash-lite", "label": "Gemini 2.5 Flash-Lite"},
]
PROMPT = """
Analyze this image. First, determine if this image contains food or not.
If the image does NOT contain any food item, return ONLY this exact JSON:
{"error": "not_food"}
If the image DOES contain food, return ONLY a valid JSON array with nutritional info.
Each item in the array should be a JSON object with these exact keys:
- "Food Item": name of the food
- "Calories (kcal)": estimated calories
- "Protein (g)": estimated protein in grams
- "Carbs (g)": estimated carbohydrates in grams
- "Fat (g)": estimated fat in grams
- "Fiber (g)": estimated fiber in grams
- "Sugar (g)": estimated sugar in grams
- "Health Rating": one of "Healthy", "Moderate", or "Unhealthy"
If there are multiple food items visible, include each as a separate object in the array.
Do NOT include any markdown formatting, code fences, or extra text — just the raw JSON.
"""
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])


def analyze():
    try:
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No image uploaded"}), 400
        # Read image bytes

        image_bytes = file.read()
        image_data = {
            "mime_type": file.content_type,
            "data": image_bytes,
        }
        last_error = None
        for m in MODELS:
            try:
                model = genai.GenerativeModel(m["name"])
                response = model.generate_content([PROMPT, image_data])
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]

                text = text.strip()
                data = json.loads(text)
                if isinstance(data, dict) and data.get("error") == "not_food":
                    return jsonify({"error": "Please select a valid food image."}), 400
                return jsonify({"results": data, "model_used": m["label"]})
            
            except Exception as e:
                last_error = str(e)
                print(f"[!] {m['label']} failed: {last_error}, trying next...")
                continue

        return jsonify({"error": f"All models failed. Last error: {last_error}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)