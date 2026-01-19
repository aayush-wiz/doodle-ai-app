import React, { useState, useCallback, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import ShowcaseSection from './components/ShowcaseSection';
import DashboardSection from './components/DashboardSection';
import AuthLayout from './components/AuthLayout';
import Login from './components/Login';
import Register from './components/Register';
import Library from './components/Library';
import ApiDocumentation from './components/ApiDocumentation';
import GuidedLearning from './components/GuidedLearning';

const DEFAULT_HERO_BG = "/images/heroimage.png";
const DEFAULT_SHOWCASE_BG = "/showcase-bw.png";

import PricingSection from './components/PricingSection';
import FeaturesSection from './components/FeaturesSection';
import Footer from './components/Footer';

import VideoGridSection from './components/VideoGridSection';

// Landing Page Component (Extracted from original App)
const LandingPage = () => {
  const navigate = useNavigate();
  const [heroBg, setHeroBg] = useState<string>(DEFAULT_HERO_BG);
  const [showcaseBg, setShowcaseBg] = useState<string>(DEFAULT_SHOWCASE_BG);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    setHeroBg(DEFAULT_HERO_BG);
    setShowcaseBg(DEFAULT_SHOWCASE_BG);
  }, []);

  const handleGenerateTheme = useCallback(async () => {
    // Gemini theme generation removed as per user request
    console.log("Theme generation is currently disabled.");
  }, []);

  const handleLaunchApp = () => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <main className="w-full min-h-screen relative bg-[#F9F7F1] font-sans selection:bg-black selection:text-white">
      <Navbar onConsoleClick={handleLaunchApp} />
      <HeroSection
        mainImage={heroBg}
        secondaryImage={showcaseBg}
        isGenerating={isGenerating}
        onGenerate={handleGenerateTheme}
      />
      <VideoGridSection />
      <ShowcaseSection backgroundImage={showcaseBg} />
      <FeaturesSection />
      <PricingSection />
      <Footer />
    </main>
  );
};

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />

        {/* API Documentation */}
        <Route path="/api" element={<ApiDocumentation />} />

        {/* Guided Learning */}
        <Route path="/guided-learning" element={<GuidedLearning />} />

        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        {/* Protected App Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardSection />
          </ProtectedRoute>
        } />

        <Route path="/library" element={
          <ProtectedRoute>
            <Library />
          </ProtectedRoute>
        } />

      </Routes>
    </BrowserRouter>
  );
};

export default App;