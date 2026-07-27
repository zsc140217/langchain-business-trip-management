#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LangSmith Trace Viewer - generate interactive HTML flowchart."""
import argparse, json, os, re, sys, textwrap
from datetime import datetime
from pathlib import Path
from typing import Any
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
def load_langsmith_client():
    try:
        from langsmith import Client as LangSmithClient
    except ImportError:
        print("[ERROR] langsmith SDK not installed"); sys.exit(1)
    api_key = os.getenv("LANGCHAIN_API_KEY")
    api_url = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    if not api_key:
        print("[ERROR] LANGCHAIN_API_KEY not set"); sys.exit(1)
    try:
        client = LangSmithClient(api_url=api_url, api_key=api_key)
        _ = client.list_projects(limit=1)
        return client
    except Exception as e:
        print(f"[ERROR] LangSmith connection failed: {e}"); sys.exit(1)
def compute_duration(start, end) -> float:
    if not start or not end: return 0
    return (end - start).total_seconds() * 1000
def format_duration(ms: float) -> str:
    if ms <= 0: return "N/A"
    if ms < 1000: return f"{ms:.0f}ms"
    elif ms < 60000: return f"{ms / 1000:.1f}s"
    else: return f"{ms / 60000:.1f}m"
def truncate_json(data: Any, max_depth: int = 4, max_len: int = 300) -> Any:
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if max_depth <= 0: result[k] = f"... ({type(v).__name__})"
            else: result[k] = truncate_json(v, max_depth - 1, max_len)
        return result
    elif isinstance(data, list):
        if len(data) > 10:
            shorter = list(data[:10])
            shorter.append(f"... ({len(data)} items)")
            return shorter
        if max_depth <= 0: return [f"... ({len(data)} items)"]
        return [truncate_json(item, max_depth - 1, max_len) for item in data]
    elif isinstance(data, str) and len(data) > max_len: return data[:max_len] + "..."
    return data
def fetch_full_tree(client, run_id, project_name=None):
    try: root = client.read_run(run_id)
    except Exception as e:
        print(f"[ERROR] Cannot read run {run_id}: {e}"); sys.exit(1)
    project_name = project_name or os.getenv("LANGCHAIN_PROJECT", "business-trip-management")
    def _build_tree(run):
        dur = compute_duration(run.start_time, run.end_time)
        node = {
            "id": str(run.id), "name": run.name or "unnamed",
            "run_type": run.run_type or "unknown",
            "inputs": truncate_json(run.inputs) if run.inputs else {},
            "outputs": truncate_json(run.outputs) if run.outputs else {},
            "error": run.error, "duration_ms": dur,
            "tags": list(run.tags) if run.tags else [], "children": [],
        }
        try:
            child_runs = list(client.list_runs(project_name=project_name, parent_run_id=run.id, limit=200))
            child_runs.sort(key=lambda r: r.dotted_order or "")
            for child in child_runs: node["children"].append(_build_tree(child))
        except Exception as e: node["children_error"] = str(e)
        return node
    return _build_tree(root)
def list_recent_runs(client, project_name, limit=10):
    try:
        return list(client.list_runs(project_name=project_name, execution_order=1, limit=limit,
            select=["id","name","run_type","start_time","end_time","error","tags"]))
    except Exception:
        return list(client.list_runs(project_name=project_name, execution_order=1, limit=limit))
def print_runs_table(runs):
    print(f"\n{'#':<4} {'Name':<36} {'Type':<12} {'Duration':<10} {'Status':<8}")
    print("-" * 75)
    for i, run in enumerate(runs, 1):
        name = (run.name or "unnamed")[:35]
        rtype = (run.run_type or "?")[:11]
        dur = format_duration(compute_duration(run.start_time, run.end_time))
        status = "ERROR" if run.error else "OK"
        print(f"{i:<4} {name:<36} {rtype:<12} {dur:<10} {status:<8}")
