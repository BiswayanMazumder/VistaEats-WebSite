from flask import Flask, request, jsonify
from supabase import create_client, Client
import re

app = Flask(__name__)

# Supabase credentials
SUPABASE_URL = "https://hwbzxdwtutipncvjwfrg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3Ynp4ZHd0dXRpcG5jdmp3ZnJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA1ODE4OTcsImV4cCI6MjA2NjE1Nzg5N30._pYfuukAbKhk0bEyu6iSpQ4cFwZdnOzFx5bOj1QbPaM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password strength checker
def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[\W_]', password)
    )

# Register route
@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    print("📥 Incoming registration data:", data)  # Debug print

    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role = 'user'

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if not is_strong_password(password):
        return jsonify({"error": "Password must be at least 8 characters and include uppercase, lowercase, digit, and special character"}), 400

    if role not in ['admin', 'user']:
        return jsonify({"error": "Invalid role. Only 'admin' and 'user' allowed."}), 400

    user = supabase.table('users').select('*').eq('username', username).execute()
    if user.data and len(user.data) > 0:
        return jsonify({"error": "User already exists"}), 409

    supabase.table('users').insert({'username': username, 'password': password, 'role': role}).execute()
    return jsonify({"message": "User registered", "role": role}), 201

# Login route
@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    print("📥 Incoming login data:", data)  # Debug print

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = supabase.table('users').select('*').eq('username', username).eq('password', password).execute()
    if user.data and len(user.data) > 0:
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.data[0]['id'],
                "username": user.data[0]['username'],
                "role": user.data[0]['role']
            }
        }), 200

    return jsonify({"error": "Invalid username or password"}), 401

# Delete user by ID
@app.route('/user/delete', methods=['DELETE'])
def delete_user():
    data = request.get_json()
    print("📥 Incoming delete request:", data)  # Debug print

    user_id = data.get('id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = supabase.table('users').select('*').eq('id', user_id).execute()
    if not user.data or len(user.data) == 0:
        return jsonify({"error": "User not found"}), 404

    supabase.table('users').delete().eq('id', user_id).execute()
    return jsonify({"message": f"User with ID '{user_id}' deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
