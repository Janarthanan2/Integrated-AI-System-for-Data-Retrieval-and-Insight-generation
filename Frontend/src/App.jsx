import React, { useState, useRef, useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { Sparkles, Settings, LogOut, User, PanelLeftClose, PanelLeft, Sun, Moon } from 'lucide-react';
import SettingsModal from './components/SettingsModal';
import ChatInput from './components/ChatInput';
import ChatHistory from './components/ChatHistory';
import Sidebar from './components/Sidebar';
import AuthModal from './components/AuthModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ConversationsProvider, useConversations } from './contexts/ConversationsContext';
import { API_URL, authHeaders } from './api/config';
import * as conversationsApi from './api/conversations';

import { LandingPage } from './components/LandingPage';

// Inner App component that uses contexts
function AppContent() {
    const { user, isAuthenticated, logout } = useAuth();
    const {
        activeConversationId,
        messages,
        createNewConversation,
        startNewChat,
        updateSidebarItem,
    } = useConversations();

    const [query, setQuery] = useState("");
    const [history, setHistory] = useState([]); // Local history for non-authenticated users
    const [isLoading, setIsLoading] = useState(false);
    const abortControllerRef = useRef(null);
    const [showSettings, setShowSettings] = useState(false);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);

    // Model selection state
    const [selectedModel, setSelectedModel] = useState(null);
    const [availableModels, setAvailableModels] = useState([]);

    // Fetch available models on mount
    useEffect(() => {
        const fetchModels = async () => {
            try {
                const res = await fetch(`${API_URL}/models`);
                if (res.ok) {
                    const data = await res.json();
                    setAvailableModels(data.models);
                    setSelectedModel(data.current);
                }
            } catch (err) {
                console.error('Failed to fetch models:', err);
            }
        };
        fetchModels();
    }, []);

    // Handle Mobile Sidebar auto-close on resize/selection
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth <= 768) {
                setSidebarOpen(false);
            } else {
                setSidebarOpen(true);
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);


    // Theme State
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('theme') || 'dark';
    });

    // Apply theme to document
    const applyTheme = (selectedTheme) => {
        const root = document.documentElement;
        let effectiveTheme = selectedTheme;

        if (selectedTheme === 'system') {
            effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        if (effectiveTheme === 'dark') {
            root.classList.add('dark-theme');
            root.classList.remove('light-theme');
        } else {
            root.classList.add('light-theme');
            root.classList.remove('dark-theme');
        }
    };

    // Handle theme change
    const handleThemeChange = (newTheme) => {
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    // Apply theme on mount and listen for system preference changes
    useEffect(() => {
        applyTheme(theme);

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleSystemChange = () => {
            if (theme === 'system') {
                applyTheme('system');
            }
        };

        mediaQuery.addEventListener('change', handleSystemChange);
        return () => mediaQuery.removeEventListener('change', handleSystemChange);
    }, [theme]);

    const toggleTheme = () => {
        // Cycle: light -> dark -> system -> light (or just light/dark for the toggle)
        // For simplicity, let's just toggle between light and dark when using the header icon
        if (theme === 'light' || theme === 'system') {
            handleThemeChange('dark');
        } else {
            handleThemeChange('light');
        }
    };

    // Sync messages from context to local history when conversation changes
    useEffect(() => {
        if (isAuthenticated && messages.length > 0) {
            // Convert API messages to local format
            const convertedHistory = messages.map(msg => {
                const chartArtifact = msg.artifacts?.find(a => a.type === 'chart');
                let chart = null;
                if (chartArtifact) {
                    chart = {
                        type: chartArtifact.chart_type,
                        data: chartArtifact.data_snapshot || chartArtifact.spec
                    };
                }
                return {
                    role: msg.role,
                    content: msg.content,
                    chart: chart,
                };
            });
            setHistory(convertedHistory);
        }
    }, [messages, isAuthenticated]);

    // Clear history when starting new chat
    useEffect(() => {
        if (!activeConversationId && isAuthenticated) {
            setHistory([]);
        }
    }, [activeConversationId, isAuthenticated]);

    // Clear history on logout
    useEffect(() => {
        if (!isAuthenticated) {
            setHistory([]);
        }
    }, [isAuthenticated]);

    // Settings Handlers
    const handleClearHistory = () => {
        setHistory([]);
        if (isAuthenticated) {
            startNewChat();
        }
    };

    // Quick Action Handler
    const handleQuickAction = (text) => {
        setQuery(text);
    };

    // Handle Submit
    const handleSubmit = async (overrideQuery) => {
        // Handle Stop Generation
        if (isLoading) {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
                abortControllerRef.current = null;
            }
            setIsLoading(false);
            return;
        }

        const effectiveQuery = overrideQuery || query;
        if (!effectiveQuery.trim()) return;

        const userMsg = { role: "user", content: effectiveQuery };

        // Optimistic UI: Add message immediately
        setHistory(prev => [...prev, userMsg]);
        setQuery("");
        setIsLoading(true);

        // Create new AbortController
        abortControllerRef.current = new AbortController();

        // Track conversation ID for this request
        let currentConversationId = activeConversationId;

        try {
            // If authenticated and no active conversation, create one
            if (isAuthenticated && !currentConversationId) {
                try {
                    const newConv = await createNewConversation(effectiveQuery);
                    currentConversationId = newConv.id;

                    // Store user message in DB
                    await conversationsApi.sendMessage({
                        conversation_id: currentConversationId,
                        content: effectiveQuery,
                        role: 'user'
                    });
                } catch (err) {
                    console.error('Failed to create conversation:', err);
                }
            } else if (isAuthenticated && currentConversationId) {
                // Store user message in DB
                try {
                    await conversationsApi.sendMessage({
                        conversation_id: currentConversationId,
                        content: effectiveQuery,
                        role: 'user'
                    });
                } catch (err) {
                    console.error('Failed to save message:', err);
                }
            }

            // Call the query API
            const response = await fetch(`${API_URL}/query`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...authHeaders(),
                },
                body: JSON.stringify({
                    query: userMsg.content,
                    history: history,
                    session_id: currentConversationId || "",
                }),
                signal: abortControllerRef.current.signal
            });

            if (!response.ok) {
                throw new Error("Network response was not ok");
            }

            // Stream handling
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMsg = { role: "assistant", content: "", chart: null };

            // Add placeholder for streaming
            setHistory(prev => [...prev, assistantMsg]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n").filter(line => line.trim() !== "");

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line);

                        if (data.type === "token") {
                            assistantMsg.content += data.chunk;
                            setHistory(prev => {
                                const newHistory = [...prev];
                                newHistory[newHistory.length - 1] = { ...assistantMsg };
                                return newHistory;
                            });
                        } else if (data.type === "chart") {
                            assistantMsg.chart = data.content;
                            setHistory(prev => {
                                const newHistory = [...prev];
                                newHistory[newHistory.length - 1] = { ...assistantMsg };
                                return newHistory;
                            });
                        } else if (data.type === "error") {
                            assistantMsg.content += `\n[Error: ${data.content}]`;
                            setHistory(prev => {
                                const newHistory = [...prev];
                                newHistory[newHistory.length - 1] = { ...assistantMsg };
                                return newHistory;
                            });
                        }
                    } catch (e) {
                        console.error("Error parsing chunk", e);
                    }
                }
            }

            // Save assistant response to DB if authenticated
            if (isAuthenticated && currentConversationId && assistantMsg.content) {
                try {
                    const savedMsg = await conversationsApi.sendMessage({
                        conversation_id: currentConversationId,
                        content: assistantMsg.content,
                        role: 'assistant'
                    });

                    // Update sidebar
                    updateSidebarItem(currentConversationId, effectiveQuery.substring(0, 100));

                    // Save chart artifact if present
                    if (assistantMsg.chart) {
                        try {
                            await conversationsApi.createArtifact({
                                message_id: savedMsg.message_id,
                                conversation_id: currentConversationId,
                                type: 'chart',
                                chart_type: assistantMsg.chart.type,
                                data_snapshot: assistantMsg.chart.data
                            });
                        } catch (aErr) {
                            console.error("Failed to save artifact:", aErr);
                        }
                    }
                } catch (err) {
                    console.error('Failed to save assistant message:', err);
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                console.error("Error:", error);
                setHistory(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error connecting to the server." }]);
            }
        } finally {
            setIsLoading(false);
        }
    };


    if (!isAuthenticated) {
        return (
            <>
                <LandingPage
                    onLogin={() => setShowAuthModal(true)}
                    onSignup={() => setShowAuthModal(true)}
                    currentTheme={theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme}
                    onToggleTheme={toggleTheme}
                />
                <AuthModal
                    show={showAuthModal}
                    onClose={() => setShowAuthModal(false)}
                    theme={theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme}
                />
            </>
        );
    }

    return (
        <div className="d-flex vh-100 overflow-hidden text-gray-900 bg-white">

            {/* Sidebar (Conversation History) - Only show if authenticated */}
            {isAuthenticated && (
                <>
                    {/* Mobile Backdrop */}
                    {sidebarOpen && window.innerWidth <= 768 && (
                        <div
                            className="mobile-backdrop"
                            onClick={() => setSidebarOpen(false)}
                        />
                    )}

                    {/* Always render sidebar but control visibility with classes for animations */}
                    {/* Note: In previous implementation we unmounted. For smooth slide-in on mobile, we might keep it mounted but translated. */}
                    {/* However, the CSS `sidebar-open` requires the element to exist. */}
                    {/* Let's try mounting it conditionally but using the `sidebar-open` class for the transition if mounted. */}
                    {/* Actually, to support desktop-collapsible and mobile-drawer, strict conditional rendering is tricky for CSS transitions. */}
                    {/* For now, we will rely on the `sidebarOpen` state. */}
                    {sidebarOpen && (
                        <Sidebar
                            isOpen={sidebarOpen}
                            onClose={() => setSidebarOpen(false)}
                            theme={theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme}
                        />
                    )}
                </>
            )}

            {/* Main Chat Area */}
            <div className="flex-grow-1 d-flex flex-column relative px-0 bg-white">

                {/* Header Bar */}
                <div className="d-flex align-items-center justify-content-between p-2 px-3 border-bottom bg-white">
                    <div className="d-flex align-items-center gap-2">
                        {isAuthenticated && (
                            <button
                                onClick={() => setSidebarOpen(!sidebarOpen)}
                                className="btn btn-link p-1 text-muted"
                                title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
                            >
                                {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeft size={20} />}
                            </button>
                        )}
                        <div className="d-flex align-items-center gap-2">
                            <div className="p-2 rounded-circle d-flex align-items-center justify-content-center"
                                style={{
                                    width: '36px',
                                    height: '36px',
                                    background: 'linear-gradient(135deg, #22D3EE, #3B82F6)',
                                    boxShadow: '0 0 10px rgba(34, 211, 238, 0.4)'
                                }}>
                                <Sparkles size={18} className="text-white" />
                            </div>
                            <span className="fw-semibold" style={{ color: '#374151' }}>NovaChat</span>
                        </div>
                    </div>

                    <div className="d-flex align-items-center gap-2">
                        {/* Global Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="btn btn-link p-1 text-muted"
                            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
                        >
                            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                        </button>

                        {isAuthenticated ? (
                            <>
                                <span className="small text-muted d-none d-md-inline">
                                    {user?.email}
                                </span>
                                <button
                                    onClick={() => setShowSettings(true)}
                                    className="btn btn-link p-1 text-muted"
                                    title="Settings"
                                >
                                    <Settings size={18} />
                                </button>
                                <button
                                    onClick={logout}
                                    className="btn btn-link p-1 text-muted"
                                    title="Logout"
                                >
                                    <LogOut size={18} />
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={() => setShowAuthModal(true)}
                                className="btn btn-sm px-3 py-1"
                                style={{
                                    background: theme === 'light' ? 'linear-gradient(135deg, #FF6B6B, #FF8E53)' : 'linear-gradient(135deg, #22D3EE, #3B82F6)',
                                    border: 'none',
                                    color: 'white',
                                    borderRadius: '8px',
                                    fontWeight: '500',
                                }}
                            >
                                <User size={14} className="me-1" />
                                Sign In
                            </button>
                        )}
                    </div>
                </div>

                <Container fluid className="flex-grow-1 d-flex flex-column p-0 overflow-hidden position-relative">

                    <ChatHistory
                        history={history}
                        isLoading={isLoading}
                        onQuickAction={handleQuickAction}
                        theme={theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme}
                    />

                    <ChatInput
                        query={query}
                        setQuery={setQuery}
                        onSend={() => handleSubmit()}
                        isLoading={isLoading}
                        onNewChat={handleClearHistory}
                        selectedModel={selectedModel}
                        onModelChange={(model) => {
                            setSelectedModel(model);
                            // Refresh available models list to update is_active flags
                            fetch(`${API_URL}/models`).then(r => r.json()).then(d => setAvailableModels(d.models)).catch(() => { });
                        }}
                        availableModels={availableModels}
                    />

                </Container>
            </div>

            {/* Modals */}
            <SettingsModal
                show={showSettings}
                onClose={() => setShowSettings(false)}
                onClearHistory={handleClearHistory}
                currentTheme={theme}
                onThemeChange={handleThemeChange}
            />

            <AuthModal
                show={showAuthModal}
                onClose={() => setShowAuthModal(false)}
                theme={theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme}
            />
        </div>
    );
}

// Main App with Providers
function App() {
    return (
        <AuthProvider>
            <ConversationsProvider>
                <AppContent />
            </ConversationsProvider>
        </AuthProvider>
    );
}

export default App;
