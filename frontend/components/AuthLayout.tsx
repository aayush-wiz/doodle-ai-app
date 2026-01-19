import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout: React.FC = () => {
    return (
        <div className="flex h-screen w-full bg-[#FAFAF9]">
            {/* Left Side - Image */}
            <div className="hidden lg:flex lg:w-1/2 relative bg-[#F9F7F1] items-center justify-center p-12">
                <div className="relative w-full max-w-lg aspect-square">
                    <img
                        src="/images/heroimage.png"
                        alt="Branding"
                        className="object-contain w-full h-full drop-shadow-2xl"
                    />
                </div>
            </div>

            {/* Right Side - Form */}
            <div className="flex-1 flex flex-col justify-center items-center p-8 bg-white">
                <div className="w-full max-w-md">
                    <Outlet />
                </div>
            </div>
        </div>
    );
};

export default AuthLayout;
