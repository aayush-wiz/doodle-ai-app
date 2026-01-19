import React, { useState, useEffect } from 'react';
import {
    Home,
    Grid,
    Video,
    Play,
    Mic,
    Palette,
    Timer,
    Send,
    Box,
    ArrowLeft,
    MoreVertical,
    Search,
    Bell,
    Plus,
    Clock,
    Globe,
    Loader2,
    Settings,
    LogOut
} from 'lucide-react';
import { getVideosByUserId, getHistoryByUserId, getUserByUsername } from '../lib/db';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// --- Types & Mock Data ---

interface VideoItem {
    id: number;
    title: string;
    author: string;
    views: string;
    duration: string;
    image: string;
    category: string;
    url?: string;
    isLoading?: boolean;
    progressStatus?: string;
}

const TRENDING_VIDEOS: VideoItem[] = [
    {
        id: 1,
        title: "How Human Evolution Works",
        author: "Evolution Studies",
        views: "2.0M",
        duration: "02:00",
        image: "/images/category/science.png", // Keeps generic Science
        category: "Science",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_the_human_evolution_works.mp4"
    },
    {
        id: 2,
        title: "How the Stock Market Works",
        author: "Finance Hub",
        views: "1.5M",
        duration: "03:00",
        image: "/images/category/tech.png", // Start generic Tech
        category: "Technology",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_stock_market_works_in_new_york_and_london_tech_centers.mp4"
    },
    {
        id: 3,
        title: "How Linear Regression Works",
        author: "ML Academy",
        views: "890K",
        duration: "02:15",
        image: "/images/category/math.png",
        category: "Math",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_linear_regression_works.mp4"
    },
    {
        id: 4,
        title: "Transformer Architecture Explained",
        author: "AI Insights",
        views: "950K",
        duration: "02:45",
        image: "/images/category/transformer.png", // UNIQUE
        category: "Technology",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/what_is_encoder_decoder_transformer_architecture_and_how_it_works.mp4"
    },
    {
        id: 5,
        title: "How Human DNA Evolves",
        author: "Biology Channel",
        views: "1.1M",
        duration: "01:50",
        image: "/images/category/dna.png", // UNIQUE
        category: "Science",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_the_human_dna_evolves.mp4"
    },
    {
        id: 6,
        title: "How Black Holes Are Formed",
        author: "Cosmos Academy",
        views: "2.3M",
        duration: "01:45",
        image: "/images/category/blackhole.png", // UNIQUE
        category: "Science",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_black_holes_are_formed.mp4"
    },
    {
        id: 7,
        title: "How Black Holes Form",
        author: "Space Explorers",
        views: "1.8M",
        duration: "01:30",
        image: "/images/category/blackhole.png", // UNIQUE (Shared)
        category: "Science",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/how_black_holes_form.mp4"
    },
    {
        id: 8,
        title: "Special Theory of Relativity",
        author: "Physics Pro",
        views: "3.2M",
        duration: "02:30",
        image: "/images/category/relativity.png", // UNIQUE
        category: "Science",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/special_theory_of_relativity.mp4"
    },
    {
        id: 9,
        title: "LSTM with Self Attention",
        author: "Deep Learning Lab",
        views: "720K",
        duration: "02:10",
        image: "/images/category/lstm.png", // UNIQUE
        category: "Technology",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/lstm_with_self_attention.mp4"
    },
    {
        id: 10,
        title: "How a Combustion Engine Works",
        author: "Engineering World",
        views: "1.4M",
        duration: "01:55",
        image: "/images/category/engine.png", // UNIQUE
        category: "Technology",
        url: "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/category/combustion_engine.mp4"
    }
];

const MY_LIBRARY_MOCK: VideoItem[] = [
    {
        id: 101,
        title: "My First AI Scene",
        author: "Bruce Wayne",
        views: "12",
        duration: "00:45",
        image: "https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=800&auto=format&fit=crop",
        category: "Personal"
    }
];

const HISTORY_ITEMS = [
    "Quantum Physics explainer",
    "Lo-fi study room environment",
    "Calculus visualization 3D"
];

