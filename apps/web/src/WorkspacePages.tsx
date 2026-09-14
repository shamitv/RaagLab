import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Generation, Project } from "./client";
import { api, defaults } from "./client";

type ProjectSummary = Omit<Project, "jobs">;
type ProjectPage = { items: ProjectSummary[]; next_cursor: string | null };
type LibraryItem = {
  project_id: string;
  project_title: string;
  version_id: string;
  version_number: number;
  version_label: string;
  favorite: boolean;
  created_at: string;
  genre: string | null;
  language: string | null;
  duration_seconds: number | null;
  available: boolean;
};
type LibraryPage = { items: LibraryItem[]; next_cursor: string | null };
type WorkspaceSettings = {
  revision: number;
  generation_defaults: {
    instruments: Generation["instruments"];
    mood: Generation["mood"];
    language: Generation["language"];
    genre: Generation["genre"];
    tempo: Generation["tempo"];
    vocal_type: "Instrumental";
    duration_seconds: number;
    lyrics_mode: "user" | "static" | "mock";
  };
  volume: number;
  repeat_mode: "off" | "one" | "all";
  export_format: "wav";
};
type Template = {
  id: string;
  revision: number;
  name: string;
  description: string;
  draft: Generation;
};

function queryString(values: Record<string, string | null | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values))
    if (value) query.set(key, value);
  return query.size ? `?${query}` : "";
}

