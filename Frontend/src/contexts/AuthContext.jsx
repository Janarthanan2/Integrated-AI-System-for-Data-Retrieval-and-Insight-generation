/**
 * Authentication Context
 * Provides user authentication state throughout the app
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getCurrentUser, login as apiLogin, register as apiRegister, logout as apiLogout } from '../api/auth';
import { getAuthToken, removeAuthToken } from '../api/config';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    // Check for existing token on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = getAuthToken();
            if (token) {
                try {
                    const userData = await getCurrentUser();
                    setUser(userData);
                    setIsAuthenticated(true);
                } catch (error) {
                    console.error('Token validation failed:', error);
                    removeAuthToken();
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    const login = useCallback(async (credentials) => {
        setIsLoading(true);
        try {
            const response = await apiLogin(credentials);
            setUser(response.user);
            setIsAuthenticated(true);
            return response;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const register = useCallback(async (userData) => {
        setIsLoading(true);
        try {
            const response = await apiRegister(userData);
            setUser(response.user);
            setIsAuthenticated(true);
            return response;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        apiLogout();
        setUser(null);
        setIsAuthenticated(false);
    }, []);

    const value = {
        user,
        isLoading,
        isAuthenticated,
        login,
        register,
        logout,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
