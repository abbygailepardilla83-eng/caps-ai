from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
import spacy
import re
@app.route('/chat', methods=['POST'])
def chat():
    ...

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("SpaCy model not found. Installing...")
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Database setup
def init_db():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  role TEXT DEFAULT 'student',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create chat sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  session_id TEXT UNIQUE NOT NULL,
                  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Create messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT NOT NULL,
                  sender TEXT NOT NULL,
                  message TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id))''')
    
    conn.commit()
    conn.close()

init_db()

# Knowledge base for SLSU
KNOWLEDGE_BASE = {
    'professor': {
        'keywords': ['professor', 'teacher', 'instructor', 'faculty', 'prof'],
        'response': '''📚 **SLSU Professors:**

**Computer Science Department:**
- Dr. Maria Santos - Database Systems, AI
- Prof. Juan Cruz - Web Development, Programming
- Dr. Ana Reyes - Data Science, Machine Learning

**Engineering Department:**
- Engr. Pedro Garcia - Circuit Design
- Dr. Rosa Mendoza - Thermodynamics

**Business Department:**
- Prof. Carlos Ramos - Marketing, Management
- Dr. Linda Torres - Accounting, Finance

Would you like specific information about any professor?'''
    },
    'subject': {
        'keywords': ['subject', 'course', 'class', 'curriculum', 'subjects'],
        'response': '''📖 **Available Subjects:**

**1st Year:**
- Introduction to Computing
- Mathematics for IT
- English Communication
- Filipino
- Physical Education

**2nd Year:**
- Data Structures & Algorithms
- Database Management
- Web Development
- Object-Oriented Programming
- Discrete Mathematics

**3rd Year:**
- Software Engineering
- Computer Networks
- Mobile Development
- Information Security

**4th Year:**
- Capstone Project
- Thesis Writing
- Elective Courses

Which year level interests you?'''
    },
    'admission': {
        'keywords': ['admission', 'enroll', 'requirements', 'entrance', 'apply'],
        'response': '''📝 **Admission Requirements:**

**For Freshmen:**
1. Form 138 (High School Report Card)
2. PSA Birth Certificate
3. Certificate of Good Moral Character
4. 2x2 ID Photos (4 copies)
5. Medical Certificate

**For Transferees:**
1. Transcript of Records
2. Certificate of Good Moral Character
3. Honorable Dismissal
4. PSA Birth Certificate
5. 2x2 ID Photos (4 copies)

**Entrance Exam:** Required for all applicants
**Application Period:** May - July

Need help with the application process?'''
    },
    'grading': {
        'keywords': ['grade', 'grading', 'gwa', 'passing', 'marks'],
        'response': '''📊 **SLSU Grading System:**

**Grading Scale:**
- 1.0 - 1.5: Excellent
- 1.6 - 2.0: Very Good
- 2.1 - 2.5: Good
- 2.6 - 3.0: Satisfactory
- 3.1 - 5.0: Failed

**Passing Grade:** 3.0
**Dean's List:** GWA of 1.75 or higher
**President's List:** GWA of 1.5 or higher

**Grade Computation:**
- Prelim: 20%
- Midterm: 20%
- Pre-Final: 20%
- Final: 40%

Need help calculating your GWA?'''
    },
    'calendar': {
        'keywords': ['calendar', 'schedule', 'semester', 'academic calendar', 'school year'],
        'response': '''📅 **SLSU Academic Calendar 2024-2025:**

**First Semester:**
- Enrollment: August 1-15, 2024
- Classes Start: August 19, 2024
- Prelim Exam: September 23-27
- Midterm Exam: October 28 - November 1
- Pre-Final Exam: December 2-6
- Final Exam: January 13-17, 2025
- Semester End: January 20, 2025

**Second Semester:**
- Enrollment: January 27 - February 7, 2025
- Classes Start: February 10, 2025

**Holidays:**
- Christmas Break: December 16 - January 5
- Holy Week: April 2025

Need specific dates for events?'''
    },
    'announcement': {
        'keywords': ['announcement', 'news', 'update', 'event'],
        'response': '''📢 **Latest Announcements:**

🎓 **Upcoming Events:**
1. **Job Fair 2024** - November 15-16
   Location: University Gymnasium

2. **Research Congress** - December 5
   Submit abstracts by November 20

3. **Intramurals** - January 2025
   Registration now open

4. **Scholarship Applications** - Deadline: November 30
   Check Student Affairs Office

5. **Library Extended Hours** - Now open until 9 PM
   Effective immediately

