import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secure MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

try:
    db = client.get_default_database()
except Exception:
    db = client.get_database("Guessin_game_db")


@app.route('/')
def index():
    """Serves the main Mini App UI."""
    initial_section = request.args.get('section', 'speedrun')
    return render_template('index.html', initial_section=initial_section)


def safe_int(value) -> int:
    """Helper to convert any MongoDB value (str/float/int/None) into a clean integer."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def format_user_name(user_doc) -> str:
    """Extracts a clean, non-empty display name from user profile documents."""
    name = user_doc.get("first_name") or user_doc.get("username")
    if name:
        return str(name).strip()
    return f"Warrior #{str(user_doc.get('user_id', ''))[-4:] or 'Arena'}"


@app.route('/api/stats/<section>')
def get_stats(section):
    """
    Feeds mode-specific rankings to the frontend.
    Handles instant live score updates, type conversions, and zero-record fallbacks.
    """
    try:
        users = []

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. SPEEDRUN RUSH (Timed Mode /start_sp)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if section == 'speedrun':
            cursor = db.users.find({
                "$or": [
                    {"coins_speedrun": {"$gt": 0}},
                    {"coins": {"$gt": 0}}
                ]
            })

            user_pool = list(cursor)

            def extract_speedrun_coins(u):
                sp_coins = safe_int(u.get("coins_speedrun"))
                if sp_coins > 0:
                    return sp_coins
                # Fallback to total coins for older sessions
                return safe_int(u.get("coins"))

            user_pool.sort(key=extract_speedrun_coins, reverse=True)

            for u in user_pool[:10]:
                score = extract_speedrun_coins(u)
                if score > 0:
                    users.append({
                        "name": format_user_name(u),
                        "score": score,
                        "label": "Speed Coins"
                    })

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. GROUP LOBBIES (2v2 Faction Wars /start_battle)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif section == 'group':
            cursor = db.users.find({
                "$or": [
                    {"coins_group": {"$gt": 0}},
                    {"group_wins": {"$gt": 0}},
                    {"coins": {"$gt": 0}}
                ]
            })

            user_pool = list(cursor)

            def extract_group_coins(u):
                grp_coins = safe_int(u.get("coins_group"))
                if grp_coins > 0:
                    return grp_coins
                # Check group wins or total coins fallback
                if safe_int(u.get("group_wins")) > 0:
                    return safe_int(u.get("coins"))
                return 0

            user_pool.sort(key=extract_group_coins, reverse=True)

            for u in user_pool[:10]:
                score = extract_group_coins(u)
                if score > 0:
                    users.append({
                        "name": format_user_name(u),
                        "score": score,
                        "label": "Group Coins"
                    })

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. SOLO ARENA (4-Player Survival /arena)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif section == 'solo':
            cursor = db.users.find({
                "$or": [
                    {"coins_solo": {"$gt": 0}},
                    {"solo_games_played": {"$gt": 0}}
                ]
            })

            user_pool = list(cursor)

            def extract_solo_coins(u):
                solo_coins = safe_int(u.get("coins_solo"))
                if solo_coins > 0:
                    return solo_coins
                return 0

            user_pool.sort(key=extract_solo_coins, reverse=True)

            for u in user_pool[:10]:
                score = extract_solo_coins(u)
                if score > 0:
                    users.append({
                        "name": format_user_name(u),
                        "score": score,
                        "label": "Solo Coins"
                    })

        return jsonify(users)

    except Exception as e:
        print(f"Leaderboard Query Error: {e}")
        return jsonify([]), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
