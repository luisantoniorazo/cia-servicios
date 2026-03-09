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
  const [companySlug, setCompanySlug] = useState(localStorage.getItem("cia_company_slug"));

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
        // Don't auto-logout on 401 for login endpoints
        const url = error.config?.url || "";
        if (!url.includes("/login") && !url.includes("/setup") && !url.includes("/info")) {
          logout();
        }
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

  // Super Admin Login
  const superAdminLogin = async (email, password, admin_key) => {
    const response = await api.post("/super-admin/login", { email, password, admin_key });
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem("cia_token", access_token);
    localStorage.removeItem("cia_company_slug");
    setToken(access_token);
    setUser(userData);
    setCompany(null);
    setCompanySlug(null);
    
    return userData;
  };

  // Super Admin Setup
  const setupSuperAdmin = async () => {
    const response = await api.post("/super-admin/setup");
    return response.data;
  };

  // Super Admin Logout
  const superAdminLogout = () => {
    localStorage.removeItem("cia_token");
    localStorage.removeItem("cia_company_slug");
    setToken(null);
    setUser(null);
    setCompany(null);
    setCompanySlug(null);
  };

  // Company Login
  const companyLogin = async (slug, email, password) => {
    const response = await api.post(`/empresa/${slug}/login`, { email, password });
    const { access_token, user: userData, company: companyData } = response.data;
    
    localStorage.setItem("cia_token", access_token);
    localStorage.setItem("cia_company_slug", slug);
    setToken(access_token);
    setUser(userData);
    setCompany(companyData);
    setCompanySlug(slug);
    
    return { user: userData, company: companyData };
  };

  // Company Logout
  const logout = () => {
    const savedSlug = localStorage.getItem("cia_company_slug");
    localStorage.removeItem("cia_token");
    localStorage.removeItem("cia_company_slug");
    setToken(null);
    setUser(null);
    setCompany(null);
    setCompanySlug(null);
    return savedSlug;
  };

  const isSuperAdmin = () => user?.role === "super_admin";
  const isAdmin = () => user?.role === "admin" || user?.role === "super_admin";
  const isManager = () => user?.role === "manager" || isAdmin();

  const value = {
    user,
    token,
    company,
    companySlug,
    loading,
    // Super Admin
    superAdminLogin,
    setupSuperAdmin,
    superAdminLogout,
    // Company
    companyLogin,
    logout,
    // Helpers
    isSuperAdmin,
    isAdmin,
    isManager,
    api,
    setCompany,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
