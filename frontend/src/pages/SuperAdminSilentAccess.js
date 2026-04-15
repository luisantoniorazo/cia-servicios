import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Badge } from "../components/ui/badge";
import { Search, Eye, Users, FileText, Briefcase, Receipt, ArrowLeft, Building2, Activity, LogIn, ExternalLink } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SuperAdminSilentAccess() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [searchResults, setSearchResults] = useState(null);
  
  // Data views
  const [viewType, setViewType] = useState(null);
  const [viewData, setViewData] = useState(null);
  const [detailModal, setDetailModal] = useState({ open: false, data: null, type: null });
  
  // Impersonation
  const [impersonateModal, setImpersonateModal] = useState({ open: false, company: null, users: [] });
  const [impersonating, setImpersonating] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const res = await fetch(`${API_URL}/api/super-admin/companies`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCompanies(data);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };

  const fetchCompanyData = async (companyId, type) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/super-admin/silent/companies/${companyId}/${type}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setViewData(data);
        setViewType(type);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/super-admin/silent/search?q=${encodeURIComponent(searchQuery)}&search_type=${searchType}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data);
        setViewType('search');
      }
    } catch (error) {
      console.error('Error searching:', error);
    }
    setLoading(false);
  };

  const handleBack = () => {
    if (viewType) {
      setViewType(null);
      setViewData(null);
      setSearchResults(null);
    } else {
      setSelectedCompany(null);
    }
  };

  // Impersonation functions
  const handleImpersonateCompany = async (company) => {
    setImpersonating(true);
    try {
      const res = await fetch(`${API_URL}/api/super-admin/impersonate/company/${company.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Abrir en nueva pestaña con el token
        const url = `${window.location.origin}${data.redirect_url}?impersonate_token=${data.access_token}`;
        window.open(url, '_blank');
      } else {
        alert('Error al impersonar usuario');
      }
    } catch (error) {
      console.error('Error impersonating:', error);
      alert('Error al impersonar usuario');
    }
    setImpersonating(false);
  };

  const handleShowUsers = async (company) => {
    try {
      const res = await fetch(`${API_URL}/api/super-admin/companies/${company.id}/users-list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setImpersonateModal({ open: true, company: data.company, users: data.users });
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleImpersonateUser = async (userId) => {
    setImpersonating(true);
    try {
      const res = await fetch(`${API_URL}/api/super-admin/impersonate/${userId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Abrir en nueva pestaña con el token
        const url = `${window.location.origin}${data.redirect_url}?impersonate_token=${data.access_token}`;
        window.open(url, '_blank');
        setImpersonateModal({ open: false, company: null, users: [] });
      } else {
        alert('Error al impersonar usuario');
      }
    } catch (error) {
      console.error('Error impersonating:', error);
      alert('Error al impersonar usuario');
    }
    setImpersonating(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount || 0);
  };

  // Render company selector
  const renderCompanySelector = () => (
    <div className="space-y-6">
      {/* Search Bar */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Search className="w-5 h-5" />
            Búsqueda Global (Sin Registro)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input
              placeholder="Buscar por nombre, RFC, email, folio..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="bg-slate-900 border-slate-600 text-white flex-1"
            />
            <Select value={searchType} onValueChange={setSearchType}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todo</SelectItem>
                <SelectItem value="clients">Clientes</SelectItem>
                <SelectItem value="quotes">Cotizaciones</SelectItem>
                <SelectItem value="invoices">Facturas</SelectItem>
                <SelectItem value="projects">Proyectos</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} disabled={loading}>
              <Search className="w-4 h-4 mr-2" />
              Buscar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Companies List */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            Seleccionar Empresa para Ver Datos o Impersonar
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {companies.map((company) => (
              <Card 
                key={company.id}
                className="bg-slate-900/50 border-slate-600 hover:border-blue-500 transition-all"
              >
                <CardContent className="p-4">
                  <h3 className="text-white font-semibold truncate">{company.business_name}</h3>
                  <p className="text-slate-400 text-sm truncate">{company.trade_name || '-'}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant={company.status === 'active' ? 'default' : 'secondary'}>
                      {company.status === 'active' ? 'Activa' : 'Inactiva'}
                    </Badge>
                    <span className="text-slate-500 text-xs">{company.license_type}</span>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
                      onClick={() => setSelectedCompany(company)}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      Ver Datos
                    </Button>
                    <Button 
                      size="sm" 
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => handleImpersonateCompany(company)}
                      disabled={impersonating}
                    >
                      <LogIn className="w-3 h-3 mr-1" />
                      Entrar
                    </Button>
                  </div>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    className="w-full mt-2 text-slate-400 hover:text-white"
                    onClick={() => handleShowUsers(company)}
                  >
                    <Users className="w-3 h-3 mr-1" />
                    Ver usuarios para impersonar
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Render company actions
  const renderCompanyActions = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={handleBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Volver
        </Button>
        <div>
          <h2 className="text-xl text-white font-bold">{selectedCompany.business_name}</h2>
          <p className="text-slate-400 text-sm">{selectedCompany.trade_name}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'clients')}
        >
          <Users className="w-6 h-6 text-blue-400" />
          <span className="text-white">Clientes</span>
        </Button>
        
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'quotes')}
        >
          <FileText className="w-6 h-6 text-green-400" />
          <span className="text-white">Cotizaciones</span>
        </Button>
        
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'invoices')}
        >
          <Receipt className="w-6 h-6 text-yellow-400" />
          <span className="text-white">Facturas</span>
        </Button>
        
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'projects')}
        >
          <Briefcase className="w-6 h-6 text-purple-400" />
          <span className="text-white">Proyectos</span>
        </Button>
        
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'users')}
        >
          <Users className="w-6 h-6 text-pink-400" />
          <span className="text-white">Usuarios</span>
        </Button>
        
        <Button
          variant="outline"
          className="h-24 flex-col gap-2 bg-slate-800/50 border-slate-600 hover:bg-slate-700"
          onClick={() => fetchCompanyData(selectedCompany.id, 'activity')}
        >
          <Activity className="w-6 h-6 text-orange-400" />
          <span className="text-white">Actividad</span>
        </Button>
      </div>
    </div>
  );

  // Render data table
  const renderDataView = () => {
    if (loading) {
      return <div className="text-center text-white py-8">Cargando...</div>;
    }

    if (!viewData && !searchResults) return null;

    const data = searchResults || viewData;
    
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </Button>
          <h2 className="text-xl text-white font-bold">
            {viewType === 'search' ? `Resultados de búsqueda: "${searchQuery}"` : 
             viewType === 'clients' ? 'Clientes' :
             viewType === 'quotes' ? 'Cotizaciones' :
             viewType === 'invoices' ? 'Facturas' :
             viewType === 'projects' ? 'Proyectos' :
             viewType === 'users' ? 'Usuarios' :
             viewType === 'activity' ? 'Actividad Reciente' : ''}
          </h2>
          {data.total_clients && <Badge>{data.total_clients} registros</Badge>}
          {data.total_quotes && <Badge>{data.total_quotes} registros</Badge>}
          {data.total_invoices && <Badge>{data.total_invoices} registros</Badge>}
          {data.total_projects && <Badge>{data.total_projects} registros</Badge>}
          {data.total_users && <Badge>{data.total_users} registros</Badge>}
          {data.total_records && <Badge>{data.total_records} registros</Badge>}
        </div>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-0">
            {viewType === 'search' && searchResults && (
              <div className="p-4 space-y-4">
                {searchResults.clients?.length > 0 && (
                  <div>
                    <h3 className="text-white font-semibold mb-2">Clientes ({searchResults.clients.length})</h3>
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-300">Nombre</TableHead>
                          <TableHead className="text-slate-300">RFC</TableHead>
                          <TableHead className="text-slate-300">Email</TableHead>
                          <TableHead className="text-slate-300">Teléfono</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {searchResults.clients.map((client) => (
                          <TableRow key={client.id} className="border-slate-700 hover:bg-slate-700/50 cursor-pointer"
                            onClick={() => setDetailModal({ open: true, data: client, type: 'client' })}>
                            <TableCell className="text-white">{client.name || client.trade_name}</TableCell>
                            <TableCell className="text-slate-300">{client.rfc || '-'}</TableCell>
                            <TableCell className="text-slate-300">{client.email || '-'}</TableCell>
                            <TableCell className="text-slate-300">{client.phone || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
                {searchResults.quotes?.length > 0 && (
                  <div>
                    <h3 className="text-white font-semibold mb-2">Cotizaciones ({searchResults.quotes.length})</h3>
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-300">Folio</TableHead>
                          <TableHead className="text-slate-300">Título</TableHead>
                          <TableHead className="text-slate-300">Total</TableHead>
                          <TableHead className="text-slate-300">Estado</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {searchResults.quotes.map((quote) => (
                          <TableRow key={quote.id} className="border-slate-700 hover:bg-slate-700/50 cursor-pointer"
                            onClick={() => setDetailModal({ open: true, data: quote, type: 'quote' })}>
                            <TableCell className="text-white">{quote.quote_number}</TableCell>
                            <TableCell className="text-slate-300">{quote.title || '-'}</TableCell>
                            <TableCell className="text-slate-300">{formatCurrency(quote.total)}</TableCell>
                            <TableCell><Badge>{quote.status}</Badge></TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            )}

            {viewType === 'clients' && viewData?.clients && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Nombre</TableHead>
                    <TableHead className="text-slate-300">RFC</TableHead>
                    <TableHead className="text-slate-300">Email</TableHead>
                    <TableHead className="text-slate-300">Teléfono</TableHead>
                    <TableHead className="text-slate-300">Tipo</TableHead>
                    <TableHead className="text-slate-300">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.clients.map((client) => (
                    <TableRow key={client.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{client.name || client.trade_name}</TableCell>
                      <TableCell className="text-slate-300">{client.rfc || '-'}</TableCell>
                      <TableCell className="text-slate-300">{client.email || '-'}</TableCell>
                      <TableCell className="text-slate-300">{client.phone || '-'}</TableCell>
                      <TableCell>
                        <Badge variant={client.is_prospect ? 'secondary' : 'default'}>
                          {client.is_prospect ? 'Prospecto' : 'Cliente'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost" onClick={() => setDetailModal({ open: true, data: client, type: 'client' })}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {viewType === 'quotes' && viewData?.quotes && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Folio</TableHead>
                    <TableHead className="text-slate-300">Título</TableHead>
                    <TableHead className="text-slate-300">Total</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.quotes.map((quote) => (
                    <TableRow key={quote.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{quote.quote_number}</TableCell>
                      <TableCell className="text-slate-300">{quote.title || '-'}</TableCell>
                      <TableCell className="text-slate-300">{formatCurrency(quote.total)}</TableCell>
                      <TableCell><Badge>{quote.status}</Badge></TableCell>
                      <TableCell className="text-slate-300">{formatDate(quote.created_at)}</TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost" onClick={() => setDetailModal({ open: true, data: quote, type: 'quote' })}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {viewType === 'invoices' && viewData?.invoices && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Folio</TableHead>
                    <TableHead className="text-slate-300">Concepto</TableHead>
                    <TableHead className="text-slate-300">Total</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.invoices.map((invoice) => (
                    <TableRow key={invoice.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{invoice.invoice_number}</TableCell>
                      <TableCell className="text-slate-300">{invoice.concept || '-'}</TableCell>
                      <TableCell className="text-slate-300">{formatCurrency(invoice.total)}</TableCell>
                      <TableCell><Badge>{invoice.status}</Badge></TableCell>
                      <TableCell className="text-slate-300">{formatDate(invoice.created_at)}</TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost" onClick={() => setDetailModal({ open: true, data: invoice, type: 'invoice' })}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {viewType === 'projects' && viewData?.projects && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Folio</TableHead>
                    <TableHead className="text-slate-300">Nombre</TableHead>
                    <TableHead className="text-slate-300">Valor</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.projects.map((project) => (
                    <TableRow key={project.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{project.project_number}</TableCell>
                      <TableCell className="text-slate-300">{project.name || '-'}</TableCell>
                      <TableCell className="text-slate-300">{formatCurrency(project.value)}</TableCell>
                      <TableCell><Badge>{project.status}</Badge></TableCell>
                      <TableCell className="text-slate-300">{formatDate(project.created_at)}</TableCell>
                      <TableCell>
                        <Button size="sm" variant="ghost" onClick={() => setDetailModal({ open: true, data: project, type: 'project' })}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {viewType === 'users' && viewData?.users && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Nombre</TableHead>
                    <TableHead className="text-slate-300">Email</TableHead>
                    <TableHead className="text-slate-300">Rol</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Último acceso</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.users.map((user) => (
                    <TableRow key={user.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{user.full_name}</TableCell>
                      <TableCell className="text-slate-300">{user.email}</TableCell>
                      <TableCell><Badge>{user.role}</Badge></TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                          {user.is_active ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-300">{formatDate(user.last_login)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {viewType === 'activity' && viewData?.activity && (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300">Usuario</TableHead>
                    <TableHead className="text-slate-300">Acción</TableHead>
                    <TableHead className="text-slate-300">Detalles</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {viewData.activity.map((log, idx) => (
                    <TableRow key={idx} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell className="text-white">{formatDate(log.timestamp)}</TableCell>
                      <TableCell className="text-slate-300">{log.user_name || log.user_email || '-'}</TableCell>
                      <TableCell><Badge>{log.action}</Badge></TableCell>
                      <TableCell className="text-slate-300 max-w-md truncate">{log.details || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              size="sm"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              onClick={() => navigate('/admin-portal/dashboard')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver al Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <Eye className="w-6 h-6 text-red-400" />
                Acceso Silencioso
              </h1>
              <p className="text-slate-400 text-sm">
                Acceso sin registro en bitácoras ni historiales
              </p>
            </div>
          </div>
        </div>

        {viewType ? renderDataView() : 
         selectedCompany ? renderCompanyActions() : 
         renderCompanySelector()}

        {/* Detail Modal */}
        <Dialog open={detailModal.open} onOpenChange={(open) => setDetailModal({ ...detailModal, open })}>
          <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {detailModal.type === 'client' && 'Detalle del Cliente'}
                {detailModal.type === 'quote' && 'Detalle de Cotización'}
                {detailModal.type === 'invoice' && 'Detalle de Factura'}
                {detailModal.type === 'project' && 'Detalle del Proyecto'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {detailModal.data && (
                <pre className="bg-slate-900 p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(detailModal.data, null, 2)}
                </pre>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Impersonate User Modal */}
        <Dialog open={impersonateModal.open} onOpenChange={(open) => setImpersonateModal({ ...impersonateModal, open })}>
          <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <LogIn className="w-5 h-5 text-green-400" />
                Impersonar Usuario - {impersonateModal.company?.business_name}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-slate-400 text-sm">
                Selecciona el usuario como el cual deseas ingresar. Se abrirá una nueva pestaña con su sesión.
              </p>
              {impersonateModal.users.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No hay usuarios en esta empresa</p>
              ) : (
                <div className="space-y-2">
                  {impersonateModal.users.map((user) => (
                    <div 
                      key={user.id}
                      className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-green-500 transition-all"
                    >
                      <div>
                        <p className="text-white font-medium">{user.full_name}</p>
                        <p className="text-slate-400 text-sm">{user.email}</p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                            {user.role}
                          </Badge>
                          <Badge variant={user.is_active ? 'outline' : 'destructive'}>
                            {user.is_active ? 'Activo' : 'Inactivo'}
                          </Badge>
                        </div>
                      </div>
                      <Button 
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => handleImpersonateUser(user.id)}
                        disabled={impersonating}
                      >
                        <LogIn className="w-4 h-4 mr-1" />
                        Entrar como este usuario
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setImpersonateModal({ open: false, company: null, users: [] })}>
                Cancelar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
