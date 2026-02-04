
import React from 'react';
import { BarChart3, Brain, Zap, Shield, TrendingUp, MessageSquare, Database, Sparkles, CheckCircle2 } from 'lucide-react';

export function LandingPage({ onLogin, onSignup }) {
    const features = [
        {
            icon: Brain,
            title: 'AI-Powered Insights',
            description: 'Advanced RAG technology analyzes your business data and documents to provide intelligent, context-aware answers.'
        },
        {
            icon: MessageSquare,
            title: 'Natural Conversation',
            description: 'Ask questions in plain English. No complex queries or technical knowledge required.'
        },
        {
            icon: TrendingUp,
            title: 'Real-Time Analytics',
            description: 'Get instant access to KPIs, trends, and performance metrics across your entire business.'
        },
        {
            icon: Database,
            title: 'Multi-Source Integration',
            description: 'Connect databases, documents, and data warehouses in one unified analytics platform.'
        },
        {
            icon: Zap,
            title: 'Guided Exploration',
            description: 'Smart follow-up questions help you dive deeper and uncover hidden insights automatically.'
        },
        {
            icon: Shield,
            title: 'Enterprise Security',
            description: 'Bank-level encryption and role-based access control keep your data safe and compliant.'
        }
    ];

    const useCases = [
        {
            question: '"Why did revenue drop last quarter?"',
            insight: 'Get root cause analysis with regional breakdowns, category impacts, and actionable recommendations.'
        },
        {
            question: '"Show me top performing products"',
            insight: 'Instantly view rankings with margins, inventory levels, and demand forecasts.'
        },
        {
            question: '"Compare this year vs last year"',
            insight: 'Automated YoY analysis with trend visualization and variance explanations.'
        }
    ];

    const primaryGradient = 'linear-gradient(135deg, #FF6B6B, #FF8E53)';
    const textGradient = {
        background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#F9FAFB' }} className="d-flex flex-column font-inter">
            {/* Navigation */}
            <nav className="sticky-top bg-white border-bottom border-light shadow-sm" style={{ zIndex: 100 }}>
                <div className="container py-3">
                    <div className="d-flex align-items-center justify-content-between">
                        <div className="d-flex align-items-center gap-3">
                            <div className="d-flex align-items-center justify-content-center rounded-3 shadow-sm"
                                style={{ width: '40px', height: '40px', background: primaryGradient }}>
                                <BarChart3 className="text-white" size={24} />
                            </div>
                            <div>
                                <h1 className="h5 mb-0 fw-bold text-dark">NovaChat</h1>
                                <p className="mb-0 text-muted small">Business Intelligence Assistant</p>
                            </div>
                        </div>
                        <div className="d-flex align-items-center gap-3">
                            <button
                                onClick={onLogin}
                                className="btn btn-link text-decoration-none text-secondary fw-semibold"
                            >
                                Login
                            </button>
                            <button
                                onClick={onSignup}
                                className="btn text-white fw-semibold px-4 py-2 rounded-3 shadow-sm border-0 transition-all hover-transform"
                                style={{ background: primaryGradient }}
                            >
                                Get Started
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="py-5" style={{ background: 'linear-gradient(180deg, #FFF5F5 0%, #FFFFFF 100%)' }}>
                <div className="container pt-4 pb-5">
                    <div className="text-center mx-auto" style={{ maxWidth: '800px' }}>
                        <div className="d-inline-flex align-items-center gap-2 px-3 py-1 bg-white border border-danger text-danger rounded-pill mb-4 shadow-sm">
                            <Sparkles size={16} className="text-danger opacity-75" />
                            <span className="small fw-semibold text-danger">Powered by Advanced RAG Technology</span>
                        </div>

                        <h2 className="display-4 fw-bold text-dark mb-4 lh-tight">
                            Your Business Data,<br />
                            <span style={textGradient}> Explained Intelligently</span>
                        </h2>

                        <p className="lead text-muted mb-5" style={{ lineHeight: '1.8' }}>
                            Ask questions in natural language. Get instant insights from your databases, documents, and data warehouses.
                            No SQL required. No waiting for reports. Just intelligent answers.
                        </p>
                    </div>

                    {/* Hero Visual Mockup */}
                    <div className="mt-5 position-relative mx-auto" style={{ maxWidth: '1000px' }}>
                        <div className="bg-white rounded-4 shadow-lg border overflow-hidden">
                            {/* Browser Header */}
                            <div className="bg-light px-4 py-3 border-bottom d-flex align-items-center gap-2">
                                <div className="d-flex gap-2">
                                    <div className="rounded-circle bg-danger opacity-50" style={{ width: 12, height: 12 }}></div>
                                    <div className="rounded-circle bg-warning opacity-50" style={{ width: 12, height: 12 }}></div>
                                    <div className="rounded-circle bg-success opacity-50" style={{ width: 12, height: 12 }}></div>
                                </div>
                                <span className="ms-3 small text-muted fw-medium">Analytics Assistant</span>
                            </div>

                            {/* Chat Interface Mockup */}
                            <div className="p-4 p-md-5 bg-white">
                                <div className="d-flex flex-column gap-4">
                                    {/* User Message */}
                                    <div className="d-flex justify-content-end">
                                        <div className="text-white rounded-4 rounded-top-right-0 px-4 py-3 shadow-sm"
                                            style={{ background: primaryGradient, maxWidth: '400px', borderTopRightRadius: '4px' }}>
                                            Why did sales drop in the South region?
                                        </div>
                                    </div>

                                    {/* Assistant Message */}
                                    <div className="d-flex gap-3">
                                        <div className="flex-shrink-0">
                                            <div className="rounded-circle d-flex align-items-center justify-content-center"
                                                style={{ width: 36, height: 36, background: primaryGradient }}>
                                                <Brain size={20} className="text-white" />
                                            </div>
                                        </div>
                                        <div className="bg-light rounded-4 rounded-top-left-0 p-4 border shadow-sm" style={{ borderTopLeftRadius: '4px', maxWidth: '650px' }}>
                                            <p className="text-dark mb-3">
                                                Sales in the South region decreased by <strong className="text-danger">12% in Q2</strong>, mainly due to higher discounts in the Furniture category.
                                            </p>
                                            <p className="text-muted small mb-2 fw-semibold">Key Insights:</p>
                                            <ul className="text-secondary small mb-0 ps-3">
                                                <li className="mb-1">Total sales dropped from $850K to $748K</li>
                                                <li className="mb-1">Furniture category saw a 23% decline</li>
                                                <li>Discount rates increased from 8% to 15%</li>
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="d-flex gap-2 ps-5 ms-2">
                                        <span className="badge bg-white text-secondary border px-3 py-2 rounded-pill fw-normal d-flex align-items-center gap-2">
                                            <TrendingUp size={14} className="text-muted" /> View monthly trend
                                        </span>
                                        <span className="badge bg-white text-secondary border px-3 py-2 rounded-pill fw-normal d-flex align-items-center gap-2">
                                            <BarChart3 size={14} className="text-muted" /> Category breakdown
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Use Cases Grid */}
            <section className="py-5 bg-white">
                <div className="container py-4">
                    <div className="text-center mb-5">
                        <h3 className="h2 fw-bold text-dark mb-3">See It In Action</h3>
                        <p className="lead text-muted">Real questions, instant insights</p>
                    </div>
                    <div className="row g-4">
                        {useCases.map((useCase, index) => (
                            <div key={index} className="col-md-4">
                                <div className="h-100 p-4 rounded-4 border bg-white hover-shadow transition-all" style={{ transition: 'box-shadow 0.3s' }}>
                                    <div className="fw-semibold mb-3 fs-5" style={{ color: '#FF6B6B' }}>{useCase.question}</div>
                                    <p className="text-muted mb-0">{useCase.insight}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-5" style={{ backgroundColor: '#F9FAFB' }}>
                <div className="container py-4">
                    <div className="text-center mb-5">
                        <h3 className="h2 fw-bold text-dark mb-3">Everything You Need</h3>
                        <p className="lead text-muted">Powerful features designed for modern business analytics</p>
                    </div>
                    <div className="row g-4">
                        {features.map((feature, index) => {
                            const Icon = feature.icon;
                            return (
                                <div key={index} className="col-md-4 col-lg-4">
                                    <div className="card h-100 border-0 shadow-sm rounded-4 hover-translate-y transition-all">
                                        <div className="card-body p-4">
                                            <div className="mb-4 d-inline-flex p-3 rounded-3 bg-opacity-10"
                                                style={{ backgroundColor: '#FFF5F5' }}>
                                                <Icon className="text-danger" size={24} style={{ color: '#FF6B6B' }} />
                                            </div>
                                            <h4 className="h5 fw-bold mb-3 text-dark">{feature.title}</h4>
                                            <p className="card-text text-muted">{feature.description}</p>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-5 bg-white">
                <div className="container py-4">
                    <div className="rounded-5 p-5 text-center text-white position-relative overflow-hidden shadow-lg"
                        style={{ background: primaryGradient }}>
                        <div className="position-relative z-10">
                            <h3 className="display-5 fw-bold mb-4">
                                Ready to Transform Your Analytics?
                            </h3>
                            <p className="lead mb-5 opacity-90 mx-auto" style={{ maxWidth: '600px' }}>
                                Join thousands of teams making data-driven decisions faster with AI-powered insights.
                            </p>
                            <button
                                onClick={onSignup}
                                className="btn btn-light btn-lg px-5 py-3 rounded-3 fw-bold text-danger shadow-sm border-0"
                                style={{ color: '#FF6B6B' }}
                            >
                                Start Your Free Trial
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-4 bg-white border-top">
                <div className="container text-center">
                    <div className="d-flex flex-column flex-md-row justify-content-between align-items-center gap-3">
                        <div className="d-flex align-items-center gap-2">
                            <div className="d-flex align-items-center justify-content-center rounded-2"
                                style={{ width: '24px', height: '24px', background: primaryGradient }}>
                                <BarChart3 className="text-white" size={14} />
                            </div>
                            <small className="text-muted">© 2026 NovaChat. All rights reserved.</small>
                        </div>
                        <div className="d-flex gap-4">
                            <a href="#" className="text-muted text-decoration-none small">Privacy Policy</a>
                            <a href="#" className="text-muted text-decoration-none small">Terms of Service</a>
                            <a href="#" className="text-muted text-decoration-none small">Contact</a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}

// Helper Style Class for Hover effects (can be moved to CSS)
const styles = `
.hover-shadow:hover { box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important; }
.hover-translate-y:hover { transform: translateY(-5px); }
.lh-tight { line-height: 1.2; }
`;
