"""Build app-launcher's Pages index.html from `app-registry/*.json`.

The launcher's local Streamlit version manages start/stop/PID for each app.
A browser can't do that without a local agent, so this static viewer is the
honest compromise: it shows the same registry, organised and searchable,
with one-click "Copy launch command" so users can paste into a terminal.

Local rebuild:
    python tools/build_index.py
"""
from __future__ import annotations

import json
import pathlib
from textwrap import dedent

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "app-registry"
OUT = ROOT / "index.html"

# Hand-curated mapping from registry id → external links.
# Updated as repos / deploys come online; entries without a value are omitted
# from the resulting card.
EXTERNAL = {
    "analysis-hub":         {"github": "https://github.com/shihuiarenjinba-png/analysis-hub"},
    "bpp-tool":             {"github": "https://github.com/shihuiarenjinba-png/bpp",
                              "live":  "https://bpp-smoky.vercel.app"},
    "factor-simulator":     {"github": "https://github.com/shihuiarenjinba-png/factor-simulator",
                              "live":  "https://shihuiarenjinba-png.github.io/factor-simulator/"},
    "regime-simulator":     {"github": "https://github.com/shihuiarenjinba-png/simulator",
                              "live":  "https://shihuiarenjinba-png.github.io/simulator/"},
    "portfolio-analysis":   {"github": "https://github.com/shihuiarenjinba-png/app"},
}


