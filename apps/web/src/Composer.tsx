import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { components } from "./api.generated";
import {
  api,
  defaults,
  validDraft,
  versionInputs,
  type Generation,
  type Job,
  type Project,
  type Version,
} from "./client";
import { readDraft, writeDraft, type LocalDraft } from "./drafts";
import { Player } from "./Player";
const terminal = new Set(["succeeded", "failed", "cancelled", "timed_out"]);
type Caps = components["schemas"]["CapabilitiesResponse"];
type Summary = components["schemas"]["VersionView"];
export function Composer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<Generation>(defaults),
    [caps, setCaps] = useState<Caps | null>(null),
    [project, setProject] = useState<Project | null>(null);
  const [version, setVersion] = useState<Version | null>(null),
    [history, setHistory] = useState<Summary[]>([]),
    [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [saveState, setSaveState] = useState("Local draft"),
    [busy, setBusy] = useState(false),
    [online, setOnline] = useState(navigator.onLine);
  const [reload, setReload] = useState(0);
  const [loaded, setLoaded] = useState(false),
    [dirty, setDirty] = useState(false),
    [conflict, setConflict] = useState<LocalDraft | null>(null);
  const [instruction, setInstruction] = useState(""),
    [editing, setEditing] = useState(false),
    [lyrics, setLyrics] = useState(""),
    [label, setLabel] = useState(""),
    [title, setTitle] = useState("");
  const [focused, setFocused] = useState<"mood" | "instruments" | null>(null),
    [iterationDraft, setIterationDraft] = useState<Generation>(defaults);
  const [desktop, setDesktop] = useState(window.innerWidth >= 1200);
  const generation = useRef(0),
    selection = useRef(0),
    projectRef = useRef<Project | null>(null),
    draftRef = useRef(draft),
    dirtyRef = useRef(dirty);
  const versionRef = useRef(version);
  versionRef.current = version;
  projectRef.current = project;
  draftRef.current = draft;
  dirtyRef.current = dirty;
  const baseRevision = useRef<number | null>(null),
    transfer = useRef<Generation | null>(null);
  const submission = useRef<{ path: string; body: string; key: string } | null>(
    null,
  );
  useEffect(() => {
    try {
      submission.current = JSON.parse(
        sessionStorage.getItem("museforge-submission") ?? "null",
      );
    } catch {
      /* New intent if storage is invalid. */
    }
    const query = matchMedia("(min-width:1200px)");
    const resize = () => setDesktop(query.matches);
    query.addEventListener("change", resize);
    return () => query.removeEventListener("change", resize);
  }, []);
  function adopt(v: Version) {
    versionRef.current = v;
    setVersion(v);
    setLabel(v.label);
    setLyrics(v.lyrics);
    setEditing(false);
    setFocused(null);
    setInstruction("");
    setIterationDraft(versionInputs(v));
  }
  async function versions(projectId: string) {
    let cursor: string | null = null;
    const items: Summary[] = [];
    do {
      const page: components["schemas"]["VersionPage"] = await api(
        `/api/v1/projects/${projectId}/versions?limit=100${cursor ? "&cursor=" + encodeURIComponent(cursor) : ""}`,
      );
      items.push(...page.items);
      cursor = page.next_cursor;
    } while (cursor);
    return items.sort((a, b) => a.number - b.number);
  }
  useEffect(() => {
    const token = ++generation.current;
    ++selection.current;
    setLoaded(false);
    setVersion(null);
    setHistory([]);
    setJob(null);
    setProject(null);
    setConflict(null);
    setError("");
    async function load() {
      try {
        const [cap, local, p] = await Promise.all([
          api<Caps>("/api/v1/capabilities"),
          readDraft(id ?? "create").catch(() => {
            setError(
              "Local draft storage unavailable; save to the server to retain edits.",
            );
            return undefined;
          }),
          id ? api<Project>(`/api/v1/projects/${id}`) : Promise.resolve(null),
        ]);
        const list = p ? await versions(p.id) : [];
        const v = p?.active_version_id
          ? await api<Version>(`/api/v1/versions/${p.active_version_id}`)
          : null;
        if (token !== generation.current) return;
        setCaps(cap);
        setProject(p);
        setTitle(p?.title ?? "");
        setHistory(list);
        setJob(
          p?.jobs.find((j) => !terminal.has(j.state)) ?? p?.jobs[0] ?? null,
        );
        if (v) adopt(v);
        const server =
          p && Object.keys(p.draft).length
            ? (p.draft as Generation)
            : {
                ...defaults,
                lyrics: { mode: cap.default_lyrics_mode },
                duration_seconds: cap.duration.default,
              };
        baseRevision.current = p?.revision ?? null;
        if (transfer.current) {
          setDraft(transfer.current);
          transfer.current = null;
          setDirty(true);
        } else if (
          local?.dirty &&
          local.baseRevision === (p?.revision ?? null)
        ) {
          setDraft(local.draft);
          setDirty(true);
        } else {
          setDraft(server);
          setDirty(false);
          if (local?.dirty) setConflict(local);
        }
        setSaveState(p ? "Saved project" : "Local draft");
        setLoaded(true);
        setOnline(true);
      } catch (e) {
        if (token === generation.current) {
          setError((e as Error).message);
          setOnline(false);
        }
      }
    }
    void load();
    return () => {
      ++generation.current;
    };
  }, [id, reload]);
  useEffect(() => {
    if (!loaded) return;
    const timer = setTimeout(() => {
      void writeDraft(id ?? "create", {
        draft,
        baseRevision: baseRevision.current,
        editedAt: Date.now(),
        dirty,
      }).catch(() =>
        setError(
          "Local draft storage failed. Keep this tab open and save the project.",
        ),
      );
    }, 200);
    return () => clearTimeout(timer);
  }, [draft, dirty, id, loaded, project?.revision]);
  useEffect(() => {
    const leave = (e: BeforeUnloadEvent) => {
      if (dirtyRef.current && saveState === "Save failed") {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", leave);
    return () => window.removeEventListener("beforeunload", leave);
  }, [saveState]);
  async function reconcile(completedId?: string) {
    const token = generation.current;
    const p = id ? await api<Project>(`/api/v1/projects/${id}`) : null;
    const list = p ? await versions(p.id) : [];
    const chosen = selection.current;
    const v = p?.active_version_id
      ? await api<Version>(`/api/v1/versions/${p.active_version_id}`)
      : null;
    if (
      token !== generation.current ||
      (p && projectRef.current && p.revision < projectRef.current.revision)
    )
      return;
    if (
      p &&
      completedId &&
      p.active_version_id === completedId &&
      p.revision === (projectRef.current?.revision ?? 0) + 1 &&
      baseRevision.current === projectRef.current?.revision
    )
      baseRevision.current = p.revision;
    setProject(p);
    setHistory(list);
    if (v && chosen === selection.current && v.id !== versionRef.current?.id)
      adopt(v);
    if (p) {
      setJob(p.jobs.find((j) => !terminal.has(j.state)) ?? p.jobs[0] ?? null);
    }
    setOnline(true);
  }
  useEffect(() => {
    const offline = () => setOnline(false);
    const reconnect = () => {
      setNotice("Reconnecting…");
      void reconcile()
        .then(() => setNotice("Connected; server state refreshed."))
        .catch((e) => setError(e.message));
    };
    window.addEventListener("offline", offline);
    window.addEventListener("online", reconnect);
    return () => {
      window.removeEventListener("offline", offline);
      window.removeEventListener("online", reconnect);
    };
  }, [id, version?.id]);
  useEffect(() => {
    if (!job || terminal.has(job.state)) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let delay = 1000;
    async function poll() {
      try {
        const next = await api<Job>(`/api/v1/jobs/${job!.id}`);
        if (stopped) return;
        setJob(next);
        setOnline(true);
        if (terminal.has(next.state)) {
          await reconcile(next.result_version_id ?? undefined);
          if (!stopped)
            setNotice(
              next.state === "succeeded"
                ? "New version available in history."
                : "Generation " + next.state.replaceAll("_", " "),
            );
          return;
        }
        delay = document.hidden ? 10000 : 1000;
      } catch {
        if (!stopped) {
          setOnline(false);
          setNotice("Connection interrupted; reconnecting…");
        }
        delay = Math.min(10000, delay * 2);
      }
      if (!stopped) timer = setTimeout(poll, delay);
    }
    timer = setTimeout(poll, delay);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [job?.id, id]);
  function change<K extends keyof Generation>(key: K, value: Generation[K]) {
    setDraft((old) => ({ ...old, [key]: value }));
    setDirty(true);
    setSaveState("Unsaved changes");
  }
  async function patchProject(body: components["schemas"]["ProjectPatch"]) {
    const current = projectRef.current;
    if (!current) throw new Error("Open a project first");
    const result = await api<Project>(`/api/v1/projects/${current.id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      headers: { "If-Match": `"${current.revision}"` },
    });
    if (baseRevision.current === current.revision)
      baseRevision.current = result.revision;
    projectRef.current = result;
    setProject(result);
    return result;
  }
  async function selectVersion(identifier: string) {
    const token = ++selection.current;
    setBusy(true);
    setError("");
    try {
      const result = await api<Version>(`/api/v1/versions/${identifier}`);
      await patchProject({ active_version_id: identifier });
      if (token === selection.current) adopt(result);
      return token === selection.current;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    setBusy(true);
    setSaveState("Saving…");
    setError("");
    try {
      const p = project
        ? await patchProject({ title, draft })
        : await api<Project>("/api/v1/projects", {
            method: "POST",
            body: JSON.stringify({
              title: title || draft.brief.slice(0, 120) || "Untitled project",
              draft,
            }),
          });
      baseRevision.current = p.revision;
      await writeDraft(p.id, {
        draft,
        baseRevision: p.revision,
        editedAt: Date.now(),
        dirty: false,
      });
      setDirty(false);
      setSaveState("Saved to server");
      if (!id) navigate(`/projects/${p.id}`);
    } catch (e) {
      setSaveState("Save failed");
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submit(path: string, body: unknown) {
    setBusy(true);
    setError("");
    try {
      const serialized = JSON.stringify(body);
      if (
        submission.current?.body !== serialized ||
        submission.current.path !== path
      )
        submission.current = {
          path,
          body: serialized,
          key: crypto.randomUUID(),
        };
      sessionStorage.setItem(
        "museforge-submission",
        JSON.stringify(submission.current),
      );
      await writeDraft(id ?? "create", {
        draft,
        baseRevision: baseRevision.current,
        editedAt: Date.now(),
        dirty,
      });
      const result = await api<components["schemas"]["Accepted"]>(path, {
        method: "POST",
        body: serialized,
        headers: { "Idempotency-Key": submission.current.key },
      });
      sessionStorage.removeItem("museforge-submission");
      submission.current = null;
      if (id !== result.project_id) {
        transfer.current = draft;
        navigate(`/projects/${result.project_id}`);
      } else setJob(await api<Job>(result.status_url));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function iterate(
    operation: components["schemas"]["Iteration"]["operation"],
  ) {
    if (!version) return;
    const inputs = {
      ...iterationDraft,
      iteration_instruction: instruction.trim() ? instruction : null,
    };
    if (operation === "lyrics_edit")
      inputs.lyrics = { mode: "user", text: lyrics };
    if (operation === "variation") inputs.seed = null;
    await submit(`/api/v1/versions/${version.id}/iterations`, {
      operation,
      inputs,
    });
  }
  async function metadata(body: components["schemas"]["VersionPatch"]) {
    if (!version) return;
    setBusy(true);
    try {
      const v = await api<Version>(`/api/v1/versions/${version.id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
        headers: { "If-Match": `"${version.revision}"` },
      });
      setVersion(v);
      setHistory((old) => old.map((item) => (item.id === v.id ? v : item)));
      setNotice("Version metadata saved.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const blocked = busy || !online || !loaded;
  const generating = !!job && !terminal.has(job.state);
  const lyricsCard = version ? (
    <section key="lyrics" className="card" aria-label="Generated Lyrics">
      <h2>Lyrics · {version.provenance.lyrics.source}</h2>
      <button
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(version.lyrics);
            setNotice("Lyrics copied.");
          } catch {
            setNotice(
              "Copy failed. Select the lyrics text below and copy manually.",
            );
          }
        }}
      >
        Copy lyrics
      </button>
      {editing ? (
        <>
          <label>
            Refine lyrics
            <textarea
              autoFocus
              aria-label="Refine lyrics"
              value={lyrics}
              onChange={(e) => setLyrics(e.target.value)}
            />
          </label>
          <p>Audio unchanged: saving creates a lyrics-only version.</p>
          <div className="actions">
            <button
              className="primary"
              disabled={
                blocked ||
                generating ||
                !validDraft({
                  ...iterationDraft,
                  lyrics: { mode: "user", text: lyrics },
                })
              }
              onClick={() => void iterate("lyrics_edit")}
            >
              Apply lyrics
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setLyrics(version.lyrics);
              }}
            >
              Cancel lyrics edit
            </button>
          </div>
        </>
      ) : (
        <>
          <pre className="lyrics" tabIndex={0}>
            {version.lyrics}
          </pre>
          <button onClick={() => setEditing(true)}>Refine Lyrics</button>
        </>
      )}
    </section>
  ) : null;
  const player = version ? (
    <Player
      key="player"
      version={version}
      collection={history.map((v) => v.id)}
      select={selectVersion}
      disabled={blocked}
    />
  ) : null;
  return (
    <>
      <p className="demo-note">
        Original instrumental demo. Musical controls are saved intent; demo
        audio does not faithfully implement them or sing lyrics.
      </p>
      <div role="status">
        {notice}
        {!online &&
          " Offline. Local drafts are retained; server actions are paused."}
      </div>
      {error && (
        <div role="alert">
          {error}
          <button
            onClick={() => {
              if (!loaded) {
                setReload((x) => x + 1);
                return;
              }
              void reconcile()
                .then(() =>
                  setError(
                    "Server state reloaded; review your local draft before saving.",
                  ),
                )
                .catch((e) => setError(e.message));
            }}
          >
            Reload server state
          </button>
        </div>
      )}
      {conflict && (
        <section className="card">
          <h2>Recovered draft needs review</h2>
          <p>
            The server revision changed. Keep your local edits or use the loaded
            server draft.
          </p>
          <pre className="lyrics">{conflict.draft.brief}</pre>
          <button
            onClick={() => {
              setDraft(conflict.draft);
              setDirty(true);
              setConflict(null);
              setSaveState("Unsaved changes");
            }}
          >
            Keep local edits
          </button>
          <button
            onClick={() => {
              setConflict(null);
              setDirty(false);
            }}
          >
            Use server draft
          </button>
        </section>
      )}
      <div className="studio">
        <form
          className="composer card"
          onSubmit={(e) => {
            e.preventDefault();
            void submit("/api/v1/generations", {
              ...draft,
              project_id: id ?? null,
            });
          }}
        >
          <fieldset disabled={!loaded} className="composer-fields">
            <h2>Song Brief</h2>
            <label>
              Music brief
              <textarea
                required
                aria-describedby="brief-help"
                aria-invalid={Array.from(draft.brief).length > 500}
                value={draft.brief}
                onChange={(e) => change("brief", e.target.value)}
              />
            </label>
            <small id="brief-help">
              {Array.from(draft.brief).length}/500 characters. Describe your
              original idea.
            </small>
            <button
              type="button"
              onClick={() => {
                const examples: [
                  string,
                  Generation["language"],
                  Generation["mood"],
                ][] = [
                  [
                    "A calm Hindi song about the first light on a quiet terrace.",
                    "Hindi",
                    "Calm",
                  ],
                  [
                    "An energetic Tamil song about cycling home under the stars.",
                    "Tamil",
                    "Energetic",
                  ],
                  [
                    "A happy English song about meeting an old friend in spring.",
                    "English",
                    "Happy",
                  ],
                ];
                const ex =
                  examples[
                    (examples.findIndex((x) => x[0] === draft.brief) + 1) %
                      examples.length
                  ];
                setDraft({
                  ...draft,
                  brief: ex[0],
                  language: ex[1],
                  mood: ex[2],
                });
                setDirty(true);
              }}
            >
              Try an example
            </button>
            <fieldset>
              <legend>Instruments</legend>
              <div className="chips">
                {caps?.instruments.map((value) => (
                  <button
                    type="button"
                    key={value}
                    aria-pressed={draft.instruments.includes(value as never)}
                    onClick={() =>
                      change(
                        "instruments",
                        (draft.instruments.includes(value as never)
                          ? draft.instruments.filter((x) => x !== value)
                          : [
                              ...draft.instruments,
                              value,
                            ]) as Generation["instruments"],
                      )
                    }
                  >
                    {value}
                  </button>
                ))}
              </div>
            </fieldset>
            {(["mood", "language"] as const).map((key) => (
              <fieldset key={key}>
                <legend>{key === "mood" ? "Mood" : "Language"}</legend>
                <div className="chips">
                  {(key === "mood" ? caps?.moods : caps?.languages)?.map(
                    (value) => (
                      <label className="radio-chip" key={value}>
                        <input
                          type="radio"
                          name={key}
                          checked={draft[key] === value}
                          onChange={() => change(key, value as never)}
                        />
                        <span>{value}</span>
                      </label>
                    ),
                  )}
                </div>
              </fieldset>
            ))}
            <div className="music-fields">
              {(["genre", "tempo"] as const).map((key) => (
                <label key={key}>
                  {key === "genre" ? "Genre" : "Tempo"}
                  <select
                    value={draft[key]}
                    onChange={(e) => change(key, e.target.value as never)}
                  >
                    {(key === "genre"
                      ? caps?.genres
                      : ["Slow", "Medium", "Fast"]
                    )?.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
              ))}
              <label>
                Vocal Type
                <select disabled value="Instrumental">
                  <option>Instrumental</option>
                  <option>Male Vocals</option>
                  <option>Female Vocals</option>
                  <option>Mixed Vocals</option>
                </select>
              </label>
            </div>
            <small>Sung vocals require a capable real provider.</small>
            <label>
              Lyrics source
              <select
                value={draft.lyrics?.mode ?? "mock"}
                onChange={(e) =>
                  change("lyrics", {
                    ...draft.lyrics,
                    mode: e.target.value as "user" | "static" | "mock",
                  })
                }
              >
                <option value="user">Your exact lyrics</option>
                <option value="static">Original static fixture</option>
                <option value="mock">Generated demo lyrics</option>
              </select>
            </label>
            {draft.lyrics?.mode === "user" && (
              <label>
                Your lyrics
                <textarea
                  aria-label="Your lyrics"
                  required
                  value={draft.lyrics.text ?? ""}
                  onChange={(e) =>
                    change("lyrics", { mode: "user", text: e.target.value })
                  }
                />
                <small>
                  Up to 20,000 characters / 80,000 UTF-8 bytes. Whitespace is
                  preserved.
                </small>
              </label>
            )}
            <details>
              <summary>Advanced Options</summary>
              <p>
                Provider: {caps?.provider_id ?? "Loading…"} · CPU demo ·{" "}
                {caps?.readiness.state}
              </p>
              <label>
                Duration (seconds)
                <input
                  type="number"
                  min="5"
                  max="30"
                  value={draft.duration_seconds}
                  onChange={(e) =>
                    change("duration_seconds", Number(e.target.value))
                  }
                />
              </label>
              <label>
                Seed (optional)
                <input
                  type="number"
                  min="0"
                  max="4294967295"
                  value={draft.seed ?? ""}
                  onChange={(e) =>
                    change(
                      "seed",
                      e.target.value === "" ? null : Number(e.target.value),
                    )
                  }
                />
              </label>
              <small>
                Duration and seed affect demo audio. Exact musical refinement is
                unavailable.
              </small>
            </details>
            <button
              className="primary generate"
              disabled={blocked || generating || !validDraft(draft)}
            >
              {busy ? "Submitting…" : "Generate"}
            </button>
            <label>
              Project title
              <input
                maxLength={120}
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setDirty(true);
                }}
              />
            </label>
            <button
              type="button"
              disabled={
                blocked || !validDraft(draft) || (!!project && !title.trim())
              }
              onClick={() => void save()}
            >
              Save Project
            </button>
            <small role="status">{saveState}</small>
          </fieldset>
        </form>
        <div className="results">
          {job && (
            <section className="card" aria-label="Generation status">
              <p role="status">
                {job.state} · {job.stage.replaceAll("_", " ")} · dispatch{" "}
                {job.dispatch_status} · attempt {job.attempt_count} · worker{" "}
                {job.provider_readiness.state}
              </p>
              {job.error && <p role="alert">{job.error.message}</p>}
              {!terminal.has(job.state) && (
                <button
                  disabled={blocked || job.state === "cancellation_requested"}
                  onClick={() =>
                    void api<Job>(`/api/v1/jobs/${job.id}/cancel`, {
                      method: "POST",
                    })
                      .then(setJob)
                      .catch((e) => setError(e.message))
                  }
                >
                  Cancel generation
                </button>
              )}
              {["failed", "cancelled", "timed_out"].includes(job.state) && (
                <button
                  disabled={blocked || !validDraft(draft)}
                  onClick={() =>
                    void submit("/api/v1/generations", {
                      ...draft,
                      project_id: id,
                    })
                  }
                >
                  Generate again
                </button>
              )}
            </section>
          )}
          {!version ? (
            <section className="card empty">
              <h2>Your music starts with an idea</h2>
              <p>
                Generate a demo to hear real audio, preserve your lyrics, and
                explore versions.
              </p>
            </section>
          ) : (
            <section aria-label="Generated result">
              <div className="result-pair">
                {desktop ? [lyricsCard, player] : [player, lyricsCard]}
              </div>
              <section className="card">
                <h2>Iterate</h2>
                <p>
                  Another original demo will be produced. Precise semantic audio
                  changes are not supported. Source: {version.label}.
                </p>
                <label>
                  Tell us how you’d like to change the song
                  <textarea
                    maxLength={2000}
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                  />
                </label>
                {focused === "mood" && (
                  <label>
                    Iteration mood
                    <select
                      autoFocus
                      value={iterationDraft.mood}
                      onChange={(e) =>
                        setIterationDraft({
                          ...iterationDraft,
                          mood: e.target.value as Generation["mood"],
                        })
                      }
                    >
                      {caps?.moods.map((m) => (
                        <option key={m}>{m}</option>
                      ))}
                    </select>
                  </label>
                )}
                {focused === "instruments" && (
                  <fieldset>
                    <legend>Iteration instruments</legend>
                    <div className="chips">
                      {caps?.instruments.map((i) => (
                        <button
                          key={i}
                          aria-pressed={iterationDraft.instruments.includes(
                            i as never,
                          )}
                          onClick={() =>
                            setIterationDraft({
                              ...iterationDraft,
                              instruments: (iterationDraft.instruments.includes(
                                i as never,
                              )
                                ? iterationDraft.instruments.filter(
                                    (x) => x !== i,
                                  )
                                : [
                                    ...iterationDraft.instruments,
                                    i,
                                  ]) as Generation["instruments"],
                            })
                          }
                        >
                          {i}
                        </button>
                      ))}
                    </div>
                  </fieldset>
                )}
                <button
                  className="primary apply"
                  disabled={
                    blocked ||
                    generating ||
                    !instruction.trim() ||
                    !validDraft(iterationDraft)
                  }
                  onClick={() => void iterate("refine")}
                >
                  Apply Changes
                </button>
                <div className="actions">
                  <button
                    disabled={blocked || generating}
                    onClick={() => void iterate("regenerate")}
                  >
                    Regenerate
                  </button>
                  <button
                    onClick={() => {
                      setFocused("mood");
                      setInstruction("Change the mood");
                    }}
                  >
                    Change Mood
                  </button>
                  <button
                    onClick={() => {
                      setFocused("instruments");
                      setInstruction("Try new instruments");
                    }}
                  >
                    Try New Instruments
                  </button>
                  <button
                    disabled={blocked || generating}
                    onClick={() => void iterate("variation")}
                  >
                    Create Variation
                  </button>
                </div>
              </section>
              <details className="card" open={desktop}>
                <summary>Song Structure</summary>
                <p>
                  Structure unavailable. The demo provider supplies no measured
                  or estimated section boundaries.
                </p>
                <p>
                  Measured artifact duration: {version.audio.duration_seconds}{" "}
                  seconds.
                </p>
              </details>
              <details className="card" open={desktop}>
                <summary>Version History ({history.length})</summary>
                <label>
                  Completed versions
                  <select
                    disabled={blocked}
                    value={version.id}
                    onChange={(e) => void selectVersion(e.target.value)}
                  >
                    {history.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.number}. {v.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="version-list">
                  {history.map((v) => (
                    <button
                      key={v.id}
                      disabled={blocked}
                      aria-pressed={v.id === version.id}
                      onClick={() => void selectVersion(v.id)}
                    >
                      Version {v.number} · {v.label}
                    </button>
                  ))}
                </div>
                <p>
                  Parent:{" "}
                  {version.parent_version_id
                    ? (history.find((v) => v.id === version.parent_version_id)
                        ?.label ?? version.parent_version_id)
                    : "Original generation"}
                </p>
                <button
                  disabled={blocked}
                  aria-pressed={version.favorite}
                  onClick={() => void metadata({ favorite: !version.favorite })}
                >
                  {version.favorite ? "Unfavorite" : "Favorite"}
                </button>
                <label>
                  Version label
                  <input
                    maxLength={120}
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                  />
                </label>
                <button
                  disabled={blocked || !label.trim()}
                  onClick={() => void metadata({ label })}
                >
                  Rename version
                </button>
              </details>
            </section>
          )}
        </div>
      </div>
    </>
  );
}
export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    api<{ items: Project[] }>("/api/v1/projects?limit=100")
      .then((r) => setProjects(r.items))
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      {error && <p role="alert">{error}</p>}
      <ul className="project-list">
        {projects.map((p) => (
          <li key={p.id}>
            <Link to={`/projects/${p.id}`}>{p.title}</Link>
          </li>
        ))}
      </ul>
      <Link to="/create">Create music</Link>
    </>
  );
}
