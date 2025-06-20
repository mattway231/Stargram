from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)
DB_URL = os.getenv("DATABASE_URL")

@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    user_id = data.get('user_id')
    
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT is_member FROM users WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                return jsonify({"is_member": bool(result and result[0])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
