/**
 * Sidebar Component
 * Displays conversation history with search and new chat functionality
 */
import React, { useState } from 'react';
import {
    MessageSquare,
    Plus,
    Search,
    Trash2,
    Edit3,
    Check,
    X,
    Clock,
    Loader
} from 'lucide-react';
import { useConversations } from '../contexts/ConversationsContext';

const Sidebar = ({ isOpen, onClose, theme = 'light' }) => {
    const {
        conversations,
        activeConversationId,
        isLoadingSidebar,
        selectConversation,
        startNewChat,
        deleteConversation,
        updateTitle,
    } = useConversations();

    const isDark = theme === 'dark';
    const themeStyles = {
        gradient: isDark ? 'linear-gradient(135deg, #22D3EE, #3B82F6)' : 'linear-gradient(135deg, #FF6B6B, #FF8E53)',
        activeItemBg: isDark ? 'rgba(34, 211, 238, 0.1)' : '#FFE5E5',
        activeIconColor: isDark ? '#22D3EE' : '#FF6B6B',
        sidebarBg: isDark ? '#111827' : '#FAFAFA',
        borderColor: isDark ? '#374151' : '#E5E7EB',
        textPrimary: isDark ? '#F9FAFB' : '#1F2937',
        textSecondary: isDark ? '#9CA3AF' : '#6B7280',
        inputBg: isDark ? '#1F2937' : '#F3F4F6'
    };

    const [searchQuery, setSearchQuery] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [deletingId, setDeletingId] = useState(null);

    // Filter conversations by search
    const filteredConversations = conversations.filter(conv =>
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.last_message?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Format relative time
    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    // Start editing title
    const handleStartEdit = (e, conv) => {
        e.stopPropagation();
        setEditingId(conv.id);
        setEditTitle(conv.title);
    };

    // Save edited title
    const handleSaveEdit = async (e) => {
        e.stopPropagation();
        if (editTitle.trim()) {
            await updateTitle(editingId, editTitle.trim());
        }
        setEditingId(null);
    };

    // Cancel editing
    const handleCancelEdit = (e) => {
        e.stopPropagation();
        setEditingId(null);
    };

    // Handle delete
    const handleDelete = async (e, convId) => {
        e.stopPropagation();
        setDeletingId(convId);
        try {
            await deleteConversation(convId);
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <div
            className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
            style={{
                width: '280px',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: themeStyles.sidebarBg,
                borderRight: `1px solid ${themeStyles.borderColor}`,
            }}
        >
            {/* Header */}
            <div className="p-3 border-bottom d-flex gap-2" style={{ borderColor: themeStyles.borderColor }}>
                <button
                    onClick={startNewChat}
                    className="btn flex-grow-1 d-flex align-items-center justify-content-center gap-2 py-2"
                    style={{
                        background: themeStyles.gradient,
                        border: 'none',
                        color: 'white',
                        borderRadius: '10px',
                        fontWeight: '500',
                    }}
                >
                    <Plus size={18} />
                    New Chat
                </button>

                {/* Mobile Close Button */}
                <button
                    className="btn d-md-none d-flex align-items-center justify-content-center p-2"
                    onClick={onClose}
                    style={{
                        color: themeStyles.textSecondary,
                        backgroundColor: themeStyles.inputBg,
                        borderRadius: '10px'
                    }}
                >
                    <X size={20} />
                </button>
            </div>

            {/* Search */}
            <div className="px-3 py-2">
                <div className="position-relative">
                    <Search
                        size={16}
                        className="position-absolute"
                        style={{ left: '12px', top: '50%', transform: 'translateY(-50%)', color: themeStyles.textSecondary }}
                    />
                    <input
                        type="text"
                        placeholder="Search conversations..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="form-control form-control-sm"
                        style={{
                            paddingLeft: '36px',
                            backgroundColor: themeStyles.inputBg,
                            border: 'none',
                            borderRadius: '8px',
                            color: themeStyles.textPrimary
                        }}
                    />
                </div>
            </div>

            {/* Conversations List */}
            <div
                className="flex-grow-1 overflow-auto px-2 py-1"
                style={{ scrollbarWidth: 'thin' }}
            >
                {isLoadingSidebar ? (
                    <div className="d-flex justify-content-center align-items-center py-4">
                        <Loader size={24} className="animate-spin" style={{ color: themeStyles.textSecondary }} />
                    </div>
                ) : filteredConversations.length === 0 ? (
                    <div className="text-center py-4 small" style={{ color: themeStyles.textSecondary }}>
                        {searchQuery ? 'No matching conversations' : 'No conversations yet'}
                    </div>
                ) : (
                    filteredConversations.map(conv => (
                        <div
                            key={conv.id}
                            onClick={() => selectConversation(conv.id)}
                            className={`conversation-item p-2 rounded-2 mb-1 cursor-pointer`}
                            style={{
                                backgroundColor: activeConversationId === conv.id ? themeStyles.activeItemBg : 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                            }}
                        >
                            <div className="d-flex align-items-start gap-2">
                                <MessageSquare
                                    size={16}
                                    className="mt-1 flex-shrink-0"
                                    style={{ color: activeConversationId === conv.id ? themeStyles.activeIconColor : themeStyles.textSecondary }}
                                />

                                <div className="flex-grow-1 min-width-0">
                                    {editingId === conv.id ? (
                                        <div className="d-flex gap-1">
                                            <input
                                                type="text"
                                                value={editTitle}
                                                onChange={(e) => setEditTitle(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="form-control form-control-sm py-0"
                                                style={{ fontSize: '13px', backgroundColor: themeStyles.inputBg, color: themeStyles.textPrimary, border: `1px solid ${themeStyles.borderColor}` }}
                                                autoFocus
                                            />
                                            <button
                                                className="btn btn-link p-0 text-success"
                                                onClick={handleSaveEdit}
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                className="btn btn-link p-0"
                                                onClick={handleCancelEdit}
                                                style={{ color: themeStyles.textSecondary }}
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            <div
                                                className="fw-medium text-truncate"
                                                style={{ fontSize: '13px', color: themeStyles.textPrimary }}
                                            >
                                                {conv.title}
                                            </div>
                                            {conv.last_message && (
                                                <div
                                                    className="text-truncate"
                                                    style={{ fontSize: '11px', color: themeStyles.textSecondary }}
                                                >
                                                    {conv.last_message}
                                                </div>
                                            )}
                                            <div
                                                className="d-flex align-items-center gap-1 mt-1"
                                                style={{ fontSize: '10px', color: themeStyles.textSecondary }}
                                            >
                                                <Clock size={10} />
                                                {formatTime(conv.updated_at)}
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Actions */}
                                {editingId !== conv.id && (
                                    <div className="conversation-actions d-flex gap-1">
                                        <button
                                            className="btn btn-link p-1"
                                            onClick={(e) => handleStartEdit(e, conv)}
                                            title="Rename"
                                            style={{ color: themeStyles.textSecondary }}
                                        >
                                            <Edit3 size={12} />
                                        </button>
                                        <button
                                            className="btn btn-link p-1 text-danger"
                                            onClick={(e) => handleDelete(e, conv.id)}
                                            disabled={deletingId === conv.id}
                                            title="Delete"
                                        >
                                            {deletingId === conv.id ? (
                                                <Loader size={12} className="animate-spin" />
                                            ) : (
                                                <Trash2 size={12} />
                                            )}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Footer */}
            <div className="p-2 border-top text-center" style={{ borderColor: themeStyles.borderColor }}>
                <small style={{ fontSize: '10px', color: themeStyles.textSecondary }}>
                    {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
                </small>
            </div>
        </div>
    );
};

export default Sidebar;
