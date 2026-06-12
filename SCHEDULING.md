# Scheduling

The pipeline is designed to run daily via cron. During an active NBA season,
a daily run keeps game logs, rolling metrics, and outlier detection current.

## Crontab entry

Run `crontab -e` and add:

```
0 9 * * * /path/to/nba_analytics/.venv/bin/python3 /path/to/nba_analytics/run_pipeline.py >> /path/to/nba_analytics/pipeline.log 2>&1
```

### Schedule breakdown (`0 9 * * *`)
- minute: 0
- hour: 9
- day-of-month: any
- month: any
- day-of-week: any

→ Runs at 9:00 AM daily.

### Notes
- Absolute paths are required — cron does not inherit your shell environment,
  working directory, or virtualenv.
- `2>&1` redirects stderr into the log file so failed runs are captured.
- The orchestrator (`run_pipeline.py`) uses `sys.executable`, so all
  subprocess steps run under the same virtualenv as the scheduler.
- On failure, a Discord webhook fires with the failing step and error tail;
  on success, a green confirmation is sent.

## Production note
For a single linear daily job, cron is sufficient. For task dependencies,
retries, backfills, or observability, an orchestrator like Airflow or
Dagster would be the appropriate upgrade.