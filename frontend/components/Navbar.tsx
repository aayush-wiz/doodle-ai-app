import React from 'react';
import { useNavigate } from 'react-router-dom';

interface NavbarProps {
  onConsoleClick: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onConsoleClick }) => {
  const navigate = useNavigate();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-transparent backdrop-blur-none transition-all duration-300">
      {/* Logo Area */}
      <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
        <img src="/images/black.png" alt="chytr logo" className="w-10 h-10 object-contain" />
        <div className="flex flex-col">
          <span className="text-4xl font-bold font-serif-brand text-black tracking-tight group-hover:opacity-70 transition-opacity flex items-center gap-1.5 leading-none">
            chytr <span className="font-normal font-sans opacity-60 text-lg">(चित्र)</span>
          </span>
          <span className="text-xs font-medium text-gray-500 tracking-wide font-sans mt-1 group-hover:opacity-70 transition-opacity">
            We doodlize everything
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-6">

        {/* <button
          onClick={onConsoleClick}
          className="text-sm font-medium px-5 py-2 bg-black text-white hover:bg-gray-800 transition-all rounded-lg"
        >
          Launch App
        </button> */}

        <button
          onClick={() => navigate('/guided-learning')}
          className="text-sm font-medium text-black hover:text-gray-600 transition-colors"
        >
          Guided Learning
        </button>

        <button
          onClick={() => navigate('/api')}
          className="text-sm font-medium text-black hover:text-gray-600 transition-colors"
        >
          API
        </button>

        <a
          href="mailto:hritvik@nanosecondlabs.com"
          className="text-sm font-medium px-5 py-2 bg-black text-white hover:bg-gray-800 transition-all rounded-lg"
        >
          Book Demo
        </a>
      </div>
    </nav>
  );
};

export default Navbar;