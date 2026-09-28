const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export type Provenance<T> = { value: T; source: string; note?: string | null };

export interface ManagementDashboard {
  ai_spend: Provenance<number | string>;
  ai_assisted_tasks: number;
  total_tasks: number;
  completed_tasks: number;
  time_saved_minutes: Provenance<number>;
  estimated_business_value: Provenance<number>;
  net_estimated_value: Provenance<number | string>;
  aggregate_roi_percentage: Provenance<number | string>;
  roi_multiple: { value: number | string };
  ai_adoption_pct: number;
  cost_per_ai_assisted_task: number | string;
  department_stats: Array<{
    department_id: string;
    department: string;
    employees: number;
    tasks: number;
    ai_assisted_tasks: number;
    ai_adoption_pct: number;
    time_saved_minutes: number;
    ai_spend: number | string;
  }>;
  provider_stats: Record<string, { events: number; total_tokens: number; cost: number | string }>;
  tasks_with_cost_data: number;
  tasks_missing_cost_data: number;
}

export interface Task {
  id: string;
  employee_id: string;
  title: string;
  description: string | null;
  category: string | null;
  baseline_minutes: number | null;
  started_at: string | null;
  completed_at: string | null;
  actual_minutes: number | null;
  status: string;
}

export interface ROI {
  task_id: string;
  time_saved_minutes: number | null;
  time_saved_percentage: number | null;
  estimated_labor_value: number | null;
  ai_cost: number | null;
  net_value: number | null;
  roi_percentage: number | null;
  roi_multiple: number | null;
  calculation_status: "calculated" | "partial" | "unavailable";
}

export interface Employee {
  id: string;
  name: string;
  email: string;
  department_id: string | null;
  role: string;
  hourly_cost: number;
}

export interface Department {
  id: string;
  name: string;
}

export interface AIUsageEvent {
  id: string;
  provider: string;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  cost: number | null;
  source: string;
}

export interface TaskOutcome {
  id: string;
  task_id: string;
  files_changed: number;
  lines_added: number;
  lines_removed: number;
  commits: number;
  tests_run: number;
  tests_passed: number;
  build_passed: boolean | null;
  output_generated: boolean;
}

export interface ConnectorStatus {
  name: string;
  available: boolean;
  reason: string;
}

export interface PromptAnalysis {
  scores: Record<string, number>;
  missing: string[];
  suggestions: string[];
  improved_prompt: string;
}

export const api = {
  managementDashboard: () => request<ManagementDashboard>("/api/dashboard/management"),
  departmentDashboard: (id: string) => request<any>(`/api/dashboard/department/${id}`),
  employeeDashboard: (id: string) => request<any>(`/api/dashboard/employee/${id}`),
  tasks: (params?: { employee_id?: string; status?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<Task[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
  },
  task: (id: string) => request<Task>(`/api/tasks/${id}`),
  taskROI: (id: string) => request<ROI>(`/api/tasks/${id}/roi`).catch(() => null),
  taskAIEvents: (id: string) => request<AIUsageEvent[]>(`/api/tasks/${id}/ai-events`),
  taskOutcome: (id: string) => request<TaskOutcome>(`/api/tasks/${id}/outcome`).catch(() => null),
  employees: () => request<Employee[]>("/api/employees"),
  departments: () => request<Department[]>("/api/departments"),
  connectors: () => request<ConnectorStatus[]>("/api/connectors"),
  analyzePrompt: (prompt: string) =>
    request<PromptAnalysis>("/api/prompt/analyze", { method: "POST", body: JSON.stringify({ prompt }) }),
};

export function formatValue(v: number | string | null | undefined, prefix = ""): string {
  if (v === null || v === undefined) return "N/A";
  if (typeof v === "string") return v;
  return `${prefix}${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
