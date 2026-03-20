import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { Shield, Lock, Mail, AlertTriangle } from "lucide-react";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg";

export const SuperAdminLogin = () => {
  const navigate = useNavigate();
  const { superAdminLogin, setupSuperAdmin } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  
  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await superAdminLogin(loginForm.email, loginForm.password);
      toast.success("Acceso concedido");
      navigate("/admin-portal/dashboard");
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        toast.error(detail);
      } else {
        toast.error("Error de autenticación");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetup = async () => {
    setIsLoading(true);
    try {
      const response = await setupSuperAdmin();
      toast.success("Super Admin creado exitosamente");
      setLoginForm({
        email: response.email,
        password: response.password,
      });
      setShowSetup(false);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail === "Super Admin ya existe") {
        toast.info("Super Admin ya existe. Por favor inicia sesión.");
      } else {
        toast.error("Error al crear Super Admin");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4" data-testid="super-admin-login-page">
      <div className="w-full max-w-md space-y-6 animate-fade-in">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-amber-500/20 p-4 rounded-full">
              <Shield className="h-12 w-12 text-amber-500" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white font-[Chivo]">Portal Super Admin</h1>
            <p className="text-slate-400 mt-2">Gestión de Licencias y Empresas</p>
          </div>
        </div>

        {/* Warning */}
        <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-sm text-amber-200 text-sm">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>Acceso restringido. Solo administradores autorizados.</span>
        </div>

        <Card className="border-0 shadow-2xl bg-slate-800/50 backdrop-blur">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-2xl font-bold text-center text-white">Acceso Administrativo</CardTitle>
            <CardDescription className="text-center text-slate-400">
              Ingresa tus credenciales de Super Admin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-300">Correo electrónico</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="Ingresa tu correo"
                    className="pl-9 bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                    data-testid="super-admin-email-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-300">Contraseña</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Ingresa tu contraseña"
                    className="pl-9 bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                    data-testid="super-admin-password-input"
                  />
                </div>
              </div>
              <Button
                type="submit"
                className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
                disabled={isLoading}
                data-testid="super-admin-login-btn"
              >
                {isLoading ? "Verificando..." : "Acceder al Portal"}
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-700">
              <Button
                variant="outline"
                className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
                onClick={handleSetup}
                disabled={isLoading}
                data-testid="setup-super-admin-btn"
              >
                <Shield className="mr-2 h-4 w-4" />
                Configurar Super Admin Inicial
              </Button>
              <p className="text-xs text-slate-500 text-center mt-2">
                Solo usar si es la primera configuración del sistema
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-center gap-3">
          <img src={LOGO_URL} alt="CIA" className="h-8 w-auto opacity-50" />
          <p className="text-sm text-slate-500">
            CIA SERVICIOS - Sistema de Control
          </p>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminLogin;
