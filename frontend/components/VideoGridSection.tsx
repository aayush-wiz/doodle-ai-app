import React from 'react';
import { Volume2, VolumeX, Play, Pause, Maximize2, X } from 'lucide-react';
import { useState, useRef } from 'react';

const FEATURED_VIDEO = "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/crousel1.mp4";

const GRID_VIDEOS = [
    "/video_pythagorean_theorem.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/coursel2.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/crousel3.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_e093f069_normal.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_00f0e35a_normal.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_0b0234a9_normal.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_0f493bf6_normal.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_6d67d7cf_normal.mp4",
    "https://pub-612f51ca88124ba3a54a8e01c27ff576.r2.dev/video_e093f069_normal.mp4"
];

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

const VideoGridSection: React.FC = () => {
    const [selectedVideo, setSelectedVideo] = useState<string | null>(null);

    return (
        <section className="py-24 bg-[#F9F7F1]">
            <div className="max-w-[1400px] mx-auto px-6 md:px-12">

                {/* 1. DOODLE CREATIONS SECTION */}
                <div className="mb-24">
                    <div className="mb-12 border-b border-black/10 pb-6 flex flex-col md:flex-row justify-between items-end gap-6">
                        <div>
                            <h3 className="text-gray-400 font-light tracking-widest text-sm uppercase mb-2">
                                AI Generated Content
                            </h3>
                            <h2 className="text-5xl md:text-6xl font-serif-brand font-bold tracking-tight text-black mix-blend-multiply">
                                DOODLE CREATIONS
                            </h2>
                        </div>
                        <p className="text-gray-500 max-w-sm text-sm leading-relaxed text-right md:text-left">
                            Explore the possibilities of AI-driven animation. From rough sketches to polished motion graphics in seconds.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-12">
                        {DOODLE_VIDEOS.map((video, index) => (
                            <div key={index} className="group cursor-pointer flex flex-col gap-4">
                                <div className="relative aspect-video bg-gray-100 overflow-hidden">
                                    {/* Simple refined border/shadow */}
                                    <div className="absolute inset-0 border border-black/5 z-20 pointer-events-none transition-colors group-hover:border-black/20"></div>

                                    <VideoPlayer
                                        url={video.url}
                                        className="object-cover transform transition-transform duration-700 group-hover:scale-105"
                                        onExpand={() => setSelectedVideo(video.url)}
                                    />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold tracking-wide uppercase text-black group-hover:text-blue-600 transition-colors">
                                        {video.title}
                                    </h4>
                                    <span className="text-xs text-gray-400 font-mono mt-1 block">
                                        0{index + 1} / GEN AI
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 2. CORPORATE TRAINING SECTION */}
                <div className="mb-24">
                    <div className="mb-12 border-b border-black/10 pb-6 flex flex-col md:flex-row justify-between items-end gap-6">
                        <div>
                            <h3 className="text-blue-500 font-bold tracking-widest text-sm uppercase mb-2">
                                Enterprise Solutions
                            </h3>
                            <h2 className="text-5xl md:text-6xl font-serif-brand font-bold tracking-tight text-black mix-blend-multiply">
                                CORPORATE TRAINING
                            </h2>
                        </div>
                        <p className="text-gray-500 max-w-sm text-sm leading-relaxed text-right md:text-left">
                            Specialized compliance and safety modules generated on-demand. Consistent quality, strictly adhered guidelines.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-12">
                        {TRAINING_VIDEOS.map((video, index) => (
                            <div key={index} className="group cursor-pointer flex flex-col gap-4">
                                <div className="relative aspect-video bg-gray-100 overflow-hidden">
                                    <div className="absolute inset-0 border border-black/5 z-20 pointer-events-none transition-colors group-hover:border-blue-500/30"></div>
                                    <VideoPlayer
                                        url={video.url}
                                        className="object-cover transform transition-transform duration-700 group-hover:scale-105"
                                        onExpand={() => setSelectedVideo(video.url)}
                                    />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold tracking-wide uppercase text-black group-hover:text-blue-600 transition-colors">
                                        {video.title}
                                    </h4>
                                    <span className="text-xs text-gray-400 font-mono mt-1 block">
                                        DEMO 0{index + 1} / SAFETY
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 3. CARTOON / ENTERTAINMENT SECTION */}
                <div>
                    <div className="mb-12 border-b border-black/10 pb-6 flex flex-col md:flex-row justify-between items-end gap-6">
                        <div>
                            <h3 className="text-purple-500 font-bold tracking-widest text-sm uppercase mb-2">
                                Creative Storytelling
                            </h3>
                            <h2 className="text-5xl md:text-6xl font-serif-brand font-bold tracking-tight text-black mix-blend-multiply">
                                CARTOON & <span className="font-bold">FUN</span>
                            </h2>
                        </div>
                        <p className="text-gray-500 max-w-sm text-sm leading-relaxed text-right md:text-left">
                            Engaging vibrant styles for entertainment, social media, and children's content.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-12">
                        {CARTOON_VIDEOS.map((video, index) => (
                            <div key={index} className="group cursor-pointer flex flex-col gap-4">
                                <div className="relative aspect-video bg-gray-100 overflow-hidden">
                                    <div className="absolute inset-0 border border-black/5 z-20 pointer-events-none transition-colors group-hover:border-purple-500/30"></div>
                                    <VideoPlayer
                                        url={video.url}
                                        className="object-cover transform transition-transform duration-700 group-hover:scale-105"
                                        onExpand={() => setSelectedVideo(video.url)}
                                    />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold tracking-wide uppercase text-black group-hover:text-blue-600 transition-colors">
                                        {video.title}
                                    </h4>
                                    <span className="text-xs text-gray-400 font-mono mt-1 block">
                                        EPISODE 0{index + 1} / TOON
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>

            {/* Video Modal */}
            {selectedVideo && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/95 backdrop-blur-sm p-4 animate-in fade-in duration-300">
                    <button
                        onClick={() => setSelectedVideo(null)}
                        className="fixed top-8 right-8 p-3 hover:bg-black hover:text-white transition-colors rounded-full z-50 group"
                    >
                        <X className="w-8 h-8 text-black group-hover:text-white transition-colors" />
                    </button>
                    <div className="relative w-full max-w-7xl aspect-video bg-black shadow-2xl overflow-hidden">
                        <VideoPlayer url={selectedVideo} className="object-contain" />
                    </div>
                </div>
            )}
        </section>
    );
};

interface VideoPlayerProps {
    url: string;
    className?: string; // Allow passing object-fit classes
    onExpand?: () => void;
}

const VideoPlayer = ({ url, className = "object-contain", onExpand }: VideoPlayerProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(true);
    const [isMuted, setIsMuted] = useState(true);

    const togglePlay = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const toggleMute = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (videoRef.current) {
            videoRef.current.muted = !isMuted;
            setIsMuted(!isMuted);
        }
    };

    const handleExpand = (e: React.MouseEvent) => {
        e.stopPropagation();
        onExpand?.();
    };

    return (
        <div className="relative w-full h-full group cursor-pointer" onClick={togglePlay}>
            <video
                ref={videoRef}
                src={url}
                muted={isMuted}
                loop
                autoPlay
                playsInline
                className={`w-full h-full ${className}`}
            />

            {/* Controls Overlay */}
            <div className="absolute bottom-3 left-3 flex gap-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button
                    onClick={toggleMute}
                    className="p-1.5 bg-white/90 hover:bg-white text-black rounded-full shadow-lg transition-transform hover:scale-105 border border-black/10"
                >
                    {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </button>
                <div className="p-1.5 bg-white/90 text-black rounded-full shadow-lg border border-black/10">
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </div>
            </div>

            {/* Expand Button */}
            {onExpand && (
                <div className="absolute top-3 right-3 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <button
                        onClick={handleExpand}
                        className="p-1.5 bg-white/90 hover:bg-white text-black rounded-full shadow-lg transition-transform hover:scale-105 border border-black/10"
                    >
                        <Maximize2 className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Center Play Button (only when paused) */}
            {!isPlaying && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-black/20">
                    <div className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center shadow-xl border border-black/10">
                        <Play className="w-6 h-6 text-black fill-black ml-1" />
                    </div>
                </div>
            )}
        </div>
    );
};

export default VideoGridSection;
