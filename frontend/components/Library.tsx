import React, { useEffect, useState } from 'react';
import { Play } from 'lucide-react';
import Navbar from './Navbar';
import { getAllVideos, Video as DBVideo } from '../lib/db';

// Note: This component shows ALL videos (not user-specific)
// For user-specific, you'd need to pass userId or get from context

const Library: React.FC = () => {
    const [videos, setVideos] = useState<DBVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchVideos();
    }, []);

    const fetchVideos = async () => {
        try {
            // Direct Neon query - no backend needed
            const data = await getAllVideos();
            setVideos(data);
        } catch (err: any) {
            console.error('Failed to fetch videos from Neon:', err);
            setError(err.message || 'Failed to load videos');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F9F7F1]">
            <Navbar onConsoleClick={() => { }} />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">My Library</h1>

                {loading ? (
                    <div className="text-center py-12">Loading...</div>
                ) : error ? (
                    <div className="text-center text-red-500 py-12">{error}</div>
                ) : videos.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">No videos yet. Generate something!</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {videos.map((video) => (
                            <div key={video.id} className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 hover:shadow-md transition-shadow">
                                <div className="aspect-video bg-gray-100 relative group">
                                    <video
                                        src={video.url}
                                        controls
                                        className="w-full h-full object-cover"
                                        poster="/images/heroimage.png"
                                    />
                                </div>
                                <div className="p-4">
                                    <h3 className="font-semibold text-gray-900 truncate">{video.title}</h3>
                                    <p className="text-sm text-gray-500 mt-1">
                                        {new Date(video.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Library;