def escape_html(text):
    if not isinstance(text, str): text = str(text)
    return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")
def badge_class(run_type):
    m = {"chain":"b-chain","llm":"b-llm","tool":"b-tool","retriever":"b-retriever","agent":"b-agent","prompt":"b-prompt"}
    return m.get(run_type,"b-unknown")
def fmt_json(data):
    try: text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    except Exception: text = str(data)
    text = escape_html(text)
    text = re.sub(r'("[^"]*")\s*:', r'<span class="jk">\1</span>:', text)
    text = re.sub(r':\s*("[^"]*")', r': <span class="jv">\1</span>', text)
    text = re.sub(r':\s*(-?\d+\.?\d*)', r': <span class="jn">\1</span>', text)
    text = re.sub(r':\s*(true|false|null)', r': <span class="jb">\1</span>', text)
    return text
def count_nodes(tree):
    n = 1
    for c in tree.get("children", []): n += count_nodes(c)
    return n
def _render(node, is_root=False):
    parts = []
    css = "card"
    if is_root: css += " root"
    if node.get("error"): css += " err"
    bc = badge_class(node.get("run_type",""))
    nm = escape_html(node.get("name","?"))
    rt = escape_html(node.get("run_type","?"))
    dur = f"{node.get('duration_ms',0):.0f}ms" if node.get("duration_ms") else "N/A"
    tags = node.get("tags",[])
    inp = node.get("inputs",{})
    out = node.get("outputs",{})
    kids = node.get("children",[])
    parts.append(f'<div class="{css}" onclick="tog(this)">')
    parts.append(f'  <div class="hdr">')
    parts.append(f'    <span class="bdg {bc}">{rt}</span>')
    parts.append(f'    <span class="nn">{nm}</span>')
    if tags:
        tgs = "".join(f'<span class="tg">{escape_html(t)}</span>' for t in tags[:5])
        parts.append(f'    <span class="tgs">{tgs}</span>')
    if node.get("error"): parts.append(f'    <span class="err-bdg">ERROR</span>')
    parts.append(f'    <span class="dur">{dur}</span>')
    parts.append(f'  </div>')
    parts.append(f'  <div class="bod">')
    if node.get("error"):
        parts.append(f'    <div class="st">Error</div>')
        parts.append(f'    <div class="jbx err-bx">{escape_html(node["error"])}</div>')
    if inp:
        parts.append(f'    <div class="st">Input</div>')
        parts.append(f'    <div class="jbx">{fmt_json(inp)}</div>')
    if out and not node.get("error"):
        parts.append(f'    <div class="st">Output</div>')
        parts.append(f'    <div class="jbx">{fmt_json(out)}</div>')
    elif not out and not node.get("error") and node.get("run_type") != "retriever":
        parts.append(f'    <div class="no">(no output data)</div>')
    parts.append(f'  </div>')
    parts.append(f'</div>')
    if kids:
        parts.append(f'<div class="kids">')
        for c in kids: parts.append(_render(c))
        parts.append(f'</div>')
    return "\n".join(parts)
def render_tree(tree): return _render(tree, is_root=True)
def save_html(html, output_path):
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return path.resolve()
def cmd_list(args):
    client = load_langsmith_client()
    project = args.project or os.getenv("LANGCHAIN_PROJECT","business-trip-management")
    runs = list_recent_runs(client, project, limit=args.limit)
    if not runs: print(f"[INFO] No traces found for: {project}"); return
    print(f"\nRecent traces for project: {project}")
    print_runs_table(runs)
