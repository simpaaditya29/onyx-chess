import os
import pandas as pd

PUZZLE_DB = "data/blunder_bank.csv"
OUTPUT_HTML = "dashboard.html"

def build_dashboard():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} does not exist.")
        return

    df = pd.read_csv(PUZZLE_DB)
    total = len(df)
    solved = len(df[df["solved"] == True])
    accuracy = (len(df[(df["solved"] == True) & (df["attempts"] == 1)]) / total * 100) if total > 0 else 0
    avg_cpl = df["cp_loss"].abs().mean() if "cp_loss" in df.columns else 0

    # Tag Analytics
    tag_stats = ""
    if "tags" in df.columns:
        all_tags = df['tags'].str.split(', ').explode()
        tag_counts = all_tags.value_counts().head(5)
        for tag, count in tag_counts.items():
            tag_stats += f'<div class="card"><div class="card-title">{tag} Blunders</div><div class="card-value">{count}</div></div>'

    rows_html = ""
    for idx, row in df.iterrows():
        status_badge = '<span class="badge solved">Solved</span>' if row.get("solved") else '<span class="badge pending">Due</span>'
        tags_display = str(row.get("tags", "None"))
        
        # Safely pull the new opening theory columns
        eco = str(row.get("eco", "???"))
        opening = str(row.get("opening_name", "Unknown"))
        
        rows_html += f"""
        <tr>
            <td>#{idx + 1}</td>
            <td>{status_badge}</td>
            <td>Box {int(row.get("box_level", 1))}</td>
            <td>{row.get("turn", "White")}</td>
            <td class="loss">-{abs(int(row.get("cp_loss", 0)))} cp</td>
            <td style="font-size:12px; color:#a8a8b3;">{tags_display}</td>
            <td style="font-size:12px; color:#3498db;">{eco} - {opening}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Onyx Chess Analytics</title>
    <style>
        body {{ background-color: #121214; color: #e1e1e6; font-family: -apple-system, sans-serif; margin: 0; padding: 30px; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 1px solid #29292e; padding-bottom: 20px; }}
        h1 {{ margin: 0; color: #00b37e; font-size: 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 25px 0; }}
        .card {{ background: #202024; border: 1px solid #29292e; border-radius: 8px; padding: 18px; }}
        .card-title {{ font-size: 12px; text-transform: uppercase; color: #a8a8b3; }}
        .card-value {{ font-size: 26px; font-weight: bold; margin-top: 8px; color: #ffffff; }}
        table {{ width: 100%; border-collapse: collapse; background: #202024; border-radius: 8px; margin-top: 20px; text-align: left; }}
        th, td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #29292e; }}
        th {{ background: #19191b; color: #a8a8b3; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
        .badge.solved {{ background: #015f43; color: #00b37e; }}
        .badge.pending {{ background: #7c2d12; color: #f97316; }}
        .loss {{ color: #f75a68; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Onyx Chess Trainer Dashboard</h1>
        <span>Persistent Blunder Bank</span>
    </div>

    <h3 style="margin-top: 30px; color: #a8a8b3;">Core Metrics</h3>
    <div class="grid">
        <div class="card"><div class="card-title">Total Positions</div><div class="card-value">{total}</div></div>
        <div class="card"><div class="card-title">Completed</div><div class="card-value">{solved}</div></div>
        <div class="card"><div class="card-title">1st Try Accuracy</div><div class="card-value">{accuracy:.1f}%</div></div>
        <div class="card"><div class="card-title">Avg Severity</div><div class="card-value">-{avg_cpl:.0f} cp</div></div>
    </div>

    <h3 style="margin-top: 30px; color: #a8a8b3;">Tactical Weakness Profile</h3>
    <div class="grid">
        {tag_stats}
    </div>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Status</th>
                <th>SRS Level</th>
                <th>Turn</th>
                <th>Blunder Cost</th>
                <th>Tactical Tags</th>
                <th>Opening / Theory</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Dashboard generated: {os.path.abspath(OUTPUT_HTML)}")

if __name__ == "__main__":
    build_dashboard()