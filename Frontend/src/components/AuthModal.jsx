/**
 * Login/Register Modal Component
 */
import React, { useState } from 'react';
import { Modal, Form, Button, Alert, Tabs, Tab, Spinner } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, User, Sparkles } from 'lucide-react';

const AuthModal = ({ show, onClose }) => {
    const { login, register, isLoading } = useAuth();
    const [activeTab, setActiveTab] = useState('login');
    const [error, setError] = useState('');

    // Form state
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');

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

    return (
        <Modal
            show={show}
            onHide={onClose}
            centered
            className="auth-modal"
            backdrop="static"
        >
            <Modal.Header className="border-0 pb-0">
                <Modal.Title className="w-100 text-center">
                    <div className="d-flex align-items-center justify-content-center gap-2 mb-2">
                        <div className="p-2 rounded-circle" style={{ background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)' }}>
                            <Sparkles size={24} className="text-white" />
                        </div>
                    </div>
                    <h4 className="fw-bold mb-1">Welcome to NovaChat</h4>
                    <p className="text-muted small mb-0">Your AI-powered analytics assistant</p>
                </Modal.Title>
            </Modal.Header>

            <Modal.Body className="px-4 pb-4">
                {error && (
                    <Alert variant="danger" className="py-2 small" dismissible onClose={() => setError('')}>
                        {error}
                    </Alert>
                )}

                <Tabs
                    activeKey={activeTab}
                    onSelect={(k) => { setActiveTab(k); resetForm(); }}
                    className="mb-3 justify-content-center"
                    fill
                >
                    <Tab eventKey="login" title="Sign In">
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-medium">Email</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text bg-light border-end-0">
                                        <Mail size={16} className="text-muted" />
                                    </span>
                                    <Form.Control
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="border-start-0"
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-medium">Password</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text bg-light border-end-0">
                                        <Lock size={16} className="text-muted" />
                                    </span>
                                    <Form.Control
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="border-start-0"
                                    />
                                </div>
                            </Form.Group>

                            <Button
                                type="submit"
                                className="w-100 py-2 fw-medium"
                                style={{ background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)', border: 'none' }}
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
                                <Form.Label className="small fw-medium">Username</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text bg-light border-end-0">
                                        <User size={16} className="text-muted" />
                                    </span>
                                    <Form.Control
                                        type="text"
                                        placeholder="johndoe"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        required
                                        minLength={3}
                                        className="border-start-0"
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-3">
                                <Form.Label className="small fw-medium">Email</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text bg-light border-end-0">
                                        <Mail size={16} className="text-muted" />
                                    </span>
                                    <Form.Control
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="border-start-0"
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <Form.Label className="small fw-medium">Password</Form.Label>
                                <div className="input-group">
                                    <span className="input-group-text bg-light border-end-0">
                                        <Lock size={16} className="text-muted" />
                                    </span>
                                    <Form.Control
                                        type="password"
                                        placeholder="Min 6 characters"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="border-start-0"
                                    />
                                </div>
                            </Form.Group>

                            <Button
                                type="submit"
                                className="w-100 py-2 fw-medium"
                                style={{ background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)', border: 'none' }}
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
