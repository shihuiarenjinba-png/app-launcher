from __future__ import annotations

from pathlib import Path

import streamlit as st

from launcher_core.diagnostics import (
    build_log_prompt,
    find_broken_registry_files,
    find_missing_entries,
    find_port_conflicts,
    tail_text,
)
from launcher_core.link_manager import describe_path, open_path
from launcher_core.ollama_client import generate, load_ollama_config
from launcher_core.process_manager import (
    load_pids,
    reconcile_pids,
    start_app,
    stop_app,
)
from launcher_core.registry import AppDefinition, load_apps


BASE_DIR = Path(__file__).resolve().parent
PID_PATH = BASE_DIR / ".launcher_pids.json"
LOG_DIR = BASE_DIR / "logs"


def get_log_path(app: AppDefinition, running: dict) -> Path:
    info = running.get(app.id, {})
    if info.get("log"):
        return Path(info["log"])
    return LOG_DIR / f"{app.id}.log"


def render_link_buttons(app: AppDefinition) -> None:
    links = app.links or []
    for index, link in enumerate(links):
        label = f"{link.label}を開く"
        if st.button(label, key=f"open-{app.id}-{index}", use_container_width=True):
            ok, msg = open_path(link.path)
            (st.success if ok else st.error)(msg)


def render_app_card(app: AppDefinition, host: str, running: dict, ollama_config: dict) -> None:
    is_running = app.id in running
    status = "起動中" if is_running else "停止中"
    app_url = f"http://{host}:{app.port}"
    log_path = get_log_path(app, running)

    with st.container(border=True):
        top_cols = st.columns([5, 1.2, 1.2, 1.4])
        with top_cols[0]:
            badge = "保護対象" if app.protected else app.category
            st.markdown(f"### {app.name}")
            st.caption(f"{badge} / `{app.entry.relative_to(BASE_DIR) if app.entry.is_relative_to(BASE_DIR) else app.entry}` / port={app.port}")
            if app.description:
                st.write(app.description)
            if app.tags:
                st.caption("タグ: " + ", ".join(app.tags))
        with top_cols[1]:
            st.metric("状態", status)
        with top_cols[2]:
            if st.button("起動", key=f"start-{app.id}", disabled=is_running, use_container_width=True):
                ok, msg = start_app(app, PID_PATH, LOG_DIR, host)
                (st.success if ok else st.error)(msg)
                st.rerun()
        with top_cols[3]:
            if st.button("停止", key=f"stop-{app.id}", disabled=not is_running, use_container_width=True):
                ok, msg = stop_app(app, PID_PATH)
                (st.info if ok else st.error)(msg)
                st.rerun()

        action_cols = st.columns([1.3, 1.3, 1.3, 2.2])
        with action_cols[0]:
            st.link_button("ブラウザで開く", app_url, disabled=not is_running, use_container_width=True)
        with action_cols[1]:
            if st.button("フォルダを開く", key=f"open-cwd-{app.id}", use_container_width=True):
                ok, msg = open_path(app.cwd)
                (st.success if ok else st.error)(msg)
        with action_cols[2]:
            if st.button("設定を開く", key=f"open-source-{app.id}", disabled=app.source is None, use_container_width=True):
                ok, msg = open_path(app.source or BASE_DIR)
                (st.success if ok else st.error)(msg)
        with action_cols[3]:
            st.caption(f"Python: `{app.python or 'ランチャー実行環境'}`")

        with st.expander("詳細・リンク・ログ"):
            detail_cols = st.columns([1, 1])
            with detail_cols[0]:
                st.write("**関連リンク**")
                render_link_buttons(app)
                st.write("**パス状態**")
                st.code(
                    "\n".join(
                        [
                            f"entry: {describe_path(app.entry)} - {app.entry}",
                            f"cwd: {describe_path(app.cwd)} - {app.cwd}",
                            f"source: {app.source or 'config fallback'}",
                        ]
                    ),
                    language="text",
                )
            with detail_cols[1]:
                st.write("**ログ**")
                if log_path.exists():
                    st.caption(str(log_path))
                    st.code(tail_text(log_path, 40), language="text")
                else:
                    st.info("まだログはありません。")

                if app.ai.get("logDiagnosis") and st.button("Ollamaでログ診断", key=f"ai-log-{app.id}", disabled=not log_path.exists()):
                    log_text = tail_text(log_path, 120)
                    ok, result = generate(ollama_config, build_log_prompt(app.name, log_text), model_key="default_model")
                    (st.success if ok else st.error)(result)


