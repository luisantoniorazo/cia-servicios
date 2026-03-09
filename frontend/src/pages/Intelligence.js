import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import {
  Sparkles,
  Brain,
  TrendingUp,
  FileText,
  Zap,
  Send,
  Loader2,
  Bot,
  User,
  RefreshCw,
  BarChart3,
} from "lucide-react";

export const Intelligence = () => {
  const { api, company } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickPrompts = [
    {
      icon: TrendingUp,
      label: "Análisis Financiero",
      prompt: "Dame un análisis de la situación financiera actual de la empresa, incluyendo facturación, cobranza y proyección.",
    },
    {
      icon: BarChart3,
      label: "Estado de Proyectos",
      prompt: "¿Cuál es el estado general de los proyectos activos? Identifica riesgos y oportunidades.",
    },
    {
      icon: FileText,
      label: "Pipeline Comercial",
      prompt: "Analiza el pipeline de cotizaciones y prospectos. ¿Qué probabilidad de conversión tenemos?",
    },
    {
      icon: Zap,
      label: "Recomendaciones",
      prompt: "Dame 3 recomendaciones accionables para mejorar la eficiencia operativa esta semana.",
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    const userMessage = prompt.trim();
    setPrompt("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await api.post("/ai/chat", {
        message: userMessage,
        context: `Empresa: ${company?.business_name || "N/A"}`,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.data.response, model: response.data.model },
      ]);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al comunicarse con IA"));
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Lo siento, hubo un error al procesar tu solicitud. Por favor intenta de nuevo.", error: true },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickPrompt = (promptText) => {
    setPrompt(promptText);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="intelligence-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-purple-500" />
            <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Inteligencia Empresarial</h1>
          </div>
          <p className="text-muted-foreground">Análisis avanzado y predicciones con IA</p>
        </div>
        {messages.length > 0 && (
          <Button variant="outline" onClick={clearChat} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Nueva conversación
          </Button>
        )}
      </div>

      {/* AI Status Card */}
      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-slate-900">Módulo de IA Activo</h3>
                <Badge className="bg-emerald-100 text-emerald-700">GPT-5.2</Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Powered by OpenAI • Análisis contextual de {company?.business_name || "tu empresa"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Quick Prompts */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="font-semibold text-slate-700">Consultas rápidas</h3>
          {quickPrompts.map((qp, idx) => (
            <Card
              key={idx}
              className="cursor-pointer hover:border-purple-300 hover:bg-purple-50/50 transition-colors"
              onClick={() => handleQuickPrompt(qp.prompt)}
            >
              <CardContent className="p-3 flex items-center gap-3">
                <qp.icon className="h-5 w-5 text-purple-500" />
                <span className="text-sm font-medium">{qp.label}</span>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Chat Area */}
        <Card className="lg:col-span-3">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-purple-500" />
              Asistente IA
            </CardTitle>
            <CardDescription>
              Pregunta sobre proyectos, finanzas, clientes o solicita análisis
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Messages */}
            <ScrollArea className="h-[400px] pr-4 mb-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                  <Brain className="h-12 w-12 mb-4 text-purple-200" />
                  <p className="font-medium">¿En qué puedo ayudarte hoy?</p>
                  <p className="text-sm mt-1">Pregunta sobre tu negocio o usa las consultas rápidas</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      {msg.role === "assistant" && (
                        <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                          <Bot className="h-4 w-4 text-purple-600" />
                        </div>
                      )}
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : msg.error
                            ? "bg-red-50 text-red-800 border border-red-200"
                            : "bg-slate-100 text-slate-800"
                        }`}
                      >
                        <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                        {msg.model && (
                          <div className="text-xs mt-2 opacity-60">Modelo: {msg.model}</div>
                        )}
                      </div>
                      {msg.role === "user" && (
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                          <User className="h-4 w-4 text-white" />
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-purple-600" />
                      </div>
                      <div className="bg-slate-100 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">Analizando...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* Input */}
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Escribe tu consulta aquí..."
                className="min-h-[60px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                data-testid="ai-prompt-input"
              />
              <Button
                type="submit"
                disabled={!prompt.trim() || isLoading}
                className="bg-purple-600 hover:bg-purple-700 px-6"
                data-testid="ai-send-btn"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Intelligence;
