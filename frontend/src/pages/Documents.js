import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatDate , getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  FileBox,
  Plus,
  MoreVertical,
  Download,
  Trash2,
  FileText,
  Image,
  File,
  FolderOpen,
  AlertTriangle,
  Upload,
  Loader2,
  Search,
} from "lucide-react";

const DOCUMENT_CATEGORIES = [
  { value: "planos", label: "Planos" },
  { value: "contratos", label: "Contratos" },
  { value: "cotizaciones", label: "Cotizaciones" },
  { value: "reportes", label: "Reportes Técnicos" },
  { value: "fotografias", label: "Fotografías" },
  { value: "manuales", label: "Manuales" },
  { value: "otros", label: "Otros" },
];

export const Documents = () => {
  const { api, company } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [searchFilter, setSearchFilter] = useState("");
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    project_id: "",
    category: "",
    notes: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [docsRes, projectsRes] = await Promise.all([
        api.get(`/documents?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
      ]);
      setDocuments(docsRes.data);
      setProjects(projectsRes.data);
    } catch (error) {
      toast.error("Error al cargar documentos");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error("Por favor selecciona un archivo");
      return;
    }

    setUploading(true);
    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Content = reader.result.split(',')[1]; // Remove data:... prefix
        
        await api.post("/files/upload", {
          filename: formData.name || selectedFile.name,
          content: base64Content,
          content_type: selectedFile.type,
          project_id: formData.project_id || null,
          category: formData.category || "otros",
        });
        
        toast.success("Documento subido exitosamente");
        setDialogOpen(false);
        resetForm();
        fetchData();
      };
      reader.onerror = () => {
        toast.error("Error al leer el archivo");
      };
      reader.readAsDataURL(selectedFile);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al subir documento"));
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Max 5MB check
      if (file.size > 5 * 1024 * 1024) {
        toast.error("El archivo excede 5MB");
        return;
      }
      setSelectedFile(file);
      if (!formData.name) {
        setFormData(prev => ({ ...prev, name: file.name }));
      }
    }
  };

  const handleDownload = async (docId, filename) => {
    try {
      toast.info("Descargando...");
      const response = await api.get(`/files/${docId}/download`);
      const { content, content_type } = response.data;
      
      // Convert base64 to blob
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: content_type });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("Descarga completada");
    } catch (error) {
      toast.error("Error al descargar");
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm("¿Estás seguro de eliminar este documento?")) return;
    try {
      await api.delete(`/documents/${docId}`);
      toast.success("Documento eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar documento");
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      project_id: "",
      category: "",
      notes: "",
    });
    setSelectedFile(null);
  };

  const getProjectName = (projectId) => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name || "General";
  };

  const getCategoryLabel = (value) => {
    const cat = DOCUMENT_CATEGORIES.find((c) => c.value === value);
    return cat?.label || value;
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "planos":
        return <FileText className="h-4 w-4" />;
      case "fotografias":
        return <Image className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  // Filtrar por categoría y búsqueda
  const filteredDocs = documents.filter((d) => {
    const matchesCategory = categoryFilter === "all" || d.category === categoryFilter;
    if (!searchFilter.trim()) return matchesCategory;
    
    const search = searchFilter.toLowerCase();
    const matchesSearch = 
      d.name?.toLowerCase().includes(search) ||
      d.notes?.toLowerCase().includes(search) ||
      d.category?.toLowerCase().includes(search) ||
      d.file_name?.toLowerCase().includes(search);
    
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="documents-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Gestión Documental</h1>
          <p className="text-muted-foreground">Repositorio de documentos con control de versiones</p>
        </div>
        <Button className="btn-industrial" onClick={() => setDialogOpen(true)} data-testid="add-document-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nuevo Documento
        </Button>
      </div>

      {/* Search and Category Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar documentos..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="pl-10"
            data-testid="document-search-input"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={categoryFilter === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setCategoryFilter("all")}
          >
            Todos ({documents.length})
          </Button>
          {DOCUMENT_CATEGORIES.map((cat) => {
            const count = documents.filter((d) => d.category === cat.value).length;
            return (
              <Button
                key={cat.value}
                variant={categoryFilter === cat.value ? "default" : "outline"}
                size="sm"
                onClick={() => setCategoryFilter(cat.value)}
              >
                {cat.label} ({count})
              </Button>
            );
          })}
        </div>
      </div>

      {/* Documents Table */}
      <Card data-testid="documents-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileBox className="h-5 w-5 text-primary" />
            Documentos
          </CardTitle>
          <CardDescription>
            {filteredDocs.length} documento(s) encontrado(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Documento</TableHead>
                  <TableHead>Proyecto</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Versión</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      <FolderOpen className="h-12 w-12 mx-auto mb-2 text-slate-300" />
                      No hay documentos registrados
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDocs.map((doc) => (
                    <TableRow key={doc.id} data-testid={`document-row-${doc.id}`}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getCategoryIcon(doc.category)}
                          <div>
                            <div className="font-medium">{doc.name}</div>
                            {doc.notes && (
                              <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                                {doc.notes}
                              </div>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{getProjectName(doc.project_id)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{getCategoryLabel(doc.category)}</Badge>
                      </TableCell>
                      <TableCell>v{doc.version}</TableCell>
                      <TableCell>{formatDate(doc.created_at)}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {doc.file_data && (
                              <DropdownMenuItem onClick={() => handleDownload(doc.id, doc.name)}>
                                <Download className="mr-2 h-4 w-4" />
                                Descargar
                              </DropdownMenuItem>
                            )}
                            {doc.file_url && !doc.file_data && (
                              <DropdownMenuItem onClick={() => window.open(doc.file_url, "_blank")}>
                                <Download className="mr-2 h-4 w-4" />
                                Ver enlace
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => handleDelete(doc.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create Document Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Subir Documento</DialogTitle>
              <DialogDescription>
                Sube un archivo al repositorio (máx. 5MB)
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              {/* File Upload */}
              <div className="grid gap-2">
                <Label htmlFor="file">Archivo *</Label>
                <div className="border-2 border-dashed rounded-lg p-4 text-center hover:border-primary transition-colors">
                  <input
                    type="file"
                    id="file"
                    className="hidden"
                    onChange={handleFileSelect}
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.dwg"
                    data-testid="document-file-input"
                  />
                  <label htmlFor="file" className="cursor-pointer">
                    {selectedFile ? (
                      <div className="flex items-center justify-center gap-2 text-primary">
                        <File className="h-6 w-6" />
                        <span className="font-medium">{selectedFile.name}</span>
                        <span className="text-sm text-muted-foreground">
                          ({(selectedFile.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <Upload className="h-8 w-8" />
                        <span>Haz clic para seleccionar archivo</span>
                        <span className="text-xs">PDF, DOC, XLS, imágenes (máx. 5MB)</span>
                      </div>
                    )}
                  </label>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="name">Nombre del Documento</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Se usará el nombre del archivo si está vacío"
                  data-testid="document-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="project_id">Proyecto</Label>
                  <Select
                    value={formData.project_id}
                    onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="General" />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="category">Categoría</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Otros" />
                    </SelectTrigger>
                    <SelectContent>
                      {DOCUMENT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button 
                type="submit" 
                className="btn-industrial" 
                disabled={!selectedFile || uploading}
                data-testid="save-document-btn"
              >
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Subiendo...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Subir Documento
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Documents;
