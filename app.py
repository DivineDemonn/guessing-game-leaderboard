import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secure MongoDB Connection
# Heroku will provide this environment variable
MONGO_URI = os.getenv("MONGO_URI") 
client = MongoClient(MONGO_URI)

# IMPORTANT: Replace 'guessing_game' with your actual MongoDB database name if different
db = client.get_database("guessing_game") 

@app.route('/')
def index():
    """Serves the main Mini App UI."""
    # Reads the ?section= parameter from your Bot's URL button (defaults to 'earners')
    initial_section = request.args.get('section', 'earners')
    return render_template('index.html', initial_section=initial_section)

@app.route('/api/stats/<section>')
def get_stats(section):
    """API endpoint that feeds live database info to the frontend."""
    try:
        users = []
        if section == 'earners':
            cursor = db.users.find({"coins": {"$gt": 0}}, {"_id": 0, "username": 1, "first_name": 1, "coins": 1}).sort("coins", -1).limit(10)
            users = [{"name": u.get("first_name", "Unknown"), "score": u.get("coins", 0), "label": "Pts"} for u in cursor]
            
        elif section == 'duelists':
            cursor = db.users.find({"duel_wins": {"$gt": 0}}, {"_id": 0, "username": 1, "first_name": 1, "duel_wins": 1}).sort("duel_wins", -1).limit(10)
            users = [{"name": u.get("first_name", "Unknown"), "score": u.get("duel_wins", 0), "label": "Wins"} for u in cursor]
            
        elif section == 'champions':
            cursor = db.users.find({"group_wins": {"$gt": 0}}, {"_id": 0, "username": 1, "first_name": 1, "group_wins": 1}).sort("group_wins", -1).limit(10)
            users = [{"name": u.get("first_name", "Unknown"), "score": u.get("group_wins", 0), "label": "Wins"} for u in cursor]
            
        return jsonify(users)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
