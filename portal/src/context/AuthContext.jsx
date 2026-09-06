import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('idp_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('idp_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [activeWorkspace, setActiveWorkspace] = useState(() => {
    return localStorage.getItem('idp_active_ws') || 'ws-dev';
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verifySession() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch('/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
          localStorage.setItem('idp_user', JSON.stringify(userData));
          if (userData.workspaces && userData.workspaces.length > 0) {
            if (!userData.workspaces.includes(activeWorkspace)) {
              setActiveWorkspace(userData.workspaces[0]);
              localStorage.setItem('idp_active_ws', userData.workspaces[0]);
            }
          }
        } else if (res.status === 401) {
          logout();
        }
      } catch (err) {
        console.error('Session verification failed:', err);
      } finally {
        setLoading(false);
      }
    }
    verifySession();
  }, [token]);

  const login = async (username, password) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Invalid username or password');
    }

    const data = await res.json();
    const accessToken = data.access_token;
    setToken(accessToken);
    localStorage.setItem('idp_token', accessToken);

    // Fetch user profile immediately
    const meRes = await fetch('/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    });
    if (meRes.ok) {
      const userData = await meRes.json();
      setUser(userData);
      localStorage.setItem('idp_user', JSON.stringify(userData));
      if (userData.workspaces && userData.workspaces.length > 0) {
        setActiveWorkspace(userData.workspaces[0]);
        localStorage.setItem('idp_active_ws', userData.workspaces[0]);
      }
      return userData;
    }
    return null;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('idp_token');
    localStorage.removeItem('idp_user');
  };

  const switchWorkspace = (ws) => {
    setActiveWorkspace(ws);
    localStorage.setItem('idp_active_ws', ws);
  };

  const isAdmin = user?.role === 'platform_admin';

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        activeWorkspace,
        switchWorkspace,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isAdmin,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
