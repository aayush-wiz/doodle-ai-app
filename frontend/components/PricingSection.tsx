import React from 'react';
import { Check } from 'lucide-react';

const pricingTiers = [
    {
        name: 'Free',
        price: '$0',
        description: 'Perfect for trying out the magic.',
        features: [
            '3 Videos per month',
            'Standard Voices',
            '720p Export Quality',
            'Watermarked'
        ],
        cta: 'Get Started',
        highlighted: false
    },
    {
        name: 'Pro',
        price: '$29',
        period: '/mo',
        description: 'For creators and educators.',
        features: [
            'Unlimited Videos',
            'Premium AI Voices (Cloning)',
            '4K Export Quality',
            'No Watermark',
            'Commercial Usage Rights'
        ],
        cta: 'Upgrade to Pro',
        highlighted: true
    },
    {
        name: 'Enterprise',
        price: 'Custom',
        description: 'For teams and organizations.',
        features: [
            'API Access',
            'Dedicated Support',
            'Custom Branding',
            'SSO & Security'
        ],
        cta: 'Contact Sales',
        highlighted: false
    }
];

const PricingSection: React.FC = () => {
    return (
        <section className="py-24 px-6 md:px-12 bg-white border-t border-gray-100">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-serif-brand font-bold text-gray-900 mb-4 tracking-tight">Simple Pricing</h2>
                    <p className="text-lg text-gray-500 max-w-2xl mx-auto">
                        Start for free and scale as you create. No hidden fees.
                    </p>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {pricingTiers.map((tier) => (
                        <div
                            key={tier.name}
                            className={`relative rounded-3xl p-8 flex flex-col transition-all duration-300 ${tier.highlighted
                                ? 'bg-black text-white shadow-2xl scale-105 z-10'
                                : 'bg-gray-50 text-gray-900 border border-gray-100 hover:shadow-lg hover:scale-[1.02]'
                                }`}
                        >
                            {tier.highlighted && (
                                <div className="absolute top-0 right-0 left-0 -mt-4 text-center">
                                    <span className="bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                                        Most Popular
                                    </span>
                                </div>
                            )}

                            <div className="mb-8">
                                <h3 className={`text-xl font-bold mb-2 ${tier.highlighted ? 'text-gray-100' : 'text-gray-900'}`}>{tier.name}</h3>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-4xl font-bold">{tier.price}</span>
                                    {tier.period && <span className={`text-sm ${tier.highlighted ? 'text-gray-400' : 'text-gray-500'}`}>{tier.period}</span>}
                                </div>
                                <p className={`mt-4 text-sm ${tier.highlighted ? 'text-gray-400' : 'text-gray-500'}`}>
                                    {tier.description}
                                </p>
                            </div>

                            <ul className="flex-1 space-y-4 mb-8">
                                {tier.features.map((feature) => (
                                    <li key={feature} className="flex items-center gap-3 text-sm">
                                        <div className={`rounded-full p-1 ${tier.highlighted ? 'bg-gray-800' : 'bg-gray-200'}`}>
                                            <Check size={12} className={tier.highlighted ? 'text-white' : 'text-black'} />
                                        </div>
                                        <span className={tier.highlighted ? 'text-gray-200' : 'text-gray-700'}>{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={`w-full py-4 px-6 rounded-xl font-bold text-sm transition-colors ${tier.highlighted
                                    ? 'bg-white text-black hover:bg-gray-200'
                                    : 'bg-black text-white hover:bg-gray-800'
                                    } ${tier.name !== 'Free' ? 'cursor-not-allowed opacity-70' : ''}`}
                                disabled={tier.name !== 'Free'}
                            >
                                {tier.name === 'Free' ? tier.cta : 'Coming Soon'}
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default PricingSection;
