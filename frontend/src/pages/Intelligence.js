import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage, formatDate } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  Sparkles,
  Brain,
  Send,
  Loader2,
  Bot,
  User,
  RefreshCw,
  Paperclip,
  Save,
  History,
  Trash2,
  MessageSquare,
  X,
  File,
  Image,
} from "lucide-react";

export const Intelligence = () => {
  const { api, company, user } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [savedConversations, setSavedConversations] = useState([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSavedConversations();
  }, []);

  const fetchSavedConversations = async () => {
    try {
      const response = await api.get("/ai/conversations");
      setSavedConversations(response.data);
    } catch (error) {
      console.log("No saved conversations");
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    const validFiles = files.filter(file => {
      if (file.size > maxSize) {
        toast.error(`${file.name} excede el límite de 5MB`);
        return false;
      }
      return true;
    });

    // Convert to base64
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setAttachedFiles(prev => [...prev, {
          name: file.name,
          type: file.type,
          size: file.size,
          data: e.target.result
        }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeFile = (index) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if ((!prompt.trim() && attachedFiles.length === 0) || isLoading) return;

    const userMessage = prompt.trim() || "Analiza los archivos adjuntos";
    setPrompt("");
    
    const userMsgObj = { 
      role: "user", 
      content: userMessage,
      files: attachedFiles.length > 0 ? attachedFiles.map(f => ({ name: f.name, type: f.type })) : null
    };
    
    setMessages((prev) => [...prev, userMsgObj]);
    setIsLoading(true);

    try {
      const response = await api.post("/ai/chat", {
        message: userMessage,
        context: `Empresa: ${company?.business_name || "N/A"}`,
        files: attachedFiles.length > 0 ? attachedFiles : null,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.data.response, model: response.data.model },
      ]);
      
      setAttachedFiles([]);
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

  const clearChat = () => {
    setMessages([]);
    setAttachedFiles([]);
    setCurrentConversationId(null);
  };

  const saveConversation = async () => {
    if (messages.length === 0) {
      toast.error("No hay mensajes para guardar");
      return;
    }

    const title = messages[0]?.content?.substring(0, 50) + "..." || "Conversación sin título";
    
    try {
      const response = await api.post("/ai/conversations", {
        title,
        messages,
        conversation_id: currentConversationId,
      });
      
      setCurrentConversationId(response.data.id);
      toast.success("Conversación guardada");
      fetchSavedConversations();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al guardar conversación"));
    }
  };

  const loadConversation = (conversation) => {
    setMessages(conversation.messages || []);
    setCurrentConversationId(conversation.id);
    setHistoryOpen(false);
    toast.success("Conversación cargada");
  };

  const deleteConversation = async (conversationId, e) => {
    e.stopPropagation();
    
    try {
      await api.delete(`/ai/conversations/${conversationId}`);
      toast.success("Conversación eliminada");
      fetchSavedConversations();
      
      if (currentConversationId === conversationId) {
        clearChat();
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al eliminar conversación"));
    }
  };

  const getFileIcon = (type) => {
    if (type?.startsWith('image/')) return Image;
    return File;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="intelligence-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-purple-500" />
            <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Inteligencia Empresarial</h1>
          </div>
          <p className="text-muted-foreground">Análisis avanzado y predicciones con IA</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setHistoryOpen(true)} className="gap-2">
            <History className="h-4 w-4" />
            Historial
            {savedConversations.length > 0 && (
              <Badge variant="secondary" className="ml-1">{savedConversations.length}</Badge>
            )}
          </Button>
          {messages.length > 0 && (
            <>
              <Button variant="outline" onClick={saveConversation} className="gap-2">
                <Save className="h-4 w-4" />
                Guardar
              </Button>
              <Button variant="outline" onClick={clearChat} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Nueva
              </Button>
            </>
          )}
        </div>
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
                Powered by OpenAI • Análisis contextual de {company?.business_name || "tu empresa"} • Soporta archivos
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chat Area - Full Width */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-purple-500" />
            Asistente IA
            {currentConversationId && (
              <Badge variant="outline" className="text-xs">Guardada</Badge>
            )}
          </CardTitle>
          <CardDescription>
            Pregunta lo que necesites sobre tu empresa o adjunta archivos para análisis
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Messages */}
          <ScrollArea className="h-[400px] pr-4 mb-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                <Brain className="h-12 w-12 mb-4 text-purple-200" />
                <p className="font-medium">¿En qué puedo ayudarte hoy?</p>
                <p className="text-sm mt-1">Escribe tu pregunta o adjunta archivos para análisis</p>
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
                          ? "bg-red-50 border border-red-200"
                          : "bg-muted"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      {msg.files && msg.files.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {msg.files.map((f, fidx) => (
                            <Badge key={fidx} variant="secondary" className="text-xs">
                              <Paperclip className="h-3 w-3 mr-1" />
                              {f.name}
                            </Badge>
                            ))}
                          </div>
                        )}
                        {msg.model && (
                          <p className="text-xs mt-2 opacity-70">Modelo: {msg.model}</p>
                        )}
                      </div>
                      {msg.role === "user" && (
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                          <User className="h-4 w-4 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-purple-600" />
                      </div>
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span className="text-sm">Analizando...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* Attached Files Preview */}
            {attachedFiles.length > 0 && (
              <div className="mb-3 p-2 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500 mb-2">Archivos adjuntos:</p>
                <div className="flex flex-wrap gap-2">
                  {attachedFiles.map((file, idx) => {
                    const FileIcon = getFileIcon(file.type);
                    return (
                      <div key={idx} className="flex items-center gap-2 bg-white border rounded px-2 py-1">
                        <FileIcon className="h-4 w-4 text-slate-500" />
                        <span className="text-xs truncate max-w-[100px]">{file.name}</span>
                        <button onClick={() => removeFile(idx)} className="text-red-500 hover:text-red-700">
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                className="hidden"
                multiple
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                title="Adjuntar archivo"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Escribe tu pregunta o adjunta un archivo para análisis..."
                className="min-h-[44px] max-h-32 resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <Button type="submit" disabled={isLoading || (!prompt.trim() && attachedFiles.length === 0)} className="btn-industrial">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>
        </Card>

      {/* History Dialog */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Historial de Conversaciones
            </DialogTitle>
            <DialogDescription>
              Conversaciones guardadas previamente
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[400px] overflow-y-auto">
            {savedConversations.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No hay conversaciones guardadas</p>
                <p className="text-sm">Usa el botón "Guardar" para guardar una conversación</p>
              </div>
            ) : (
              <div className="space-y-2">
                {savedConversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => loadConversation(conv)}
                    className="p-3 border rounded-lg hover:bg-slate-50 cursor-pointer group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-sm truncate">{conv.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(conv.created_at)} • {conv.messages?.length || 0} mensajes
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 h-8 w-8"
                        onClick={(e) => deleteConversation(conv.id, e)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setHistoryOpen(false)}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Intelligence;
