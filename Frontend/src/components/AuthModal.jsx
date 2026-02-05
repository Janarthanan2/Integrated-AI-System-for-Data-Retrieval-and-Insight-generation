/**
 * Login/Register Modal Component
 */
import React, { useState } from 'react';
import { Modal, Form, Button, Alert, Tabs, Tab, Spinner } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, User, Sparkles } from 'lucide-react';

const AuthModal = ({ show, onClose, theme = 'light' }) => {
    const { login, register, isLoading } = useAuth();
    const [activeTab, setActiveTab] = useState('login');
    const [error, setError] = useState('');

    const isDark = theme === 'dark';

    // Form state
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');

    const themeStyles = {
        gradient: isDark ? 'linear-gradient(135deg, #22D3EE, #3B82F6)' : 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
        inputBg: isDark ? '#1F2937' : '#F9FAFB',
        inputBorder: isDark ? '#374151' : '#DEE2E6',
        inputText: isDark ? '#F3F4F6' : '#1F2937',
        textMuted: isDark ? '#9CA3AF' : '#6C757D',
        modalBg: isDark ? '#111827' : '#FFFFFF',
        modalText: isDark ? '#F9FAFB' : '#212529',
        iconColor: isDark ? '#22D3EE' : '#FF6B6B'
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            if (activeTab === 'login') {
                await login({ email, password });
            } else {
                await register({ email, username, password });
            }
            // Clear form and close
            setEmail('');
            setPassword('');
            setUsername('');
            onClose();
        } catch (err) {
            setError(err.message || 'Authentication failed');
        }
    };

    const resetForm = () => {
        setEmail('');
        setPassword('');
        setUsername('');
        setError('');
    };

    const inputGroupStyle = {
        backgroundColor: themeStyles.inputBg,
        borderColor: themeStyles.inputBorder,
        color: themeStyles.inputText
    };

    return (
        <Modal
            show={show}
            onHide={onClose}
            centered
            className="auth-modal"
            contentClassName={isDark ? 'bg-dark text-light border-secondary' : 'bg-white border-0'}
            backdrop="static"
        >
            <Modal.Header className="border-0 pb-0" style={{ backgroundColor: themeStyles.modalBg, color: themeStyles.modalText }}>
                <Modal.Title className="w-100 text-center">
                    <div className="d-flex align-items-center justify-content-center gap-2 mb-2">
                        <div className="p-2 rounded-circle" style={{ background: themeStyles.gradient }}>
                            <Sparkles size={24} className="text-white" />
                        </div>
                    </div>
                    <h4 className="fw-bold mb-1">Welcome to NovaChat</h4>
                    <p className="small mb-0" style={{ color: themeStyles.textMuted }}>Your AI-powered analytics assistant</p>
                </Modal.Title>
            </Modal.Header>

            <Modal.Body className="px-4 pb-4" style={{ backgroundColor: themeStyles.modalBg }}>
                {error && (
                    <Alert variant="danger" className="py-2 small" dismissible onClose={() => setError('')}>
                        {error}
                    </Alert>
                )}

                <Tabs
                    activeKey={activeTab}
                    onSelect={(k) => { setActiveTab(k); resetForm(); }}
                    className="mb-3 justify-content-center border-bottom-0"
                    fill
                >
                    <Tab eventKey="login" title="Sign In">
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-medium" style={{ color: themeStyles.modalText }}>Email</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text border-end-0" style={{ ...inputGroupStyle }}>
                                        <Mail size={16} style={{ color: themeStyles.textMuted }} />
                                    </span>
                                    <Form.Control
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="border-start-0 shadow-none"
                                        style={inputGroupStyle}
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-medium" style={{ color: themeStyles.modalText }}>Password</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text border-end-0" style={{ ...inputGroupStyle }}>
                                        <Lock size={16} style={{ color: themeStyles.textMuted }} />
                                    </span>
                                    <Form.Control
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="border-start-0 shadow-none"
                                        style={inputGroupStyle}
                                    />
                                </div>
                            </Form.Group>

                            <Button
                                type="submit"
                                className="w-100 py-2 fw-medium transition-all hover-scale"
                                style={{ background: themeStyles.gradient, border: 'none' }}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <><Spinner size="sm" className="me-2" /> Signing in...</>
                                ) : (
                                    'Sign In'
                                )}
                            </Button>
                        </Form>
                    </Tab>

                    <Tab eventKey="register" title="Create Account">
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-medium" style={{ color: themeStyles.modalText }}>Username</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text border-end-0" style={{ ...inputGroupStyle }}>
                                        <User size={16} style={{ color: themeStyles.textMuted }} />
                                    </span>
                                    <Form.Control
                                        type="text"
                                        placeholder="johndoe"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        required
                                        minLength={3}
                                        className="border-start-0 shadow-none"
                                        style={inputGroupStyle}
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-medium" style={{ color: themeStyles.modalText }}>Email</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text border-end-0" style={{ ...inputGroupStyle }}>
                                        <Mail size={16} style={{ color: themeStyles.textMuted }} />
                                    </span>
                                    <Form.Control
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="border-start-0 shadow-none"
                                        style={inputGroupStyle}
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-medium" style={{ color: themeStyles.modalText }}>Password</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text border-end-0" style={{ ...inputGroupStyle }}>
                                        <Lock size={16} style={{ color: themeStyles.textMuted }} />
                                    </span>
                                    <Form.Control
                                        type="password"
                                        placeholder="Min 6 characters"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="border-start-0 shadow-none"
                                        style={inputGroupStyle}
                                    />
                                </div>
                            </Form.Group>

                            <Button
                                type="submit"
                                className="w-100 py-2 fw-medium transition-all hover-scale"
                                style={{ background: themeStyles.gradient, border: 'none' }}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <><Spinner size="sm" className="me-2" /> Creating account...</>
                                ) : (
                                    'Create Account'
                                )}
                            </Button>
                        </Form>
                    </Tab>
                </Tabs>
            </Modal.Body>
        </Modal>
    );
};

export default AuthModal;
