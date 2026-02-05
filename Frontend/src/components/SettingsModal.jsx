import React, { useEffect, useState } from 'react';
import { X, Trash2, Palette, Monitor, Info, ChevronRight, Moon, Sun } from 'lucide-react';

export default function SettingsModal({ show, onClose, onClearHistory, currentTheme, onThemeChange }) {
    const [animateIn, setAnimateIn] = useState(false);

    useEffect(() => {
        if (show) {
            setAnimateIn(true);
        } else {
            setAnimateIn(false);
        }
    }, [show]);

    if (!show) return null;

    return (
        <div
            className={`position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center`}
            style={{
                background: 'rgba(0, 0, 0, 0.4)',
                zIndex: 1050,
                backdropFilter: 'blur(8px)',
                opacity: animateIn ? 1 : 0,
                transition: 'opacity 0.2s ease-in-out'
            }}
            onClick={onClose}
        >
            <div
                className="bg-white rounded-4 shadow-lg overflow-hidden d-flex flex-column"
                style={{
                    width: '500px',
                    maxWidth: '90%',
                    maxHeight: '85vh',
                    transform: animateIn ? 'scale(1) translateY(0)' : 'scale(0.95) translateY(20px)',
                    transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
                }}
                onClick={(e) => e.stopPropagation()}
            >

                {/* Header */}
                <div className="d-flex align-items-center justify-content-between px-4 py-3 border-bottom bg-white sticky-top">
                    <h5 className="m-0 fw-bold text-dark d-flex align-items-center gap-2">
                        Settings
                    </h5>
                    <button
                        onClick={onClose}
                        className="btn btn-light rounded-circle p-2 d-flex align-items-center justify-content-center border-0 text-secondary"
                        style={{ width: '32px', height: '32px', transition: 'background-color 0.2s' }}
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-4 overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>

                    {/* Appearance Section */}
                    <div className="mb-4">
                        <label className="small fw-bold text-secondary text-uppercase tracking-wider mb-3 d-block ps-1">Appearance</label>
                        <div className="bg-light rounded-4 p-1 d-flex mb-3 border">
                            <button
                                className={`btn border-0 flex-grow-1 py-2 rounded-3 d-flex align-items-center justify-content-center gap-2 fw-medium transition-all ${currentTheme === 'light' ? 'bg-white shadow-sm text-dark' : 'text-muted'}`}
                                onClick={() => onThemeChange('light')}
                            >
                                <Sun size={16} /> Light
                            </button>
                            <button
                                className={`btn border-0 flex-grow-1 py-2 rounded-3 d-flex align-items-center justify-content-center gap-2 fw-medium transition-all ${currentTheme === 'dark' ? 'bg-white shadow-sm text-dark' : 'text-muted'}`}
                                onClick={() => onThemeChange('dark')}
                            >
                                <Moon size={16} /> Dark
                            </button>
                            <button
                                className={`btn border-0 flex-grow-1 py-2 rounded-3 d-flex align-items-center justify-content-center gap-2 fw-medium transition-all ${currentTheme === 'system' ? 'bg-white shadow-sm text-dark' : 'text-muted'}`}
                                onClick={() => onThemeChange('system')}
                            >
                                <Monitor size={16} /> System
                            </button>
                        </div>
                        <p className="small text-muted mb-0 ps-1">
                            {currentTheme === 'system'
                                ? 'Theme will follow your system preferences'
                                : `Using ${currentTheme} theme`}
                        </p>
                    </div>

                    {/* Data Control Section */}
                    <div className="mb-4">
                        <label className="small fw-bold text-secondary text-uppercase tracking-wider mb-3 d-block ps-1">Data & Storage</label>
                        <div className="d-flex flex-column gap-2">
                            <button
                                onClick={() => {
                                    if (window.confirm("Are you sure you want to clear the entire chat history?")) {
                                        onClearHistory();
                                        onClose();
                                    }
                                }}
                                className="btn btn-outline-danger w-100 text-start p-3 rounded-4 border hover-bg-danger-subtle border-danger-subtle transition d-flex align-items-center justify-content-between group"
                            >
                                <div className="d-flex align-items-center gap-3">
                                    <div className="p-2 rounded-3 bg-danger bg-opacity-10 text-danger">
                                        <Trash2 size={20} />
                                    </div>
                                    <div>
                                        <span className="d-block fw-semibold text-dark">Clear Chat History</span>
                                        <span className="small text-muted">Permanently remove all messages</span>
                                    </div>
                                </div>
                                <ChevronRight size={18} className="text-muted opacity-50" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-3 bg-light border-top text-center d-flex align-items-center justify-content-center gap-2">
                    <Info size={14} className="text-muted" />
                    <span className="small text-muted font-monospace">NovaChat AI v1.2.0 • Build 2026.02</span>
                </div>
            </div>
        </div>
    );
}
