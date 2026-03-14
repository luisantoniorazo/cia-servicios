import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { toast } from "sonner";
import { Bell, Plus, Calendar, Check, Trash2, Clock } from "lucide-react";

export const Reminders = () => {
  const { api } = useAuth();
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [includeCompleted, setIncludeCompleted] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    remind_at: "",
    entity_type: "",
    entity_id: "",
  });

  useEffect(() => {
    fetchReminders();
  }, [includeCompleted]);

  const fetchReminders = async () => {
    try {
      const response = await api.get(`/reminders?include_completed=${includeCompleted}`);
      setReminders(response.data);
    } catch (error) {
      toast.error("Error al cargar recordatorios");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.post("/reminders", {
        ...formData,
        remind_at: new Date(formData.remind_at).toISOString(),
      });
      toast.success("Recordatorio creado");
      setDialogOpen(false);
      setFormData({ title: "", description: "", remind_at: "", entity_type: "", entity_id: "" });
      fetchReminders();
    } catch (error) {
      toast.error("Error al crear recordatorio");
    }
  };

  const handleComplete = async (id) => {
    try {
      await api.patch(`/reminders/${id}/complete`);
      toast.success("Recordatorio completado");
      fetchReminders();
    } catch (error) {
      toast.error("Error al completar recordatorio");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar este recordatorio?")) return;
    try {
      await api.delete(`/reminders/${id}`);
      toast.success("Recordatorio eliminado");
      fetchReminders();
    } catch (error) {
      toast.error("Error al eliminar recordatorio");
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString("es-MX", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isOverdue = (dateStr) => {
    return new Date(dateStr) < new Date();
  };

  const isToday = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  // Set default datetime to now + 1 hour
  const getDefaultDateTime = () => {
    const date = new Date();
    date.setHours(date.getHours() + 1, 0, 0, 0);
    return date.toISOString().slice(0, 16);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="reminders-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-[Chivo]">Recordatorios</h1>
          <p className="text-muted-foreground">Gestiona tus recordatorios y tareas pendientes</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={includeCompleted}
              onCheckedChange={setIncludeCompleted}
            />
            Mostrar completados
          </label>
          <Button className="btn-industrial" onClick={() => {
            setFormData({ ...formData, remind_at: getDefaultDateTime() });
            setDialogOpen(true);
          }}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo
          </Button>
        </div>
      </div>

      {reminders.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No tienes recordatorios</p>
              <p className="text-sm">Crea uno para no olvidar tus tareas importantes</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {reminders.map((reminder) => (
            <Card
              key={reminder.id}
              className={`transition-all ${
                reminder.completed
                  ? "opacity-60"
                  : isOverdue(reminder.remind_at)
                  ? "border-red-300 bg-red-50"
                  : isToday(reminder.remind_at)
                  ? "border-amber-300 bg-amber-50"
                  : ""
              }`}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={reminder.completed}
                    onCheckedChange={() => !reminder.completed && handleComplete(reminder.id)}
                    disabled={reminder.completed}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className={`font-medium ${reminder.completed ? "line-through text-muted-foreground" : ""}`}>
                          {reminder.title}
                        </h3>
                        {reminder.description && (
                          <p className="text-sm text-muted-foreground mt-1">{reminder.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {!reminder.completed && isOverdue(reminder.remind_at) && (
                          <Badge variant="destructive" className="text-xs">Vencido</Badge>
                        )}
                        {!reminder.completed && isToday(reminder.remind_at) && !isOverdue(reminder.remind_at) && (
                          <Badge className="bg-amber-500 text-xs">Hoy</Badge>
                        )}
                        {reminder.completed && (
                          <Badge variant="outline" className="text-xs text-emerald-600">Completado</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(reminder.remind_at)}
                      </span>
                      {reminder.entity_type && (
                        <Badge variant="outline" className="text-xs capitalize">
                          {reminder.entity_type}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleDelete(reminder.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo Recordatorio</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Título *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="¿Qué necesitas recordar?"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Detalles adicionales..."
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>Fecha y Hora *</Label>
                <Input
                  type="datetime-local"
                  value={formData.remind_at}
                  onChange={(e) => setFormData({ ...formData, remind_at: e.target.value })}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial">
                <Bell className="h-4 w-4 mr-2" />
                Crear Recordatorio
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Reminders;