def cmd_view(args):
    client = load_langsmith_client()
    project = args.project or os.getenv("LANGCHAIN_PROJECT","business-trip-management")
    if args.run_id: run_id = args.run_id
    elif args.recent is not None:
        runs = list_recent_runs(client, project, limit=args.recent)
        if not runs or len(runs) < args.recent:
            print(f"[ERROR] Only {len(runs) if runs else 0} traces"); return
        r = runs[args.recent - 1]; run_id = str(r.id)
        print(f"Selected #{args.recent}: {r.name} [{r.run_type}]")
    else:
        runs = list_recent_runs(client, project, limit=20)
        if not runs: print("[ERROR] No traces found"); return
        print("\nRecent traces:"); print_runs_table(runs)
        try:
            idx = int(input("\nEnter # to view: "))
            r = runs[idx - 1]; run_id = str(r.id)
        except (ValueError, IndexError): print("[ERROR] Invalid"); return
    print(f"Fetching run {run_id} ...")
    tree = fetch_full_tree(client, run_id, project)
    total = count_nodes(tree); print(f"Done. {total} nodes.")
    html = generate_html(tree)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in tree["name"][:30])
    out = args.output or f"trace_{safe}_{ts}.html"
    saved = save_html(html, out); print(f"\nSaved: {saved}")
    try:
        import webbrowser; webbrowser.open(str(saved)); print("Opened in browser.")
    except Exception: pass
