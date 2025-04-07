"""
Module for the Dota Discord Bot Dashboard.
"""
import os
import time
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple

from flask import Blueprint, request, jsonify, g, current_app
from dotenv import load_dotenv

auth_blueprint = Blueprint('auth', __name__)
logger = logging.getLogger('DotaDiscordBot.WebApp')

# Load .env
load_dotenv()

# Grab admin credentials from environment
ENV_ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')
ENV_ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'admin')

# Token storage with improved structure
class TokenStorage:
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}

    def add_token(self, username: str, role: str, expiry_hours: int = 12) -> Tuple[str, datetime]:
        """Add a new token for a user."""
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=expiry_hours)

        self.tokens[token] = {
            'username': username,
            'role': role,
            'expiry': expiry,
            'created_at': datetime.utcnow(),
            'last_used': datetime.utcnow()
        }

        return token, expiry

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a token and return user info if valid."""
        if token not in self.tokens:
            return None

        token_data = self.tokens[token]
        now = datetime.utcnow()

        # Check expiration
        if now > token_data['expiry']:
            del self.tokens[token]
            return None

        # Update last used time
        token_data['last_used'] = now

        return token_data

    def remove_token(self, token: str) -> bool:
        """Remove a token (logout)."""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False

    def record_failed_attempt(self, ip_address: str) -> int:
        """Record a failed login attempt and return the total attempts."""
        now = datetime.utcnow()

        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = {
                'attempts': 1,
                'first_attempt': now,
                'last_attempt': now
            }
        else:
            # Reset attempts if last attempt was more than 1 hour ago
            if now - self.failed_attempts[ip_address]['last_attempt'] > timedelta(hours=1):
                self.failed_attempts[ip_address] = {
                    'attempts': 1,
                    'first_attempt': now,
                    'last_attempt': now
                }
            else:
                self.failed_attempts[ip_address]['attempts'] += 1
                self.failed_attempts[ip_address]['last_attempt'] = now

        return self.failed_attempts[ip_address]['attempts']

    def cleanup_expired(self):
        """Clean up expired tokens and old failed attempts."""
        now = datetime.utcnow()

        # Clean expired tokens
        expired_tokens = [
            token for token, data in self.tokens.items()
            if now > data['expiry']
        ]
        for token in expired_tokens:
            del self.tokens[token]

        # Clean old failed attempts (older than 24 hours)
        old_attempts = [
            ip for ip, data in self.failed_attempts.items()
            if now - data['last_attempt'] > timedelta(hours=24)
        ]
        for ip in old_attempts:
            del self.failed_attempts[ip]

# Initialize token storage
token_storage = TokenStorage()

def require_auth(func):
    """Decorator to require a valid token."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'Missing or invalid token'}), 401

        token = auth_header.split(' ')[1]
        token_data = token_storage.validate_token(token)

        if not token_data:
            return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401

        # Put user info in flask.g
        g.user = token_data['username']
        g.role = token_data['role']
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator to require admin role."""
    @wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.role != 'admin':
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
        return func(*args, **kwargs)
    return wrapper


@auth_blueprint.before_app_request
def before_request():
    """Run before each request to clean up expired tokens."""
    token_storage.cleanup_expired()


@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Log in a user by checking the .env credentials only.
    Returns a JWT-like token in JSON if successful, else 401.
    """
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': 'Username and password are required'
        }), 400

    # Get client IP (consider X-Forwarded-For for proxies)
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Check for too many failed attempts
    attempts = token_storage.record_failed_attempt(client_ip)
    if attempts > 5:
        logger.warning(f"Too many failed login attempts from IP: {client_ip}")
        return jsonify({
            'status': 'error',
            'message': 'Too many failed login attempts. Please try again later.'
        }), 429

    # Strong password comparison (resist timing attacks)
    valid_password = slow_compare(
        hashlib.sha256(password.encode()).hexdigest(),
        hashlib.sha256(ENV_ADMIN_PASS.encode()).hexdigest()
    )

    # Compare with environment-based admin
    if username == ENV_ADMIN_USER and valid_password:
        # Generate token with 12 hour expiry
        token, expiry = token_storage.add_token(username, 'admin', 12)

        logger.info(f"Successful login for user '{username}' from IP '{client_ip}'")

        return jsonify({
            'status': 'success',
            'data': {
                'token': token,
                'username': username,
                'role': 'admin',
                'expiry': expiry.isoformat()
            }
        })
    else:
        logger.warning(f"Failed login attempt for user '{username}' from IP '{client_ip}'")

        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401


@auth_blueprint.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Log out by removing the token from active_tokens."""
    token = request.headers['Authorization'].split(' ')[1]
    if token_storage.remove_token(token):
        return jsonify({'status': 'success', 'message': 'Logged out successfully'})
    return jsonify({'status': 'error', 'message': 'Invalid token'}), 400


@auth_blueprint.route('/status', methods=['GET'])
@require_auth
def status():
    """Check authentication status."""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1]
    token_data = token_storage.validate_token(token)

    if not token_data:
        return jsonify({'status': 'error', 'message': 'Token expired'}), 401

    # Calculate remaining time
    expiry = token_data['expiry']
    remaining_seconds = int((expiry - datetime.utcnow()).total_seconds())

    return jsonify({
        'status': 'success',
        'data': {
            'username': token_data['username'],
            'role': token_data['role'],
            'expiry': expiry.isoformat(),
            'remaining_seconds': remaining_seconds
        }
    })


@auth_blueprint.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """Refresh the authentication token."""
    old_token = request.headers['Authorization'].split(' ')[1]
    token_data = token_storage.validate_token(old_token)

    if not token_data:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

    # Remove old token
    token_storage.remove_token(old_token)

    # Generate new token
    new_token, expiry = token_storage.add_token(token_data['username'], token_data['role'])

    return jsonify({
        'status': 'success',
        'data': {
            'token': new_token,
            'username': token_data['username'],
            'role': token_data['role'],
            'expiry': expiry.isoformat()
        }
    })


def slow_compare(a, b):
    """
    Perform a constant-time comparison of two strings to resist timing attacks.
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)

    # Add a small delay to further resist timing analysis
    time.sleep(0.01)

    return result == 0