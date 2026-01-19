import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye } from 'lucide-react';

// --- VIDEO CONSTANTS (Moved from VideoGridSection) ---
const DOODLE_VIDEOS = [
    { url: "/video_pythagorean_theorem.mp4", title: "The Pythagorean Theorem" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/crousel1.mp4", title: "ML vs Traditional Code" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/coursel2.mp4", title: "LLM Architecture" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/crousel3.mp4", title: "Transformer Attention" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_e093f069_normal.mp4", title: "GPU Architecture" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_0b0234a9_normal.mp4", title: "K-Means Clustering" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_0f493bf6_normal.mp4", title: "Neural Networks" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_00f0e35a_normal.mp4", title: "Encoder-Decoder" },
    { url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_6d67d7cf_normal.mp4", title: "Black Holes" }
];

const TRAINING_VIDEOS = [
    { url: "/training_demos/warehouse_lifting.mp4", title: "Warehouse Safety: Lifting" },
    { url: "/training_demos/food_safety.mp4", title: "Food Hygiene Protocols" },
    { url: "/training_demos/phishing_demo.mp4", title: "Cybersecurity: Phishing" },
    { url: "/training_demos/forklift_demo.mp4", title: "Safety: Forklift Ops" },
    { url: "/training_demos/sales_demo.mp4", title: "Sales: Closing Techniques" }
];

const CARTOON_VIDEOS = [
    { url: "/cartoon/video_history_of_pizza_cartoon.mp4", title: "The History of Pizza" },
    { url: "/cartoon/video_8f44fab4_cartoon.mp4", title: "Narrative Stories" },
    { url: "/cartoon/video_c040c1e6_cartoon.mp4", title: "Character Focus" },
    { url: "/cartoon/video_c9f33199_cartoon.mp4", title: "Dynamic Action" }
];

// Combine into a structured object for easy access
const CATEGORIES: Record<string, { url: string; title: string }[]> = {
    "Generate Mathematics": DOODLE_VIDEOS,
    "Corporate Training": TRAINING_VIDEOS,
    "Character Learning": CARTOON_VIDEOS
};

const GuidedLearning: React.FC = () => {
    const navigate = useNavigate();
    // State for active category (default to first key)
    const [activeCategory, setActiveCategory] = useState<string>(Object.keys(CATEGORIES)[0]);

    // State for currently playing video (default to first video of first category)
    const [currentVideo, setCurrentVideo] = useState(CATEGORIES[Object.keys(CATEGORIES)[0]][0]);

    // State for loaded video content
    const [videoContent, setVideoContent] = useState<any>(null);
    const [loadingContent, setLoadingContent] = useState<boolean>(false);

    // Helper function to map video title to JSON file path
    const getContentPath = (category: string, title: string): string => {
        const categoryMap: Record<string, string> = {
            "Generate Mathematics": "generate-mathematics",
            "Corporate Training": "corporate-training",
            "Character Learning": "character-learning"
        };
        const slug = title.toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '')
            .replace(/:/g, '') // Remove colons
            .replace(/\s+/g, '-'); // Replace spaces with hyphens
        return `/guided-learning/${categoryMap[category]}/${slug}.json`;
    };

    // Load content when currentVideo changes
    useEffect(() => {
        const loadContent = async () => {
            setLoadingContent(true);
            try {
                const path = getContentPath(activeCategory, currentVideo.title);
                const response = await fetch(path);
                if (response.ok) {
                    const data = await response.json();
                    setVideoContent(data);
                } else {
                    console.warn(`Content not found for ${currentVideo.title}`);
                    setVideoContent(null);
                }
            } catch (error) {
                console.error('Error loading content:', error);
                setVideoContent(null);
            } finally {
                setLoadingContent(false);
            }
        };

        loadContent();
    }, [currentVideo, activeCategory]);

    // Handler for changing category
    const handleCategoryChange = (category: string) => {
        setActiveCategory(category);
        // Automatically switch to the first video of the new category
        setCurrentVideo(CATEGORIES[category][0]);
    };

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-black font-sans pt-24 px-6 md:px-12">
            {/* HEADER (Replicated from Navbar for consistency) */}
            <nav className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 py-6 flex justify-between items-center bg-[#FAFAFA]/95 backdrop-blur-sm transition-all duration-300">
                {/* Logo Area */}
                <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
                    <img src="/images/black.png" alt="chytr logo" className="w-10 h-10 object-contain" />
                    <span className="text-4xl font-bold font-serif-brand text-black tracking-tight group-hover:opacity-70 transition-opacity flex items-center gap-1.5">
                        chytr <span className="font-normal font-sans opacity-60 text-lg">(चित्र)</span>
                    </span>
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-6">
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

            <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-8 pt-6">

                {/* LEFT SIDEBAR: Category Selector */}
                <aside className="w-full md:w-64 flex-shrink-0 hidden md:block md:sticky md:top-24 md:h-[calc(100vh-8rem)] md:overflow-y-auto">

                    <h3 className="font-bold text-lg mb-4">Categories</h3>
                    <ul className="space-y-2">
                        {Object.keys(CATEGORIES).map((category, idx) => (
                            <li
                                key={idx}
                                onClick={() => handleCategoryChange(category)}
                                className={`text-sm cursor-pointer transition-colors px-2 py-1.5 rounded-md ${activeCategory === category
                                    ? 'bg-black text-white font-bold shadow-md ring-1 ring-black/5'
                                    : 'text-gray-600 hover:bg-gray-100 hover:text-black'
                                    }`}
                            >
                                {category}
                            </li>
                        ))}
                    </ul>
                </aside>

                {/* MAIN CONTENT: Active Video Player */}
                <main className="flex-1 min-w-0">
                    <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-100 p-6">

                        {/* Video Player Container */}
                        <div className="aspect-video w-full bg-black rounded-xl overflow-hidden mb-6 relative">
                            <video
                                key={currentVideo.url} // Key prop ensures video reloads when url changes
                                src={currentVideo.url}
                                className="w-full h-full object-contain"
                                controls
                                autoPlay
                            />
                        </div>

                        {/* Metadata tags */}
                        <div className="flex items-center justify-between mb-4">
                            <span className="px-3 py-1 bg-red-50 text-red-600 text-xs font-bold uppercase tracking-wider rounded-full">
                                {activeCategory === "Generate Mathematics" ? "AI MATH" :
                                    activeCategory === "Corporate Training" ? "DEMO MODULE" : "CHARACTER"}
                            </span>
                        </div>

                        {/* Title */}
                        <h1 className="text-3xl font-serif-brand font-bold mb-4 leading-tight">
                            {currentVideo.title}
                        </h1>

                        {/* Author / Actions */}
                        <div className="flex items-center justify-between border-b border-gray-100 pb-6 mb-6">
                            <div className="text-xs text-gray-500">
                                <span className="font-bold text-gray-900 uppercase">GENERATED BY CHYTR AI</span>
                                <br />
                                {new Date().toLocaleDateString()}
                            </div>
                        </div>

                        {/* Dynamic Content from JSON */}
                        {loadingContent ? (
                            <div className="text-gray-500 text-sm">Loading content...</div>
                        ) : videoContent?.content ? (
                            <div className="prose max-w-none text-gray-600 space-y-6 text-sm leading-relaxed">
                                {/* Introduction */}
                                <p className="text-base text-gray-700">
                                    {videoContent.content.introduction}
                                </p>

                                {/* Chapters */}
                                {videoContent.content.chapters && videoContent.content.chapters.map((chapter: any, idx: number) => (
                                    <div key={idx} className="space-y-3">
                                        <h3 className="text-lg font-semibold text-gray-900 mt-6 mb-3">
                                            {chapter.heading}
                                        </h3>
                                        <p className="text-gray-700 leading-relaxed">
                                            {chapter.content}
                                        </p>
                                        {/* Formulas */}
                                        {chapter.formulas && chapter.formulas.length > 0 && (
                                            <div className="mt-4 space-y-2">
                                                {chapter.formulas.map((formula: string, fIdx: number) => (
                                                    <div key={fIdx} className="bg-gray-50 border-l-4 border-blue-500 p-3 rounded-r font-mono text-xs text-gray-800">
                                                        {formula}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}

                                {/* Conclusion */}
                                {videoContent.content.conclusion && (
                                    <p className="text-base text-gray-700 mt-6 pt-4 border-t border-gray-200">
                                        {videoContent.content.conclusion}
                                    </p>
                                )}

                                {/* Key Points */}
                                {videoContent.content.keyPoints && videoContent.content.keyPoints.length > 0 && (
                                    <div className="mt-6 pt-4 border-t border-gray-200">
                                        <h4 className="text-base font-semibold text-gray-900 mb-3">Key Points:</h4>
                                        <ul className="space-y-2 list-disc list-inside text-gray-700">
                                            {videoContent.content.keyPoints.map((point: string, idx: number) => (
                                                <li key={idx}>{point}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="prose max-w-none text-gray-600 space-y-4 text-sm leading-relaxed">
                                <p>
                                    This video demonstrates our advanced video generation capabilities.
                                    The content is dynamically created to suit specific use cases, ranging from educational doodles
                                    to professional corporate training modules and engaging entertainment.
                                </p>
                                <p>
                                    Explore the sidebar to view more videos in this category, or switch categories to see different styles and applications of our technology.
                                </p>
                            </div>
                        )}

                    </div>
                </main>

                {/* RIGHT SIDEBAR: Playlist for Active Category */}
                <aside className="w-full md:w-80 flex-shrink-0 md:sticky md:top-24 md:h-[calc(100vh-8rem)] md:overflow-y-auto">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-lg">In This Category</h3>
                        <span className="text-xs text-gray-500">{CATEGORIES[activeCategory].length} Videos</span>
                    </div>

                    <div className="space-y-6">
                        {CATEGORIES[activeCategory].map((video, idx) => (
                            <div
                                key={idx}
                                className={`group cursor-pointer rounded-xl p-2 transition-colors ${currentVideo.url === video.url ? 'bg-black shadow-md ring-1 ring-black/5' : 'hover:bg-gray-50'
                                    }`}
                                onClick={() => setCurrentVideo(video)}
                            >
                                <div className="aspect-video w-full bg-black rounded-lg overflow-hidden mb-3 relative">
                                    <video
                                        src={video.url}
                                        className="w-full h-full object-cover"
                                        preload="auto"
                                        muted
                                        loop
                                        playsInline
                                        autoPlay
                                    />
                                    {currentVideo.url === video.url && (
                                        <div className="absolute inset-0 bg-black/10 flex items-center justify-center">
                                            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md">
                                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <div className="flex items-start gap-2">
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${currentVideo.url === video.url ? 'bg-black text-white' : 'bg-gray-100 text-gray-600'
                                        }`}>
                                        {currentVideo.url === video.url ? 'PLAYING' : 'WATCH'}
                                    </span>
                                </div>
                                <h4 className={`font-bold text-sm mt-2 leading-snug group-hover:text-black transition-colors ${currentVideo.url === video.url ? 'text-white' : 'text-black'
                                    }`}>
                                    {video.title}
                                </h4>
                                <div className={`flex items-center gap-2 mt-2 text-xs ${currentVideo.url === video.url ? 'text-gray-300' : 'text-gray-400'}`}>
                                    <Eye size={12} /> {(Math.random() * 5 + 1).toFixed(1)}k
                                </div>
                            </div>
                        ))}
                    </div>
                </aside>

            </div>
        </div>
    );
};

export default GuidedLearning;
