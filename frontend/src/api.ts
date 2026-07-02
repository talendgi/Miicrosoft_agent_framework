import type { Connection, ExecutionRecord, Pipeline } from "./types";

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json() as Promise<T>;
};

export const api = {
  executors: () => request("/api/executors"),
  connections: {
    list: () => request<Connection[]>("/api/connections"),
    create: (payload: Omit<Connection, "id">) =>
      request<Connection>("/api/connections", { method: "POST", body: JSON.stringify(payload) }),
    update: (id: string, payload: Omit<Connection, "id">) =>
      request<Connection>(`/api/connections/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
    remove: (id: string) => 
      request<{ ok: boolean }>(`/api/connections/${id}`, { method: "DELETE" }),
    test: (id: string) => 
      request<{ status: string; message: string; details?: any; result?: any }>(`/api/connections/${id}/test`, { method: "POST" })
  },
  pipelines: {
    list: () => request<Pipeline[]>("/api/pipelines"),
    create: (payload: Omit<Pipeline, "id">) =>
      request<Pipeline>("/api/pipelines", { method: "POST", body: JSON.stringify(payload) }),
    update: (id: string, payload: Omit<Pipeline, "id">) =>
      request<Pipeline>(`/api/pipelines/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
    remove: (id: string) => 
      request<{ ok: boolean }>(`/api/pipelines/${id}`, { method: "DELETE" }),
    run: (id: string) => 
      request<{ execution: ExecutionRecord }>(`/api/pipelines/${id}/run`, { method: "POST" }),
  },
  executions: {
    list: () => 
      request<ExecutionRecord[]>("/api/executions"),
    delete: (id: string) => 
      request<{ ok: boolean }>(`/api/executions/${id}`, { method: "DELETE" }),
    clearAll: () => 
      request<{ ok: boolean }>("/api/executions", { method: "DELETE" }),
  },
};