import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("cia_token"));
  const [loading, setLoading] = useState(true);
  const [company, setCompany] = useState(null);

  const api = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
      "Content-Type": "application/json",
    },
  });

  api.interceptors.request.use((config) => {
    const storedToken = localStorage.getItem("cia_token");
    if (storedToken) {
      config.headers.Authorization = `Bearer ${storedToken}`;
    }
    return config;
  });

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        logout();
      }
      return Promise.reject(error);
    }
  );

  const fetchUser = useCallback(async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
      
      if (response.data.company_id) {
        const companyResponse = await api.get(`/companies/${response.data.company_id}`);
        setCompany(companyResponse.data);
      }
    } catch (error) {
      console.error("Error fetching user:", error);
      logout();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token, fetchUser]);

  const login = async (email, password) => {
    const response = await api.post("/auth/login", { email, password });
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem("cia_token", access_token);
    setToken(access_token);
    setUser(userData);
    
    if (userData.company_id) {
      const companyResponse = await api.get(`/companies/${userData.company_id}`);
      setCompany(companyResponse.data);
    }
    
    return userData;
  };

  const register = async (userData) => {
    const response = await api.post("/auth/register", userData);
    const { access_token, user: newUser } = response.data;
    
    localStorage.setItem("cia_token", access_token);
    setToken(access_token);
    setUser(newUser);
    
    return newUser;
  };

  const logout = () => {
    localStorage.removeItem("cia_token");
    setToken(null);
    setUser(null);
    setCompany(null);
  };

  const isSuperAdmin = () => user?.role === "super_admin";
  const isAdmin = () => user?.role === "admin" || user?.role === "super_admin";
  const isManager = () => user?.role === "manager" || isAdmin();

  const value = {
    user,
    token,
    company,
    loading,
    login,
    register,
    logout,
    isSuperAdmin,
    isAdmin,
    isManager,
    api,
    setCompany,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