const CATEGORIES = ["All Videos", "Science", "Technology", "Art", "Music", "History", "Math"];



type ViewType = 'home' | 'category' | 'library';
type SidebarView = 'main' | 'history';

// --- Components ---

const DashboardSection: React.FC = () => {
    const [currentView, setCurrentView] = useState<ViewType>('home');
    const [sidebarView, setSidebarView] = useState<SidebarView>('main');

    const [searchQuery, setSearchQuery] = useState("");
    const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);

    // Creation State
    const [topic, setTopic] = useState("");
    const [voice, setVoice] = useState("");
    const [style, setStyle] = useState("normal");
    const [language, setLanguage] = useState("en");
    const [beats, setBeats] = useState<number>(0);

    // App State
    const [voicesList, setVoicesList] = useState<Record<string, string>>({});
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    // Current User State
    const [currentUser, setCurrentUser] = useState<{ id: number; username: string; email: string; plan?: string; video_count?: number } | null>(null);

    // Fetch Current User on Mount (Sync with DB Directly)
    // We use direct DB here because Login.tsx uses client-side auth/placeholder tokens, 
    // so calling the backend /users/me endpoint will fail with 401.
    useEffect(() => {
        const fetchUser = async () => {
            const storedUserStr = localStorage.getItem('currentUser');
            if (storedUserStr) {
                try {
                    const storedUser = JSON.parse(storedUserStr);
                    // Refresh data from DB to get latest video_count
                    if (storedUser.username) {
                        const freshUser = await getUserByUsername(storedUser.username);
                        if (freshUser) {
                            setCurrentUser(freshUser);
                            localStorage.setItem('currentUser', JSON.stringify(freshUser));
                        } else {
                            // User possibly deleted?
                            handleLogout();
                        }
                    }
                } catch (e) {
                    console.error("Failed to sync user session", e);
                    // Fallback to what we have
                    if (currentUser) setCurrentUser(currentUser);
                }
            }
        };
        fetchUser();
    }, []);

    // User Menu State
    const [showUserMenu, setShowUserMenu] = useState(false);

    // Logout Handler
    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('currentUser'); // Clear session
        window.location.href = '/login';
    };

    // Fetch Voices on Mount
    useEffect(() => {
        fetch(`${API_URL}/voices`)
            .then(res => res.json())
            .then(data => {
                setVoicesList(data.voices || {});
                if (data.voices && Object.keys(data.voices).length > 0) {
                    setVoice(Object.keys(data.voices)[0]);
                }
            })
            .catch(err => console.error("Failed to fetch voices:", err));
    }, []);

    const handleGenerate = async () => {
        if (!topic.trim()) return;

        setIsGenerating(true);
        setGeneratedVideo(null);
        setErrorMsg(null);

        if (!currentUser) {
            setErrorMsg("Please login directly.");
            setIsGenerating(false);
            return;
        }

        try {
            // Construct WebSocket URL
            const wsUrl = API_URL.replace(/^http/, 'ws') + '/ws/generate';
            const socket = new WebSocket(wsUrl);

            // 1. Immediate UI Feedback
            const tempId = Date.now();
            const tempVideo: VideoItem = {
                id: tempId,
                title: topic,
                author: currentUser.username || "You",
                views: "0",
                duration: "--:--",
                image: "/images/heroimage.png", // specific placeholder?
                category: "Generating",
                isLoading: true,
                progressStatus: "Starting..."
            };
            setPendingVideo(tempVideo);
            setCurrentView('library'); // Redirect to library immediately
            setIsGenerating(true);     // Keep existing flag for now if needed, but pendingVideo handles the card

            socket.onopen = () => {
                // Send Initial Config
                socket.send(JSON.stringify({
                    topic: topic,
                    style: style,
                    voice: voice,
                    language: language,
                    max_beats: beats,
                    user_id: currentUser.id
                }));
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log("WS Message:", data);

                if (data.status === 'processing') {
                    setPendingVideo(prev => prev ? { ...prev, progressStatus: data.message || "Processing..." } : null);
                } else if (data.status === 'success') {
                    // Success!
                    // 1. Clear pending
                    setPendingVideo(null);
                    // 2. Refresh library data to get the real video from DB
                    //    But we can also just append it locally if we match the format:
                    const newVideo: VideoItem = {
                        id: data.id,
                        title: topic, // or data.title
                        author: "You",
                        views: "0",
                        duration: "00:30", // Placeholder or from backend
                        image: "/images/heroimage.png",
                        category: "Generated",
                        url: data.video_url
                    };
                    setLibraryVideos(prev => [newVideo, ...prev]);
                    setIsGenerating(false);
                    socket.close();
                } else if (data.status === 'error') {
                    setErrorMsg(data.detail || "Generation failed.");
                    setPendingVideo(null); // Remove card on error
                    setIsGenerating(false);
                    socket.close();
                }
            };

            socket.onerror = (error) => {
                console.error("WebSocket Error:", error);
                setErrorMsg("Connection error.");
                setIsGenerating(false);
            };

            socket.onclose = () => {
                console.log("WebSocket Closed");
                if (isGenerating && !generatedVideo) {
                    // If closed unexpectedly without success/error
                    // This might happen on normal close too, check flags
                }
            };

        } catch (e: any) {
            setErrorMsg(e.message || "Network error.");
            setIsGenerating(false);
        }
    };

    // Data State
    const [historyItems, setHistoryItems] = useState<any[]>([]); // Using any for quick mapping
    const [libraryVideos, setLibraryVideos] = useState<VideoItem[]>([]);
    const [categoryVideos, setCategoryVideos] = useState<VideoItem[]>([]); // New state for category items
    const [pendingVideo, setPendingVideo] = useState<VideoItem | null>(null);
    const [loadingData, setLoadingData] = useState(false);

    // Click Handlers for History & Library
    const handleHistoryClick = (item: any) => {
        if (item.video_url) {
            setGeneratedVideo(item.video_url);
            setTopic(item.query);
            setCurrentView('home');
            setSidebarView('main');
        } else {
            // If no video, maybe just populate the topic?
            setTopic(item.query);
            setCurrentView('home');
            setSidebarView('main');
        }
    };

    const handleLibraryClick = (video: VideoItem) => {
        if (video.url) {
            setGeneratedVideo(video.url);
            setTopic(video.title);
            setCurrentView('home');
        } else {
            console.warn("No URL for library video");
        }
    };

    // Fetch User Data (History, Library, Categories) - DIRECT NEON QUERIES
    useEffect(() => {
        const fetchData = async () => {
            setLoadingData(true);
            try {
                // 1. Fetch Categories (Public - always fetch if in category view)
                // 1. Fetch Categories (Public - always fetch if in category view)
                if (currentView === 'category') {
                    setCategoryVideos(TRENDING_VIDEOS);
                }

                // 2. Fetch User Data (Private - only if logged in)
                if (currentUser) {
                    // History
                    if (sidebarView === 'history') {
                        const histData = await getHistoryByUserId(currentUser.id);
                        setHistoryItems(histData);
                    }
                    // Library
                    if (currentView === 'library') {
                        const libData = await getVideosByUserId(currentUser.id);
                        const mappedVideos: VideoItem[] = libData.map((v) => ({
                            id: v.id,
                            title: v.title,
                            author: "You",
                            views: "0",
                            duration: "00:30",
                            image: "/images/heroimage.png",
                            category: "Generated",
                            url: v.url
                        }));
                        setLibraryVideos(mappedVideos);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch data from Neon:", err);
            } finally {
                setLoadingData(false);
            }
        };

        fetchData();
    }, [currentView, sidebarView, currentUser]);

    const videosToDisplay = currentView === 'category'
        ? categoryVideos
        : (currentView === 'library' && pendingVideo ? [pendingVideo, ...libraryVideos] : libraryVideos);

    return (
        <div className="flex h-screen w-full bg-[#F9F7F1] font-sans overflow-hidden text-gray-900">

            {/* 1. Left Sidebar Navigation (Soft Theme) */}
            <aside className="w-64 flex flex-col border-r border-gray-100 bg-[#F9F7F1] shrink-0 z-20">

                {/* Brand */}
                <div className="h-20 flex items-center px-6 gap-3">
                    <img src="/images/black.png" alt="chytr logo" className="w-8 h-8 object-contain" />
                    <span className="font-bold text-3xl font-serif-brand tracking-tight text-black">chytr <span className="font-normal font-sans text-lg">(चित्र)</span></span>
                </div>

                {/* Container for Sliding Views */}
                <div className="flex-1 relative overflow-hidden bg-[#F9F7F1]">

                    {/* MAIN MENU VIEW */}
                    <div className={`absolute inset-0 flex flex-col transition-transform duration-300 ease-in-out ${sidebarView === 'main' ? 'translate-x-0' : '-translate-x-full'}`}>

                        {/* CTA Button */}
                        <div className="p-6 pb-2">
                            <button
                                onClick={() => { setCurrentView('home'); setGeneratedVideo(null); setTopic(''); }}
                                className="w-full flex items-center justify-center gap-2 bg-black text-white py-3 hover:bg-gray-800 hover:shadow-lg transition-all rounded-xl font-bold text-sm shadow-md"
                            >
                                <Plus size={18} />
                                <span>New Video</span>
                            </button>
                        </div>

                        {/* Usage Stats Widget */}
                        {currentUser?.plan === 'free' && (
                            <div className="px-6 mb-2 animate-fade-in-up">
                                <div className="p-3 bg-white border border-gray-200 rounded-xl shadow-sm">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Free Plan</span>
                                        <span className="text-[10px] font-bold text-gray-900">{3 - (currentUser.video_count || 0)} left</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden mb-1">
                                        <div
                                            className="bg-black h-full rounded-full transition-all duration-500"
                                            style={{ width: `${Math.min(((currentUser.video_count || 0) / 3) * 100, 100)}%` }}
                                        ></div>
                                    </div>
                                    <div className="text-[10px] text-gray-400 text-center">
                                        {currentUser.video_count || 0} / 3 Videos Used
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Navigation */}
                        <nav className="flex-1 overflow-y-auto py-4 px-4 space-y-1">
                            <SidebarItem
                                icon={<Home size={20} />}
                                label="Home"
                                active={currentView === 'home'}
                                onClick={() => setCurrentView('home')}
                            />
                            <SidebarItem
                                icon={<Grid size={20} />}
                                label="Category"
                                active={currentView === 'category'}
                                onClick={() => setCurrentView('category')}
                            />
                            <SidebarItem
                                icon={<Video size={20} />}
                                label="My Library"
                                active={currentView === 'library'}
                                onClick={() => setCurrentView('library')}
                            />

                            {/* History Button (Triggers slide) */}
                            <SidebarItem
                                icon={<Clock size={20} />}
                                label="History"
                                onClick={() => setSidebarView('history')}
                            />
                        </nav>
                    </div>

                    {/* HISTORY OVERLAY VIEW */}
                    <div className={`absolute inset-0 flex flex-col bg-[#F9F7F1] transition-transform duration-300 ease-in-out ${sidebarView === 'history' ? 'translate-x-0' : 'translate-x-full'}`}>

                        {/* Back Button Header */}
                        <div className="p-4 border-b border-gray-100">
                            <button
                                onClick={() => setSidebarView('main')}
                                className="flex items-center gap-2 text-sm font-bold text-gray-800 hover:text-black transition-colors group"
                            >
                                <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                                <span>Back</span>
                            </button>
                        </div>

                        {/* History Content */}
                        <div className="flex-1 overflow-y-auto py-2">
                            <div className="px-4 py-2">
                                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                                    Recent
                                </h3>
                            </div>
                            <div className="space-y-1 px-2">
                                {historyItems.length === 0 ? (
                                    <div className="px-3 py-2 text-xs text-gray-400">No recent history</div>
                                ) : (
                                    historyItems.map((item, i) => (
                                        <button
                                            key={item.id || i}
                                            onClick={() => handleHistoryClick(item)}
                                            className="w-full text-left px-3 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg truncate transition-colors flex flex-col"
                                        >
                                            <span>{item.query}</span>
                                            <span className="text-[10px] text-gray-400 mt-0.5">{new Date(item.created_at).toLocaleDateString()}</span>
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                </div>

                {/* User Footer with Dropdown */}
                <div className="p-4 border-t border-gray-100 z-10 relative">
                    <div
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center gap-3 cursor-pointer hover:bg-gray-100 p-2 rounded-lg transition-colors"
                    >
                        <div className="w-8 h-8 rounded-full border border-gray-200 bg-black flex items-center justify-center text-white font-bold text-sm">
                            {currentUser?.username?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-sm font-bold truncate">{currentUser?.username || 'Guest'}</div>
                            <div className="text-xs text-gray-500 truncate">{currentUser?.email || 'Not logged in'}</div>
                            {currentUser?.plan === 'free' && (
                                <div className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full inline-block mt-1 w-fit">
                                    {currentUser.video_count || 0}/3 Videos
                                </div>
                            )}
                        </div>
                        <Settings size={16} className="text-gray-400" />
                    </div>

                    {/* Dropdown Menu */}
                    {showUserMenu && (
                        <div className="absolute bottom-full left-4 right-4 mb-2 bg-white border border-gray-100 rounded-xl shadow-xl overflow-hidden animate-fade-in-up">
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                            >
                                <LogOut size={16} />
                                <span>Log out</span>
                            </button>
                        </div>
                    )}
                </div>
            </aside>

            {/* 2. Main Content Area */}
            <main className="flex-1 flex flex-col relative min-w-0 bg-[#F9F7F1]">

                {/* Top Header */}
                <header className="h-16 flex items-center justify-between px-8 bg-[#F9F7F1] shrink-0 z-10">
                    <div className="flex-1 flex items-center">
                        {currentView === 'library' ? (
                            <div className="flex items-center gap-3 w-full max-w-2xl bg-white px-3 py-2 shadow-sm rounded-lg focus-within:ring-2 ring-black/5 transition-all">
                                <Search className="w-4 h-4 text-gray-400" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search your library..."
                                    className="flex-1 outline-none text-sm font-medium placeholder:text-gray-400 bg-transparent"
                                />
                            </div>
                        ) : (
                            <div className="font-bold text-sm text-gray-900 tracking-wide">
                                STUDIO v2.0
                            </div>
                        )}
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto scrollbar-hide flex flex-col">

                    {/* --- VIEW: HOME (CREATION STUDIO) --- */}
                    {currentView === 'home' && (
                        <div className="flex-1 flex flex-col pb-20">

                            {/* STATE 1: No Video Yet */}
                            {!generatedVideo && !isGenerating && (
                                <div className="flex-1 flex flex-col items-center justify-center px-8 pt-6">
                                    <div className="mb-6 text-center">
                                        <h2 className="text-3xl font-bold font-serif-brand text-gray-900 tracking-tight leading-tight mb-2">
                                            Create Magic
                                        </h2>
                                        <p className="text-gray-500 text-sm">Turn your ideas into visual stories.</p>
                                    </div>

                                    {/* Full Input Container (Soft Card) */}
                                    <div className="w-full max-w-2xl relative animate-fade-in-up">
                                        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 flex flex-col transition-all border border-gray-100">
                                            <textarea
                                                value={topic}
                                                onChange={(e) => setTopic(e.target.value)}
                                                className="w-full h-32 p-6 text-lg font-medium outline-none resize-none placeholder:text-gray-300 bg-transparent"
                                                placeholder="Describe your video idea... e.g. 'How do black holes work?'"
                                                disabled={isGenerating}
                                            ></textarea>
                                            <div className="px-4 py-3 bg-gray-50/50 flex items-center justify-between gap-4 border-t border-gray-100 flex-wrap">
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <CustomVoiceSelect voice={voice} setVoice={setVoice} voicesList={voicesList} disabled={false} />
                                                    <ChipSelect value={style} onChange={setStyle} icon={<Palette size={14} />} options={[{ value: 'normal', label: 'Normal' }, { value: 'solid', label: 'Solid' }, { value: 'pencil', label: 'Pencil' }]} />
                                                    <ChipSelect value={language} onChange={setLanguage} icon={<Globe size={14} />} options={[{ value: 'en', label: 'EN' }, { value: 'es', label: 'ES' }, { value: 'fr', label: 'FR' }, { value: 'de', label: 'DE' }, { value: 'hi', label: 'HI' }, { value: 'ja', label: 'JA' }, { value: 'zh', label: 'ZH' }]} />
                                                    <ChipSelect value={String(beats)} onChange={(v) => setBeats(parseInt(v))} icon={<Timer size={14} />} options={[
                                                        { value: '0', label: 'Auto' },
                                                        { value: '1', label: '1 Scene' },
                                                        { value: '2', label: '2 Scenes' },
                                                        { value: '3', label: '3 Scenes' },
                                                        { value: '4', label: '4 Scenes' },
                                                        { value: '5', label: '5 Scenes' },
                                                        { value: '6', label: '6 Scenes' },
                                                        { value: '7', label: '7 Scenes' },
                                                        { value: '8', label: '8 Scenes' },
                                                        { value: '9', label: '9 Scenes' },
                                                        { value: '10', label: '10 Scenes' }
                                                    ]} />
                                                </div>
                                                <button onClick={handleGenerate} disabled={!topic.trim()} className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md flex-shrink-0 transition-all ${!topic.trim() ? 'bg-gray-200 cursor-not-allowed' : 'bg-black text-white hover:bg-gray-800 hover:scale-105'}`}>
                                                    <Send className="w-4 h-4 ml-0.5" />
                                                </button>
                                            </div>
                                        </div>
                                        {errorMsg && <div className="mt-4 p-3 bg-red-50 border border-red-100 text-red-600 rounded-lg text-sm text-center">{errorMsg}</div>}
                                    </div>
                                </div>
                            )}

                            {/* STATE 2: Generating */}
                            {isGenerating && (
                                <div className="flex-1 flex flex-col items-center justify-center">
                                    <div className="text-center animate-pulse">
                                        <div className="w-16 h-16 rounded-full border-4 border-gray-100 border-t-black animate-spin mx-auto mb-6"></div>
                                        <h3 className="text-xl font-bold text-gray-900 mb-2">Dreaming up your video...</h3>
                                        <p className="text-sm text-gray-500">"{topic}"</p>
                                    </div>
                                </div>
                            )}

                            {/* STATE 3: Video Generated */}
                            {generatedVideo && !isGenerating && (
                                <div className="flex flex-col">
                                    {/* Compact Query Bar */}
                                    <div className="sticky top-0 z-20 bg-[#F9F7F1]/95 backdrop-blur-sm border-b border-gray-100 py-4 px-4 mb-6 transition-all">
                                        <div className="flex items-center gap-3 max-w-5xl mx-auto">
                                            <div className="flex-1 bg-white border border-gray-100 shadow-sm rounded-full px-4 py-2 flex items-center gap-3">
                                                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                                <span className="font-medium text-sm truncate flex-1 text-gray-700">{topic}</span>
                                            </div>
                                            <a
                                                href={generatedVideo}
                                                download
                                                className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 font-bold text-sm border border-gray-200 hover:bg-gray-50 transition-all rounded-full"
                                            >
                                                Download
                                            </a>
                                            <button
                                                onClick={() => { setGeneratedVideo(null); setTopic(''); }}
                                                className="flex items-center gap-2 px-4 py-2 bg-black text-white font-bold text-sm hover:bg-gray-800 transition-all rounded-full shadow-md hover:shadow-lg"
                                            >
                                                <Plus size={16} />
                                                New Video
                                            </button>
                                        </div>
                                    </div>

                                    {/* Video Display */}
                                    <div className="w-full max-w-5xl mx-auto px-4 animate-fade-in-up pb-12">
                                        <div className="w-full aspect-video bg-black rounded-2xl shadow-2xl overflow-hidden relative ring-1 ring-black/5">
                                            <video src={generatedVideo} controls autoPlay className="w-full h-full" />
                                        </div>
                                    </div>
                                </div>
                            )}

                        </div>
                    )}

                    {/* --- VIEW: CATEGORY (TRENDING) & LIBRARY --- */}
                    {/* --- VIEW: CATEGORY (TRENDING) & LIBRARY --- */}
                    {currentView !== 'home' && (
                        <div className="p-8">
                            {/* Page Header */}
                            <div className="flex items-end justify-between mb-8">
                                <div>
                                    <h1 className="text-3xl font-bold font-serif-brand mb-2 tracking-tight text-gray-900">
                                        {currentView === 'category' ? 'Categories' : 'My Library'}
                                    </h1>
                                    {currentView === 'library' && (
                                        <p className="text-gray-500 text-sm">
                                            Your personal collection.
                                        </p>
                                    )}
                                </div>
                            </div>

                            {/* Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
                                {videosToDisplay.map(video => (
                                    <VideoCard key={video.id} video={video} onClick={() => currentView === 'library' ? handleLibraryClick(video) : setSelectedVideo(video)} />
                                ))}
                            </div>
                        </div>
                    )}

                </div>
                {/* Video Player Modal */}
                {
                    selectedVideo && (
                        <div
                            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8"
                            onClick={() => setSelectedVideo(null)}
                        >
                            <div
                                className="w-full max-w-5xl bg-black rounded-2xl overflow-hidden shadow-2xl"
                                onClick={e => e.stopPropagation()}
                            >
                                {/* Close Button */}
                                <div className="flex items-center justify-between p-4 bg-gray-900">
                                    <div>
                                        <h2 className="text-white font-bold text-lg">{selectedVideo.title}</h2>
                                        <p className="text-gray-400 text-sm">{selectedVideo.author} • {selectedVideo.views} views</p>
                                    </div>
                                    <button
                                        onClick={() => setSelectedVideo(null)}
                                        className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
                                    >
                                        <span className="text-white text-xl">×</span>
                                    </button>
                                </div>
                                {/* Video Player */}
                                <div className="aspect-video w-full">
                                    <video
                                        src={selectedVideo.url}
                                        controls
                                        autoPlay
                                        className="w-full h-full"
                                    />
                                </div>
                            </div>
                        </div>
                    )
                }
            </main >
        </div >
    );
};

// --- Helper Components ---

const SidebarItem: React.FC<{ icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }> = ({ icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${active
            ? 'bg-white text-black font-bold shadow-sm ring-1 ring-gray-200'
            : 'text-gray-500 hover:bg-gray-100/50 hover:text-black'
            }`}
    >
        <div className={active ? "text-black" : "text-gray-400"}>{icon}</div>
        <span className="text-sm font-medium">{label}</span>
    </button>
);



const VideoCard: React.FC<{ video: VideoItem; onClick?: () => void }> = ({ video, onClick }) => (
    <div className={`group cursor-pointer flex flex-col h-full ${video.isLoading ? 'animate-pulse' : ''}`} onClick={!video.isLoading ? onClick : undefined}>
        <div className="aspect-video w-full rounded-xl bg-[#FDFCF9] relative overflow-hidden shadow-sm group-hover:shadow-md transition-all border border-gray-100">
            {video.isLoading ? (
                <div className="w-full h-full flex flex-col items-center justify-center bg-gray-50">
                    <Loader2 className="w-8 h-8 text-black animate-spin mb-2" />
                    <span className="text-xs font-medium text-gray-500">{video.progressStatus || "Cooking..."}</span>
                </div>
            ) : (
                video.url ? (
                    <video
                        src={video.url}
                        className="w-full h-full object-cover"
                        controls={false}
                        onMouseOver={e => (e.target as HTMLVideoElement).play()}
                        onMouseOut={e => (e.target as HTMLVideoElement).pause()}
                        muted
                        loop
                        poster={video.image}
                    />
                ) : (
                    <img src={video.image} alt={video.title} className="w-full h-full object-contain p-6 opacity-95 group-hover:opacity-100 transition-opacity group-hover:scale-105 duration-500" />
                )
            )}

            {!video.isLoading && (
                <>
                    {/* Play button overlay */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20">
                        <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform">
                            <Play className="w-5 h-5 text-black fill-black ml-0.5" />
                        </div>
                    </div>
                    <div className="absolute bottom-2 right-2 bg-black/70 backdrop-blur-md text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md">
                        {video.duration}
                    </div>
                </>
            )}
        </div>
        <div className="mt-3 flex gap-3">
            <div className="w-8 h-8 shrink-0 bg-gray-100 rounded-full overflow-hidden">
                {video.isLoading ? (
                    <div className="w-full h-full bg-gray-200"></div>
                ) : (
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${video.author}`} alt="Avatar" className="w-full h-full" />
                )}
            </div>
            <div className="flex-1 min-w-0">
                <h3 className="font-bold text-sm leading-tight line-clamp-2 group-hover:text-black transition-colors">
                    {video.title}
                </h3>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    <span>{video.author}</span>
                    {!video.isLoading && (
                        <>
                            <span>•</span>
                            <span>{video.views}</span>
                        </>
                    )}
                </div>
            </div>
        </div>
    </div>
);

interface CustomVoiceSelectProps {
    voice: string;
    setVoice: (voice: string) => void;
    voicesList: Record<string, string>;
    disabled: boolean;
}

const CustomVoiceSelect: React.FC<CustomVoiceSelectProps> = ({ voice, setVoice, voicesList, disabled }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const dropdownRef = React.useRef<HTMLDivElement>(null);

    const filteredVoices = Object.keys(voicesList).filter(v =>
        v.toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-bold transition-all ${voice ? 'bg-black text-white border-black' : 'bg-white hover:bg-gray-50'
                    } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                <Mic size={14} className={voice ? "text-white" : "text-gray-500"} />
                <span className="max-w-[100px] truncate">{voice || "Select Voice"}</span>
            </button>

            {isOpen && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-white border border-gray-100 shadow-xl z-50 max-h-48 flex flex-col rounded-xl overflow-hidden animate-fade-in-up origin-top-left">
                    <div className="p-2 border-b border-gray-50 bg-gray-50/50">
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search voices..."
                            className="w-full bg-white border border-gray-200 rounded-md px-2 py-1 outline-none text-xs focus:ring-1 ring-black/10"
                            autoFocus
                        />
                    </div>
                    <div className="overflow-y-auto flex-1 p-1">
                        {filteredVoices.length > 0 ? filteredVoices.map(v => (
                            <button
                                key={v}
                                onClick={() => {
                                    setVoice(v);
                                    setIsOpen(false);
                                    setSearchTerm("");
                                }}
                                className={`w-full text-left px-2 py-1.5 text-xs font-medium rounded-md hover:bg-gray-100 transition-colors truncate ${voice === v ? 'bg-black/5 text-black' : 'text-gray-600'
                                    }`}
                            >
                                {v}
                            </button>
                        )) : (
                            <div className="p-3 text-center text-xs text-gray-400">
                                No voices found
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

interface ChipSelectProps {
    value: string;
    onChange: (value: string) => void;
    icon: React.ReactNode;
    options: { value: string; label: string }[];
}

const ChipSelect: React.FC<ChipSelectProps> = ({ value, onChange, icon, options }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = React.useRef<HTMLDivElement>(null);
    const selectedLabel = options.find(o => o.value === value)?.label || value;

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-bold transition-all bg-white text-gray-700 hover:bg-gray-50"
            >
                {icon}
                <span>{selectedLabel}</span>
            </button>
            {isOpen && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-white border border-gray-100 shadow-xl z-50 flex flex-col rounded-xl overflow-hidden animate-fade-in-up origin-top-left max-h-60">
                    <div className="flex flex-col p-1 overflow-y-auto">
                        {options.map(opt => (
                            <button
                                key={opt.value}
                                onClick={() => {
                                    onChange(opt.value);
                                    setIsOpen(false);
                                }}
                                className={`w-full text-left px-4 py-2.5 text-xs font-medium rounded-md hover:bg-gray-100 transition-colors ${value === opt.value ? 'bg-black/5 text-black' : 'text-gray-600'
                                    }`}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardSection;