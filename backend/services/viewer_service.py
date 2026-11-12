import html
from pathlib import Path


def render_html(file_path: Path, display_name: str) -> str:
    ext = file_path.suffix.lower()
    raw_bytes = file_path.read_bytes()

    if ext in ('.txt', '.md', '.markdown', '.sql', '.html', '.htm', '.json', '.yaml', '.yml', '.csv'):
        content = raw_bytes.decode('utf-8', errors='replace')
        escaped = html.escape(content)
        body = f"""
        <div class="header">
            <span class="fname">📄 {html.escape(display_name)}</span>
            <span class="fmeta">{len(raw_bytes):,} bytes · {ext.upper().lstrip('.')}</span>
        </div>
        <pre><code>{escaped}</code></pre>
        """
    else:
        escaped_name = html.escape(display_name)
        body = f"""
        <div class="binary">
            <div class="icon">📦</div>
            <h2>{escaped_name}</h2>
            <p>Binary or structured document ({len(raw_bytes):,} bytes). Preview extracted text in the main workspace.</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html.escape(display_name)} — GRID Viewer</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 24px;
            background: #0b1002;
            color: #f7f7fb;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            line-height: 1.6;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 14px;
            margin-bottom: 16px;
            border-bottom: 1px solid rgba(183, 255, 0, 0.2);
        }}
        .fname {{
            font-weight: 700;
            font-size: 14px;
            color: #b7ff00;
        }}
        .fmeta {{
            font-size: 11px;
            color: #8c9b78;
        }}
        pre {{
            background: #162204;
            border: 1px solid rgba(183, 255, 0, 0.15);
            border-radius: 10px;
            padding: 16px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
            color: #e2ecd1;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .binary {{
            text-align: center;
            padding: 60px 20px;
        }}
        .binary .icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        .binary h2 {{
            color: #b7ff00;
            margin: 0 0 8px;
        }}
        .binary p {{
            color: #8c9b78;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    {body}
</body>
</html>
"""