def main() -> None:
    config, apps = load_apps(BASE_DIR)
    host = str(config.get("host", "127.0.0.1"))
    running = reconcile_pids(PID_PATH, load_pids(PID_PATH))
    ollama_config = load_ollama_config(BASE_DIR)

    st.set_page_config(page_title="ローカルアプリ母艦", page_icon="🚀", layout="wide")
    st.title("ローカルアプリ母艦")
    st.caption(f"root: `{BASE_DIR}` / apps: {len(apps)} / running: {len(running)} / Ollama: `{ollama_config['default_model']}`")

    broken_registry = find_broken_registry_files(BASE_DIR / "app-registry")
    missing_entries = find_missing_entries(apps)
    port_conflicts = find_port_conflicts(apps)

    if broken_registry or missing_entries or port_conflicts:
        with st.expander(
            f"⚠️ 自己診断: 問題 {len(broken_registry) + len(missing_entries) + len(port_conflicts)} 件",
            expanded=True,
        ):
            if broken_registry:
                st.error("**壊れた registry ファイル**（読み込みをスキップしました）")
                for path, msg in broken_registry:
                    st.write(f"- `{path.name}` — {msg}")
            if missing_entries:
                st.error("**entry ファイルが見つかりません**（起動できません）")
                for name, entry in missing_entries:
                    st.write(f"- `{name}` → `{entry}`")
            if port_conflicts:
                st.warning("**ポート衝突**（同時起動すると後発が失敗します）")
                for port, names in port_conflicts:
                    st.write(f"- ポート **{port}**: " + ", ".join(f"`{n}`" for n in names))
    else:
        st.success("✅ 自己診断: 問題なし（registry / entry / port すべてクリーン）")

    controls = st.columns([2.5, 1.5, 1.2, 1.2])
    with controls[0]:
        query = st.text_input("検索", placeholder="アプリ名、カテゴリ、タグで検索")
    with controls[1]:
        categories = ["すべて"] + sorted({app.category for app in apps})
        category = st.selectbox("カテゴリ", categories)
    with controls[2]:
        running_only = st.toggle("起動中のみ", value=False)
    with controls[3]:
        protected_only = st.toggle("保護対象のみ", value=False)

    filtered = apps
    if category != "すべて":
        filtered = [app for app in filtered if app.category == category]
    if running_only:
        filtered = [app for app in filtered if app.id in running]
    if protected_only:
        filtered = [app for app in filtered if app.protected]
    if query.strip():
        needle = query.strip().lower()
        filtered = [
            app
            for app in filtered
            if needle in app.name.lower()
            or needle in app.category.lower()
            or any(needle in tag.lower() for tag in app.tags)
        ]

    st.markdown("---")
    if not filtered:
        st.warning("条件に合うアプリがありません。")
    for app in filtered:
        render_app_card(app, host, running, ollama_config)

    st.markdown("---")
    with st.expander("ランチャー設定"):
        st.write("アプリを増やす場合は `app-registry/*.json` を追加します。`launcher.py` 本体を直接編集する必要はありません。")
        st.code(str(BASE_DIR / "app-registry"), language="text")
        st.write("Ollama設定")
        st.json(ollama_config)


if __name__ == "__main__":
    main()
