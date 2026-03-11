import React, { useMemo, useRef, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { ChevronLeft, ChevronRight, Calendar, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { formatCurrency } from "../lib/utils";

const STATUS_COLORS = {
  quotation: "#64748b",
  authorized: "#f59e0b",
  in_progress: "#3b82f6",
  completed: "#10b981",
  cancelled: "#ef4444",
};

const STATUS_LABELS = {
  quotation: "Cotización",
  authorized: "Autorizado",
  in_progress: "En Progreso",
  completed: "Completado",
  cancelled: "Cancelado",
};

const PHASE_COLORS = {
  negotiation: "#8b5cf6",
  purchases: "#f59e0b",
  process: "#3b82f6",
  delivery: "#10b981",
};

const PHASE_LABELS = {
  negotiation: "Negociación",
  purchases: "Compras",
  process: "Proceso",
  delivery: "Entrega",
};

export const GanttChart = ({ projects, tasks, clients, onProjectClick }) => {
  const containerRef = useRef(null);
  const [viewMode, setViewMode] = useState("month"); // week, month, quarter
  const [scrollOffset, setScrollOffset] = useState(0);
  const [expandedProjects, setExpandedProjects] = useState({});

  // Calculate time range
  const timeRange = useMemo(() => {
    const now = new Date();
    let minDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    let maxDate = new Date(now.getFullYear(), now.getMonth() + 6, 0);

    projects.forEach((p) => {
      if (p.start_date) {
        const start = new Date(p.start_date);
        if (start < minDate) minDate = new Date(start.getFullYear(), start.getMonth(), 1);
      }
      if (p.end_date) {
        const end = new Date(p.end_date);
        if (end > maxDate) maxDate = new Date(end.getFullYear(), end.getMonth() + 1, 0);
      }
      if (p.commitment_date) {
        const commit = new Date(p.commitment_date);
        if (commit > maxDate) maxDate = new Date(commit.getFullYear(), commit.getMonth() + 1, 0);
      }
    });

    return { minDate, maxDate };
  }, [projects]);

  // Generate time columns based on view mode
  const timeColumns = useMemo(() => {
    const columns = [];
    const { minDate, maxDate } = timeRange;
    const current = new Date(minDate);

    while (current <= maxDate) {
      if (viewMode === "week") {
        const weekStart = new Date(current);
        const weekEnd = new Date(current);
        weekEnd.setDate(weekEnd.getDate() + 6);
        columns.push({
          key: `${current.getFullYear()}-W${Math.ceil(current.getDate() / 7)}`,
          label: `Sem ${Math.ceil(current.getDate() / 7)}`,
          subLabel: current.toLocaleDateString("es-MX", { month: "short" }),
          start: new Date(weekStart),
          end: new Date(weekEnd),
        });
        current.setDate(current.getDate() + 7);
      } else if (viewMode === "month") {
        columns.push({
          key: `${current.getFullYear()}-${current.getMonth()}`,
          label: current.toLocaleDateString("es-MX", { month: "short" }),
          subLabel: current.getFullYear(),
          start: new Date(current.getFullYear(), current.getMonth(), 1),
          end: new Date(current.getFullYear(), current.getMonth() + 1, 0),
        });
        current.setMonth(current.getMonth() + 1);
      } else {
        const quarter = Math.floor(current.getMonth() / 3);
        columns.push({
          key: `${current.getFullYear()}-Q${quarter + 1}`,
          label: `Q${quarter + 1}`,
          subLabel: current.getFullYear(),
          start: new Date(current.getFullYear(), quarter * 3, 1),
          end: new Date(current.getFullYear(), quarter * 3 + 3, 0),
        });
        current.setMonth(current.getMonth() + 3);
      }
    }
    return columns;
  }, [timeRange, viewMode]);

  // Calculate bar position and width
  const calculateBarStyle = (startDate, endDate) => {
    if (!startDate) return null;

    const { minDate, maxDate } = timeRange;
    const totalDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date(start.getTime() + 30 * 24 * 60 * 60 * 1000);

    const startOffset = Math.max(0, (start - minDate) / (1000 * 60 * 60 * 24));
    const duration = Math.max(1, (end - start) / (1000 * 60 * 60 * 24));

    const left = (startOffset / totalDays) * 100;
    const width = (duration / totalDays) * 100;

    return { left: `${left}%`, width: `${Math.min(width, 100 - left)}%` };
  };

  const getClientName = (clientId) => {
    const client = clients?.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

  const toggleProjectExpand = (projectId) => {
    setExpandedProjects((prev) => ({
      ...prev,
      [projectId]: !prev[projectId],
    }));
  };

  const getProjectTasks = (projectId) => {
    return tasks?.filter((t) => t.project_id === projectId) || [];
  };

  // Today marker position
  const todayPosition = useMemo(() => {
    const { minDate, maxDate } = timeRange;
    const today = new Date();
    if (today < minDate || today > maxDate) return null;
    const totalDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
    const offset = (today - minDate) / (1000 * 60 * 60 * 24);
    return `${(offset / totalDays) * 100}%`;
  }, [timeRange]);

  const columnWidth = viewMode === "week" ? 60 : viewMode === "month" ? 80 : 100;

  return (
    <Card className="overflow-hidden" data-testid="gantt-chart">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Calendario Gantt
            </CardTitle>
            <CardDescription>Visualización de timeline de proyectos</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex border rounded-md">
              <Button
                variant={viewMode === "week" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("week")}
                className="rounded-r-none"
              >
                Semana
              </Button>
              <Button
                variant={viewMode === "month" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("month")}
                className="rounded-none border-x"
              >
                Mes
              </Button>
              <Button
                variant={viewMode === "quarter" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("quarter")}
                className="rounded-l-none"
              >
                Trimestre
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto" ref={containerRef}>
          <div className="min-w-[800px]">
            {/* Timeline Header */}
            <div className="flex border-b bg-slate-50 sticky top-0 z-10">
              <div className="w-[280px] min-w-[280px] p-3 border-r font-medium text-sm bg-slate-100">
                Proyecto
              </div>
              <div className="flex-1 flex">
                {timeColumns.map((col) => (
                  <div
                    key={col.key}
                    className="text-center border-r p-2 text-xs"
                    style={{ minWidth: columnWidth, width: columnWidth }}
                  >
                    <div className="font-medium">{col.label}</div>
                    <div className="text-muted-foreground">{col.subLabel}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Projects */}
            {projects.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                No hay proyectos con fechas asignadas
              </div>
            ) : (
              projects.map((project) => {
                const barStyle = calculateBarStyle(project.start_date, project.end_date || project.commitment_date);
                const projectTasks = getProjectTasks(project.id);
                const isExpanded = expandedProjects[project.id];

                return (
                  <div key={project.id}>
                    {/* Project Row */}
                    <div className="flex border-b hover:bg-slate-50 transition-colors group">
                      <div className="w-[280px] min-w-[280px] p-3 border-r">
                        <div className="flex items-start gap-2">
                          {projectTasks.length > 0 && (
                            <button
                              onClick={() => toggleProjectExpand(project.id)}
                              className="mt-1 text-muted-foreground hover:text-foreground"
                            >
                              {isExpanded ? (
                                <ChevronLeft className="h-4 w-4 rotate-90" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </button>
                          )}
                          <div className="flex-1 min-w-0">
                            <div
                              className="font-medium truncate cursor-pointer hover:text-primary"
                              onClick={() => onProjectClick?.(project)}
                            >
                              {project.name}
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {getClientName(project.client_id)}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge
                                className="text-xs"
                                style={{
                                  backgroundColor: `${STATUS_COLORS[project.status]}20`,
                                  color: STATUS_COLORS[project.status],
                                }}
                              >
                                {STATUS_LABELS[project.status]}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {project.total_progress}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div
                        className="flex-1 relative"
                        style={{ minWidth: timeColumns.length * columnWidth }}
                      >
                        {/* Grid lines */}
                        <div className="absolute inset-0 flex">
                          {timeColumns.map((col) => (
                            <div
                              key={col.key}
                              className="border-r h-full"
                              style={{ minWidth: columnWidth, width: columnWidth }}
                            />
                          ))}
                        </div>

                        {/* Today marker */}
                        {todayPosition && (
                          <div
                            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                            style={{ left: todayPosition }}
                          />
                        )}

                        {/* Project bar */}
                        {barStyle && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div
                                  className="absolute top-3 h-8 rounded-md cursor-pointer shadow-sm transition-all hover:shadow-md"
                                  style={{
                                    ...barStyle,
                                    backgroundColor: STATUS_COLORS[project.status],
                                  }}
                                >
                                  <div className="h-full flex items-center px-2">
                                    <div
                                      className="h-full bg-white/30 rounded-sm transition-all"
                                      style={{ width: `${project.total_progress}%` }}
                                    />
                                  </div>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent side="top" className="max-w-xs">
                                <div className="space-y-1">
                                  <div className="font-medium">{project.name}</div>
                                  <div className="text-xs">
                                    {project.start_date &&
                                      `Inicio: ${new Date(project.start_date).toLocaleDateString("es-MX")}`}
                                  </div>
                                  <div className="text-xs">
                                    {(project.end_date || project.commitment_date) &&
                                      `Fin: ${new Date(project.end_date || project.commitment_date).toLocaleDateString("es-MX")}`}
                                  </div>
                                  <div className="text-xs">Progreso: {project.total_progress}%</div>
                                  <div className="text-xs">
                                    Monto: {formatCurrency(project.contract_amount)}
                                  </div>
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}

                        {/* Commitment date marker */}
                        {project.commitment_date && (
                          <div
                            className="absolute top-3 h-8 flex items-center"
                            style={{
                              left: calculateBarStyle(
                                project.commitment_date,
                                project.commitment_date
                              )?.left,
                            }}
                          >
                            <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[10px] border-b-amber-500" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Tasks (if expanded) */}
                    {isExpanded &&
                      projectTasks.map((task) => {
                        const taskBarStyle = task.due_date
                          ? calculateBarStyle(
                              task.created_at || project.start_date,
                              task.due_date
                            )
                          : null;

                        return (
                          <div
                            key={task.id}
                            className="flex border-b bg-slate-50/50 text-sm"
                          >
                            <div className="w-[280px] min-w-[280px] p-2 pl-10 border-r">
                              <div className="truncate text-muted-foreground">
                                {task.name || task.description}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge variant="outline" className="text-xs">
                                  {task.status === "completed"
                                    ? "Completada"
                                    : task.status === "in_progress"
                                    ? "En Progreso"
                                    : "Pendiente"}
                                </Badge>
                                {task.estimated_hours && (
                                  <span className="text-xs text-muted-foreground">
                                    {task.estimated_hours}h
                                  </span>
                                )}
                              </div>
                            </div>
                            <div
                              className="flex-1 relative"
                              style={{ minWidth: timeColumns.length * columnWidth }}
                            >
                              {/* Grid lines */}
                              <div className="absolute inset-0 flex">
                                {timeColumns.map((col) => (
                                  <div
                                    key={col.key}
                                    className="border-r h-full opacity-50"
                                    style={{ minWidth: columnWidth, width: columnWidth }}
                                  />
                                ))}
                              </div>

                              {/* Today marker */}
                              {todayPosition && (
                                <div
                                  className="absolute top-0 bottom-0 w-0.5 bg-red-500/50 z-10"
                                  style={{ left: todayPosition }}
                                />
                              )}

                              {/* Task bar */}
                              {taskBarStyle && (
                                <div
                                  className="absolute top-2 h-5 rounded cursor-pointer"
                                  style={{
                                    ...taskBarStyle,
                                    backgroundColor:
                                      task.status === "completed"
                                        ? "#10b981"
                                        : task.status === "in_progress"
                                        ? "#3b82f6"
                                        : "#94a3b8",
                                  }}
                                />
                              )}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="border-t p-3 bg-slate-50 flex flex-wrap items-center gap-4 text-xs">
          <span className="font-medium">Leyenda:</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span>Hoy</span>
          </div>
          {Object.entries(STATUS_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: STATUS_COLORS[key] }}
              />
              <span>{label}</span>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-b-[6px] border-b-amber-500" />
            <span>Fecha compromiso</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GanttChart;
