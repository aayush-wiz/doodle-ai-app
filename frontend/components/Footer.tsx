import React from 'react';

const Footer: React.FC = () => {
    return (
        <footer className="bg-black text-white py-12 px-6 md:px-12 border-t border-gray-900">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">

                {/* Brand */}
                <div className="flex flex-col items-center md:items-start">
                    <div className="flex items-center gap-3 mb-2">
                        <img src="/images/white.png" alt="chytr logo" className="w-8 h-8 object-contain" />
                        <span className="text-4xl font-bold font-serif-brand tracking-tight">chytr <span className="font-normal font-sans text-lg opacity-70">(चित्र)</span></span>
                    </div>
                    <p className="text-gray-400 text-sm mt-2">Turning ideas into visual stories.</p>
                </div>

                {/* Links */}
                <div className="flex gap-8 text-sm font-medium text-gray-400">
                    <a href="#" className="hover:text-white transition-colors">Privacy</a>
                    <a href="#" className="hover:text-white transition-colors">Terms</a>
                    <a href="#" className="hover:text-white transition-colors">Twitter</a>
                    <a href="#" className="hover:text-white transition-colors">Contact</a>
                </div>

                {/* Copyright */}
                <div className="text-gray-600 text-xs">
                    &copy; {new Date().getFullYear()} Chroma Labs Inc.
                </div>
            </div>
        </footer>
    );
};

export default Footer;
