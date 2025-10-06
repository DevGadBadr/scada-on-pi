from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

def calculate_generator_hours(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    rows: list of dicts with keys: 'timestamp', 'gen', 'state'
      - timestamp: e.g. '2025-10-05 09:00:00+03' or datetime
      - gen: 'gen1', 'gen2', ...
      - state: True/False (or 'true'/'false'/1/0)
    returns: {'Generator 1': 'H:MM', ...}
    """

    def to_bool(v) -> bool:
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("1", "true", "on", "yes")

    def parse_ts(v) -> datetime:
        if isinstance(v, datetime):
            dt = v
        else:
            # allow both "YYYY-MM-DD HH:MM:SS[.fff][+TZ]" or ISO
            s = str(v).replace("T", " ")
            dt = datetime.fromisoformat(s)
        # make sure we have tz-aware to do safe arithmetic
        if dt.tzinfo is None:
            # assume local time as UTC if tz missing (safer for diffs)
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    # group by generator
    gen_events: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        g = r["gen"]
        gen_events.setdefault(g, []).append({
            "t": parse_ts(r["timestamp"]),
            "on": to_bool(r["state"]),
        })

    # sort each generator’s events by time
    for g in gen_events:
        gen_events[g].sort(key=lambda e: e["t"])

    now_aware = datetime.now(timezone.utc)

    results: Dict[str, str] = {}
    for g, events in gen_events.items():
        total = timedelta(0)
        current_on_start: datetime | None = None

        for ev in events:
            t = ev["t"]
            on = ev["on"]

            if on:
                # start ON if not already running
                if current_on_start is None:
                    current_on_start = t
                else:
                    # consecutive ON → keep earliest start (ignore)
                    pass
            else:
                # OFF → close if running
                if current_on_start is not None:
                    if t > current_on_start:
                        total += (t - current_on_start)
                    # reset regardless (defensive)
                    current_on_start = None
                else:
                    # OFF without prior ON → ignore (outside window)
                    pass

        # still ON at the end → count until now
        if current_on_start is not None:
            end_t = now_aware.astimezone(current_on_start.tzinfo)
            if end_t > current_on_start:
                total += (end_t - current_on_start)

        # format H:MM
        secs = int(total.total_seconds())
        h = secs // 3600
        m = (secs % 3600) // 60

        gen_number = g.replace("gen", "").strip() or g
        results[f"Generator {gen_number}"] = f"{h}:{m:02d}"

    return results
