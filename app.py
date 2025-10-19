import mysql.connector
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import spacy
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# --- SpaCy NLP Initialization ---
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ SpaCy model loaded successfully.")
except OSError:
    print("❌ SpaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

# --- Database Config ---
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ia_chatbot"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# --- MLChatbotEngine Class ---
class MLChatbotEngine:
    def __init__(self, excel_file='chatbot_dataset.xlsx'):
        self.excel_file = excel_file
        self.qa_data = None
        self.vectorizer = None
        self.question_vectors = None
        self.load_dataset()

    def load_dataset(self):
        try:
            if os.path.exists(self.excel_file):
                self.qa_data = pd.read_excel(self.excel_file)
                self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', ngram_range=(1, 2), max_features=500)
                self.question_vectors = self.vectorizer.fit_transform(self.qa_data['question'].fillna(''))
                with open('ml_model.pkl', 'wb') as f:
                    pickle.dump({'vectorizer': self.vectorizer, 'question_vectors': self.question_vectors, 'qa_data': self.qa_data}, f)
            else:
                print(f"⚠️ Dataset not found: {self.excel_file}")
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")

    def find_best_answer(self, user_question, threshold=0.25):
        if self.vectorizer is None:
            return None, 0.0
        try:
            user_vector = self.vectorizer.transform([user_question])
            similarities = cosine_similarity(user_vector, self.question_vectors)[0]
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            if best_score >= threshold:
                return {
                    'answer': self.qa_data.iloc[best_idx]['answer'],
                    'category': self.qa_data.iloc[best_idx]['category'],
                    'confidence': float(best_score),
                }, best_score
            return None, best_score
        except Exception as e:
            print(f"Error in find_best_answer: {e}")
            return None, 0.0

ml_engine = MLChatbotEngine()

# --- Intent Detection ---
def determine_intent(message):
    if not nlp:
        return "fallback"
    doc = nlp(message.lower())
    if any(token.text in ["hi", "hello", "hey"] for token in doc):
        return "greeting"
    for token in doc:
        lemma = token.lemma_
        if lemma in ["admission", "enroll", "apply"]:
            return "admission_info"
        if lemma in ["grade", "gwa", "score"]:
            return "grading_info"
        if lemma in ["subject", "class"]:
            return "subject_list"
        if lemma in ["professor", "teacher"]:
            return "professor_list"
    return "ml_search"

# --- Routes ---
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "Please enter a message."})
    intent = determine_intent(message)
    if intent == "greeting":
        reply = "👋 Hello! I'm your SLSU AI Academic Assistant."
    elif intent == "admission_info":
        reply = "📋 Admission Requirements: Examination Permit, 2x2 pictures, Good Moral Certificate, Academic Records."
    else:
        ml_result, score = ml_engine.find_best_answer(message)
        reply = ml_result['answer'] if ml_result else "🤔 Sorry, I don’t have information about that."
    return jsonify({"reply": reply})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# --- Main Entry Point ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
