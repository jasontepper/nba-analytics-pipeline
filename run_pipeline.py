import subprocess
import sys
import time
import json
import urllib.request
from pathlib import Path

# Discord webhook URL — set this to your webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1514828710061281291/X5m3wh-0kNpbBxiYUTGRKKGFAag-X217m7HCiarh5UYjkPX8NH2wQD__rcYdEYj6IHrS"

PROJECT_ROOT = Path(__file__).parent
PYTHON = sys.executable  # use the same Python (the venv's) that runs this script

# Pipeline steps in order: (label, script path relative to project root)
STEPS = [
    ("Load reference data", "ingestion/load_reference.py"),
    ("Load game logs",       "ingestion/load_game_logs.py"),
    ("Compute metrics",      "transforms/compute_metrics.py"),
    ("Detect outliers",      "transforms/detect_outliers.py"),
]


def notify_discord(title, description, color):
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
        }]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "nba-pipeline/1.0",
        },
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Discord notification failed: {e}")


def run_step(label, script):
    """Run one script. Returns (success, output)."""
    script_path = PROJECT_ROOT / script
    # Each script imports `db`, which lives in ingestion/, so run from that script's own dir
    cwd = script_path.parent
    result = subprocess.run(
        [PYTHON, script_path.name],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    success = result.returncode == 0
    output = result.stdout if success else result.stderr
    return success, output


def main():
    start = time.time()
    print(f"Pipeline started.")

    for label, script in STEPS:
        print(f"--- {label} ---")
        success, output = run_step(label, script)
        print(output)

        if not success:
            elapsed = round(time.time() - start, 1)
            notify_discord(
                title="❌ NBA pipeline failed",
                description=f"Failed at step: **{label}**\n```\n{output[-500:]}\n```\nElapsed: {elapsed}s",
                color=15158332,  # red
            )
            print(f"Pipeline FAILED at: {label}")
            sys.exit(1)

    elapsed = round(time.time() - start, 1)
    notify_discord(
        title="✅ NBA pipeline succeeded",
        description=f"All {len(STEPS)} steps completed.\nElapsed: {elapsed}s",
        color=3066993,  # green
    )
    print(f"Pipeline succeeded in {elapsed}s")


if __name__ == "__main__":
    main()