def load_apps() -> list[dict]:
    out = []
    for f in sorted(REG.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            print(f"  skip {f.name}: {e}")
            continue
        ext = EXTERNAL.get(data.get("id"), {})
        entry = data.get("entry", "")
        cwd = data.get("cwd", ".")
        port = data.get("port") or 8501
        out.append({
            "id":          data.get("id", f.stem),
            "name":        data.get("name", f.stem),
            "category":    data.get("category", "Lab"),
            "description": data.get("description", ""),
            "type":        data.get("type", "streamlit"),
            "entry":       entry,
            "cwd":         cwd,
            "port":        port,
            "tags":        data.get("tags", []),
            "status":      data.get("status") or ("active" if not data.get("merged_into") else "merged"),
            "merged_into": data.get("merged_into"),
            "favorite":    bool(data.get("favorite", False)),
            "hidden":      bool(data.get("hidden", False)),
            "priority":    data.get("priority", 999),
            "github":      ext.get("github"),
            "live":        ext.get("live"),
            "launch_cmd":  f"cd {cwd} && streamlit run {pathlib.PurePosixPath(entry).name} --server.port {port}",
        })
    out.sort(key=lambda r: (not r["favorite"], r["priority"], r["name"]))
    return out


STATUS_BADGE = {
    "active":       ("active",       "#10b981"),
    "merged":       ("merged",       "#0ea5e9"),
    "experimental": ("experimental", "#f59e0b"),
    "on-hold":      ("on-hold",      "#94a3b8"),
}


def render(apps: list[dict]) -> str:
    cats = sorted({a["category"] for a in apps})
    statuses = sorted({a["status"] for a in apps})
    apps_json = json.dumps(apps, ensure_ascii=False, separators=(",", ":"))

    return dedent(f"""\
    <!doctype html>
    <html lang="ja"><head><meta charset="utf-8">
    <title>app-launcher — ローカルアプリ母艦</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="description" content="11 個のローカル Streamlit アプリを検索・カテゴリ別に表示し、起動コマンドをワンクリックでコピー。">
    <meta property="og:title" content="app-launcher — ローカルアプリ母艦">
    <meta property="og:description" content="Registry viewer. 検索, カテゴリ/状態フィルタ, 起動コマンドコピー, キーボードショートカット対応。">
    <style>
    *{{box-sizing:border-box}}
    html,body{{margin:0;background:#f8fafc;color:#0f172a;
      font-family:system-ui,-apple-system,"Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif;
      -webkit-text-size-adjust:100%}}
    a{{color:#0ea5e9;text-decoration:none}}
    a:hover{{text-decoration:underline}}
    .wrap{{max-width:1080px;margin:0 auto;padding:24px 18px 64px}}
    header{{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}}
    .icon{{font-size:30px;line-height:1}}
    header h1{{margin:0;font-size:24px;font-weight:700;letter-spacing:-.01em;flex:1}}
    .icon-btn{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;width:36px;height:36px;
      cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:16px;color:#334155}}
    .icon-btn:hover{{background:#f1f5f9;color:#0f172a}}
    .sub{{color:#64748b;margin:0 0 18px;font-size:14px;line-height:1.6}}
    .controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:18px}}
    #q{{flex:1 1 220px;min-width:200px;padding:10px 14px;border:1px solid #e2e8f0;border-radius:8px;
      background:#fff;font-size:14px;color:#0f172a;font-family:inherit}}
    #q:focus{{outline:none;border-color:#0ea5e9;box-shadow:0 0 0 3px rgb(14 165 233 /.18)}}
    .chips{{display:flex;flex-wrap:wrap;gap:6px}}
    .chip{{padding:5px 12px;border-radius:999px;border:1px solid #e2e8f0;background:#fff;
      cursor:pointer;font-size:12.5px;color:#334155;font-weight:600;user-select:none;
      font-family:inherit}}
    .chip:hover{{background:#f1f5f9}}
    .chip.on{{background:#0ea5e9;color:#fff;border-color:#0ea5e9}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}}
    .card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px 18px;
      box-shadow:0 1px 3px rgb(0 0 0 /.04);display:flex;flex-direction:column;gap:8px;
      transition:.15s}}
    .card:hover{{transform:translateY(-1px);border-color:#cbd5e1}}
    .card .top{{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}}
    .card .name{{font-weight:700;font-size:15px;color:#0f172a}}
    .card .name .star{{color:#f59e0b;margin-right:4px}}
    .badges-row{{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}}
    .badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;
      background:#f1f5f9;color:#334155}}
    .badge.cat{{background:#e0f2fe;color:#0369a1}}
    .badge.status{{color:#fff}}
    .desc{{font-size:13px;color:#475569;line-height:1.55;margin:4px 0 0}}
    .meta{{display:flex;flex-wrap:wrap;gap:10px;font-size:11.5px;color:#94a3b8;
      font-variant-numeric:tabular-nums}}
    .actions{{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}}
    .btn{{padding:5px 11px;border-radius:6px;font-size:12px;font-weight:600;border:1px solid #e2e8f0;
      background:#fff;color:#334155;cursor:pointer;text-decoration:none!important;
      font-family:inherit;display:inline-flex;align-items:center;gap:4px}}
    .btn:hover{{background:#f1f5f9;color:#0f172a}}
    .btn.primary{{background:#0ea5e9;color:#fff;border-color:#0ea5e9}}
    .btn.primary:hover{{background:#0284c7;color:#fff}}
    .btn.ok{{background:#10b981;color:#fff;border-color:#10b981}}
    .stats{{font-size:12.5px;color:#64748b;margin-bottom:8px}}
    .empty{{padding:40px;text-align:center;color:#94a3b8;font-size:14px}}
    .toast{{position:fixed;bottom:24px;left:50%;transform:translate(-50%,80px);
      background:#0f172a;color:#f8fafc;padding:10px 18px;border-radius:999px;
      font-size:13px;font-weight:600;opacity:0;transition:.25s;pointer-events:none;z-index:9999;
      box-shadow:0 8px 24px rgb(0 0 0 /.25)}}
    .toast.show{{transform:translate(-50%,0);opacity:1}}
    @media(prefers-color-scheme:dark){{
      body{{background:#0a0f1a;color:#f1f5f9}}
      .sub{{color:#94a3b8}}
      .icon-btn,#q,.chip,.card,.btn{{background:#0f172a;border-color:#1f2a3a;color:#cbd5e1}}
      .icon-btn:hover,.chip:hover,.btn:hover{{background:#1e293b;color:#f8fafc}}
      .badge{{background:#1e293b;color:#cbd5e1}}
      .badge.cat{{background:#0c4a6e;color:#7dd3fc}}
      .card:hover{{border-color:#334155}}
      .desc{{color:#cbd5e1}}
      .stats{{color:#94a3b8}}
    }}
    @media(max-width:480px){{
      .wrap{{padding:16px 12px 48px}}
      header h1{{font-size:20px}}
      .grid{{grid-template-columns:1fr}}
    }}
    </style></head><body><div class="wrap">

    <header>
      <span class="icon">🚀</span>
      <h1>app-launcher</h1>
      <button class="icon-btn" id="theme" title="テーマ (t)">🌗</button>
    </header>
    <p class="sub">ローカル Streamlit アプリ {len(apps)} 件を <code>app-registry/*.json</code> から自動集約。
    起動コマンドはコピーしてターミナルに貼り付け、停止は <code>Ctrl+C</code>。
    分析結果が Web 公開済みのアプリは「Open Live」で直接アクセスできます。</p>

    <div class="controls">
      <input id="q" type="search" placeholder="名前・説明・タグで検索 ( / でフォーカス)" autocomplete="off">
    </div>
    <div class="controls">
      <div class="chips" id="cat-chips">
        <button class="chip on" data-cat="">All categories</button>
        {''.join(f'<button class="chip" data-cat="{c}">{c}</button>' for c in cats)}
      </div>
    </div>
    <div class="controls">
      <div class="chips" id="status-chips">
        <button class="chip on" data-status="">All statuses</button>
        {''.join(f'<button class="chip" data-status="{s}">{s}</button>' for s in statuses)}
      </div>
    </div>
    <div class="stats" id="stats"></div>
    <div class="grid" id="grid"></div>
    <div class="empty" id="empty" style="display:none">該当するアプリがありません</div>

    <div class="toast" id="toast"></div>

    <script>
    const APPS = {apps_json};
    const STATUS_COLORS = {{"active":"#10b981","merged":"#0ea5e9","experimental":"#f59e0b","on-hold":"#94a3b8"}};

    const q       = document.getElementById("q");
    const grid    = document.getElementById("grid");
    const empty   = document.getElementById("empty");
    const stats   = document.getElementById("stats");
    const toast   = document.getElementById("toast");
    let activeCat = "", activeStatus = "";

    function showToast(msg) {{
      toast.textContent = msg; toast.classList.add("show");
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => toast.classList.remove("show"), 1600);
    }}

    function copy(text, label) {{
      navigator.clipboard.writeText(text).then(
        () => showToast((label||"コピー") + "しました"),
        () => showToast("コピー失敗")
      );
    }}

    function render() {{
      const term = q.value.trim().toLowerCase();
      let shown = 0;
      grid.innerHTML = "";
      for (const a of APPS) {{
        if (activeCat && a.category !== activeCat) continue;
        if (activeStatus && a.status !== activeStatus) continue;
        if (term && !(
          a.name.toLowerCase().includes(term) ||
          a.description.toLowerCase().includes(term) ||
          (a.tags || []).some(t => t.toLowerCase().includes(term))
        )) continue;
        shown++;
        const card = document.createElement("div");
        card.className = "card";
        const statusColor = STATUS_COLORS[a.status] || "#64748b";
        const starStr = a.favorite ? '<span class="star">★</span>' : "";
        const tags = (a.tags||[]).slice(0,4).map(t=>`<span class="badge">${{t}}</span>`).join("");
        const mergedInto = a.merged_into ? `<span class="badge">→ ${{a.merged_into}}</span>` : "";
        const actions = [];
        if (a.live)   actions.push(`<a class="btn primary" href="${{a.live}}" target="_blank" rel="noopener">▶ Open Live</a>`);
        if (a.github) actions.push(`<a class="btn" href="${{a.github}}" target="_blank" rel="noopener">📦 GitHub</a>`);
        actions.push(`<button class="btn" data-copy="${{encodeURIComponent(a.launch_cmd)}}">⎘ 起動コマンド</button>`);
        card.innerHTML = `
          <div class="top">
            <div>
              <div class="name">${{starStr}}${{a.name}}</div>
              <div class="badges-row">
                <span class="badge cat">${{a.category}}</span>
                <span class="badge status" style="background:${{statusColor}}">${{a.status}}</span>
                ${{mergedInto}}
                ${{tags}}
              </div>
            </div>
          </div>
          <p class="desc">${{a.description || "（説明未設定）"}}</p>
          <div class="meta">
            <span>port: ${{a.port}}</span>
            <span>entry: ${{a.entry}}</span>
          </div>
          <div class="actions">${{actions.join("")}}</div>
        `;
        grid.appendChild(card);
      }}
      empty.style.display = shown ? "none" : "block";
      stats.textContent = `${{shown}} / ${{APPS.length}} apps`;
      grid.querySelectorAll("[data-copy]").forEach(b => {{
        b.addEventListener("click", () => {{
          const cmd = decodeURIComponent(b.getAttribute("data-copy"));
          copy(cmd, "起動コマンドを");
          b.classList.add("ok"); b.textContent = "Copied!";
          setTimeout(()=>{{ b.classList.remove("ok"); b.innerHTML="⎘ 起動コマンド"; }}, 1200);
        }});
      }});
    }}

    q.addEventListener("input", render);
    document.querySelectorAll("#cat-chips .chip").forEach(c=>c.addEventListener("click", () => {{
      document.querySelectorAll("#cat-chips .chip").forEach(x=>x.classList.remove("on"));
      c.classList.add("on"); activeCat = c.dataset.cat; render();
    }}));
    document.querySelectorAll("#status-chips .chip").forEach(c=>c.addEventListener("click", () => {{
      document.querySelectorAll("#status-chips .chip").forEach(x=>x.classList.remove("on"));
      c.classList.add("on"); activeStatus = c.dataset.status; render();
    }}));

    // Theme
    const html = document.documentElement;
    function applyTheme(t) {{
      if (t === "light") html.style.colorScheme = "light";
      else if (t === "dark") html.style.colorScheme = "dark";
      else html.style.colorScheme = "";
    }}
    applyTheme(localStorage.getItem("theme") || "auto");
    document.getElementById("theme").addEventListener("click", () => {{
      const cur = localStorage.getItem("theme") || "auto";
      const next = cur === "auto" ? "dark" : cur === "dark" ? "light" : "auto";
      localStorage.setItem("theme", next); applyTheme(next);
      showToast("テーマ: " + (next === "auto" ? "自動" : next));
    }});

    // Shortcuts
    document.addEventListener("keydown", e => {{
      if (/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {{
        if (e.key === "Escape") {{ document.activeElement.blur(); }}
        return;
      }}
      if (e.metaKey || e.ctrlKey) return;
      if (e.key === "/") {{ e.preventDefault(); q.focus(); }}
      else if (e.key === "t") {{ e.preventDefault(); document.getElementById("theme").click(); }}
    }});

    render();
    </script>
    </body></html>
    """)


def main():
    apps = load_apps()
    OUT.write_text(render(apps), encoding="utf-8")
    print(f"WROTE {OUT} ({OUT.stat().st_size:,} bytes) for {len(apps)} apps")


if __name__ == "__main__":
    main()
