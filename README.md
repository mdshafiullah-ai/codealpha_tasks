# 🌐 Language Translation Tool

A polished, web-based language translation application built with **Python (Flask)** and the **Google Cloud Translation API**. Created as part of the **CodeAlpha Internship** program.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Text Translation** | Translate text between 100+ languages using Google Cloud Translation API v2 |
| **Auto-detect Language** | Automatically detects the source language when set to "Auto-detect" |
| **Speech-to-Text Input** | 🎤 Click the microphone button to dictate text using the browser's Web Speech API |
| **Swap Languages** | One-click button to swap source and target languages along with text |
| **Copy to Clipboard** | Instantly copy the translated result |
| **Common Languages** | 20 most-used languages promoted to the top of the dropdown |
| **Responsive Design** | Clean, modern UI that works on desktop, tablet, and mobile |
| **Error Handling** | Graceful handling of API errors, network issues, and missing configuration |
| **Keyboard Shortcut** | Press `Ctrl+Enter` (or `Cmd+Enter` on Mac) to translate |

---

## 📋 Prerequisites

- **Python 3.9+** installed
- A **Google Cloud** account with the **Cloud Translation API** enabled
- A **Google Cloud API key**

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/CodeAlpha-Language-Translation.git
cd CodeAlpha-Language-Translation
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
# Copy the example env file
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Open `.env` and replace `your_api_key_here` with your actual Google Cloud Translation API key:

```
GOOGLE_TRANSLATE_API_KEY=AIzaSy...your-key-here
```

### 5. Run the application

```bash
python app.py
```

Open your browser and navigate to **http://localhost:5000**

---

## 🔑 Getting a Google Cloud Translation API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Search for **"Cloud Translation API"** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API Key**
7. Copy the key and paste it into your `.env` file

> **Note**: The Translation API has a free tier (500,000 characters/month). Beyond that, standard pricing applies. See [Google's pricing page](https://cloud.google.com/translate/pricing) for details.

---

## 📁 Project Structure

```
CodeAlpha-Language-Translation/
├── app.py                 # Flask backend – API routes and server
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── templates/
│   └── index.html         # Jinja2 HTML template (main UI)
└── static/
    ├── style.css           # Styles (responsive, modern design)
    └── script.js           # Client-side logic (API calls, speech, etc.)
```

---

## 🎤 Speech-to-Text

The app includes **optional speech-to-text input** powered by the browser's [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API):

- **Supported browsers**: Chrome, Edge, Safari (desktop and mobile)
- **How to use**: Click the 🎤 microphone icon next to the source text area
- The button will pulse red while listening; click again to stop
- The recognition language is automatically set to match the selected source language
- If your browser doesn't support the Speech API, the microphone button is simply hidden

> **Note**: Speech recognition requires an internet connection in most browsers (the audio is processed by cloud services).

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `GOOGLE_TRANSLATE_API_KEY` | *(required)* | Your Google Cloud API key |
| `PORT` | `5000` | Port the Flask server listens on |
| `FLASK_DEBUG` | `1` | Set to `0` for production |

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, Requests
- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks needed)
- **API**: Google Cloud Translation API v2 (REST)
- **Speech**: Web Speech API (browser-native)
- **Fonts/Icons**: Google Fonts (Inter), Material Icons

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Acknowledgments

- [Google Cloud Translation API](https://cloud.google.com/translate)
- [CodeAlpha](https://www.codealpha.tech/) Internship Program
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
