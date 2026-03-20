import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { toast } from "sonner";
import { Building2, Lock, Mail, AlertTriangle } from "lucide-react";

export const CompanyLogin = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { companyLogin, api } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [loadingCompany, setLoadingCompany] = useState(true);
  const [error, setError] = useState(null);
  
  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  useEffect(() => {
    fetchCompanyInfo();
  }, [slug]);

  const fetchCompanyInfo = async () => {
    try {
      const response = await api.get(`/empresa/${slug}/info`);
      setCompanyInfo(response.data);
      setError(null);
    } catch (err) {
      setError("Empresa no encontrada");
    } finally {
      setLoadingCompany(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await companyLogin(slug, loginForm.email, loginForm.password);
      toast.success("Bienvenido");
      navigate(`/empresa/${slug}/dashboard`);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        toast.error(detail);
      } else {
        toast.error("Credenciales inválidas");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (loadingCompany) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          <Skeleton className="h-20 w-20 rounded-full mx-auto" />
          <Skeleton className="h-8 w-48 mx-auto" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center py-12">
            <AlertTriangle className="h-16 w-16 text-amber-500 mb-4" />
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Empresa no encontrada</h2>
            <p className="text-muted-foreground text-center mb-6">
              La empresa "{slug}" no existe o no está disponible.
            </p>
            <Button variant="outline" onClick={() => navigate("/")}>
              Volver al inicio
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="login-bg flex items-center justify-center p-3 sm:p-4" data-testid="company-login-page">
      <div className="w-full max-w-md space-y-4 sm:space-y-6 animate-fade-in">
        {/* Company Header */}
        <div className="text-center space-y-3 sm:space-y-4">
          <div className="flex justify-center">
            {(companyInfo?.logo_url || companyInfo?.logo_file) ? (
              <div className="bg-white/10 backdrop-blur-sm p-3 sm:p-4 rounded-lg">
                <img
                  src={companyInfo.logo_url || (companyInfo.logo_file ? `data:image/jpeg;base64,${companyInfo.logo_file}` : '')}
                  alt={companyInfo.business_name}
                  className="h-12 sm:h-16 w-auto"
                  data-testid="company-logo"
                />
              </div>
            ) : (
              <div className="bg-white/10 backdrop-blur-sm p-3 sm:p-4 rounded-lg">
                <Building2 className="h-12 w-12 sm:h-16 sm:w-16 text-white" />
              </div>
            )}
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white font-[Chivo]">
              {companyInfo?.business_name}
            </h1>
            <p className="text-slate-300 mt-1 sm:mt-2 text-sm sm:text-base">Sistema de Control Empresarial</p>
          </div>
        </div>

        <Card className="border-0 shadow-2xl">
          <CardHeader className="space-y-1 pb-3 sm:pb-4 p-4 sm:p-6">
            <CardTitle className="text-xl sm:text-2xl font-bold text-center">Iniciar Sesión</CardTitle>
            <CardDescription className="text-center text-xs sm:text-sm">
              Ingresa tus credenciales asignadas
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <form onSubmit={handleLogin} className="space-y-3 sm:space-y-4">
              <div className="space-y-1.5 sm:space-y-2">
                <Label htmlFor="email" className="text-sm">Correo electrónico</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="usuario@empresa.com"
                    className="pl-9 h-10 sm:h-11"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                    data-testid="company-email-input"
                  />
                </div>
              </div>
              <div className="space-y-1.5 sm:space-y-2">
                <Label htmlFor="password" className="text-sm">Contraseña</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-9 h-10 sm:h-11"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                    data-testid="company-password-input"
                  />
                </div>
              </div>
              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90 h-10 sm:h-11"
                disabled={isLoading}
                data-testid="company-login-btn"
              >
                {isLoading ? "Verificando..." : "Iniciar Sesión"}
              </Button>
            </form>

            <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t text-center">
              <button
                type="button"
                onClick={() => navigate(`/empresa/${slug}/forgot-password`)}
                className="text-xs sm:text-sm text-primary hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs sm:text-sm text-slate-400">
          &copy; 2024 CIA Servicios. Control Integral Administrativo.
        </p>
      </div>
    </div>
  );
};

export default CompanyLogin;
