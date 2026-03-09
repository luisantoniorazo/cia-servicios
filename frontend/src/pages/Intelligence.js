import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import {
  Sparkles,
  Brain,
  TrendingUp,
  FileText,
  Zap,
  Lock,
  Send,
  Loader2,
} from "lucide-react";

export const Intelligence = () => {
  const { company } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const features = [
    {
      icon: Brain,
      title: "Análisis Predictivo",
      description: "Predicción de proyectos y servicios basada en datos históricos",
      status: "coming_soon",
    },
    {
      icon: TrendingUp,
      title: "Análisis Financiero",
      description: "Insights automáticos sobre rentabilidad y flujo de efectivo",
      status: "coming_soon",
    },
    {
      icon: FileText,
      title: "Automatización de Cotizaciones",
      description: "Generación automática de cotizaciones basadas en proyectos similares",
      status: "coming_soon",
    },
    {
      icon: Zap,
      title: "Optimización de Recursos",
      description: "Recomendaciones para optimizar tiempos y costos",
      status: "coming_soon",
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setResponse("");

    // Simulated response - will be replaced with actual AI integration
    setTimeout(() => {
      setResponse(`**Análisis de CIA SERVICIOS**

Basado en tu consulta: "${prompt}"

Esta funcionalidad de Inteligencia Artificial está siendo desarrollada. Próximamente podrás:

1. **Obtener insights** sobre tus proyectos y clientes
2. **Predecir** tendencias de negocio
3. **Automatizar** la generación de cotizaciones
4. **Optimizar** recursos y tiempos

La integración con OpenAI GPT-5.2, Claude Sonnet 4.5 y Gemini 3 Flash está preparada y lista para activarse.

*Contacta al administrador para activar las funcionalidades de IA.*`);
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="intelligence-page">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-purple-500" />
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Inteligencia Empresarial</h1>
        </div>
        <p className="text-muted-foreground">Análisis avanzado y predicciones con IA</p>
      </div>

      {/* AI Status Card */}
      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-full">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Módulo de IA</h3>
                <p className="text-sm text-muted-foreground">
                  Arquitectura preparada para OpenAI, Claude y Gemini
                </p>
              </div>
            </div>
            <Badge variant="outline" className="border-purple-300 text-purple-700">
              <Lock className="h-3 w-3 mr-1" />
              Próximamente
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {features.map((feature, index) => (
          <Card key={index} className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-100/50 to-transparent rounded-bl-full" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="p-2 bg-purple-100 rounded-sm w-fit">
                  <feature.icon className="h-5 w-5 text-purple-600" />
                </div>
                <Badge variant="outline" className="text-xs">
                  Próximamente
                </Badge>
              </div>
              <CardTitle className="text-lg mt-3">{feature.title}</CardTitle>
              <CardDescription>{feature.description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* AI Chat Interface (Demo) */}
      <Card data-testid="ai-chat-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Asistente IA
          </CardTitle>
          <CardDescription>
            Consulta información sobre tu empresa (versión demo)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Textarea
              placeholder="Ejemplo: ¿Cuáles son mis proyectos más rentables? ¿Cómo puedo mejorar mi tasa de conversión?"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              className="resize-none"
              data-testid="ai-prompt-input"
            />
            <div className="flex justify-end">
              <Button
                type="submit"
                className="bg-purple-600 hover:bg-purple-700"
                disabled={isLoading || !prompt.trim()}
                data-testid="ai-submit-btn"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analizando...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Consultar
                  </>
                )}
              </Button>
            </div>
          </form>

          {response && (
            <div className="p-4 bg-slate-50 rounded-sm border-l-4 border-purple-500 animate-slide-in">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-purple-500" />
                <span className="font-medium text-sm text-purple-700">Respuesta IA</span>
              </div>
              <div className="prose prose-sm max-w-none">
                {response.split("\n").map((line, i) => (
                  <p key={i} className="mb-2 text-slate-700">
                    {line.startsWith("**") ? (
                      <strong>{line.replace(/\*\*/g, "")}</strong>
                    ) : line.startsWith("*") ? (
                      <em className="text-muted-foreground">{line.replace(/\*/g, "")}</em>
                    ) : (
                      line
                    )}
                  </p>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integration Info */}
      <Card>
        <CardHeader>
          <CardTitle>Integraciones de IA Disponibles</CardTitle>
          <CardDescription>Modelos de lenguaje configurados para este sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-sm">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 bg-emerald-100 rounded flex items-center justify-center">
                  <span className="text-emerald-700 font-bold text-xs">GPT</span>
                </div>
                <div>
                  <h4 className="font-medium">OpenAI GPT-5.2</h4>
                  <p className="text-xs text-muted-foreground">Análisis avanzado</p>
                </div>
              </div>
            </div>
            <div className="p-4 border rounded-sm">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 bg-orange-100 rounded flex items-center justify-center">
                  <span className="text-orange-700 font-bold text-xs">C</span>
                </div>
                <div>
                  <h4 className="font-medium">Claude Sonnet 4.5</h4>
                  <p className="text-xs text-muted-foreground">Análisis detallado</p>
                </div>
              </div>
            </div>
            <div className="p-4 border rounded-sm">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                  <span className="text-blue-700 font-bold text-xs">G</span>
                </div>
                <div>
                  <h4 className="font-medium">Gemini 3 Flash</h4>
                  <p className="text-xs text-muted-foreground">Respuestas rápidas</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Intelligence;
