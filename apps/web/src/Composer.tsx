import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { components } from './api.generated';

type Generation = components['schemas']['Generation'];
type Job = components['schemas']['JobView'];
type Version = components['schemas']['VersionDetail'];
type Project = components['schemas']['ProjectDetail'];
type Caps = components['schemas']['CapabilitiesResponse'];
const defaults: Generation = {brief: '', instruments: ['Piano'], mood: 'Calm', language: 'English', genre: 'Indie Pop', tempo: 'Medium', vocal_type: 'Instrumental', lyrics: {mode: 'mock'}, duration_seconds: 8};
const terminal = new Set(['succeeded', 'failed', 'cancelled', 'timed_out']);
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {signal: AbortSignal.timeout(10000), ...init, headers: {'Content-Type': 'application/json', ...init?.headers}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.message ?? 'Request failed');
  return data;
}
export function Composer() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<Generation>(() => {try {return JSON.parse(sessionStorage.getItem('museforge-draft') ?? 'null') ?? defaults;} catch {return defaults;}});
  const initialDraft = useRef(draft);
  const [caps, setCaps] = useState<Caps | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [version, setVersion] = useState<Version | null>(null);
  const [history, setHistory] = useState<{id: string; label: string}[]>([]);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const submission = useRef<{body: string; key: string} | null>((() => {try {return JSON.parse(sessionStorage.getItem('museforge-submission') ?? 'null');} catch {return null;}})());
  const selection = useRef(0);
  useEffect(() => {try {sessionStorage.setItem('museforge-draft', JSON.stringify(draft));} catch {setError('Local draft storage unavailable; keep this tab open to retain edits.');}}, [draft]);
  useEffect(() => {api<Caps>('/api/v1/capabilities').then(result => {setCaps(result); if (initialDraft.current === defaults) setDraft(old => old === defaults ? {...old, lyrics: {mode: result.default_lyrics_mode}, duration_seconds: result.duration.default} : old);}).catch(e => setError(e.message));}, []);
  async function selectVersion(identifier: string) {
    const token = ++selection.current;
    setVersion(null);
    try {const result = await api<Version>(`/api/v1/versions/${identifier}`); if (token === selection.current) setVersion(result);} catch(e) {if (token === selection.current) setError((e as Error).message);}
  }
  useEffect(() => {
    let active = true;
    ++selection.current; setVersion(null); setJob(null); setHistory([]);
    if (id) api<Project>(`/api/v1/projects/${id}`).then(project => {
      if (!active) return;
      setJob(project.jobs.find(j => !terminal.has(j.state)) ?? project.jobs[0] ?? null);
      if (project.active_version_id) void selectVersion(project.active_version_id);
      api<{items: Version[]}>(`/api/v1/projects/${id}/versions?limit=100`).then(v => {if(active) setHistory(v.items);}).catch(e => {if(active) setError(e.message);});
    }).catch(e => {if(active) setError(e.message);});
    return () => {active = false; ++selection.current;};
  }, [id]);
  useEffect(() => {
    if (!job || terminal.has(job.state)) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let delay = 500;
    const poll = async () => {
      try {
        const next = await api<Job>(`/api/v1/jobs/${job.id}`);
        if (stopped) return;
        setJob(next); setError('');
        if (terminal.has(next.state)) {
          if (next.result_version_id) {
            await selectVersion(next.result_version_id);
            const versions = await api<{items: Version[]}>(`/api/v1/projects/${id}/versions?limit=100`);
            if (!stopped) setHistory(versions.items);
          }
          return;
        }
        delay = Math.min(3000, delay * 1.4);
      } catch(e) {if (!stopped) setError(`Connection interrupted; reconnecting. ${(e as Error).message}`); delay = Math.min(10000, delay * 2);}
      if (!stopped) timer = setTimeout(poll, delay);
    };
    timer = setTimeout(poll, delay);
    return () => {stopped = true; clearTimeout(timer);};
  }, [job?.id, id]);
  function change<K extends keyof Generation>(key: K, value: Generation[K]) {setDraft(old => ({...old, [key]: value}));}
  async function generate(event: React.FormEvent) {
    event.preventDefault(); setSubmitting(true); setError('');
    const body = JSON.stringify({...draft, project_id: id ?? null});
    if (submission.current?.body !== body) submission.current = {body, key: crypto.randomUUID()};
    try {
      sessionStorage.setItem('museforge-submission', JSON.stringify(submission.current));
      const result = await api<components['schemas']['Accepted']>('/api/v1/generations', {method:'POST', body, headers:{'Idempotency-Key': submission.current.key}});
      submission.current = null;
      sessionStorage.removeItem('museforge-submission');
      if (id !== result.project_id) navigate(`/projects/${result.project_id}`);
      else setJob(await api<Job>(result.status_url));
    } catch(e) {setError((e as Error).message);} finally {setSubmitting(false);}
  }
  return <>
    <p className="muted">Original instrumental demo. Musical controls are saved intent; demo audio does not faithfully implement them or sing lyrics. Text lyrics are labelled by source.</p>
    {error && <p role="alert">{error}</p>}
    <form onSubmit={generate} className="composer">
      <label>Music brief<textarea required value={draft.brief} onChange={e => change('brief', e.target.value)} /></label>
      <small>{Array.from(draft.brief).length}/500 characters</small>
      <fieldset><legend>Instruments</legend>{caps?.instruments.map(value => <label className="choice" key={value}><input type="checkbox" checked={draft.instruments.includes(value as never)} onChange={e => change('instruments', (e.target.checked ? [...draft.instruments, value] : draft.instruments.filter(i => i !== value)) as Generation['instruments'])}/>{value}</label>)}</fieldset>
      {(['mood', 'language', 'genre', 'tempo'] as const).map(key => <label key={key}>{key[0].toUpperCase()+key.slice(1)}<select value={draft[key]} onChange={e => change(key, e.target.value as never)}>{(key === 'tempo' ? ['Slow','Medium','Fast'] : key === 'mood' ? caps?.moods : key === 'language' ? caps?.languages : caps?.genres)?.map(v => <option key={v}>{v}</option>)}</select></label>)}
      <label>Vocals<select value="Instrumental" disabled><option>Instrumental</option><option>Male Vocals</option><option>Female Vocals</option><option>Mixed Vocals</option></select></label><small>Sung vocals require a capable real provider.</small>
      <label>Lyrics source<select value={draft.lyrics?.mode ?? 'mock'} onChange={e => change('lyrics', {...draft.lyrics, mode:e.target.value as 'user'|'static'|'mock'})}><option value="user">Your exact lyrics</option><option value="static">Original static fixture</option><option value="mock">Generated demo lyrics</option></select></label>
      {draft.lyrics?.mode === 'user' && <label>Your lyrics<textarea required value={draft.lyrics.text ?? ''} onChange={e => change('lyrics', {...draft.lyrics, mode:'user', text:e.target.value})}/></label>}
      <label>Duration (seconds)<input type="number" min="5" max="30" required value={draft.duration_seconds} onChange={e => change('duration_seconds', Number(e.target.value))}/></label>
      <label>Seed (optional)<input type="number" min="0" max="4294967295" value={draft.seed ?? ''} onChange={e => change('seed', e.target.value === '' ? null : Number(e.target.value))}/></label>
      <button disabled={submitting || !caps || !draft.brief.trim() || Array.from(draft.brief).length > 500 || !draft.instruments.length}>{submitting ? 'Submitting…' : 'Generate'}</button>
    </form>
    {job && <section aria-label="Generation status"><p role="status">{job.state} · {job.stage.replaceAll('_', ' ')} · dispatch {job.dispatch_status} · attempt {job.attempt_count} · worker {job.provider_readiness.state}</p>{job.error && <p role="alert">{job.error.message}</p>}{!terminal.has(job.state) && <button disabled={job.state === 'cancellation_requested'} onClick={() => api<Job>(`/api/v1/jobs/${job.id}/cancel`, {method:'POST'}).then(setJob).catch(e => setError(e.message))}>Cancel generation</button>}</section>}
    {history.length > 0 && <label>Completed versions<select value={version?.id ?? ''} onChange={e => void selectVersion(e.target.value)}><option value="" disabled>Select version</option>{history.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}</select></label>}
    {version && <section aria-label="Generated result"><h2>{version.label}</h2><audio key={version.id} controls preload="metadata" src={version.audio.url} onError={() => setError('Audio is unavailable. The saved lyrics and version remain available.')}/><p><a href={version.audio.url} download={`museforge-${version.id}.wav`}>Download WAV</a> · {version.audio.duration_seconds} seconds</p><h3>Lyrics · {version.provenance.lyrics.source}</h3><pre className="lyrics">{version.lyrics}</pre></section>}
  </>;
}
export function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState('');
  useEffect(() => {api<{items: Project[]}>('/api/v1/projects?limit=100').then(r => setProjects(r.items)).catch(e => setError(e.message));}, []);
  return <>{error && <p role="alert">{error}</p>}<ul>{projects.map(p => <li key={p.id}><Link to={`/projects/${p.id}`}>{p.title}</Link></li>)}</ul><Link to="/create">Create music</Link></>;
}
