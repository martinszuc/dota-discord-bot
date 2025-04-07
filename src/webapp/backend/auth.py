"""
Authentication module for the Dota Discord Bot Dashboard.
"""

import os
import json
import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Optional, Callable

from flask import Blueprint, request, jsonify, g

# Initialize blueprint
auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger('DotaDiscordBot.WebApp')

# Directory for storing user credentials
USERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
USERS_FILE = os.path.join(USERS_DIR, 'users.json')

# In-memory token storage
active_tokens = {}

# Ensure the data directory exists
os.makedirs(USERS_DIR, exist_ok=True)


def load_users() -> Dict[str, Dict[str, Any]]:
    """
    Load user data from the JSON file.

    Returns:
        Dict: User data keyed by username.
    """
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
            return users
        else:
            # Create the file with a default admin user if it doesn't exist
            default_password = hashlib.sha256('admin'.encode()).hexdigest()
            users = {
                'admin': {
                    'password_hash': default_password,
                    'role': 'admin',
                    'created_at': datetime.now().isoformat()
                }
            }
            save_users(users)
            return users
    except Exception as e:
        logger.error(f"Error loading users: {e}", exc_info=True)
        return {}


def save_users(users: Dict[str, Dict[str, Any]]) -> bool:
    """
    Save user data to the JSON file.

    Args:
        users (Dict): User data keyed by username.

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}", exc_info=True)
        return False


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for a route.

    Args:
        f (Callable): The route function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'message': 'Missing or invalid authentication token'
            }), 401

        token = auth_header.split(' ')[1]

        if token not in active_tokens:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token'
            }), 401

        # Set user in flask.g for the route to access
        g.user = active_tokens[token]['username']
        g.role = active_tokens[token]['role']

        return f(*args, **kwargs)

    return decorated


def require_admin(f: Callable) -> Callable:
    """
    Decorator to require admin role for a route.

    Args:
        f (Callable): The route function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'message': 'Missing or invalid authentication token'
            }), 401

        token = auth_header.split(' ')[1]

        if token not in active_tokens:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token'
            }), 401

        if active_tokens[token]['role'] != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Admin privileges required'
            }), 403

        # Set user in flask.g for the route to access
        g.user = active_tokens[token]['username']
        g.role = active_tokens[token]['role']

        return f(*args, **kwargs)

    return decorated


@auth_blueprint.route('/login', methods=['POST'])
def login() -> Dict[str, Any]:
    """
    Log in a user and issue a token.

    Returns:
        Dict: The login result.
    """
    data = request.json

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Username and password are required'
        }), 400

    username = data['username']
    password = data['password']

    users = load_users()

    if username not in users:
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if users[username]['password_hash'] != password_hash:
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401

    # Create a token
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(hours=12)

    active_tokens[token] = {
        'username': username,
        'role': users[username]['role'],
        'expiry': expiry.isoformat()
    }

    return jsonify({
        'status': 'success',
        'data': {
            'token': token,
            'username': username,
            'role': users[username]['role'],
            'expiry': expiry.isoformat()
        }
    })


@auth_blueprint.route('/logout', methods=['POST'])
@require_auth
def logout() -> Dict[str, Any]:
    """
    Log out a user by invalidating their token.

    Returns:
        Dict: The logout result.
    """
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]

    if token in active_tokens:
        del active_tokens[token]

    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    })


@auth_blueprint.route('/users', methods=['GET'])
@require_admin
def get_users() -> Dict[str, Any]:
    """
    Get all users (admin only).

    Returns:
        Dict: The list of users.
    """
    users = load_users()

    # Don't include password hashes in the response
    user_list = [
        {
            'username': username,
            'role': user_data['role'],
            'created_at': user_data['created_at']
        }
        for username, user_data in users.items()
    ]

    return jsonify({
        'status': 'success',
        'data': user_list
    })


@auth_blueprint.route('/users', methods=['POST'])
@require_admin
def create_user() -> Dict[str, Any]:
    """
    Create a new user (admin only).

    Returns:
        Dict: The result of the operation.
    """
    data = request.json

    if not data or 'username' not in data or 'password' not in data or 'role' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Username, password, and role are required'
        }), 400

    username = data['username']
    password = data['password']
    role = data['role']

    if role not in ['admin', 'user']:
        return jsonify({
            'status': 'error',
            'message': 'Role must be either "admin" or "user"'
        }), 400

    users = load_users()

    if username in users:
        return jsonify({
            'status': 'error',
            'message': 'Username already exists'
        }), 409

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    users[username] = {
        'password_hash': password_hash,
        'role': role,
        'created_at': datetime.now().isoformat()
    }

    save_users(users)

    return jsonify({
        'status': 'success',
        'message': f'User {username} created successfully'
    })


@auth_blueprint.route('/users/<username>', methods=['DELETE'])
@require_admin
def delete_user(username: str) -> Dict[str, Any]:
    """
    Delete a user (admin only).

    Args:
        username (str): The username to delete.

    Returns:
        Dict: The result of the operation.
    """
    if username == 'admin':
        return jsonify({
            'status': 'error',
            'message': 'Cannot delete the admin user'
        }), 400

    users = load_users()

    if username not in users:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404

    del users[username]
    save_users(users)

    # Invalidate any active tokens for this user
    for token, data in list(active_tokens.items()):
        if data['username'] == username:
            del active_tokens[token]

    return jsonify({
        'status': 'success',
        'message': f'User {username} deleted successfully'
    })


@auth_blueprint.route('/users/<username>/password', methods=['PUT'])
@require_auth
def change_password(username: str) -> Dict[str, Any]:
    """
    Change a user's password.

    Args:
        username (str): The username to change password for.

    Returns:
        Dict: The result of the operation.
    """
    # Check if the requesting user is the same as the target user or an admin
    if g.user != username and g.role != 'admin':
        return jsonify({
            'status': 'error',
            'message': 'You can only change your own password unless you are an admin'
        }), 403

    data = request.json

    if not data or 'new_password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'New password is required'
        }), 400

    users = load_users()

    if username not in users:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404

    new_password = data['new_password']
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()

    users[username]['password_hash'] = password_hash
    save_users(users)

    return jsonify({
        'status': 'success',
        'message': 'Password changed successfully'
    })


# Clean up expired tokens periodically
@auth_blueprint.before_app_request
def cleanup_tokens():
    """Clean up expired tokens before processing a request."""
    now = datetime.now()

    for token, data in list(active_tokens.items()):
        expiry = datetime.fromisoformat(data['expiry'])
        if expiry < now:
            del active_tokens[token]