/**
 * Conversations Context
 * Manages conversation state (sidebar, active chat, messages)
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';
import * as conversationsApi from '../api/conversations';

const ConversationsContext = createContext(null);

export const useConversations = () => {
    const context = useContext(ConversationsContext);
    if (!context) {
        throw new Error('useConversations must be used within a ConversationsProvider');
    }
    return context;
};

export const ConversationsProvider = ({ children }) => {
    const { isAuthenticated } = useAuth();

    // State
    const [conversations, setConversations] = useState([]);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoadingSidebar, setIsLoadingSidebar] = useState(false);
    const [isLoadingMessages, setIsLoadingMessages] = useState(false);
    const [messagesPage, setMessagesPage] = useState(1);
    const [hasMoreMessages, setHasMoreMessages] = useState(false);

    // Load sidebar when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            loadSidebar();
        } else {
            // Clear state on logout
            setConversations([]);
            setActiveConversationId(null);
            setMessages([]);
        }
    }, [isAuthenticated]);

    // Load sidebar conversations
    const loadSidebar = useCallback(async () => {
        setIsLoadingSidebar(true);
        try {
            const response = await conversationsApi.getSidebar();
            setConversations(response.conversations);
        } catch (error) {
            console.error('Failed to load sidebar:', error);
        } finally {
            setIsLoadingSidebar(false);
        }
    }, []);

    // Select a conversation and load its messages
    const selectConversation = useCallback(async (conversationId) => {
        if (conversationId === activeConversationId) return;

        setActiveConversationId(conversationId);
        setMessages([]);
        setMessagesPage(1);
        setIsLoadingMessages(true);

        try {
            const response = await conversationsApi.getMessages(conversationId, 1, 30);
            setMessages(response.messages);
            setHasMoreMessages(response.has_more);
        } catch (error) {
            console.error('Failed to load messages:', error);
        } finally {
            setIsLoadingMessages(false);
        }
    }, [activeConversationId]);

    // Load more messages (pagination)
    const loadMoreMessages = useCallback(async () => {
        if (!activeConversationId || isLoadingMessages || !hasMoreMessages) return;

        const nextPage = messagesPage + 1;
        setIsLoadingMessages(true);

        try {
            const response = await conversationsApi.getMessages(activeConversationId, nextPage, 30);
            setMessages(prev => [...response.messages, ...prev]);
            setMessagesPage(nextPage);
            setHasMoreMessages(response.has_more);
        } catch (error) {
            console.error('Failed to load more messages:', error);
        } finally {
            setIsLoadingMessages(false);
        }
    }, [activeConversationId, messagesPage, isLoadingMessages, hasMoreMessages]);

    // Create new conversation
    const createNewConversation = useCallback(async (firstMessage = null) => {
        try {
            const data = firstMessage ? { first_message: firstMessage } : {};
            const newConversation = await conversationsApi.createConversation(data);

            // Add to sidebar (optimistic)
            setConversations(prev => [{
                id: newConversation.id,
                title: newConversation.title,
                last_message: null,
                updated_at: newConversation.updated_at,
            }, ...prev]);

            setActiveConversationId(newConversation.id);
            setMessages([]);

            return newConversation;
        } catch (error) {
            console.error('Failed to create conversation:', error);
            throw error;
        }
    }, []);

    // Start new chat (clear active)
    const startNewChat = useCallback(() => {
        setActiveConversationId(null);
        setMessages([]);
    }, []);

    // Delete conversation
    const deleteConversation = useCallback(async (conversationId) => {
        try {
            await conversationsApi.deleteConversation(conversationId);
            setConversations(prev => prev.filter(c => c.id !== conversationId));

            if (activeConversationId === conversationId) {
                setActiveConversationId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
            throw error;
        }
    }, [activeConversationId]);

    // Update conversation title
    const updateTitle = useCallback(async (conversationId, newTitle) => {
        try {
            await conversationsApi.updateConversationTitle(conversationId, newTitle);
            setConversations(prev => prev.map(c =>
                c.id === conversationId ? { ...c, title: newTitle } : c
            ));
        } catch (error) {
            console.error('Failed to update title:', error);
            throw error;
        }
    }, []);

    // Add message to current conversation (optimistic)
    const addMessage = useCallback((message) => {
        setMessages(prev => [...prev, message]);
    }, []);

    // Update last message in current conversation
    const updateLastMessage = useCallback((updater) => {
        setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages.length > 0) {
                newMessages[newMessages.length - 1] =
                    typeof updater === 'function'
                        ? updater(newMessages[newMessages.length - 1])
                        : updater;
            }
            return newMessages;
        });
    }, []);

    // Update sidebar after sending message
    const updateSidebarItem = useCallback((conversationId, lastMessage) => {
        setConversations(prev => {
            const updated = prev.map(c =>
                c.id === conversationId
                    ? { ...c, last_message: lastMessage, updated_at: new Date().toISOString() }
                    : c
            );
            // Move to top
            updated.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
            return updated;
        });
    }, []);

    const value = {
        // State
        conversations,
        activeConversationId,
        messages,
        isLoadingSidebar,
        isLoadingMessages,
        hasMoreMessages,

        // Actions
        loadSidebar,
        selectConversation,
        loadMoreMessages,
        createNewConversation,
        startNewChat,
        deleteConversation,
        updateTitle,
        addMessage,
        updateLastMessage,
        updateSidebarItem,
    };

    return (
        <ConversationsContext.Provider value={value}>
            {children}
        </ConversationsContext.Provider>
    );
};

export default ConversationsContext;