Stay updated through our official Facebook page!'''
    }
}

def process_message_nlp(message):
    """Process message using SpaCy NLP"""
    doc = nlp(message.lower())
    
    # Extract entities and keywords
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    
    return tokens, entities

def get_response(message):
    """Generate response based on message content"""
    message_lower = message.lower()
    tokens, entities = process_message_nlp(message)
    
    
    # Check knowledge base
    for category, data in KNOWLEDGE_BASE.items():
        for keyword in data['keywords']:
            if keyword in message_lower or keyword in tokens:
                return data['response']
    
    # Greetings
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greet in message_lower for greet in greetings):
        return "👋 Hello! Welcome to SLSU Intelligent Assistant! How can I help you today? You can ask about professors, subjects, admission, grading, calendar, or announcements."
    
    # Thank you
    thanks = ['thank', 'thanks', 'salamat']
    if any(thank in message_lower for thank in thanks):
        return "😊 You're welcome! Feel free to ask if you need anything else. Have a great day!"
    
    # Help
    if 'help' in message_lower:
        return """🤖 **I can help you with:**

1. 👩‍🏫 **Professors** - Faculty information
2. 📚 **Subjects** - Course listings
3. 📝 **Admission** - Requirements and process
4. 📊 **Grading** - Grading system and computation
5. 📅 **Calendar** - Academic schedule
6. 📢 **Announcements** - Latest news and events

Just ask me anything about these topics!"""
    
    # Default response
    return """I'm not sure about that specific question. 🤔

I can help you with:
- **Professors** and faculty information
- **Subjects** and curriculum
- **Admission** requirements
- **Grading** system
- **School calendar**
- **Announcements**

Could you please rephrase your question or ask about one of these topics?"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        user_email = data.get('email', 'guest@slsu.edu.ph')
        session_id = data.get('session_id', str(datetime.now().timestamp()))
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Save message to database
        save_message(session_id, user_email, 'user', message)
        
        # Generate response
        response = get_response(message)
        
        # Save bot response to database
        save_message(session_id, user_email, 'bot', response)
        
        return jsonify({'reply': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_message(session_id, user_email, sender, message):
    """Save message to database"""
    try:
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        
        # Check if user exists, if not create
        c.execute('SELECT id FROM users WHERE email = ?', (user_email,))
        user = c.fetchone()
        
        if not user:
            c.execute('INSERT INTO users (name, email) VALUES (?, ?)', 
                     ('Student User', user_email))
            user_id = c.lastrowid
        else:
            user_id = user[0]
        
        # Check if session exists, if not create
        c.execute('SELECT id FROM chat_sessions WHERE session_id = ?', (session_id,))
        session = c.fetchone()
        
        if not session:
            c.execute('INSERT INTO chat_sessions (user_id, session_id) VALUES (?, ?)',
                     (user_id, session_id))
        
        # Save message
        c.execute('INSERT INTO messages (session_id, sender, message) VALUES (?, ?, ?)',
                 (session_id, sender, message))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving message: {e}")

@app.route('/admin/history', methods=['GET'])
def get_history():
    """Get all chat history for admin"""
    try:
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                cs.session_id,
                u.name,
                u.email,
                cs.start_time,
                m.sender,
                m.message,
                m.timestamp
            FROM chat_sessions cs
            JOIN users u ON cs.user_id = u.id
            JOIN messages m ON cs.session_id = m.session_id
            ORDER BY cs.start_time DESC, m.timestamp ASC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        # Organize by session
        sessions = {}
        for row in rows:
            session_id = row[0]
            if session_id not in sessions:
                sessions[session_id] = {
                    'sessionId': session_id,
                    'userName': row[1],
                    'userEmail': row[2],
                    'startTime': row[3],
                    'messages': []
                }
            
            sessions[session_id]['messages'].append({
                'sender': row[4],
                'message': row[5],
                'timestamp': row[6]
            })
        
        return jsonify(list(sessions.values()))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def get_stats():
    """Get statistics for admin dashboard"""
    try:
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        
        # Total chats
        c.execute('SELECT COUNT(*) FROM chat_sessions')
        total_chats = c.fetchone()[0]
        
        # Total users
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        
        # Total messages
        c.execute('SELECT COUNT(*) FROM messages')
        total_messages = c.fetchone()[0]
        
        # Today's chats
        c.execute('''
            SELECT COUNT(*) FROM chat_sessions 
            WHERE DATE(start_time) = DATE('now')
        ''')
        today_chats = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'totalChats': total_chats,
            'totalUsers': total_users,
            'totalMessages': total_messages,
            'todayChats': today_chats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    print("📊 Database initialized")
    print("🤖 SpaCy NLP model loaded")
    print("🌐 Server running on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)