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

# Register route (unchanged)
@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

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

# Login route (unchanged)
@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
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

# Delete user by ID (unchanged)
@app.route('/user/delete', methods=['DELETE'])
def delete_user():
    data = request.get_json()
    user_id = data.get('id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = supabase.table('users').select('*').eq('id', user_id).execute()
    if not user.data or len(user.data) == 0:
        return jsonify({"error": "User not found"}), 404

    supabase.table('users').delete().eq('id', user_id).execute()
    return jsonify({"message": f"User with ID '{user_id}' deleted"}), 200

# Update username or password
@app.route('/user/update', methods=['PUT'])
def update_user():
    data = request.get_json()
    user_id = data.get('id')
    new_username = data.get('username')
    new_password = data.get('password')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Fetch current user data
    user_response = supabase.table('users').select('*').eq('id', user_id).execute()
    if not user_response.data or len(user_response.data) == 0:
        return jsonify({"error": "User not found"}), 404

    current_user = user_response.data[0]

    updates = {}

    # Validate and update username if provided
    if new_username:
        if new_username == current_user['username']:
            return jsonify({"error": "New username cannot be the same as the old username"}), 400
        
        # Check if new username is taken by another user
        username_check = supabase.table('users').select('*').eq('username', new_username).neq('id', user_id).execute()
        if username_check.data and len(username_check.data) > 0:
            return jsonify({"error": "Username already taken"}), 409

        updates['username'] = new_username

    # Validate and update password if provided
    if new_password:
        if not is_strong_password(new_password):
            return jsonify({"error": "Password must be at least 8 characters and include uppercase, lowercase, digit, and special character"}), 400
        
        updates['password'] = new_password

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    supabase.table('users').update(updates).eq('id', user_id).execute()
    return jsonify({"message": "User updated successfully", "updated_fields": list(updates.keys())}), 200

if __name__ == '__main__':
    app.run(debug=True)
