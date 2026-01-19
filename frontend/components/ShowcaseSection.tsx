import React, { useState } from 'react';
import { Play, Maximize2, X } from 'lucide-react';

interface ShowcaseSectionProps {
  backgroundImage: string;
}

const TABS = [
  {
    id: 'science',
    label: 'Science',
    image: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&w=2000&auto=format&fit=crop',
    video: '/video/science2.mp4',
    duration: '2:15'
  },
  {
    id: 'finance',
    label: 'Finance',
    image: 'https://images.unsplash.com/photo-1611974765270-ca12586343bb?q=80&w=2000&auto=format&fit=crop',
    video: '/video/finance.mp4',
    duration: '1:45'
  },
  {
    id: 'math',
    label: 'Mathematics',
    image: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=2000&auto=format&fit=crop',
    video: '/video/mathematics.mp4',
    duration: '3:20'
  },
  {
    id: 'biology',
    label: 'Biology',
    image: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2000&auto=format&fit=crop',
    video: '/video/biology.mp4',
    duration: '2:00'
  },
];

const ShowcaseSection: React.FC<ShowcaseSectionProps> = ({ backgroundImage }) => {
  const [activeTab, setActiveTab] = useState(TABS[0]);

  return (
    <div id="showcase-section" className="relative w-full min-h-screen bg-[#F9F7F1] flex flex-col py-24">

      <div className="flex-1 max-w-6xl mx-auto px-6 w-full flex flex-col items-center">

        {/* Header */}
        <div className="text-center mb-12 max-w-3xl">
          <div className="inline-block px-4 py-1 mb-4 border-2 border-black bg-[#4ADE80] shadow-[4px_4px_0px_0px_#000] transform -rotate-1">
            <h2 className="text-sm font-bold font-mono uppercase text-black tracking-widest">Focus Areas</h2>
          </div>
          <h2 className="text-3xl md:text-5xl font-black font-serif-brand text-black tracking-tight leading-tight mb-4">
            DOMAIN SPECIFIC EXPLORATION
          </h2>
          <p className="text-lg text-gray-700 font-medium font-mono leading-relaxed max-w-2xl mx-auto">
            Interactive doodle explainer videos generated in real-time.
          </p>
        </div>

        {/* Tabs Navigation */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 border-2 border-black font-bold font-mono text-sm uppercase tracking-wide transition-all duration-200 ${activeTab.id === tab.id
                ? 'bg-black text-white translate-y-1 shadow-none'
                : 'bg-white text-black shadow-[4px_4px_0px_0px_#000] hover:-translate-y-1 hover:shadow-[6px_6px_0px_0px_#000]'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Video Display Area - Retro Window Style */}
        <div className="w-full max-w-5xl animate-fade-in-up">
          <div className="bg-white border-2 border-black shadow-[10px_10px_0px_0px_#000] p-1">

            {/* Window Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b-2 border-black mb-1">
              <span className="font-mono text-xs font-bold uppercase">Video_Player.exe</span>
              <div className="flex gap-2">
                <button className="p-1 hover:bg-gray-300 border border-transparent hover:border-black"><Maximize2 className="w-3 h-3" /></button>
                <button className="p-1 hover:bg-[#FF5555] hover:text-white border border-transparent hover:border-black"><X className="w-3 h-3" /></button>
              </div>
            </div>

            {/* Video Content */}
            <div className="relative w-full aspect-video bg-black overflow-hidden group cursor-pointer border-2 border-black">

              <video
                key={activeTab.id}
                controls
                autoPlay
                muted
                loop
                playsInline
                className="w-full h-full object-contain bg-white"
              >
                <source src={activeTab.video} type="video/mp4" />
                Your browser does not support the video tag.
              </video>



            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ShowcaseSection;