import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createUser } from '../lib/db';

const Register: React.FC = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            // 1. Direct DB Insert (Hash calculation is inside createUser)
            const newUser = await createUser(username, email, password);

            // 2. Auto Login (Session Storage)
            localStorage.setItem('currentUser', JSON.stringify({
                id: newUser.id,
                username: newUser.username,
                email: newUser.email
            }));
            localStorage.setItem('token', 'client-side-session');

            navigate('/dashboard');

        } catch (err: any) {
            console.error(err);
            // Handle unique constraint violations blindly or parsing error string
            if (err.message && err.message.includes('unique')) {
                setError('Username or Email already exists');
            } else {
                setError(err.message || 'Registration failed');
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-3xl font-bold tracking-tight text-gray-900">Create login</h2>
                <p className="mt-2 text-sm text-gray-600">
                    Get started with Doodle AI
                </p>
            </div>

            <form className="space-y-6" onSubmit={handleRegister}>
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
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                        type="email"
                        required
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
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
                    Sign up
                </button>
            </form>

            <p className="text-center text-sm text-gray-500">
                Already have an account?{' '}
                <Link to="/login" className="font-semibold text-black hover:text-gray-800">
                    Log in
                </Link>
            </p>
        </div>
    );
};

export default Register;
