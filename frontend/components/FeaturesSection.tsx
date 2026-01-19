import React from 'react';

const features = [
    {
        image: "/images/feature-edu.png",
        title: "Education",
        description: "Transform lectures into engaging visual stories. Perfect for teachers, students, and lifelong learners."
    },
    {
        image: "/images/feature-biz.png",
        title: "Business",
        description: "Professional presentations and data storytelling. Clarify complex ideas for team meetings and sales pitches."
    },
    {
        image: "/images/feature-content.png",
        title: "Social Media",
        description: "Captivating content for TikTok, Instagram, and YouTube. Stand out with unique AI doodles and voiceovers."
    }
];

const FeaturesSection: React.FC = () => {
    return (
        <section className="py-24 px-6 md:px-12 bg-[#F9F7F1]">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-serif-brand font-bold text-gray-900 mb-4 tracking-tight">Professional for Every Domain</h2>
                    <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                        Whether you're in the classroom, the boardroom, or on social media, we've got you covered.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {features.map((feature, idx) => (
                        <div key={idx} className="flex flex-col rounded-3xl bg-white border border-gray-100 overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 group">
                            <div className="aspect-square bg-[#F9F7F1] overflow-hidden">
                                <img
                                    src={feature.image}
                                    alt={feature.title}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                />
                            </div>
                            <div className="p-8">
                                <h3 className="text-2xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                                <p className="text-gray-600 leading-relaxed text-sm">
                                    {feature.description}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default FeaturesSection;
