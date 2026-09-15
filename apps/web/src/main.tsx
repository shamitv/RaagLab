import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  NavLink,
  useLocation,
  Routes,
  Route,
} from "react-router-dom";
import type { components } from "./api.generated";
import { destinations, pageFor } from "./routes";
import "./style.css";
import { Composer } from "./Composer";
import { Library, Projects, Settings, Templates } from "./WorkspacePages";
import { SongPage } from "./SongPage";

type Readiness = components["schemas"]["Readiness"];

function App() {
  const { pathname } = useLocation();
  const page = pageFor(pathname);
  const [health, setHealth] = useState<Readiness | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    const timeout = window.setTimeout(() => {
      setOffline(true);
      controller.abort();
    }, 6000);
    fetch("/health/ready", { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (response.status !== 200 && response.status !== 503)
          throw new Error("Health unavailable");
        const data: Readiness = await response.json();
        setHealth(data);
      })
      .catch(() => {
        if (!disposed) setOffline(true);
      })
      .finally(() => window.clearTimeout(timeout));
    return () => {
      disposed = true;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, []);

  useEffect(() => {
    document.title = `${page?.title ?? "Not found"} · MuseForge AI`;
  }, [page?.title]);

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="rail">
        <NavLink className="brand" to="/create" aria-label="MuseForge AI home">
          <span aria-hidden="true">
            <svg
              viewBox="0 0 28 28"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M3 12v4m5-9v14m6-18v22m6-17v12m5-8v4" />
            </svg>
          </span>{" "}
          MuseForge <small>AI</small>
        </NavLink>
        <nav aria-label="Main navigation">
          {destinations.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  isActive || (pathname === "/" && item.path === "/create")
                    ? "active"
                    : ""
                }
              >
                <svg
                  className="nav-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path
                    d={
                      item.path === "/create"
                        ? "M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"
                        : item.path === "/songs"
                            ? "M4 5h16v14H4zM8 9h8M8 13h5"
                            : item.path === "/templates"
                              ? "M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"
                              : "M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4m0-12.8L17 7M7 17l-1.4 1.4M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
                    }
                  />
                </svg>
                {item.title}
              </NavLink>
            ))}
        </nav>
        <p className="rail-note">A local space for music and ideas.</p>
      </aside>
      <div className="workspace">
        <header>
          <span>Music workspace</span>
          <span className="badge">Playable audio</span>
        </header>
        <main id="main" tabIndex={-1}>
          <p className="eyebrow">MUSEFORGE AI</p>
          <h1>{page?.title ?? "Page not found"}</h1>
          <p className="intro">
            {page?.description ?? "This page is not part of the workspace."}
          </p>
          <Routes>
            <Route path="/" element={<Composer />} />
            <Route path="/create" element={<Composer />} />
            <Route path="/projects/:id" element={<Composer />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/library" element={<Library />} />
            <Route path="/songs" element={<Library />} />
            <Route path="/songs/:id" element={<SongPage />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/templates" element={<Templates />} />
            <Route
              path="*"
              element={
                <p>This page is not part of this workspace.</p>
              }
            />
          </Routes>
          <section className="service-status" aria-labelledby="status-title">
            <h2 id="status-title">Service status</h2>
            <p role="status">
              {offline
                ? "Service status unavailable."
                : health
                  ? health.status === "ready"
                    ? "Storage is ready."
                    : "Storage is unavailable. Check the local services."
                  : "Checking local services…"}
            </p>
            {health && (
              <dl>
                {Object.entries(health.services).map(([name, state]) => (
                  <div key={name}>
                    <dt>{name}</dt>
                    <dd>{state.replaceAll("_", " ")}</dd>
                  </div>
                ))}
              </dl>
            )}
            <a href="/docs">API documentation</a>
          </section>
        </main>
        <footer>Local workspace · CPU mock generation</footer>
      </div>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
