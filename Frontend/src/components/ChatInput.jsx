import React, { useRef, useEffect, useState } from 'react';
import { Send, Plus, Mic, Square, Check, Cpu, Loader, ChevronUp } from 'lucide-react';
import { Form } from 'react-bootstrap';
import { API_URL } from '../api/config';

const ChatInput = ({ query, setQuery, onSend, isLoading, onNewChat, selectedModel, onModelChange, availableModels }) => {
    const textareaRef = useRef(null);
    const popoverRef = useRef(null);
    const [showModelPopover, setShowModelPopover] = useState(false);
    const [isSwitching, setIsSwitching] = useState(false);

    // Dynamic Height Adjustment
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [query]);

    // Close popover on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (popoverRef.current && !popoverRef.current.contains(e.target)) {
                setShowModelPopover(false);
            }
        };
        if (showModelPopover) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showModelPopover]);

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

    const handleModelSwitch = async (modelId) => {
        if (isSwitching || modelId === selectedModel?.id) return;

        setIsSwitching(true);
        try {
            const response = await fetch(`${API_URL}/models/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId })
            });
            if (response.ok) {
                const data = await response.json();
                onModelChange(data.current);
            }
        } catch (err) {
            console.error('Failed to switch model:', err);
        } finally {
            setIsSwitching(false);
            setShowModelPopover(false);
        }
    };

    return (
        <div className="p-4 bg-white border-top border-gray-100 chat-input-container">
            <div className="d-flex align-items-center gap-2 px-3 py-2"
                style={{
                    borderRadius: '24px',
                    background: 'linear-gradient(to right, #ffffff, #fff1f2)',
                    border: '1px solid rgba(244, 63, 94, 0.1)',
                    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.05)'
                }}>

                {/* Plus Button -> Model Selector */}
                <div className="position-relative" ref={popoverRef}>
                    <button
                        onClick={() => setShowModelPopover(!showModelPopover)}
                        className="btn p-0 text-rose-500 bg-white border border-rose-100 hover:bg-rose-50 hover:text-rose-600 rounded-circle transition-all shadow-sm d-flex align-items-center justify-content-center"
                        style={{ width: '40px', height: '40px' }}
                        title="Select AI Model"
                    >
                        {isSwitching ? (
                            <Loader size={18} className="animate-spin" />
                        ) : (
                            <Plus size={20} />
                        )}
                    </button>

                    {/* Model Selection Popover */}
                    {showModelPopover && (
                        <div
                            className="model-selector-popover position-absolute shadow-lg rounded-3 overflow-hidden"
                            style={{
                                bottom: '48px',
                                left: '0',
                                width: '260px',
                                zIndex: 1060,
                                background: '#ffffff',
                                border: '1px solid rgba(0,0,0,0.08)',
                                animation: 'fadeInUp 0.2s ease'
                            }}
                        >
                            {/* Popover Header */}
                            <div className="px-3 py-2 border-bottom" style={{ background: '#f9fafb' }}>
                                <div className="d-flex align-items-center gap-2">
                                    <Cpu size={14} className="text-muted" />
                                    <span className="small fw-bold text-secondary text-uppercase" style={{ letterSpacing: '0.5px', fontSize: '11px' }}>
                                        AI Model
                                    </span>
                                </div>
                            </div>

                            {/* Model Options */}
                            <div className="p-2">
                                {(availableModels || []).map((model) => (
                                    <button
                                        key={model.id}
                                        onClick={() => handleModelSwitch(model.id)}
                                        disabled={isSwitching}
                                        className="btn w-100 text-start p-2 rounded-2 d-flex align-items-center justify-content-between mb-1 border-0"
                                        style={{
                                            backgroundColor: model.is_active ? 'rgba(244, 63, 94, 0.08)' : 'transparent',
                                            transition: 'all 0.15s ease',
                                            cursor: isSwitching ? 'wait' : 'pointer'
                                        }}
                                        onMouseEnter={(e) => {
                                            if (!model.is_active) e.currentTarget.style.backgroundColor = '#f3f4f6';
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!model.is_active) e.currentTarget.style.backgroundColor = 'transparent';
                                        }}
                                    >
                                        <div>
                                            <div className="fw-medium" style={{
                                                fontSize: '13px',
                                                color: model.is_active ? '#E11D48' : '#374151'
                                            }}>
                                                {model.name}
                                            </div>
                                            <div className="text-muted" style={{ fontSize: '11px' }}>
                                                {model.description}
                                            </div>
                                        </div>
                                        {model.is_active && (
                                            <Check size={16} style={{ color: '#E11D48' }} />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

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
                            filter: 'brightness(1)'
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
