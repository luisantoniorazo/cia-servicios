import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../lib/utils";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import { Cog, Lock, Mail, User, Building2 } from "lucide-react";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg";

export const Login = () => {
  const navigate = useNavigate();
  const { login, register, api } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    email: "",
    password: "",
    full_name: "",
    confirmPassword: "",
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const user = await login(loginForm.email, loginForm.password);
      toast.success(`Bienvenido, ${user.full_name}`);
      
      if (user.role === "super_admin") {
        navigate("/super-admin");
      } else {
        navigate("/dashboard");
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al iniciar sesión"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (registerForm.password !== registerForm.confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    
    setIsLoading(true);
    
    try {
      await register({
        email: registerForm.email,
        password: registerForm.password,
        full_name: registerForm.full_name,
        role: "user",
      });
      toast.success("Cuenta creada exitosamente");
      navigate("/dashboard");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al registrarse"));
    } finally {
      setIsLoading(false);
    }
  };

  const seedDemoData = async () => {
    setIsLoading(true);
    try {
      const response = await api.post("/seed-demo-data");
      toast.success("Datos de demostración creados. Usa: admin@cia-servicios.com / admin123");
      setLoginForm({ email: "admin@cia-servicios.com", password: "admin123" });
    } catch (error) {
      if (error.response?.data?.message === "Demo data already exists") {
        toast.info("Los datos de demostración ya existen");
        setLoginForm({ email: "admin@cia-servicios.com", password: "admin123" });
      } else {
        toast.error("Error al crear datos de demostración");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-bg flex items-center justify-center p-4" data-testid="login-page">
      <div className="w-full max-w-md space-y-6 animate-fade-in">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-white/10 backdrop-blur-sm p-4 rounded-lg">
              <img 
                src={LOGO_URL} 
                alt="CIA Servicios" 
                className="h-16 w-auto"
              />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white font-[Chivo]">CIA SERVICIOS</h1>
            <p className="text-slate-300 mt-2">Control Estratégico de Servicios y Proyectos</p>
          </div>
        </div>

        <Card className="border-0 shadow-2xl">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-2xl font-bold text-center">Acceso al Sistema</CardTitle>
            <CardDescription className="text-center">
              Ingresa tus credenciales para continuar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="login" data-testid="login-tab">Iniciar Sesión</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">Registrarse</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">Correo electrónico</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="Ingresa tu correo"
                        className="pl-9"
                        value={loginForm.email}
                        onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                        required
                        data-testid="login-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="Ingresa tu contraseña"
                        className="pl-9"
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                        required
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-primary hover:bg-primary/90" 
                    disabled={isLoading}
                    data-testid="login-submit-btn"
                  >
                    {isLoading ? "Cargando..." : "Iniciar Sesión"}
                  </Button>
                </form>
              </TabsContent>
              
              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name">Nombre completo</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="register-name"
                        type="text"
                        placeholder="Tu nombre completo"
                        className="pl-9"
                        value={registerForm.full_name}
                        onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })}
                        required
                        data-testid="register-name-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email">Correo electrónico</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="Tu correo electrónico"
                        className="pl-9"
                        value={registerForm.email}
                        onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                        required
                        data-testid="register-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="register-password"
                        type="password"
                        placeholder="••••••••"
                        className="pl-9"
                        value={registerForm.password}
                        onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                        required
                        data-testid="register-password-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-confirm">Confirmar contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="register-confirm"
                        type="password"
                        placeholder="••••••••"
                        className="pl-9"
                        value={registerForm.confirmPassword}
                        onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                        required
                        data-testid="register-confirm-input"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-primary hover:bg-primary/90" 
                    disabled={isLoading}
                    data-testid="register-submit-btn"
                  >
                    {isLoading ? "Cargando..." : "Crear Cuenta"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            <div className="mt-6 pt-6 border-t">
              <Button
                variant="outline"
                className="w-full"
                onClick={seedDemoData}
                disabled={isLoading}
                data-testid="seed-demo-btn"
              >
                <Cog className="mr-2 h-4 w-4" />
                Cargar Datos de Demostración
              </Button>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Crea datos de ejemplo para probar el sistema
              </p>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-slate-400">
          &copy; 2024 CIA Servicios. Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};

export default Login;
