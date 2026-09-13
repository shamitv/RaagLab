import type { components } from "./api.generated";
export type Generation = components["schemas"]["Generation"];
export type Version = components["schemas"]["VersionDetail"];
export type Project = components["schemas"]["ProjectDetail"];
export type Job = components["schemas"]["JobView"];
export const defaults: Generation = {
  brief: "",
  instruments: ["Piano"],
  mood: "Calm",
  language: "English",
  genre: "Indie Pop",
  tempo: "Medium",
  vocal_type: "Instrumental",
  lyrics: { mode: "mock" },
  duration_seconds: 8,
};
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    signal: AbortSignal.timeout(10000),
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      response.status === 412
        ? "Save conflict: the server changed. Reload server state before saving again; your local draft is retained."
        : (data.message ?? "Request failed"),
    );
  return data;
}
export function validDraft(d: Generation) {
  const text = d.lyrics?.text ?? "";
  return (
    !!d.brief.trim() &&
    Array.from(d.brief).length <= 500 &&
    !d.brief.includes("\0") &&
    d.instruments.length > 0 &&
    (d.lyrics?.mode !== "user" || !!text.trim()) &&
    !text.includes("\0") &&
    Array.from(text).length <= 20000 &&
    new TextEncoder().encode(text).length <= 80000 &&
    Number.isInteger(d.duration_seconds) &&
    d.duration_seconds! >= 5 &&
    d.duration_seconds! <= 30 &&
    (d.seed == null ||
      (Number.isInteger(d.seed) && d.seed >= 0 && d.seed <= 4294967295))
  );
}
export function versionInputs(v: Version): Generation {
  return Object.fromEntries(
    Object.keys({ ...defaults, seed: null, iteration_instruction: null }).map(
      (k) => [k, v.inputs[k]],
    ),
  ) as Generation;
}