def generate_html(tree):
    ncount = count_nodes(tree)
    dur = f"{tree.get('duration_ms',0):.0f}ms" if tree.get("duration_ms") else "N/A"
    body = render_tree(tree)
    name = tree.get("name","?")[:60]
    rtype = tree.get("run_type","?")
    rid = tree.get("id","")
    import html as hm; name=hm.escape(name); rtype=hm.escape(rtype); rid=hm.escape(rid)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Trace: {name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#1a1a2e;padding:20px}}
.hd{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:18px 28px;border-radius:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
.hd h1{{font-size:18px;font-weight:600}}
.hd .m{{font-size:13px;opacity:.8}}
.hd .rid{{font-family:monospace;font-size:11px;opacity:.5}}
.ctrl{{display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:16px;background:#fff;padding:10px 18px;border-radius:8px;border:1px solid #e2e4e8}}
.dot{{width:10px;height:10px;border-radius:3px;display:inline-block}}
.flowchart{{position:relative;overflow-x:auto;padding:16px 0}}
.fc-inner{{display:flex;flex-direction:column;align-items:center;min-width:min-content}}
.card{{background:#fff;border-radius:10px;border:1.5px solid #e2e4e8;margin:4px 0;width:100%;max-width:780px;box-shadow:0 1px 3px rgba(0,0,0,.06);cursor:pointer;position:relative;transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 16px rgba(0,0,0,.1)}}
.card.root{{border-color:#2563eb;border-width:2px}}
.card.err{{border-color:#dc2626;background:#fef2f2}}
.hdr{{display:flex;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid #f0f0f0;min-height:40px;flex-wrap:wrap}}
.bdg{{display:inline-flex;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;white-space:nowrap;line-height:1.4}}
.b-chain{{background:#dbeafe;color:#1e40af}}
.b-llm{{background:#ede9fe;color:#5b21b6}}
.b-tool{{background:#fef3c7;color:#92400e}}
.b-retriever{{background:#d1fae5;color:#065f46}}
.b-agent{{background:#fce7f3;color:#9d174d}}
.b-prompt{{background:#e0e7ff;color:#3730a3}}
.b-unknown{{background:#f3f4f6;color:#6b7280}}
.nn{{font-size:13px;font-weight:500;flex:1;min-width:60px}}
.dur{{font-size:11px;color:#999;font-family:monospace;white-space:nowrap}}
.err-bdg{{background:#dc2626;color:#fff;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:600}}
.tgs{{display:flex;gap:3px;flex-wrap:wrap}}
.tg{{background:#f3f4f6;color:#888;padding:0 6px;border-radius:3px;font-size:9px}}
.bod{{display:none;padding:10px 14px}}
.card.expanded .bod{{display:block}}
.st{{font-size:11px;font-weight:600;color:#777;text-transform:uppercase;letter-spacing:.4px;margin:6px 0 3px}}
.st:first-child{{margin-top:0}}
.jbx{{background:#f8fafc;border:1px solid #e2e4e8;border-radius:6px;padding:8px 12px;font-family:Consolas,JetBrains Mono,monospace;font-size:11px;line-height:1.5;overflow:auto;max-height:200px;white-space:pre-wrap}}
.err-bx{{background:#fef2f2;border-color:#fecaca;color:#991b1b}}
.no{{padding:6px 0;color:#aaa;font-size:11px;font-style:italic}}
.jk{{color:#0550ae}}
.jv{{color:#0a3069}}
.jn{{color:#0550ae}}
.jb{{color:#cf222e}}
.kids{{position:relative;display:flex;flex-direction:column;align-items:center;width:100%;padding-top:4px}}
.kids::before{{content:'';position:absolute;top:0;left:50%;width:2px;height:6px;background:#d0d5dd}}
.arr{{width:2px;height:8px;background:#d0d5dd;position:relative}}
.btn{{padding:5px 14px;background:#fff;border:1px solid #d0d5dd;border-radius:6px;font-size:12px;cursor:pointer;color:#444}}
.btn:hover{{background:#f0f0f0}}
.srch{{flex:1;max-width:280px;padding:5px 10px;border:1px solid #d0d5dd;border-radius:6px;font-size:12px}}
</style>
</head>
<body>
<div class="hd">
  <div>
    <h1>{name}</h1>
    <div class="m">type: {rtype} &middot; {dur} &middot; {ncount} nodes</div>
    <div class="rid">{rid}</div>
  </div>
</div>
<div class="ctrl">
  <button class="btn" onclick="ta()">Toggle All</button>
  <input class="srch" id="srch" placeholder="Search..." oninput="f()">
  <label style="font-size:12px;color:#666"><input type="checkbox" id="onlyErr" onchange="f()"> Errors</label>
</div>
<div class="legend">
  <span class="legend-item"><span class="dot" style="background:#dbeafe"></span>Chain</span>
  <span class="legend-item"><span class="dot" style="background:#ede9fe"></span>LLM</span>
  <span class="legend-item"><span class="dot" style="background:#fef3c7"></span>Tool</span>
  <span class="legend-item"><span class="dot" style="background:#d1fae5"></span>Retriever</span>
  <span class="legend-item"><span class="dot" style="background:#fce7f3"></span>Agent</span>
  <span class="legend-item"><span class="dot" style="background:#fef2f2;border:1px solid #fecaca"></span>Error</span>
</div>
<div class="flowchart"><div class="fc-inner">
{body}
</div></div>
<script>
function tog(el){{el.classList.toggle('expanded')}}
function ta(){{var e=document.querySelector('.card.expanded')!==null;document.querySelectorAll('.card').forEach(function(c){{c.classList.toggle('expanded',!e)}})}}
function f(){{var q=document.getElementById('srch').value.toLowerCase();var oe=document.getElementById('onlyErr').checked;document.querySelectorAll('.card').forEach(function(c){{var m=c.querySelector('.nn').textContent.toLowerCase().indexOf(q)>-1;var e=c.classList.contains('err');c.style.display=(oe?!e:true)&&(q===''||m)?'':'none'}})}}
</script>
</body>
</html>"""
def main():
    p = argparse.ArgumentParser(description="LangSmith Trace Visualizer")
    sp = p.add_subparsers(dest="command")
    lp = sp.add_parser("list", help="List recent traces")
    lp.add_argument("--project","-p"); lp.add_argument("--limit","-l",type=int,default=10)
    vp = sp.add_parser("view", help="View trace visualization")
    vp.add_argument("run_id", nargs="?"); vp.add_argument("--project","-p")
    vp.add_argument("--recent","-r",type=int); vp.add_argument("--output","-o")
    args = p.parse_args()
    if not args.command: p.print_help(); print("\nTip: try 'python tools/trace_viewer.py list'"); return
    {"list":cmd_list,"view":cmd_view}[args.command](args)
if __name__ == "__main__":
    main()
