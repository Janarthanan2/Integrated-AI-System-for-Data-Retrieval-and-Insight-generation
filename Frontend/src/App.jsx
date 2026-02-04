import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { Sparkles, Settings, Menu, LogOut, User, PanelLeftClose, PanelLeft } from 'lucide-react';
import SettingsModal from './components/SettingsModal';
import ChatInput from './components/ChatInput';
import ChatHistory from './components/ChatHistory';
import Sidebar from './components/Sidebar';
import AuthModal from './components/AuthModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ConversationsProvider, useConversations } from './contexts/ConversationsContext';
import { API_URL, authHeaders, getAuthToken } from './api/config';
import * as conversationsApi from './api/conversations';

import { LandingPage } from './components/LandingPage';

// Inner App component that uses contexts
function AppContent() {
    const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
    const {
        activeConversationId,
        messages,
        createNewConversation,
        startNewChat,
        addMessage,
        updateLastMessage,
        updateSidebarItem,
        selectConversation,
    } = useConversations();

    const [query, setQuery] = useState("");
    const [history, setHistory] = useState([]); // Local history for non-authenticated users
    const [isLoading, setIsLoading] = useState(false);
    const abortControllerRef = useRef(null);
    const [showSettings, setShowSettings] = useState(false);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Sync messages from context to local history when conversation changes
    useEffect(() => {
        if (isAuthenticated && messages.length > 0) {
            // Convert API messages to local format
            const convertedHistory = messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                chart: msg.artifacts?.find(a => a.type === 'chart')?.spec || null,
            }));
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
                        // Note: This would require the message_id from the saved message
                        // For now, charts are stored in the message content/response
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

    // Show auth modal if not loading and not authenticated
    // const shouldShowAuthPrompt = !authLoading && !isAuthenticated; // No longer needed if we switch view

    if (!isAuthenticated) {
        return (
            <>
                <LandingPage
                    onLogin={() => setShowAuthModal(true)}
                    onSignup={() => setShowAuthModal(true)}
                />
                <AuthModal
                    show={showAuthModal}
                    onClose={() => setShowAuthModal(false)}
                />
            </>
        );
    }

    return (
        <div className="d-flex vh-100 overflow-hidden text-gray-900 bg-white">

            {/* Sidebar (Conversation History) - Only show if authenticated */}
            {isAuthenticated && sidebarOpen && (
                <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
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
                                    background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)'
                                }}>
                                <Sparkles size={18} className="text-white" />
                            </div>
                            <span className="fw-semibold" style={{ color: '#374151' }}>NovaChat</span>
                        </div>
                    </div>

                    <div className="d-flex align-items-center gap-2">
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
                                    background: 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
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
                    />

                    <ChatInput
                        query={query}
                        setQuery={setQuery}
                        onSend={() => handleSubmit()}
                        isLoading={isLoading}
                        onNewChat={handleClearHistory}
                    />

                </Container>
            </div>

            {/* Modals */}
            <SettingsModal
                show={showSettings}
                onClose={() => setShowSettings(false)}
                onClearHistory={handleClearHistory}
            />

            <AuthModal
                show={showAuthModal}
                onClose={() => setShowAuthModal(false)}
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
