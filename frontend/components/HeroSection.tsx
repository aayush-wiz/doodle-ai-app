import React from 'react';
import { ArrowRight, ArrowUp } from 'lucide-react';

interface HeroSectionProps {
    mainImage: string;
    secondaryImage: string;
    isGenerating: boolean;
    onGenerate: () => void;
}

const HeroSection: React.FC<HeroSectionProps> = ({ mainImage, isGenerating, onGenerate }) => {

    // Typewriter Effect State
    const [placeholderText, setPlaceholderText] = React.useState('');
    const [phraseIndex, setPhraseIndex] = React.useState(0);
    const [isDeleting, setIsDeleting] = React.useState(false);

    const phrases = [
        "What is a black hole?",
        "Explain quantum mechanics...",
        "The history of the Roman Empire",
        "How do airplanes fly?",
        "Describe the photosynthesis process"
    ];

    React.useEffect(() => {
        const currentPhrase = phrases[phraseIndex];
        const typeSpeed = isDeleting ? 50 : 100; // Warning: fast delete, slow type

        const timer = setTimeout(() => {
            if (!isDeleting && placeholderText === currentPhrase) {
                // Finished typing, wait then delete
                setTimeout(() => setIsDeleting(true), 2000);
            } else if (isDeleting && placeholderText === '') {
                // Finished deleting, next phrase
                setIsDeleting(false);
                setPhraseIndex((prev) => (prev + 1) % phrases.length);
            } else {
                // Typing or Deleting characters
                setPlaceholderText(prev =>
                    isDeleting ? currentPhrase.substring(0, prev.length - 1) : currentPhrase.substring(0, prev.length + 1)
                );
            }
        }, typeSpeed);

        return () => clearTimeout(timer);
    }, [placeholderText, isDeleting, phraseIndex]);

    return (
        <div className="relative w-full min-h-screen bg-[#F9F7F1] text-black overflow-hidden flex flex-col justify-end pb-20 font-sans">

            {/* Background Video */}
            <div className="absolute top-0 left-0 w-full h-[65vh] z-0 overflow-hidden pointer-events-none">
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    className="w-full h-full object-cover object-top opacity-40 mix-blend-multiply"
                >
                    <source src="/video/mathematics.mp4" type="video/mp4" />
                </video>
                {/* Gradient Overlay for smooth fade into background */}
                <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-[#F9F7F1] to-transparent"></div>
            </div>



            {/* Content Container (Image + Text) */}
            <div className="flex flex-col md:flex-row items-end justify-center w-full max-w-6xl px-4 gap-12 relative z-10 h-full">

                {/* 2. Doodle Illustration ( anchored to bottom via items-end ) */}
                <div className="w-full md:w-1/2 h-[45vh] flex items-end justify-center md:justify-end pb-0">
                    <img
                        src={mainImage}
                        alt="Confusion Doodle"
                        className="h-full object-contain object-bottom"
                    />
                </div>

                {/* 3. Text Description ( Decoupled: Centered & Moved Up ) */}
                <div className="w-full md:w-1/2 flex flex-col items-center text-center self-center mb-24 md:mb-32">

                    <h1 className="text-4xl md:text-5xl font-serif-brand font-bold text-gray-900 mb-6 tracking-tight leading-tight">
                        The trouble with<br />thinking big.
                    </h1>
                    <p className="text-base font-medium text-gray-700 leading-relaxed mb-6 max-w-2xl mx-auto">
                        Turn complex ideas into clear, engaging explanatory videos in seconds. No design skills needed—just your creativity and our AI.
                    </p>

                    {/* Input Box (Dream Machine Style - Tall) */}
                    <div className="w-full max-w-2xl mb-8 relative group font-sans mx-auto">
                        <div className="bg-white rounded-[2rem] shadow-2xl p-5 h-40 flex flex-col justify-between transition-transform transform group-hover:-translate-y-1 duration-300 relative z-20">
                            <textarea
                                placeholder={placeholderText}
                                className="w-full h-full bg-transparent border-none outline-none text-gray-800 placeholder-gray-400 text-lg font-medium resize-none p-1 text-left"
                            />
                            <div className="absolute bottom-4 right-4 group/tooltip">
                                <button
                                    disabled
                                    className="bg-black/50 text-white w-10 h-10 flex items-center justify-center rounded-full transition-all shadow-lg cursor-not-allowed"
                                >
                                    <ArrowUp size={20} strokeWidth={2.5} />
                                </button>

                                {/* Tooltip */}
                                <div className="absolute bottom-full right-0 mb-3 w-64 p-3 bg-black text-white text-xs font-medium rounded-xl shadow-xl opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-200 z-30 pointer-events-none text-center">
                                    We are working on getting our server endpoint ready. We will soon be available.
                                    <div className="absolute top-full right-4 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-black"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default HeroSection;