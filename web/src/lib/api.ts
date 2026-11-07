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
  const r = await fetch("/api" + path, { method: "POST", headers: { "content-type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new ApiError(r.status, data?.detail?.message || data?.detail || r.statusText);
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
