#!/usr/bin/env python
# coding: utf-8

# In[15]:


from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from Scrapper import extract_article_text
from preprocess import clean_text
from logger_db import init_db, log_query

MODEL_DIR = "model_artifacts"
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

app = Flask(__name__)
CORS(app)

# load model & vectorizer
if not os.path.exists(VECT_PATH) or not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model artifacts not found. Run train.py first.")

vectorizer = joblib.load(VECT_PATH)
model = joblib.load(MODEL_PATH)

# init DB for logging
init_db()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error":"No URL provided"}), 400

    # Step 1: extract text
    text = extract_article_text(url)
    if not text or len(text.strip()) < 100:
        return jsonify({"error":"Could not extract sufficient article text from URL"}), 400

    # Step 2: preprocess
    cleaned = clean_text(text)

    # Step 3: vectorize
    X = vectorizer.transform([cleaned])

    # Step 4: predict probabilities
    proba = model.predict_proba(X)[0]  # [p_false, p_true] if trained that way
    # Determine label mapping: model.classes_
    mapping = {int(c): i for i,c in enumerate(model.classes_)}  # class value -> index
    # find predicted label index
    pred_index = proba.argmax()
    pred_class = model.classes_[pred_index]
    label = "Real" if int(pred_class) == 1 else "Fake"
    confidence = float(proba[pred_index])

    # Optional: log into sqlite
    try:
        log_query(url, label, confidence, len(text))
    except Exception as e:
        app.logger.warning("Logging failed: %s", e)

    return jsonify({"label": label, "confidence": round(confidence, 4)})

if __name__ == "__main__":
    app.run(port=5000, debug=True)


# In[16]:


from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from Scrapper import extract_article_text
from preprocess import clean_text
from logger_db import init_db, log_query

MODEL_DIR = "model_artifacts"
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

app = Flask(__name__)
CORS(app)

# load model & vectorizer
if not os.path.exists(VECT_PATH) or not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model artifacts not found. Run train.py first.")

vectorizer = joblib.load(VECT_PATH)
model = joblib.load(MODEL_PATH)

# init DB for logging
init_db()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error":"No URL provided"}), 400

    # Step 1: extract text
    text = extract_article_text(url)
    if not text or len(text.strip()) < 100:
        return jsonify({"error":"Could not extract sufficient article text from URL"}), 400

    # Step 2: preprocess
    cleaned = clean_text(text)

    # Step 3: vectorize
    X = vectorizer.transform([cleaned])

    # Step 4: predict probabilities
    proba = model.predict_proba(X)[0]  # [p_false, p_true] if trained that way
    pred_index = proba.argmax()
    pred_class = model.classes_[pred_index]
    label = "Real" if int(pred_class) == 1 else "Fake"
    confidence = float(proba[pred_index])

    # Optional: log into sqlite
    try:
        log_query(url, label, confidence, len(text))
    except Exception as e:
        app.logger.warning("Logging failed: %s", e)

    return jsonify({"label": label, "confidence": round(confidence, 4)})

if __name__ == "__main__":
    app.run(port=5000, debug=True)


# In[19]:


from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os

# Local imports
from Scrapper import extract_article_text
from preprocess import clean_text
from logger_db import init_db, log_query

# Model paths
MODEL_DIR = "model_artifacts"
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load model and vectorizer
if not os.path.exists(VECT_PATH) or not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model artifacts not found. Run train.py first.")

vectorizer = joblib.load(VECT_PATH)
model = joblib.load(MODEL_PATH)

# Init DB (optional logging)
init_db()

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict whether news is Real or Fake.
    Accepts JSON with either:
    - {"url": "https://example.com/article"}
    - {"text": "Some news article content..."}
    """
    data = request.get_json()

    url = data.get("url", "").strip()
    raw_text = data.get("text", "").strip()

    # Step 1: extract text from URL or use raw text
    if url:
        text = extract_article_text(url)
        if not text or len(text.strip()) < 100:
            return jsonify({"error": "Could not extract sufficient text from URL"}), 400
    elif raw_text:
        text = raw_text
    else:
        return jsonify({"error": "Provide either 'url' or 'text'"}), 400

    # Step 2: preprocess
    cleaned = clean_text(text)

    # Step 3: vectorize
    X = vectorizer.transform([cleaned])

    # Step 4: predict
    proba = model.predict_proba(X)[0]  # probabilities
    pred_index = proba.argmax()
    pred_class = model.classes_[pred_index]  # 0 or 1
    label = "Real" if pred_class == 1 else "Fake"
    confidence = float(proba[pred_index])

    # Step 5: optional logging
    try:
        log_query(url if url else "RAW_TEXT", label, confidence, len(text))
    except Exception as e:
        app.logger.warning("Logging failed: %s", e)

    return jsonify({
        "label": label,
        "confidence": round(confidence, 4)
    }), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)


# In[17]:


import os

MODEL_DIR = "model_artifacts"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


# In[18]:


import joblib

joblib.dump(vectorizer, f"{MODEL_DIR}/vectorizer.joblib")
joblib.dump(model, f"{MODEL_DIR}/model.joblib")




# import streamlit as st
# import joblib
# import os
# from Scrapper import extract_article_text
# from preprocess import clean_text

# MODEL_DIR = "model_artifacts"
# VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
# MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

# # load model & vectorizer
# vectorizer = joblib.load(VECT_PATH)
# model = joblib.load(MODEL_PATH)

# st.set_page_config(page_title="Fake News Detector", layout="centered")

# st.title("📰 Fake News Detector")
# choice = st.radio("Choose input type:", ["Enter Text", "Enter URL"])

# if choice == "Enter URL":
#     url = st.text_input("Paste the news article URL:")
#     if st.button("Check URL"):
#         if url.strip() == "":
#             st.warning("Please enter a URL.")
#         else:
#             text = extract_article_text(url)
#             if not text or len(text.strip()) < 100:
#                 st.error("Could not extract enough text from URL")
#             else:
#                 cleaned = clean_text(text)
#                 X = vectorizer.transform([cleaned])
#                 proba = model.predict_proba(X)[0]
#                 pred_index = proba.argmax()
#                 label = "Real" if model.classes_[pred_index] == 1 else "Fake"
#                 st.success(f"Prediction: **{label}** (Confidence: {proba[pred_index]*100:.2f}%)")

# else:
#     text = st.text_area("Paste or type news content:")
#     if st.button("Check Text"):
#         if text.strip() == "":
#             st.warning("Please enter some text.")
#         else:
#             cleaned = clean_text(text)
#             X = vectorizer.transform([cleaned])
#             proba = model.predict_proba(X)[0]
#             pred_index = proba.argmax()
#             label = "Real" if model.classes_[pred_index] == 1 else "Fake"
#             st.success(f"Prediction: **{label}** (Confidence: {proba[pred_index]*100:.2f}%)")