export function Projects() {
  const [search, setSearch] = useState("");
  const [archived, setArchived] = useState<"active" | "archived" | "all">(
    "active",
  );
  const [page, setPage] = useState<ProjectPage | null>(null);
  const [cursor, setCursor] = useState("");
  const [back, setBack] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const query = queryString({ q: search.trim(), archived, limit: "20", cursor });
    api<ProjectPage>(`/api/v1/projects${query}`, { signal: controller.signal })
      .then((result) => {
        setPage(result);
        setError("");
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError((e as Error).message);
      });
    return () => controller.abort();
  }, [search, archived, cursor, reload]);

  function reset(query = search, view = archived) {
    setSearch(query);
    setArchived(view);
    setCursor("");
    setBack([]);
  }
  async function archiveProject(project: ProjectSummary, next: boolean) {
    setBusy(project.id);
    setError("");
    try {
      await api<ProjectSummary>(`/api/v1/projects/${project.id}`, {
        method: "PATCH",
        body: JSON.stringify({ archived: next }),
        headers: { "If-Match": `"${project.revision}"` },
      });
      setReload((value) => value + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function duplicateProject(project: ProjectSummary) {
    setBusy(project.id);
    setError("");
    try {
      const copy = await api<ProjectSummary>(
        `/api/v1/projects/${project.id}/duplicate`,
        { method: "POST" },
      );
      window.location.assign(`/projects/${copy.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="data-page">
      <div className="toolbar">
        <label>
          Search projects
          <input
            aria-label="Search projects"
            value={search}
            maxLength={120}
            onChange={(event) => reset(event.target.value)}
          />
        </label>
        <label>
          Show
          <select
            aria-label="Project archive filter"
            value={archived}
            onChange={(event) =>
              reset(search, event.target.value as typeof archived)
            }
          >
            <option value="active">Active projects</option>
            <option value="archived">Archived projects</option>
            <option value="all">All projects</option>
          </select>
        </label>
        <Link className="button-link primary" to="/create">
          Create project
        </Link>
      </div>
      {error && <p role="alert">{error}</p>}
      {page?.items.length === 0 && (
        <section className="card empty">
          <h2>No matching projects</h2>
          <p>Save a draft from Create or change your search.</p>
        </section>
      )}
      <ul className="record-list">
        {page?.items.map((project) => (
          <li className="record-card" key={project.id}>
            <div className="record-main">
              <Link to={`/projects/${project.id}`} className="record-title">
                {project.title}
              </Link>
              <span className="muted">
                {project.archived_at ? "Archived" : "Active"} · created{" "}
                {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="actions">
              <Link className="button-link" to={`/projects/${project.id}`}>
                Open
              </Link>
              <button
                disabled={busy === project.id}
                onClick={() => void duplicateProject(project)}
              >
                Duplicate
              </button>
              <button
                disabled={busy === project.id}
                onClick={() =>
                  void archiveProject(project, !project.archived_at)
                }
              >
                {project.archived_at ? "Unarchive" : "Archive"}
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="pagination" aria-label="Project pages">
        <button
          disabled={back.length === 0}
          onClick={() => {
            const prior = [...back];
            setCursor(prior.pop() ?? "");
            setBack(prior);
          }}
        >
          Previous
        </button>
        <button
          disabled={!page?.next_cursor}
          onClick={() => {
            if (!page?.next_cursor) return;
            setBack((items) => [...items, cursor]);
            setCursor(page.next_cursor);
          }}
        >
          Next
        </button>
      </div>
    </section>
  );
}

export function Library() {
  const [search, setSearch] = useState("");
  const [favorite, setFavorite] = useState(false);
  const [genre, setGenre] = useState("");
  const [language, setLanguage] = useState("");
  const [sort, setSort] = useState<"recent" | "oldest">("recent");
  const [page, setPage] = useState<LibraryPage | null>(null);
  const [cursor, setCursor] = useState("");
  const [back, setBack] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const query = queryString({
      q: search.trim(),
      favorite_only: favorite ? "true" : null,
      genre,
      language,
      sort,
      limit: "20",
      cursor,
    });
    api<LibraryPage>(`/api/v1/library${query}`, { signal: controller.signal })
      .then((result) => {
        setPage(result);
        setError("");
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError((e as Error).message);
      });
    return () => controller.abort();
  }, [search, favorite, genre, language, sort, cursor, reload]);

  function clearPaging() {
    setCursor("");
    setBack([]);
  }
  async function toggleFavorite(item: LibraryItem) {
    setBusy(item.version_id);
    setError("");
    try {
      const version = await api<{ revision: number }>(
        `/api/v1/versions/${item.version_id}`,
      );
      await api(`/api/v1/versions/${item.version_id}`, {
        method: "PATCH",
        body: JSON.stringify({ favorite: !item.favorite }),
        headers: { "If-Match": `"${version.revision}"` },
      });
      setReload((value) => value + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="data-page">
      <div className="toolbar library-toolbar">
        <label>
          Search titles and labels
          <input
            aria-label="Search library"
            value={search}
            maxLength={120}
            onChange={(event) => {
              setSearch(event.target.value);
              clearPaging();
            }}
          />
        </label>
        <label>
          Genre
          <select
            value={genre}
            onChange={(event) => {
              setGenre(event.target.value);
              clearPaging();
            }}
          >
            <option value="">All genres</option>
            {defaultsGenre.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Language
          <select
            value={language}
            onChange={(event) => {
              setLanguage(event.target.value);
              clearPaging();
            }}
          >
            <option value="">All languages</option>
            {defaultsLanguage.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Sort
          <select
            value={sort}
            onChange={(event) => {
              setSort(event.target.value as typeof sort);
              clearPaging();
            }}
          >
            <option value="recent">Newest completed first</option>
            <option value="oldest">Oldest completed first</option>
          </select>
        </label>
        <label className="check-filter">
          <input
            type="checkbox"
            checked={favorite}
            onChange={(event) => {
              setFavorite(event.target.checked);
              clearPaging();
            }}
          />
          Favorites only
        </label>
      </div>
      {error && <p role="alert">{error}</p>}
      {page?.items.length === 0 && (
        <section className="card empty">
          <h2>Your library is ready</h2>
          <p>Completed versions will appear here. Try changing the filters.</p>
          <Link to="/create">Create music</Link>
        </section>
      )}
      <ul className="record-list">
        {page?.items.map((item) => (
          <li className="record-card" key={item.version_id}>
            <div className="record-main">
              <Link
                className="record-title"
                to={`/projects/${item.project_id}?version=${item.version_id}`}
              >
                {item.project_title}
              </Link>
              <span>
                Version {item.version_number} · {item.version_label}
              </span>
              <span className="muted">
                {[item.genre, item.language, item.duration_seconds == null ? null : `${item.duration_seconds.toFixed(0)} sec`]
                  .filter(Boolean)
                  .join(" · ")}
                {!item.available && " · audio unavailable"}
              </span>
            </div>
            <div className="actions">
              <button
                disabled={busy === item.version_id}
                aria-pressed={item.favorite}
                onClick={() => void toggleFavorite(item)}
              >
                {item.favorite ? "★ Favorited" : "☆ Favorite"}
              </button>
              <Link
                className="button-link"
                to={`/projects/${item.project_id}?version=${item.version_id}`}
              >
                Open version
              </Link>
            </div>
          </li>
        ))}
      </ul>
      <div className="pagination" aria-label="Library pages">
        <button
          disabled={back.length === 0}
          onClick={() => {
            const prior = [...back];
            setCursor(prior.pop() ?? "");
            setBack(prior);
          }}
        >
          Previous
        </button>
        <button
          disabled={!page?.next_cursor}
          onClick={() => {
            if (!page?.next_cursor) return;
            setBack((items) => [...items, cursor]);
            setCursor(page.next_cursor);
          }}
        >
          Next
        </button>
      </div>
    </section>
  );
}

export function Settings() {
  const [settings, setSettings] = useState<WorkspaceSettings | null>(null);
  const [etag, setEtag] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let disposed = false;
    fetchSettings()
      .then(({ value, tag }) => {
        if (!disposed) {
          setSettings(value);
          setEtag(tag);
        }
      })
      .catch((e) => !disposed && setError((e as Error).message));
    return () => {
      disposed = true;
    };
  }, []);

  async function reload() {
    try {
      const result = await fetchSettings();
      setSettings(result.value);
      setEtag(result.tag);
      setError("");
      setMessage("Current server settings loaded.");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function save() {
    if (!settings) return;
    setBusy(true);
    setError("");
    setMessage("Saving settings…");
    try {
      const response = await fetch("/api/v1/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "If-Match": etag },
        body: JSON.stringify({
          generation_defaults: settings.generation_defaults,
          volume: settings.volume,
          repeat_mode: settings.repeat_mode,
          export_format: settings.export_format,
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          response.status === 412
            ? "Settings changed in another tab. Reload the server settings before saving."
            : (data.message ?? "Could not save settings"),
        );
      setSettings(data as WorkspaceSettings);
      setEtag(response.headers.get("ETag") ?? `"${data.revision}"`);
      setMessage("Workspace settings saved.");
    } catch (e) {
      setMessage("");
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function updateDefaults(patch: Partial<WorkspaceSettings["generation_defaults"]>) {
    setSettings((value) =>
      value
        ? {
            ...value,
            generation_defaults: { ...value.generation_defaults, ...patch },
          }
        : value,
    );
  }

  return (
    <section className="data-page settings-page">
      {error && (
        <div role="alert">
          {error} {error.includes("another tab") && <button onClick={() => void reload()}>Reload settings</button>}
        </div>
      )}
      {message && <p role="status">{message}</p>}
      {!settings ? (
        !error && <p>Loading workspace settings…</p>
      ) : (
        <>
          <section className="card">
            <h2>Generation defaults</h2>
            <div className="settings-grid">
              <label>
                Primary instrument
                <select
                  value={settings.generation_defaults.instruments[0]}
                  onChange={(event) =>
                    updateDefaults({ instruments: [event.target.value as Generation["instruments"][number]] })
                  }
                >
                  {instruments.map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label>
                Mood
                <select value={settings.generation_defaults.mood} onChange={(event) => updateDefaults({ mood: event.target.value as Generation["mood"] })}>
                  {moods.map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label>
                Language
                <select value={settings.generation_defaults.language} onChange={(event) => updateDefaults({ language: event.target.value as Generation["language"] })}>
                  {defaultsLanguage.map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label>
                Genre
                <select value={settings.generation_defaults.genre} onChange={(event) => updateDefaults({ genre: event.target.value as Generation["genre"] })}>
                  {defaultsGenre.map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label>
                Tempo
                <select value={settings.generation_defaults.tempo} onChange={(event) => updateDefaults({ tempo: event.target.value as Generation["tempo"] })}>
                  {tempos.map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label>
                Lyrics source
                <select value={settings.generation_defaults.lyrics_mode} onChange={(event) => updateDefaults({ lyrics_mode: event.target.value as WorkspaceSettings["generation_defaults"]["lyrics_mode"] })}>
                  <option value="mock">Generated mock lyrics</option>
                  <option value="static">Static original lyrics</option>
                  <option value="user">Your lyrics</option>
                </select>
              </label>
              <label>
                Demo duration
                <input type="number" min="5" max="30" value={settings.generation_defaults.duration_seconds} onChange={(event) => updateDefaults({ duration_seconds: Number(event.target.value) })} />
              </label>
            </div>
          </section>
          <section className="card">
            <h2>Playback and export</h2>
            <div className="settings-grid">
              <label>
                Default volume
                <input type="range" min="0" max="1" step="0.05" value={settings.volume} onChange={(event) => setSettings({ ...settings, volume: Number(event.target.value) })} />
                <small>{Math.round(settings.volume * 100)}%</small>
              </label>
              <label>
                Repeat
                <select value={settings.repeat_mode} onChange={(event) => setSettings({ ...settings, repeat_mode: event.target.value as WorkspaceSettings["repeat_mode"] })}>
                  <option value="off">Off</option>
                  <option value="one">Repeat one</option>
                  <option value="all">Repeat all</option>
                </select>
              </label>
              <label>
                Export format
                <select value={settings.export_format} disabled>
                  <option value="wav">WAV</option>
                </select>
              </label>
            </div>
          </section>
          <button className="primary" disabled={busy} onClick={() => void save()}>
            Save workspace settings
          </button>
        </>
      )}
    </section>
  );
}

export function Templates() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Template[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ items: Template[] }>("/api/v1/templates")
      .then((result) => setItems(result.items))
      .catch((e) => setError((e as Error).message));
  }, []);

  const filtered = items.filter((item) =>
    `${item.name} ${item.description}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()),
  );
  return (
    <section className="data-page">
      <label className="search-field">
        Find a template
        <input value={search} maxLength={120} onChange={(event) => setSearch(event.target.value)} />
      </label>
      {error && <p role="alert">{error}</p>}
      <ul className="record-list template-list">
        {filtered.map((template) => (
          <li className="card" key={template.id}>
            <p className="eyebrow">Original template · revision {template.revision}</p>
            <h2>{template.name}</h2>
            <p>{template.description}</p>
            <p className="muted">
              {template.draft.genre} · {template.draft.mood} · {template.draft.language} · {template.draft.tempo}
            </p>
            <button
              className="primary"
              onClick={() =>
                navigate("/create", {
                  state: { applyTemplate: template.draft },
                })
              }
            >
              Apply to draft
            </button>
          </li>
        ))}
      </ul>
      {filtered.length === 0 && <p>No templates match that search.</p>}
      <p className="muted">Applying a template only updates the draft. You choose when to generate.</p>
    </section>
  );
}

async function fetchSettings() {
  const response = await fetch("/api/v1/settings", { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message ?? "Could not load settings");
  return {
    value: data as WorkspaceSettings,
    tag: response.headers.get("ETag") ?? `"${data.revision}"`,
  };
}

const defaultsGenre: Generation["genre"][] = ["Indie Pop", "Pop", "Folk", "Ambient", "Rock", "Electronic"];
const defaultsLanguage: Generation["language"][] = ["Hindi", "English", "Hinglish", "Punjabi", "Tamil"];
const moods: Generation["mood"][] = ["Happy", "Melancholic", "Romantic", "Energetic", "Calm", "Epic"];
const tempos: Generation["tempo"][] = ["Slow", "Medium", "Fast"];
const instruments: Generation["instruments"][number][] = ["Guitar", "Piano", "Tabla", "Drums", "Bass", "Strings", "Synth"];
