const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("eai_access_token") : null;
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) },
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

export interface AuthUser extends Employee { name: string; }

export interface EmployeeConnection { id: string; employee_id: string; employee_name?: string | null; provider: string; account_name: string; connected_at: string; }

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
  oauth_supported?: boolean;
}

export interface PromptAnalysis {
  scores: Record<string, number>;
  missing: string[];
  suggestions: string[];
  improved_prompt: string;
}

export interface AgentDecision {
  id: string; task_id: string | null; task_type: string; complexity: string; required_quality: number;
  selected_provider: string; selected_model: string; predicted_input_tokens: number | null;
  predicted_output_tokens: number | null; predicted_cost: number | null; predicted_latency_ms: number | null;
  predicted_quality: number; confidence: number; rationale: Record<string, unknown> | null;
  actual_input_tokens: number | null; actual_output_tokens: number | null; actual_cost: number | null;
  actual_latency_ms: number | null; actual_quality: number | null; outcome: string | null;
  verification_required: boolean | null; rework_required: boolean | null; created_at: string;
}

export interface DepartmentDashboard {
  department: string; employees: number; tasks: number; ai_assisted_tasks: number; ai_adoption_pct: number;
  time_saved_minutes: number; estimated_value: number; ai_spend: number | string; roi_percentage: number | string;
}

export interface EmployeeDashboard {
  employee: string; department_id: string | null; tasks_completed: number; ai_assisted_tasks: number;
  time_saved_minutes: number; ai_usage_events: number; ai_cost: number | string;
  estimated_value: number; roi_percentage: number | string;
}

export interface AgentAnalytics {
  recommendations: number; results_recorded: number; observed_decisions_with_cost: number;
  predicted_cost: number; actual_cost: number; cost_below_prediction_total: number;
  average_actual_quality: number | null;
  models: Record<string, { recommendations: number; evaluated: number }>;
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string; token_type: string; role: string }>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<AuthUser>("/api/auth/me"),
  bootstrapStatus: () => request<{ setup_required: boolean }>("/api/auth/bootstrap-status"),
  bootstrap: (input: { name: string; email: string; password: string }) => request<{ access_token: string; token_type: string; role: string }>("/api/auth/bootstrap", { method: "POST", body: JSON.stringify(input) }),
  managementDashboard: () => request<ManagementDashboard>("/api/dashboard/management"),
  departmentDashboard: (id: string) => request<DepartmentDashboard>(`/api/dashboard/department/${id}`),
  employeeDashboard: (id: string) => request<EmployeeDashboard>(`/api/dashboard/employee/${id}`),
  tasks: (params?: { employee_id?: string; status?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<Task[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
  },
  task: (id: string) => request<Task>(`/api/tasks/${id}`),
  taskROI: (id: string) => request<ROI>(`/api/tasks/${id}/roi`).catch(() => null),
  taskAIEvents: (id: string) => request<AIUsageEvent[]>(`/api/tasks/${id}/ai-events`),
  taskOutcome: (id: string) => request<TaskOutcome>(`/api/tasks/${id}/outcome`).catch(() => null),
  employees: () => request<Employee[]>("/api/employees"),
  createEmployee: (input: { name: string; email: string; department_id?: string | null; role: string; hourly_cost: number; password: string }) => request<Employee>("/api/employees", { method: "POST", body: JSON.stringify(input) }),
  deleteEmployee: (id: string) => request<{ status: string }>(`/api/employees/${id}`, { method: "DELETE" }),
  departments: () => request<Department[]>("/api/departments"),
  createDepartment: (name: string) => request<Department>("/api/departments", { method: "POST", body: JSON.stringify({ name }) }),
  deleteDepartment: (id: string) => request<{ status: string }>(`/api/departments/${id}`, { method: "DELETE" }),
  connectors: () => request<ConnectorStatus[]>("/api/connectors"),
  connectorAccounts: () => request<EmployeeConnection[]>("/api/connectors/accounts"),
  startOAuth: async (provider: string) => {
    const result = await request<{ authorization_url: string }>(`/api/connectors/oauth/${provider}/start`);
    window.location.assign(result.authorization_url);
  },
  disconnectAccount: (provider: string) => request<{ status: string }>(`/api/connectors/accounts/${provider}`, { method: "DELETE" }),
  analyzePrompt: (prompt: string) =>
    request<PromptAnalysis>("/api/prompt/analyze", { method: "POST", body: JSON.stringify({ prompt }) }),
  optimizeAgent: (input: { title: string; description?: string; task_type?: string; complexity?: string; required_quality: number }) =>
    request<AgentDecision>("/api/agents/optimize", { method: "POST", body: JSON.stringify(input) }),
  agentAnalytics: () => request<AgentAnalytics>("/api/agents/analytics"),
  recordAgentResult: (id: string, input: { actual_quality?: number; outcome?: string; rework_required?: boolean; actual_latency_ms?: number; actual_input_tokens?: number; actual_output_tokens?: number; actual_cost?: number }) =>
    request<AgentDecision>(`/api/agents/decisions/${id}/result`, { method: "POST", body: JSON.stringify(input) }),
};

export function formatValue(v: number | string | null | undefined, prefix = ""): string {
  if (v === null || v === undefined) return "N/A";
  if (typeof v === "string") return v;
  return `${prefix}${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
