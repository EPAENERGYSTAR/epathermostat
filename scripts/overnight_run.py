"""
overnight_run.py
================
Runs the full overnight pipeline in order:

  Step 1/4  populate eeweather cache for all 4,804 stations (--all-stations)
  Step 2/4  rebuild zipcode_usaf_station.json with optimal station matching
  Step 3/4  export updated cache.sql.gz
  Step 4/4  run full ZCTA pipeline validation (full_zcta_run.py)

Resumable: each step checks whether it has already completed via a state file
(overnight_run.state in the repo root). Re-run the script at any time to pick
up from the last completed step.

Progress is written to stdout as machine-readable PROGRESS lines:

  PROGRESS step=1/4 done=1234/2071 eta=3h22m  label=caching stations
  PROGRESS step=2/4 done=1/1 eta=0h00m  label=rebuilding JSON
  PROGRESS step=3/4 done=1/1 eta=0h00m  label=exporting cache
  PROGRESS step=4/4 done=12/68 eta=1h45m  label=running pipeline

Usage:
    nohup .venv310/bin/python scripts/overnight_run.py \\
        2>/tmp/overnight_err.log | tee /tmp/overnight_run.log &

To monitor:
    grep PROGRESS /tmp/overnight_run.log | tail -1
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_STATE_FILE = _ROOT / 'overnight_run.state'
_PYTHON = str(Path(sys.executable))

STEPS = [
    'cache_all_stations',
    'rebuild_json',
    'export_cache',
    'run_pipeline',
]


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_state():
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except Exception:
            pass
    return {'completed': []}


def _mark_done(step):
    state = _load_state()
    if step not in state['completed']:
        state['completed'].append(step)
    _STATE_FILE.write_text(json.dumps(state, indent=2))


def _is_done(step):
    return step in _load_state()['completed']


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------

def _fmt_eta(seconds):
    if seconds is None or seconds < 0:
        return '--:--'
    h, rem = divmod(int(seconds), 3600)
    return '{:d}h{:02d}m'.format(h, rem // 60)


def _progress(step_num, total_steps, done, total, eta_sec, label):
    eta = _fmt_eta(eta_sec)
    line = 'PROGRESS step={}/{} done={}/{} eta={}  label={}'.format(
        step_num, total_steps, done, total, eta, label)
    print(line, flush=True)


# ---------------------------------------------------------------------------
# Step runners
# ---------------------------------------------------------------------------

def run_cache_all_stations(step_num, total_steps):
    """Step 1: populate GHCN-H cache for all 4,804 eeweather stations."""
    label = 'caching stations'
    cmd = [_PYTHON, 'scripts/populate_ghcnh_cache.py',
           '--all-stations', '--min-quality', 'high,medium',
           '--workers', '8', '--no-export']

    total_work = None
    done = 0
    t_start = time.monotonic()
    last_progress = 0

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, cwd=str(_ROOT))
    for line in proc.stdout:
        line = line.rstrip()
        # Catch total work from startup line
        m = re.search(r'(\d+) station-years to fetch', line)
        if m:
            total_work = int(m.group(1))
        # Catch incremental progress lines
        m = re.search(r'Progress: (\d+)/(\d+) fetched', line)
        if m:
            done = int(m.group(1))
            if total_work is None:
                total_work = int(m.group(2))
        # Emit a PROGRESS line at most once per 30 s
        now = time.monotonic()
        if total_work and now - last_progress >= 30:
            elapsed = now - t_start
            rate = done / elapsed if elapsed > 0 and done > 0 else None
            eta = ((total_work - done) / rate) if rate else None
            _progress(step_num, total_steps, done, total_work or '?', eta, label)
            last_progress = now

    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError('Step {} failed (exit {})'.format(step_num, proc.returncode))
    _progress(step_num, total_steps, total_work or done, total_work or done, 0, label)
    _mark_done('cache_all_stations')


def run_rebuild_json(step_num, total_steps):
    """Step 2: rebuild zipcode_usaf_station.json."""
    label = 'rebuilding JSON'
    _progress(step_num, total_steps, 0, 1, None, label)
    cmd = [_PYTHON, 'scripts/build_zipcode_lookup.py']
    result = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError('Step {} failed'.format(step_num))
    print(result.stdout.strip(), flush=True)
    _progress(step_num, total_steps, 1, 1, 0, label)
    _mark_done('rebuild_json')


def run_export_cache(step_num, total_steps):
    """Step 3: re-run populate to export updated cache.sql.gz."""
    label = 'exporting cache'
    _progress(step_num, total_steps, 0, 1, None, label)
    cmd = [_PYTHON, 'scripts/populate_ghcnh_cache.py', '--workers', '8']
    result = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError('Step {} failed'.format(step_num))
    print(result.stdout.strip(), flush=True)
    _progress(step_num, total_steps, 1, 1, 0, label)
    _mark_done('export_cache')


def run_pipeline(step_num, total_steps):
    """Step 4: run full_zcta_run.py (resumable)."""
    label = 'running pipeline'
    cmd = [_PYTHON, 'scripts/full_zcta_run.py']

    total_batches = None
    done_batches = 0
    t_start = time.monotonic()
    batch_times = []
    last_batch_t = t_start
    last_progress = 0

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, cwd=str(_ROOT))
    for line in proc.stdout:
        line = line.rstrip()
        m = re.search(r'BATCH_PROGRESS (\d+)/(\d+)', line)
        if m:
            done_batches = int(m.group(1))
            total_batches = int(m.group(2))
            now = time.monotonic()
            batch_times.append(now - last_batch_t)
            last_batch_t = now
            avg = sum(batch_times) / len(batch_times)
            eta = avg * (total_batches - done_batches)
            _progress(step_num, total_steps, done_batches, total_batches, eta, label)
            last_progress = now
        elif 'DONE results=' in line:
            print(line, flush=True)
        elif 'batches' in line.lower() or 'remaining' in line.lower():
            # Extract total batches from startup line if we can
            m2 = re.search(r'(\d+) batches', line)
            if m2 and total_batches is None:
                total_batches = int(m2.group(1))
                _progress(step_num, total_steps, 0, total_batches, None, label)

    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError('Step {} failed (exit {})'.format(step_num, proc.returncode))
    _mark_done('run_pipeline')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

STEP_FUNCS = {
    'cache_all_stations': run_cache_all_stations,
    'rebuild_json':       run_rebuild_json,
    'export_cache':       run_export_cache,
    'run_pipeline':       run_pipeline,
}

def main():
    total = len(STEPS)
    print('overnight_run.py starting — state file: {}'.format(_STATE_FILE), flush=True)
    print('Monitor progress: grep PROGRESS /tmp/overnight_run.log | tail -1', flush=True)
    print('', flush=True)

    for i, step in enumerate(STEPS, 1):
        if _is_done(step):
            print('Step {}/{} ({}) already complete — skipping.'.format(i, total, step),
                  flush=True)
            continue
        print('=== Step {}/{}: {} ==='.format(i, total, step), flush=True)
        t0 = time.monotonic()
        STEP_FUNCS[step](i, total)
        elapsed = time.monotonic() - t0
        print('=== Step {}/{} done in {} ===\n'.format(
            i, total, _fmt_eta(elapsed)), flush=True)

    print('ALL STEPS COMPLETE', flush=True)


if __name__ == '__main__':
    main()
