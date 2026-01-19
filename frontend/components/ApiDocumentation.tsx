import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Copy, Check, Menu, X, BookOpen, GraduationCap, School, Sparkles } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ApiDocumentation: React.FC = () => {
  const navigate = useNavigate();
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('overview');

  useEffect(() => {
    const handleScroll = () => {
      const sections = ['overview', 'educational', 'training', 'cartoon'];
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = document.getElementById(section);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setMobileMenuOpen(false);
    }
  };

  const CodeBlock = ({ code, language = 'python', id }: { code: string; language?: string; id: string }) => {
    // Custom dark theme matching pure black background
    const customStyle = {
      ...vscDarkPlus,
      'pre[class*="language-"]': {
        ...vscDarkPlus['pre[class*="language-"]'],
        background: '#000000',
        border: '1px solid #171717',
        borderRadius: '0.5rem',
        padding: '1rem',
        margin: 0,
      },
      'code[class*="language-"]': {
        ...vscDarkPlus['code[class*="language-"]'],
        background: '#000000',
        color: '#d4d4d4',
        fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
        fontSize: '0.875rem',
        lineHeight: '1.5',
      },
    };

    return (
      <div className="relative group">
        <div className="absolute top-2 right-2 z-10">
          <button
            onClick={() => copyToClipboard(code, id)}
            className="p-2 bg-black hover:bg-gray-900 rounded text-gray-400 hover:text-white transition-colors border border-gray-900"
            title="Copy code"
          >
            {copiedCode === id ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
        <div className="rounded-lg overflow-hidden border border-gray-900">
          <SyntaxHighlighter
            language={language}
            style={customStyle}
            customStyle={{
              margin: 0,
              padding: '1rem',
              background: '#000000',
              borderRadius: '0.5rem',
            }}
            showLineNumbers={false}
            wrapLines={true}
            wrapLongLines={true}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      </div>
    );
  };

  const ParameterTable = ({ parameters }: { parameters: Array<{
    name: string;
    type: string;
    required: boolean;
    default?: string;
    description: string;
    values?: string;
  }> }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-gray-900">
            <th className="text-left py-3 px-4 text-gray-200 font-semibold">Parameter</th>
            <th className="text-left py-3 px-4 text-gray-200 font-semibold">Type</th>
            <th className="text-left py-3 px-4 text-gray-200 font-semibold">Required</th>
            <th className="text-left py-3 px-4 text-gray-200 font-semibold">Default</th>
            <th className="text-left py-3 px-4 text-gray-200 font-semibold">Description</th>
          </tr>
        </thead>
        <tbody>
          {parameters.map((param, idx) => (
            <tr key={idx} className="border-b border-gray-900 hover:bg-gray-900/30 transition-colors">
              <td className="py-3 px-4">
                <code className="text-blue-400 font-mono text-sm">{param.name}</code>
              </td>
              <td className="py-3 px-4 text-gray-400 text-sm">{param.type}</td>
              <td className="py-3 px-4">
                {param.required ? (
                  <span className="text-red-400 text-sm">Required</span>
                ) : (
                  <span className="text-gray-500 text-sm">Optional</span>
                )}
              </td>
              <td className="py-3 px-4 text-gray-500 text-sm font-mono">
                {param.default || '—'}
              </td>
              <td className="py-3 px-4 text-gray-200 text-sm">
                {param.description}
                {param.values && (
                  <div className="mt-1 text-gray-500 text-xs">
                    <strong>Values:</strong> {param.values}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="min-h-screen bg-black text-white w-full">
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-40 border-b border-gray-900 bg-black/95 backdrop-blur-sm">
        <div className="w-full px-6 md:px-12">
          <div className="flex items-center justify-between h-16">
            <button className="text-white text-sm font-medium">
              Documentation
            </button>
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors"
            >
              <span className="text-xl font-bold">chytr</span>
            </button>
          </div>
        </div>
      </nav>

      <div className="flex w-full">
        {/* Left Sidebar */}
        <aside className="hidden lg:block w-64 border-r border-gray-900 bg-black h-[calc(100vh-4rem)] sticky top-16 overflow-y-auto">
          <nav className="p-6 space-y-6">
            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Overview</h3>
              <button
                onClick={() => scrollToSection('overview')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  activeSection === 'overview'
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-900/30'
                }`}
              >
                API Reference
              </button>
            </div>

            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Video Generation</h3>
              <div className="space-y-1">
                <button
                  onClick={() => scrollToSection('educational')}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                    activeSection === 'educational'
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-900/50'
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  Educational API
                </button>
                <button
                  onClick={() => scrollToSection('training')}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                    activeSection === 'training'
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-900/50'
                  }`}
                >
                  <School className="w-4 h-4" />
                  Training API
                </button>
                <button
                  onClick={() => scrollToSection('cartoon')}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                    activeSection === 'cartoon'
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-900/50'
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  Cartoon Fun Doodle API
                </button>
              </div>
            </div>
          </nav>
        </aside>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden fixed top-20 left-4 z-50 p-2 bg-black rounded-md text-gray-300 hover:text-white border border-gray-900"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Mobile Sidebar */}
        {mobileMenuOpen && (
          <aside className="lg:hidden fixed inset-0 z-40 bg-black/95 backdrop-blur-sm">
            <nav className="p-6 space-y-6 pt-20">
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Overview</h3>
                <button
                  onClick={() => scrollToSection('overview')}
                  className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-gray-900"
                >
                  API Reference
                </button>
              </div>
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Video Generation</h3>
                <div className="space-y-1">
                  <button
                    onClick={() => scrollToSection('educational')}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-gray-900 flex items-center gap-2"
                  >
                    <GraduationCap className="w-4 h-4" />
                    Educational API
                  </button>
                  <button
                    onClick={() => scrollToSection('training')}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-gray-900 flex items-center gap-2"
                  >
                    <School className="w-4 h-4" />
                    Training API
                  </button>
                  <button
                    onClick={() => scrollToSection('cartoon')}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-gray-900 flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    Cartoon Fun Doodle API
                  </button>
                </div>
              </div>
            </nav>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <div className="w-full px-6 md:px-12 py-12">
            {/* Overview Section */}
            <section id="overview" className="mb-16">
              <div className="mb-4">
                <div className="flex items-center gap-4 mb-4">
                  <h1 className="text-5xl font-bold text-white">API Reference</h1>
                  <span className="px-4 py-1.5 bg-yellow-500/20 border border-yellow-500/50 rounded-full text-yellow-400 text-sm font-medium">
                    Launching Soon
                  </span>
                </div>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
                <p className="text-yellow-400 text-sm">
                  <strong className="text-yellow-300">Note:</strong> The Chytr API is currently under development and will be launching soon. 
                  This documentation is provided for preview purposes. The API endpoints are not yet publicly available.
                </p>
              </div>
              <p className="text-xl text-gray-400 mb-8">Complete guide to Chytr video generation APIs</p>
              <div className="hidden md:flex items-center gap-2">
                <button className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-900 rounded-lg hover:border-gray-800 transition-colors flex items-center gap-2">
                  <Copy className="w-4 h-4" />
                  Copy page
                </button>
              </div>

              <div className="mb-12">
                <h2 className="text-2xl font-semibold text-white mb-4">Welcome to Chytr API</h2>
                <p className="text-gray-200 mb-6">
                  Chytr provides three powerful APIs for video generation, each optimized for different use cases:
                </p>

                <div className="grid md:grid-cols-3 gap-6 mb-12">
                  <div className="bg-black border border-gray-900 rounded-lg p-6 hover:border-gray-800 transition-colors">
                    <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4">
                      <GraduationCap className="w-6 h-6 text-blue-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Educational</h3>
                    <p className="text-gray-400 text-sm">Whiteboard educational videos with flexible segmentation</p>
                  </div>

                  <div className="bg-black border border-gray-900 rounded-lg p-6 hover:border-gray-800 transition-colors">
                    <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center mb-4">
                      <School className="w-6 h-6 text-green-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Training</h3>
                    <p className="text-gray-400 text-sm">Corporate training modules with compliance-focused content</p>
                  </div>

                  <div className="bg-black border border-gray-900 rounded-lg p-6 hover:border-gray-800 transition-colors">
                    <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center mb-4">
                      <Sparkles className="w-6 h-6 text-purple-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Cartoon Fun</h3>
                    <p className="text-gray-400 text-sm">Simpsons-style fun educational content with character dialogue</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Educational API Section */}
            <section id="educational" className="mb-16 scroll-mt-20">
              <div className="border-b border-gray-900 pb-4 mb-8">
                <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                  <GraduationCap className="w-8 h-8 text-blue-400" />
                  Educational API
                </h2>
                <p className="text-gray-400">
                  Generate educational whiteboard videos with flexible segmentation for learning content
                </p>
              </div>

              <div className="space-y-8">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Description</h3>
                  <p className="text-gray-200 leading-relaxed">
                    The Educational API creates whiteboard-style educational videos optimized for learning content. 
                    It uses flexible segmentation (1-3 parts per beat) to adapt to different content types—single 
                    concepts, comparisons, or step-by-step processes. The API generates beat manifests, images, 
                    audio narration, and animated doodle videos that gradually reveal the content.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Function Signature</h3>
                  <CodeBlock
                    id="educational-signature"
                    code={`process_video_request(
    topic: str,
    style: str = "normal",
    voice: str | None = None,
    language: str | None = None,
    max_beats: int = 0
) -> str | None`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Parameters</h3>
                  <div className="bg-black">
                    <ParameterTable
                      parameters={[
                        {
                          name: 'topic',
                          type: 'string',
                          required: true,
                          description: 'The subject or topic for the educational video (e.g., "Black Hole", "Photosynthesis")',
                        },
                        {
                          name: 'style',
                          type: 'string',
                          required: false,
                          default: '"normal"',
                          description: 'Visual style for the images and doodle animation',
                          values: '"normal" (Black ink sketch), "solid" (Colorful infographic), "pencil" (Graphite pencil sketch)',
                        },
                        {
                          name: 'voice',
                          type: 'string | None',
                          required: false,
                          default: 'None',
                          description: 'ElevenLabs voice name or voice ID. If None, uses first available voice from account',
                        },
                        {
                          name: 'language',
                          type: 'string | None',
                          required: false,
                          default: 'None',
                          description: 'ISO 639-1 language code (e.g., "en", "hi", "es", "de", "fr", "ja", "zh"). Uses multilingual model for non-English',
                        },
                        {
                          name: 'max_beats',
                          type: 'int',
                          required: false,
                          default: '0',
                          description: 'Maximum number of beats/scenes to generate. If 0, generates all beats from manifest',
                        },
                      ]}
                    />
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Basic Usage</h3>
                  <CodeBlock
                    id="educational-basic"
                    code={`from generate_topic_video_v7_4_text_corrected import process_video_request

# Simple educational video
video_path = process_video_request(
    topic="Black Hole",
    style="normal",
    voice=None,
    language="en",
    max_beats=0
)

if video_path:
    print(f"Video generated: {video_path}")
else:
    print("Failed to generate video")`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Advanced Usage</h3>
                  <CodeBlock
                    id="educational-advanced"
                    code={`from generate_topic_video_v7_4_text_corrected import process_video_request

# Advanced educational video with all parameters
video_path = process_video_request(
    topic="Einstein's Theory of Relativity",
    style="pencil",  # Graphite pencil sketch style
    voice="Rachel",  # Use specific ElevenLabs voice
    language="hi",   # Hindi with English technical terms
    max_beats=5      # Limit to 5 beats for shorter video
)

if video_path:
    print(f"Educational video created: {video_path}")
else:
    print("Video generation failed")`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Setup</h3>
                  <p className="text-gray-200 mb-4">
                    Before using the API, set the following environment variables:
                  </p>
                  <CodeBlock
                    id="educational-setup"
                    code={`# Required API Keys
export OPENROUTER_API_KEY="your-openrouter-key"
export FAL_KEY="your-fal-key"
export ELEVEN_LABS_API_KEY="your-elevenlabs-key"`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Response</h3>
                  <p className="text-gray-200 mb-4">
                    Returns the file path to the generated video (MP4 format) or <code className="text-blue-400">None</code> if generation fails.
                  </p>
                  <CodeBlock
                    id="educational-response"
                    code={`# Example output path
# topic_videos_v7_4/black_hole_a1b2c3d4/video_a1b2c3d4_normal.mp4`}
                  />
                </div>
              </div>
            </section>

            {/* Training API Section */}
            <section id="training" className="mb-16 scroll-mt-20">
              <div className="border-b border-gray-900 pb-4 mb-8">
                <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                  <School className="w-8 h-8 text-green-400" />
                  Training API
                </h2>
                <p className="text-gray-400">
                  Generate corporate and industrial training modules with compliance-focused content
                </p>
              </div>

              <div className="space-y-8">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Description</h3>
                <p className="text-gray-200 leading-relaxed">
                    The Training API is optimized for corporate and industrial training modules with a focus on 
                    compliance, safety protocols, and workflow documentation. It uses a modern Corporate Memphis / 
                    Industrial Flat Design aesthetic with bold vector icons, safety color palettes (blue, yellow, 
                    green, red), and an authoritative instructional tone. Perfect for employee onboarding, safety 
                    training, and procedural documentation.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Function Signature</h3>
                  <CodeBlock
                    id="training-signature"
                    code={`process_video_request(
    topic: str,
    style: str = "normal",
    voice: str | None = None,
    language: str | None = None,
    max_beats: int = 0
) -> str | None`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Parameters</h3>
                  <ParameterTable
                    parameters={[
                      {
                        name: 'topic',
                        type: 'string',
                        required: true,
                        description: 'The training topic (e.g., "Forklift Safety Procedure", "Cybersecurity Best Practices")',
                      },
                      {
                        name: 'style',
                        type: 'string',
                        required: false,
                        default: '"normal"',
                        description: 'Visual style for training content',
                        values: '"normal" (Corporate flat design), "solid" (Colorful infographic), "pencil" (Graphite sketch), "cartoon" (Simpsons style)',
                      },
                      {
                        name: 'voice',
                        type: 'string | None',
                        required: false,
                        default: 'None',
                        description: 'ElevenLabs voice name or voice ID',
                      },
                      {
                        name: 'language',
                        type: 'string | None',
                        required: false,
                        default: 'None',
                        description: 'ISO 639-1 language code. Uses multilingual model for non-English',
                      },
                      {
                        name: 'max_beats',
                        type: 'int',
                        required: false,
                        default: '0',
                        description: 'Maximum number of beats/scenes. If 0, generates all beats',
                      },
                    ]}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Special Features</h3>
                  <ul className="list-disc list-inside text-gray-200 space-y-2 mb-6">
                    <li><strong className="text-white">Industrial Flat Design:</strong> Bold vector icons with solid colors, pure white backgrounds</li>
                    <li><strong className="text-white">Safety Color Palette:</strong> Safety Blue (#0056D2), Warning Yellow (#FFC107), Success Green (#28A745), Red (#DC3545)</li>
                    <li><strong className="text-white">Authoritative Tone:</strong> Uses "Ensure", "Verify", "Proceed" instead of casual language</li>
                    <li><strong className="text-white">Structured Content:</strong> Title slide, learning content, summary/safety check</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Basic Usage</h3>
                  <CodeBlock
                    id="training-basic"
                    code={`from generate_topic_video_v8 import process_video_request

# Basic training video
video_path = process_video_request(
    topic="Forklift Safety Procedure",
    style="normal",
    language="en"
)

if video_path:
    print(f"Training video generated: {video_path}")`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Advanced Usage</h3>
                  <CodeBlock
                    id="training-advanced"
                    code={`from generate_topic_video_v8 import process_video_request

# Advanced training video with corporate voice
video_path = process_video_request(
    topic="Cybersecurity Awareness Training",
    style="normal",      # Corporate flat design
    voice="Professional Trainer",  # Corporate-friendly voice
    language="en",
    max_beats=6          # Structured training module
)

if video_path:
    print(f"Training module created: {video_path}")`}
                  />
                </div>
              </div>
            </section>

            {/* Cartoon Fun Doodle API Section */}
            <section id="cartoon" className="mb-16 scroll-mt-20">
              <div className="border-b border-gray-900 pb-4 mb-8">
                <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                  <Sparkles className="w-8 h-8 text-purple-400" />
                  Cartoon Fun Doodle API
                </h2>
                <p className="text-gray-400">
                  Generate Simpsons-style fun educational content with character dialogue and speech bubbles
                </p>
              </div>

              <div className="space-y-8">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Description</h3>
                <p className="text-gray-200 leading-relaxed">
                    The Cartoon Fun Doodle API creates engaging educational videos in The Simpsons / Matt Groening 
                    style. It features character dialogue between Homer and Lisa Simpson, speech bubbles, character 
                    actions, and fun visual explanations. Unlike other APIs, it uses a dialogue-based structure 
                    instead of parts, making complex topics more accessible and entertaining through storytelling.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Function Signature</h3>
                  <CodeBlock
                    id="cartoon-signature"
                    code={`process_video_request(
    topic: str,
    style: str = "normal",
    voice: str | None = None,
    language: str | None = None,
    max_beats: int = 0
) -> str | None`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Parameters</h3>
                  <ParameterTable
                    parameters={[
                      {
                        name: 'topic',
                        type: 'string',
                        required: true,
                        description: 'The topic for the cartoon video (e.g., "Particle Physics", "How Plants Grow")',
                      },
                      {
                        name: 'style',
                        type: 'string',
                        required: false,
                        default: '"normal"',
                        description: 'Visual style (recommended: "cartoon" for Simpsons style)',
                        values: '"normal", "solid", "pencil", "cartoon" (The Simpsons / Matt Groening style)',
                      },
                      {
                        name: 'voice',
                        type: 'string | None',
                        required: false,
                        default: 'None',
                        description: 'ElevenLabs voice name or ID. Homer and Lisa use default character voices if not specified',
                      },
                      {
                        name: 'language',
                        type: 'string | None',
                        required: false,
                        default: 'None',
                        description: 'ISO 639-1 language code for dialogue',
                      },
                      {
                        name: 'max_beats',
                        type: 'int',
                        required: false,
                        default: '0',
                        description: 'Maximum number of dialogue beats. If 0, generates all beats',
                      },
                    ]}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Special Features</h3>
                  <ul className="list-disc list-inside text-gray-200 space-y-2 mb-6">
                    <li><strong className="text-white">Character Dialogue:</strong> Homer and Lisa Simpson have conversations about the topic</li>
                    <li><strong className="text-white">Speech Bubbles:</strong> Comic book-style speech bubbles with punchy dialogue</li>
                    <li><strong className="text-white">Character Actions:</strong> Each line includes character actions (e.g., "Pointing at diagram", "Scratching head")</li>
                    <li><strong className="text-white">Visual Descriptions:</strong> Each dialogue line has a specific visual doodle description</li>
                    <li><strong className="text-white">Automatic Voice Mapping:</strong> Homer uses voice ID "onwK4e9ZLuTAKqWW03F9", Lisa uses "21m00Tcm4TlvDq8ikWAM"</li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Dialogue Structure</h3>
                  <p className="text-gray-200 mb-4">
                    The manifest uses a <code className="text-blue-400">dialogue</code> array instead of <code className="text-blue-400">parts</code>:
                  </p>
                  <CodeBlock
                    id="cartoon-structure"
                    code={`{
  "topic": "Particle Physics",
  "beats": [
    {
      "beat_id": 1,
      "image_prompt": "Simpsons style...",
      "dialogue": [
        {
          "speaker": "Homer",
          "bubble_text": "Particles? Like tiny donuts?",
          "visual_desc": "A doodle of a donut-shaped atom splitting into smaller pieces",
          "character_action": "Holding a half-eaten donut and looking confused",
          "audio_script": "Particles? Like tiny donuts? I see this donut-shaped atom splitting apart... looks delicious!"
        },
        {
          "speaker": "Lisa",
          "bubble_text": "No! They are fundamental!",
          "visual_desc": "A chart showing the Standard Model of particle physics",
          "character_action": "Pointing confidently at the chart using a ruler",
          "audio_script": "No Dad! They are fundamental building blocks. This chart shows the Standard Model..."
        }
      ]
    }
  ]
}`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Basic Usage</h3>
                  <CodeBlock
                    id="cartoon-basic"
                    code={`from generate_topic_video_v8_1 import process_video_request

# Simple cartoon educational video
video_path = process_video_request(
    topic="Particle Physics",
    style="cartoon",  # Simpsons style
    language="en"
)

if video_path:
    print(f"Cartoon video generated: {video_path}")`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Advanced Usage</h3>
                  <CodeBlock
                    id="cartoon-advanced"
                    code={`from generate_topic_video_v8_1 import process_video_request

# Advanced cartoon video with custom parameters
video_path = process_video_request(
    topic="How Black Holes Work",
    style="cartoon",           # The Simpsons style
    voice=None,                # Uses default Homer/Lisa voices
    language="en",
    max_beats=4                # Limit dialogue beats
)

if video_path:
    print(f"Fun educational video created: {video_path}")`}
                  />
                </div>
              </div>
            </section>

            {/* Getting Started Section */}
            <section id="getting-started" className="mb-16 scroll-mt-20">
              <h2 className="text-3xl font-bold text-white mb-6">Getting Started</h2>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
                <p className="text-yellow-400 text-sm">
                  <strong className="text-yellow-300">⚠️ Launching Soon:</strong> The Chytr API is currently in development 
                  and will be launching soon. The endpoints and functionality described in this documentation will be available 
                  upon launch. Stay tuned for updates!
                </p>
              </div>
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Installation</h3>
                  <CodeBlock
                    id="installation"
                    code={`# Install required dependencies
pip install requests moviepy python-dotenv

# Clone the repository
git clone <repository-url>
cd backend

# Install dependencies from requirements.txt
pip install -r requirements.txt`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Environment Setup</h3>
                  <CodeBlock
                    id="env-setup"
                    code={`# Create a .env file in the backend directory
touch .env

# Add your API keys
echo "OPENROUTER_API_KEY=your-key-here" >> .env
echo "FAL_KEY=your-key-here" >> .env
echo "ELEVEN_LABS_API_KEY=your-key-here" >> .env`}
                  />
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4">Quick Example</h3>
                  <CodeBlock
                    id="quick-example"
                    code={`# Import the appropriate generator
from SOTA.generate_topic_video_v7_4_text_corrected import process_video_request

# Generate a simple educational video
result = process_video_request(
    topic="Black Hole",
    style="normal",
    language="en"
)

if result:
    print(f"Success! Video saved to: {result}")
else:
    print("Generation failed. Check your API keys and logs.")`}
                  />
                </div>
              </div>
            </section>
          </div>
        </main>

        {/* Right Sidebar - "On this page" */}
        <aside className="hidden xl:block w-64 border-l border-gray-900 bg-black h-[calc(100vh-4rem)] sticky top-16 overflow-y-auto">
          <nav className="p-6">
              <div className="flex items-center gap-2 mb-4">
              <Menu className="w-4 h-4 text-gray-500" />
              <h3 className="text-sm font-semibold text-gray-200">On this page</h3>
            </div>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="#overview"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection('overview');
                  }}
                  className="block px-3 py-1 text-gray-500 hover:text-white transition-colors rounded"
                >
                  Welcome to Chytr API
                </a>
              </li>
              <li>
                <a
                  href="#educational"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection('educational');
                  }}
                  className="block px-3 py-1 text-gray-500 hover:text-white transition-colors rounded"
                >
                  Educational API
                </a>
              </li>
              <li>
                <a
                  href="#training"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection('training');
                  }}
                  className="block px-3 py-1 text-gray-500 hover:text-white transition-colors rounded"
                >
                  Training API
                </a>
              </li>
              <li>
                <a
                  href="#cartoon"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection('cartoon');
                  }}
                  className="block px-3 py-1 text-gray-500 hover:text-white transition-colors rounded"
                >
                  Cartoon Fun Doodle API
                </a>
              </li>
              <li>
                <a
                  href="#getting-started"
                  onClick={(e) => {
                    e.preventDefault();
                    scrollToSection('getting-started');
                  }}
                  className="block px-3 py-1 text-gray-500 hover:text-white transition-colors rounded"
                >
                  Getting Started
                </a>
              </li>
            </ul>
          </nav>
        </aside>
      </div>
    </div>
  );
};

export default ApiDocumentation;