import React, {useState} from 'react';
import {login} from '../api';
import './Login.css';

const Login = ({onLogin}) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!username || !password) {
            setError('Username and password are required');
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const response = await login(username, password);
            console.log("Login response:", response); // debug

            const {token, username: user, role, expiry} = response.data.data;

            // Store in localStorage
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify({username: user, role, expiry}));

            // Notify parent
            onLogin({username: user, role, expiry}, token);

            setLoading(false);
        } catch (err) {
            console.error('Login error:', err);
            setError('Login failed: ' + (err.response?.data?.message || 'Unknown error'));
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1>Dota Timer Bot</h1>
                    <h2>Dashboard Login</h2>
                </div>

                {error && <div className="login-error">{error}</div>}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            disabled={loading}
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter username"
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            disabled={loading}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                        />
                    </div>

                    <button type="submit" className="login-button" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
