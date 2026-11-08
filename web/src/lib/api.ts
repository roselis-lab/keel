import { useEffect, useState } from "react";

// Every read goes through one cache, so moving between pages does not refetch what is
// already on screen, and two components asking for the same path share one request.
const cache = new Map<string, Promise<unknown>>();

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export function get<T>(path: string): Promise<T> {
  let p = cache.get(path) as Promise<T> | undefined;
  if (!p) {
    p = fetch("/api" + path, { headers: { accept: "application/json" } }).then(async (r) => {
      if (!r.ok) {
        cache.delete(path);
        const body = await r.json().catch(() => ({}));
        throw new ApiError(r.status, body?.detail?.message || body?.detail || body?.message || r.statusText);
      }
      return r.json() as Promise<T>;
    });
    cache.set(path, p);
  }
  return p;
}

export function forget(prefix: string) {
  for (const k of [...cache.keys()]) if (k.startsWith(prefix)) cache.delete(k);
}

export async function post<T>(path: string, body?: unknown): Promise<T> {
  return send<T>("POST", path, body);
}

/** One field the server refused, with its path ("weaknesses.0.text") and why. */
export interface FieldError { field: string; msg: string }
export type SendError = ApiError & { fields: FieldError[]; hint?: string };

export async function send<T>(method: "POST" | "PATCH" | "PUT" | "DELETE", path: string, body?: unknown): Promise<T> {
  const r = await fetch("/api" + path, { method, headers: { "content-type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = data?.detail;
    // FastAPI's 422 is a list of {loc, msg}; Keel's own errors are {error, field, hint}.
    const fields: FieldError[] = Array.isArray(d)
      ? d.map((e: { loc?: (string | number)[]; msg?: string }) => ({ field: (e.loc || []).filter((x) => x !== "body").join("."), msg: e.msg || "" }))
      : data?.field ? [{ field: String(data.field), msg: data.error || "" }] : [];
    const msg = Array.isArray(d) ? `${fields.length} ${fields.length === 1 ? "field needs" : "fields need"} fixing` : d?.message || d || data?.error || r.statusText;
    throw Object.assign(new ApiError(r.status, String(msg)), { fields, hint: data?.hint });
  }
  return data as T;
}

export type Loaded<T> = { data: T; error: null; loading: false } | { data: null; error: ApiError | Error; loading: false } | { data: null; error: null; loading: true };

/** Load several paths at once; the result is ready when all of them are. */
export function useApi<T extends unknown[]>(...paths: (string | null)[]): Loaded<T> {
  const key = paths.join("|");
  const [state, setState] = useState<Loaded<T>>({ data: null, error: null, loading: true });
  useEffect(() => {
    let live = true;
    setState({ data: null, error: null, loading: true });
    Promise.all(paths.map((p) => (p ? get(p) : Promise.resolve(null))))
      .then((d) => live && setState({ data: d as T, error: null, loading: false }))
      .catch((e) => live && setState({ data: null, error: e, loading: false }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state;
}

// The library lists, with the fields the list pages need, in one request each.
export const THREATS = "/threats?brief=false&include=harm&include=source&include=weaknesses&include=mitigations&include=reachability";
export const MITIGATIONS = "/mitigations?brief=false&include=purpose&include=validation&include=locus&include=failure_behavior";
