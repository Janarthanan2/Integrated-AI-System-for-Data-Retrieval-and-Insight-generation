import React, { useRef, useEffect } from 'react';
import { Send, Plus, Mic, Square } from 'lucide-react';
import { Form } from 'react-bootstrap';

const ChatInput = ({ query, setQuery, onSend, isLoading, onNewChat }) => {
    const textareaRef = useRef(null);

    // Dynamic Height Adjustment
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [query]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSend();
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSend();
    };

    return (
        <div className="p-4 bg-white border-top border-gray-100">
            <div className="d-flex align-items-center gap-2 px-3 py-2"
                style={{
                    borderRadius: '24px',
                    background: 'linear-gradient(to right, #ffffff, #fff1f2)', // Subtle White to Rose-50
                    border: '1px solid rgba(244, 63, 94, 0.1)',
                    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.05)' // Soft high elevation
                }}>
                <button
                    onClick={onNewChat}
                    className="btn p-0 text-rose-500 bg-white border border-rose-100 hover:bg-rose-50 hover:text-rose-600 rounded-circle transition-all shadow-sm d-flex align-items-center justify-content-center"
                    style={{ width: '40px', height: '40px' }}
                    title="New Chat"
                >
                    <Plus size={20} />
                </button>
                <Form onSubmit={handleSubmit} className="flex-grow-1">
                    <textarea
                        ref={textareaRef}
                        className="w-100 bg-transparent border-0 text-gray-800 focus:outline-none custom-scrollbar placeholder-gray-400"
                        style={{
                            outline: 'none',
                            boxShadow: 'none',
                            resize: 'none',
                            height: '24px',
                            maxHeight: '120px',
                            overflowY: 'auto',
                            lineHeight: '1.5'
                        }}
                        placeholder="Ask anything..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        rows={1}
                    />
                </Form>
                <div className="d-flex gap-2">
                    <button
                        className="btn p-0 text-gray-500 bg-white border border-gray-100 hover:bg-gray-50 hover:text-gray-700 rounded-circle transition-all shadow-sm d-flex align-items-center justify-content-center"
                        style={{ width: '40px', height: '40px' }}
                    >
                        <Mic size={20} />
                    </button>
                    <button
                        onClick={onSend}
                        className="btn p-0 rounded-circle text-white d-flex align-items-center justify-content-center transition-all hover:scale-105 active:scale-95"
                        disabled={!query.trim() && !isLoading}
                        style={{
                            background: isLoading ? '#F43F5E' : 'linear-gradient(135deg, #F43F5E 0%, #E11D48 100%)',
                            boxShadow: '0 4px 12px rgba(244, 63, 94, 0.3)',
                            width: '40px',
                            height: '40px',
                            opacity: (!query.trim() && !isLoading) ? 0.7 : 1,
                            cursor: (!query.trim() && !isLoading) ? 'default' : 'pointer',
                            filter: 'brightness(1)' // Default
                        }}
                        onMouseEnter={(e) => {
                            if (!(!query.trim() && !isLoading)) {
                                e.currentTarget.style.filter = 'brightness(1.1)';
                                e.currentTarget.style.boxShadow = '0 6px 20px rgba(244, 63, 94, 0.5)';
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.filter = 'brightness(1)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(244, 63, 94, 0.3)';
                        }}
                    >
                        {isLoading ? <Square size={16} fill="white" /> : <Send size={18} />}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInput;
