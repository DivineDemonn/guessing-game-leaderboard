import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# Connects to your Guessin Game database
try:
    db = client.get_default_database()
except Exception:
    db = client.get_database("Guessin_game_db")


@app.route('/')
def index():
    """Serves the main leaderboard UI."""
    initial_section = request.args.get('section', 'group')
    return render_template('index.html', initial_section=initial_section)


@app.route('/api/stats/<section>')
def get_stats(section):
    """Feeds mode-specific rankings to the frontend."""
    try:
        users = []

        if section == 'group':
            # Ranks players by Group Lobby Faction War coins
            cursor = db.users.find(
                {"$or": [{"coins_group": {"$gt": 0}}, {"group_wins": {"$gt": 0}}]},
                {"_id": 0, "username": 1, "first_name": 1, "coins_group": 1, "coins": 1}
            ).sort("coins_group", -1).limit(10)

            for u in cursor:
                score = u.get("coins_group") if u.get("coins_group") is not None else u.get("coins", 0)
                users.append({
                    "name": u.get("first_name") or u.get("username") or "Warrior",
                    "score": score,
                    "label": "Group Coins"
                })

        elif section == 'solo':
            # Ranks players by 4-Player Solo Survival coins
            cursor = db.users.find(
                {"$or": [{"coins_solo": {"$gt": 0}}, {"solo_games_played": {"$gt": 0}}]},
                {"_id": 0, "username": 1, "first_name": 1, "coins_solo": 1}
            ).sort("coins_solo", -1).limit(10)

            for u in cursor:
                users.append({
                    "name": u.get("first_name") or u.get("username") or "Warrior",
                    "score": u.get("coins_solo", 0),
                    "label": "Solo Coins"
                })

        elif section == 'speedrun':
            # Ranks players by Timed Speedrun coins (/start_sp)
            cursor = db.users.find(
                {"coins_speedrun": {"$gt": 0}},
                {"_id": 0, "username": 1, "first_name": 1, "coins_speedrun": 1}
            ).sort("coins_speedrun", -1).limit(10)

            for u in cursor:
                users.append({
                    "name": u.get("first_name") or u.get("username") or "Warrior",
                    "score": u.get("coins_speedrun", 0),
                    "label": "Speed Coins"
                })

        return jsonify(users)

    except Exception as e:
        print(f"Database query error: {e}")
        return jsonify([]), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
