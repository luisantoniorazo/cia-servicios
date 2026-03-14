import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";
import { Lock, Mail, ArrowLeft, CheckCircle, Eye, EyeOff } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const ForgotPassword = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/request-password-reset`, {
        email,
        company_slug: slug || null,
      });
      setSent(true);
      toast.success("Instrucciones enviadas a tu correo");
    } catch (error) {
      toast.error("Error al enviar solicitud");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="login-bg flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-emerald-600" />
              </div>
              <h2 className="text-xl font-semibold">¡Correo Enviado!</h2>
              <p className="text-muted-foreground">
                Si el correo <strong>{email}</strong> está registrado, recibirás instrucciones para restablecer tu contraseña.
              </p>
              <p className="text-sm text-muted-foreground">
                Revisa tu bandeja de entrada y spam.
              </p>
              <Button
                variant="outline"
                onClick={() => navigate(slug ? `/empresa/${slug}/login` : "/admin-portal")}
                className="mt-4"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Volver al Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="login-bg flex items-center justify-center p-4" data-testid="forgot-password-page">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-2">
            <Mail className="h-6 w-6 text-primary" />
          </div>
          <CardTitle>Recuperar Contraseña</CardTitle>
          <CardDescription>
            Ingresa tu correo electrónico y te enviaremos instrucciones
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Correo Electrónico</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                required
                data-testid="forgot-email-input"
              />
            </div>
            <Button type="submit" className="w-full btn-industrial" disabled={loading}>
              {loading ? "Enviando..." : "Enviar Instrucciones"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => navigate(slug ? `/empresa/${slug}/login` : "/admin-portal")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver al Login
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export const ResetPassword = () => {
  const { token, slug } = useParams();
  const navigate = useNavigate();
  const [tokenValid, setTokenValid] = useState(null);
  const [email, setEmail] = useState("");
  const [passwords, setPasswords] = useState({ new: "", confirm: "" });
  const [showPasswords, setShowPasswords] = useState({ new: false, confirm: false });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    verifyToken();
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/verify-reset-token/${token}`);
      setTokenValid(response.data.valid);
      setEmail(response.data.email || "");
    } catch (error) {
      setTokenValid(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (passwords.new !== passwords.confirm) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    if (passwords.new.length < 8) {
      toast.error("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/reset-password`, {
        token,
        new_password: passwords.new,
      });
      setSuccess(true);
      toast.success("Contraseña actualizada correctamente");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al restablecer contraseña");
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === null) {
    return (
      <div className="login-bg flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="login-bg flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <Lock className="h-6 w-6 text-red-600" />
              </div>
              <h2 className="text-xl font-semibold">Enlace Inválido</h2>
              <p className="text-muted-foreground">
                Este enlace ha expirado o ya fue utilizado. Solicita uno nuevo.
              </p>
              <Button
                onClick={() => navigate(slug ? `/empresa/${slug}/forgot-password` : "/forgot-password")}
                className="btn-industrial"
              >
                Solicitar Nuevo Enlace
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (success) {
    return (
      <div className="login-bg flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-emerald-600" />
              </div>
              <h2 className="text-xl font-semibold">¡Contraseña Actualizada!</h2>
              <p className="text-muted-foreground">
                Tu contraseña ha sido restablecida correctamente. Ya puedes iniciar sesión.
              </p>
              <Button
                onClick={() => navigate(slug ? `/empresa/${slug}/login` : "/admin-portal")}
                className="btn-industrial"
              >
                Ir al Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="login-bg flex items-center justify-center p-4" data-testid="reset-password-page">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-2">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <CardTitle>Nueva Contraseña</CardTitle>
          <CardDescription>
            Crea una nueva contraseña para <strong>{email}</strong>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Nueva Contraseña</Label>
              <div className="relative">
                <Input
                  type={showPasswords.new ? "text" : "password"}
                  value={passwords.new}
                  onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                  placeholder="••••••••"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                >
                  {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">Mínimo 8 caracteres</p>
            </div>

            <div className="space-y-2">
              <Label>Confirmar Contraseña</Label>
              <div className="relative">
                <Input
                  type={showPasswords.confirm ? "text" : "password"}
                  value={passwords.confirm}
                  onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                  placeholder="••••••••"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                >
                  {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            <Button type="submit" className="w-full btn-industrial" disabled={loading}>
              {loading ? "Actualizando..." : "Actualizar Contraseña"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default ForgotPassword;
