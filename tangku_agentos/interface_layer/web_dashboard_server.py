from __future__ import annotations

from typing import Any

from .web_dashboard import ProductionWebDashboard


class DashboardHTTPApp:
    """Small HTTP-facing adapter for serving the production dashboard shell and JSON routes."""

    def __init__(self, dashboard: ProductionWebDashboard | None = None) -> None:
        self._dashboard = dashboard or ProductionWebDashboard()

    def handle_request(self, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any], bytes]:
        payload = payload or {}
        if path == "/":
            body = self._render_shell_page()
            return 200, {"route": "shell"}, body
        if path.startswith("/api/"):
            route = path.removeprefix("/api/")
            response = self._dashboard.render_route(route, payload)
            return 200, response.output, self._encode_json(response.output)
        body = self._render_shell_page()
        return 200, {"route": "shell"}, body

    def _render_shell_page(self) -> bytes:
        html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tangku AgentOS Dashboard</title>
    <style>
      :root { color-scheme: dark; --bg: #020617; --panel: #111827; --panel-2: #1f2937; --text: #f8fafc; --muted: #94a3b8; --accent: #38bdf8; --accent-2: #a78bfa; --border: rgba(148, 163, 184, 0.18); }
      body.light { color-scheme: light; --bg: #f8fafc; --panel: #ffffff; --panel-2: #e2e8f0; --text: #0f172a; --muted: #475569; --accent: #2563eb; --accent-2: #7c3aed; --border: rgba(71, 85, 105, 0.18); }
      * { box-sizing: border-box; }
      body { font-family: Inter, Arial, sans-serif; margin: 0; background: var(--bg); color: var(--text); min-height: 100vh; }
      .shell { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
      .sidebar { background: rgba(15, 23, 42, 0.95); padding: 1.25rem; border-right: 1px solid var(--border); }
      .brand { display: flex; align-items: center; gap: 0.75rem; font-weight: 700; margin-bottom: 1.5rem; }
      .brand-badge { width: 2rem; height: 2rem; border-radius: 0.6rem; background: linear-gradient(135deg, var(--accent), var(--accent-2)); display: grid; place-items: center; }
      .nav { display: grid; gap: 0.35rem; }
      .nav a { display: block; text-decoration: none; color: var(--text); padding: 0.75rem 0.95rem; border-radius: 0.85rem; background: transparent; transition: background 150ms ease; }
      .nav a:hover, .nav a.active { background: rgba(56, 189, 248, 0.18); }
      .main { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; }
      .topbar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem; padding: 1rem 1.15rem; border: 1px solid var(--border); border-radius: 1rem; background: var(--panel); }
      .hero, .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 1rem; padding: 1.25rem; }
      .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.9rem; }
      .card { background: var(--panel-2); border-radius: 0.85rem; padding: 1rem; }
      .chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.8rem; }
      .chip { padding: 0.4rem 0.65rem; border-radius: 999px; background: rgba(56, 189, 248, 0.16); color: var(--accent); font-size: 0.9rem; }
      .muted { color: var(--muted); }
      .button { border: 1px solid var(--border); background: transparent; color: var(--text); padding: 0.65rem 1rem; border-radius: 0.85rem; cursor: pointer; transition: background 150ms ease; }
      .button:hover { background: rgba(56,189,248,0.12); }
      .panel-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
      pre.json-output { min-height: 280px; margin: 0; padding: 1rem; overflow: auto; border-radius: 0.85rem; background: rgba(15,23,42,0.95); color: var(--text); white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; border: 1px solid var(--border); }
      .route-meta { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }
      .route-meta span { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.8rem; border-radius: 999px; background: rgba(56, 189, 248, 0.12); color: var(--accent); font-size: 0.95rem; }
      @media (max-width: 900px) { .shell { grid-template-columns: 1fr; } .sidebar { border-right: 0; border-bottom: 1px solid var(--border); } }
      @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
    </style>
  </head>
  <body>
    <div class="shell">
      <aside class="sidebar" aria-label="Primary navigation">
        <div class="brand"><span class="brand-badge">TA</span><span>Tangku AgentOS</span></div>
        <nav class="nav" aria-label="Dashboard routes">
          <a href="#" data-route="chat">Chat</a>
          <a href="#" data-route="providers">Providers</a>
          <a href="#" data-route="workflows">Workflows</a>
          <a href="#" data-route="automation">Automation</a>
          <a href="#" data-route="agents">Agents</a>
          <a href="#" data-route="browser">Browser</a>
          <a href="#" data-route="plugins">Plugins</a>
          <a href="#" data-route="memory">Memory</a>
          <a href="#" data-route="system">System</a>
          <a href="#" data-route="settings">Settings</a>
        </nav>
      </aside>
      <main class="main">
        <header class="topbar" role="banner">
          <div>
            <h1>Tangku AgentOS Dashboard</h1>
            <p class="muted">Interactive frontend shell consuming existing backend JSON routes for each dashboard section.</p>
          </div>
          <div class="chip-row" aria-label="dashboard features">
            <button class="button" id="theme-toggle" type="button">Toggle theme</button>
            <span class="chip">Command Palette</span>
            <span class="chip">Keyboard shortcuts</span>
            <span class="chip">Live updates</span>
          </div>
        </header>
        <section class="hero" aria-labelledby="hero-title">
          <h2 id="hero-title">Unified workspace control center</h2>
          <p class="muted">Click any section to load backend data from the existing dashboard service. The shell is designed to deliver production-grade metadata, navigation, and client-driven route rendering without duplicating the backend architecture.</p>
          <div class="chip-row">
            <span class="chip">Responsive</span>
            <span class="chip">Accessible</span>
            <span class="chip">Desktop-ready</span>
            <span class="chip">API-first</span>
          </div>
        </section>
        <section class="panel overview" aria-label="dashboard overview">
          <div class="panel-grid">
            <article class="card"><strong>Current route</strong><div id="current-route" class="muted">system</div></article>
            <article class="card"><strong>Route status</strong><div id="route-status" class="muted">ready</div></article>
            <article class="card"><strong>Latency</strong><div id="route-latency" class="muted">n/a</div></article>
            <article class="card"><strong>Action</strong><div class="muted">Select a section from the sidebar to inspect backend capacity.</div></article>
          </div>
        </section>
        <section class="panel" aria-label="route details">
          <div class="route-meta" aria-label="route metadata">
            <span id="route-name">Route: system</span>
            <span id="route-state">State: ready</span>
            <span id="route-load">Load: n/a</span>
          </div>
          <h3 id="route-title">Route response</h3>
          <pre id="route-output" class="json-output">Loading system route...</pre>
        </section>
      </main>
    </div>
    <script>
      const navLinks = document.querySelectorAll('.nav a');
      const routeOutput = document.getElementById('route-output');
      const routeTitle = document.getElementById('route-title');
      const currentRoute = document.getElementById('current-route');
      const routeStatus = document.getElementById('route-status');
      const routeLatency = document.getElementById('route-latency');
      const routeName = document.getElementById('route-name');
      const routeState = document.getElementById('route-state');
      const routeLoad = document.getElementById('route-load');
      const themeToggle = document.getElementById('theme-toggle');

      function setActiveRoute(route) {
        navLinks.forEach((link) => link.classList.toggle('active', link.dataset.route === route));
      }

      function formatJson(data) {
        return JSON.stringify(data, null, 2);
      }

      async function loadRoute(route) {
        setActiveRoute(route);
        routeTitle.textContent = `Route response: ${route}`;
        currentRoute.textContent = route;
        routeName.textContent = `Route: ${route}`;
        routeStatus.textContent = 'loading';
        routeState.textContent = 'State: loading';
        routeOutput.textContent = 'Fetching data...';
        const start = performance.now();
        try {
          const response = await fetch(`/api/${route}`);
          const elapsed = Math.round(performance.now() - start);
          routeLatency.textContent = `${elapsed}ms`;
          routeLoad.textContent = `Load: ${elapsed}ms`;
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const payload = await response.json();
          routeStatus.textContent = payload.status || 'ok';
          routeState.textContent = `State: ${payload.status || 'ok'}`;
          routeOutput.textContent = formatJson(payload.output ? payload.output : payload);
        } catch (error) {
          routeStatus.textContent = 'error';
          routeState.textContent = 'State: error';
          routeOutput.textContent = String(error);
        }
      }

      navLinks.forEach((link) => {
        link.addEventListener('click', (event) => {
          event.preventDefault();
          const route = link.dataset.route;
          if (route) {
            loadRoute(route);
          }
        });
      });

      themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light');
      });

      document.addEventListener('keydown', function (event) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
          event.preventDefault();
          window.dispatchEvent(new CustomEvent('command-palette-open'));
        }
      });

      window.addEventListener('command-palette-open', function () {
        const palette = document.createElement('div');
        palette.setAttribute('role', 'status');
        palette.textContent = 'Command palette ready';
        palette.style.position = 'fixed';
        palette.style.right = '1rem';
        palette.style.bottom = '1rem';
        palette.style.padding = '0.75rem 1rem';
        palette.style.borderRadius = '999px';
        palette.style.background = 'rgba(56, 189, 248, 0.2)';
        document.body.appendChild(palette);
        window.setTimeout(function () { palette.remove(); }, 1400);
      });

      loadRoute('system');
    </script>
  </body>
</html>"""
        return html.encode("utf-8")

    def _encode_json(self, payload: dict[str, Any]) -> bytes:
        import json

        return json.dumps(payload).encode("utf-8")
