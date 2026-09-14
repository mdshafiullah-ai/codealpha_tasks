"""
Language Translation Tool – Flask backend.

Provides:
  POST /translate       – translate text via Google Cloud Translation API v2
  GET  /languages       – list supported languages
  GET  /                – serve the web UI
"""

import html
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()  # load .env if present

app = Flask(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
LANGUAGES_URL = "https://translation.googleapis.com/language/translate/v2/languages"
DETECT_URL = "https://translation.googleapis.com/language/translate/v2/detect"

# Common languages shown at the top of the dropdown (ISO 639-1 codes).
# The full list is still fetched from the API for completeness.
COMMON_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "bn": "Bengali",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "uk": "Ukrainian",
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def _check_api_key():
    """Return an error response tuple if the API key is missing."""
    if not GOOGLE_API_KEY:
        return (
            jsonify(
                {
                    "error": "Google Translate API key is not configured. "
                    "Set GOOGLE_TRANSLATE_API_KEY in your .env file."
                }
            ),
            500,
        )
    return None


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the main translation page."""
    return render_template("index.html")


@app.route("/languages", methods=["GET"])
def get_languages():
    """Return the list of supported languages from the Google API,
    with common languages promoted to the top."""
    err = _check_api_key()
    if err:
        return err

    try:
        resp = requests.get(
            LANGUAGES_URL,
            params={"key": GOOGLE_API_KEY, "target": "en"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Google API timed out. Please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Google API. Check your internet connection."}), 502
    except requests.exceptions.HTTPError as exc:
        msg = _extract_google_error(exc.response)
        return jsonify({"error": f"Google API error: {msg}"}), exc.response.status_code
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Unexpected error fetching languages: {exc}"}), 500

    all_langs = {
        lang["language"]: lang.get("name", lang["language"])
        for lang in data.get("data", {}).get("languages", [])
    }

    # Build ordered result: common first, then the rest alphabetically.
    common = []
    for code, fallback_name in COMMON_LANGUAGES.items():
        name = all_langs.pop(code, fallback_name)
        common.append({"code": code, "name": name})

    others = sorted(
        [{"code": c, "name": n} for c, n in all_langs.items()],
        key=lambda x: x["name"].lower(),
    )

    return jsonify({"common": common, "others": others})


@app.route("/translate", methods=["POST"])
def translate():
    """Translate text using Google Cloud Translation API v2."""
    err = _check_api_key()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    source = (body.get("source") or "").strip()
    target = (body.get("target") or "").strip()

    if not text:
        return jsonify({"error": "No text provided for translation."}), 400
    if not target:
        return jsonify({"error": "Target language is required."}), 400

    payload = {"q": text, "target": target, "format": "text"}
    if source and source != "auto":
        payload["source"] = source

    try:
        resp = requests.post(
            TRANSLATE_URL,
            params={"key": GOOGLE_API_KEY},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return jsonify({"error": "Translation request timed out. Please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Google API. Check your internet connection."}), 502
    except requests.exceptions.HTTPError as exc:
        msg = _extract_google_error(exc.response)
        return jsonify({"error": f"Google API error: {msg}"}), exc.response.status_code
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Unexpected error: {exc}"}), 500

    translations = data.get("data", {}).get("translations", [])
    if not translations:
        return jsonify({"error": "No translation returned from the API."}), 500

    result = translations[0]
    translated_text = html.unescape(result.get("translatedText", ""))
    detected_source = result.get("detectedSourceLanguage", source or "auto")

    return jsonify(
        {
            "translatedText": translated_text,
            "detectedSourceLanguage": detected_source,
        }
    )


def _extract_google_error(response):
    """Pull a human-readable message from a Google API error response."""
    try:
        err_data = response.json()
        return err_data.get("error", {}).get("message", response.text)
    except Exception:  # noqa: BLE001
        return response.text


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
