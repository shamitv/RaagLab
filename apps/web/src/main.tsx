import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, NavLink, useLocation } from 'react-router-dom';
import type { components } from './api.generated';
import { destinations, pageFor } from './routes';
import './style.css';

type Readiness = components['schemas']['Readiness'];

function App() {
  const { pathname } = useLocation();
  const page = pageFor(pathname);
  const [health, setHealth] = useState<Readiness | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    const timeout = window.setTimeout(() => { setOffline(true); controller.abort(); }, 6000);
    fetch('/health/ready', { signal: controller.signal, cache: 'no-store' })
      .then(async response => {
        if (response.status !== 200 && response.status !== 503) throw new Error('Health unavailable');
        const data: Readiness = await response.json();
        setHealth(data);
      })
      .catch(() => { if (!disposed) setOffline(true); })
      .finally(() => window.clearTimeout(timeout));
    return () => { disposed = true; window.clearTimeout(timeout); controller.abort(); };
  }, []);

  useEffect(() => { document.title = `${page?.title ?? 'Not found'} · MuseForge AI`; }, [page?.title]);

  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <aside className="rail">
      <NavLink className="brand" to="/create" aria-label="MuseForge AI home"><span aria-hidden="true">▥</span> MuseForge <small>AI</small></NavLink>
      <nav aria-label="Main navigation">
        {destinations.map(item => <NavLink key={item.path} to={item.path} className={({ isActive }) => isActive || (pathname === '/' && item.path === '/create') ? 'active' : ''}>{item.title}</NavLink>)}
      </nav>
      <p className="rail-note">A local space for music and ideas.</p>
    </aside>
    <div className="workspace">
      <header><span>Music workspace</span><span className="badge">Foundation preview</span></header>
      <main id="main" tabIndex={-1}>
        <p className="eyebrow">MUSEFORGE AI</p>
        <h1>{page?.title ?? 'Page not found'}</h1>
        <p className="intro">{page?.description ?? 'This page is not part of the workspace.'}</p>
        <section className="placeholder" aria-labelledby="preview-title">
          <div className="wave" aria-hidden="true">{[20, 44, 30, 64, 46, 80, 54, 34, 60, 26, 42].map((height, i) => <i key={i} style={{ height }} />)}</div>
          <h2 id="preview-title">{page ? 'The workspace is taking shape' : 'Find your way back'}</h2>
          <p>{page?.detail ?? 'Choose a destination from the navigation.'}</p>
          <p className="muted">This build provides navigation and service checks. It does not generate or play audio yet.</p>
        </section>
        <section className="service-status" aria-labelledby="status-title">
          <h2 id="status-title">Service status</h2>
          <p role="status">{offline ? 'Service status unavailable.' : health ? health.status === 'ready' ? 'Storage is ready.' : 'Storage is unavailable. Check the local services.' : 'Checking local services…'}</p>
          {health && <dl>{Object.entries(health.services).map(([name, state]) => <div key={name}><dt>{name}</dt><dd>{state.replaceAll('_', ' ')}</dd></div>)}</dl>}
          <a href="/docs">API documentation</a>
        </section>
      </main>
      <footer>Local workspace · CPU mock foundation</footer>
    </div>
  </>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><BrowserRouter><App /></BrowserRouter></StrictMode>);
