import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getUserByUsername, bcrypt } from '../lib/db';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            // 1. Direct DB Query for User
            const user = await getUserByUsername(username);

            if (!user) {
                throw new Error('Invalid credentials');
            }

            // 2. Client-side Hash Comparison
            if (user.hashed_password) {
                const isValid = bcrypt.compareSync(password, user.hashed_password);
                if (!isValid) {
                    throw new Error('Invalid credentials');
                }
            } else {
                // For legacy users without password or if handling differently
                throw new Error('Invalid account configuration');
            }

            // 3. Store User Session (Trusted Client-Side)
            // No JWT signing, just store the user object/ID
            localStorage.setItem('currentUser', JSON.stringify({
                id: user.id,
                username: user.username,
                email: user.email
            }));

            // "Token" is now just a placeholder for legacy checks if any remain
            localStorage.setItem('token', 'client-side-session');

            navigate('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Login failed');
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-3xl font-bold tracking-tight text-gray-900">Welcome back</h2>
                <p className="mt-2 text-sm text-gray-600">
                    Sign in to your account
                </p>
            </div>

            <form className="space-y-6" onSubmit={handleLogin}>
                {error && <div className="text-red-500 text-sm text-center">{error}</div>}
                <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <input
                        type="text"
                        required
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Password</label>
                    <input
                        type="password"
                        required
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>

                <button
                    type="submit"
                    className="flex w-full justify-center rounded-md bg-black px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
                >
                    Sign in
                </button>
            </form>

            <p className="text-center text-sm text-gray-500">
                Don't have an account?{' '}
                <Link to="/register" className="font-semibold text-black hover:text-gray-800">
                    Sign up
                </Link>
            </p>
        </div>
    );
};

export default Login;
