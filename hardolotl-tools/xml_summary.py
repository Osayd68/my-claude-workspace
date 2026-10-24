"""
Summarize a Premiere "Final Cut Pro XML" export into small, readable reports.

Works with offline media: only the edit decisions are read (clip names, source in/out,
timeline position, speed, effects), nested sequences are flattened onto the main timeline.

Output folder:
  report.md            overview: compression ratio, per-track pacing, speeds, effects, most used assets
  timeline_MM.md       every clip on the flattened timeline, one file per minute of the edit

Usage (Windows):
  python xml_summary.py "C:\\Users\\Ligoo\\Documents\\2024-08-08 11-04-08.xml"
  python xml_summary.py edit.xml --sequence "2024-08-08 11-04-08"
"""

import argparse
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote


def fmt(seconds, decimals=1):
    seconds = max(seconds, 0)
    whole = int(seconds)
    frac = f"{seconds - whole:.{decimals}f}"[1:] if decimals else ""
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}{frac}"


class Edit:
    def __init__(self, root):
        # FCP XML defines an element (file, sequence) once and later refers to it by id with an empty tag
        self.defs = {}
        for el in root.iter():
            if el.get("id") and len(el) > 0 and el.get("id") not in self.defs:
                self.defs[el.get("id")] = el
        self.clips = []

    def resolve(self, el):
        if el is not None and len(el) == 0 and el.get("id"):
            return self.defs.get(el.get("id"), el)
        return el

    @staticmethod
    def fps(el, default=25.0):
        rate = el.find("rate") if el is not None else None
        if rate is None or rate.findtext("timebase") is None:
            return default
        timebase = float(rate.findtext("timebase"))
        return timebase * 1000 / 1001 if rate.findtext("ntsc") == "TRUE" else timebase

    @staticmethod
    def speed(clip):
        for effect in clip.iter("effect"):
            if effect.findtext("effectid") == "timeremap":
                for param in effect.iter("parameter"):
                    if param.findtext("parameterid") == "speed" and param.findtext("value"):
                        return float(param.findtext("value")) / 100
        return 1.0

    @staticmethod
    def effects(clip):
        names = []
        for effect in clip.iter("effect"):
            name = effect.findtext("name")
            if name and effect.findtext("effectid") not in ("timeremap",) and name not in names:
                names.append(name)
        return names

    @staticmethod
    def clip_bounds(children, idx):
        """start/end are -1 next to a transition; take them from the neighbouring transitionitem."""
        clip = children[idx]
        start, end = int(clip.findtext("start")), int(clip.findtext("end"))
        if start == -1 and idx > 0 and children[idx - 1].tag == "transitionitem":
            start = int(children[idx - 1].findtext("start"))
        if end == -1 and idx + 1 < len(children) and children[idx + 1].tag == "transitionitem":
            end = int(children[idx + 1].findtext("end"))
        return start, end

    def walk(self, seq, kind, offset, window, track_label, depth, nest_names):
        seq_fps = self.fps(seq)
        media = seq.find(f"media/{kind}")
        if media is None:
            return
        for t_idx, track in enumerate(media.findall("track"), 1):
            label = track_label or f"{'V' if kind == 'video' else 'A'}{t_idx}"
            children = list(track)
            for idx, clip in enumerate(children):
                if clip.tag != "clipitem" or clip.findtext("enabled") == "FALSE":
                    continue
                start, end = self.clip_bounds(children, idx)
                if start < 0 or end <= start:
                    continue
                s, e = start / seq_fps, end / seq_fps
                if window:
                    s, e = max(s, window[0]), min(e, window[1])
                    if e <= s:
                        continue
                    abs_start = offset + s - window[0]
                else:
                    abs_start = offset + s
                dur = e - s
                clip_fps = self.fps(clip, seq_fps)
                src_in = int(clip.findtext("in") or 0) / clip_fps + (s - start / seq_fps)

                nested = self.resolve(clip.find("sequence"))
                if nested is not None and nested.find("media") is not None:
                    nested_fps = self.fps(nested, clip_fps)
                    n_in = int(clip.findtext("in") or 0) / nested_fps + (s - start / seq_fps)
                    self.walk(nested, kind, abs_start, (n_in, n_in + dur), label, depth + 1,
                              nest_names + [nested.findtext("name") or "nest"])
                    continue

                file_el = self.resolve(clip.find("file"))
                name = (file_el.findtext("name") if file_el is not None else None) or clip.findtext("name") or "?"
                src_dur = None
                if file_el is not None and file_el.findtext("duration"):
                    src_dur = int(file_el.findtext("duration")) / self.fps(file_el, clip_fps)
                path = unquote(file_el.findtext("pathurl") or "") if file_el is not None else ""
                self.clips.append({
                    "track": label, "kind": kind, "start": abs_start, "dur": dur, "name": name,
                    "src_in": src_in, "src_dur": src_dur, "path": path, "speed": self.speed(clip),
                    "effects": self.effects(clip), "nest": " > ".join(nest_names),
                })


def pick_sequence(root, edit, wanted):
    sequences = [s for s in root.iter("sequence") if s.find("media") is not None]
    if wanted:
        for s in sequences:
            if s.findtext("name") == wanted:
                return s
        sys.exit(f"Sequence '{wanted}' not found. Available: {', '.join(sorted({s.findtext('name') or '?' for s in sequences}))}")
    nested_ids = {edit.resolve(s).get("id") for c in root.iter("clipitem") for s in c.findall("sequence")}
    top = [s for s in sequences if s.get("id") not in nested_ids] or sequences
    return max(top, key=lambda s: int(s.findtext("duration") or 0))


def main():
    parser = argparse.ArgumentParser(description="Summarize a Final Cut Pro XML export from Premiere.")
    parser.add_argument("xml")
    parser.add_argument("--sequence", help="Name of the sequence to analyze (default: the longest top-level one)")
    parser.add_argument("--out", help="Output folder (default: <xml name>_summary next to the file)")
    args = parser.parse_args()

    xml_path = Path(args.xml)
    root = ET.parse(xml_path).getroot()
    edit = Edit(root)
    seq = pick_sequence(root, edit, args.sequence)
    seq_len = int(seq.findtext("duration") or 0) / edit.fps(seq)
    for kind in ("video", "audio"):
        edit.walk(seq, kind, 0.0, None, None, 0, [])
    clips = sorted(edit.clips, key=lambda c: (c["start"], c["track"]))
    if not clips:
        sys.exit("No clips found in the sequence.")

    out = Path(args.out) if args.out else xml_path.with_name(xml_path.stem + "_summary")
    out.mkdir(parents=True, exist_ok=True)

    by_track = defaultdict(list)
    for c in clips:
        by_track[c["track"]].append(c)

    # Raw footage = video sources longer than a few minutes; that is what got compressed into the edit
    raw = {}
    for c in clips:
        if c["kind"] == "video" and c["src_dur"] and c["src_dur"] > 300:
            raw.setdefault(c["name"], {"len": c["src_dur"], "used": 0.0, "pieces": 0})
            raw[c["name"]]["used"] += c["dur"] * c["speed"]
            raw[c["name"]]["pieces"] += 1
    raw_total = sum(r["len"] for r in raw.values())

    r = [f"# Edit summary: {seq.findtext('name')}\n",
         f"- edit length: {fmt(seq_len, 0)}",
         f"- clips on flattened timeline: {len(clips)} (video {sum(c['kind'] == 'video' for c in clips)}, "
         f"audio {sum(c['kind'] == 'audio' for c in clips)})"]
    if raw_total:
        used = sum(x["used"] for x in raw.values())
        r += [f"- raw footage referenced: {len(raw)} files, {fmt(raw_total, 0)} total",
              f"- raw footage actually used: {fmt(used, 0)} ({used / raw_total * 100:.1f}%)",
              f"- compression: {raw_total / 60:.0f} min of raw -> {seq_len / 60:.1f} min of edit "
              f"(1 min of edit per {raw_total / max(seq_len, 1):.0f} min of raw)"]

    r += ["\n## Tracks\n", "| track | clips | avg | median | covered | top assets |", "|---|---|---|---|---|---|"]
    for track in sorted(by_track, key=lambda t: (t[0], int(t[1:]))):
        items = by_track[track]
        durs = [c["dur"] for c in items]
        top = ", ".join(f"{n} x{k}" for n, k in Counter(c["name"] for c in items).most_common(3))
        r.append(f"| {track} | {len(items)} | {statistics.mean(durs):.2f}s | {statistics.median(durs):.2f}s | "
                 f"{fmt(sum(durs), 0)} | {top} |")

    r += ["\n## Pacing of the main video track (V1) per 30s\n", "| window | clips | avg clip | sped up |", "|---|---|---|---|"]
    main = by_track.get("V1", [])
    for w in range(0, int(seq_len) + 1, 30):
        win = [c for c in main if w <= c["start"] < w + 30]
        if win:
            fast = sum(c["speed"] > 1.01 for c in win)
            r.append(f"| {fmt(w, 0)} | {len(win)} | {statistics.mean(c['dur'] for c in win):.2f}s | {fast} |")

    speeds = Counter(round(c["speed"], 2) for c in clips if c["kind"] == "video")
    r += ["\n## Speeds used (video)\n"] + [f"- x{s:g}: {n} clips" for s, n in sorted(speeds.items())]

    fx = Counter(e for c in clips for e in c["effects"])
    r += ["\n## Effects (clip count)\n"] + [f"- {n}: {k}" for n, k in fx.most_common(40)]

    if raw:
        r += ["\n## Raw files\n", "| file | length | used | pieces |", "|---|---|---|---|"]
        for name, x in sorted(raw.items()):
            r.append(f"| {name} | {fmt(x['len'], 0)} | {fmt(x['used'], 0)} | {x['pieces']} |")

    assets = Counter((c["track"], c["name"]) for c in clips if c["name"] not in raw)
    r += ["\n## Assets outside the raw footage (memes, SFX, music, graphics)\n"]
    r += [f"- {track} | {name} x{k}" for (track, name), k in assets.most_common(200)]
    (out / "report.md").write_text("\n".join(r) + "\n", encoding="utf-8")

    for f in out.glob("timeline_*.md"):
        f.unlink()
    per_minute = defaultdict(list)
    for c in clips:
        per_minute[int(c["start"] // 60)].append(c)
    for minute, items in sorted(per_minute.items()):
        lines = [f"# Timeline {minute:02d}:00 - {minute:02d}:59\n",
                 "time | track | dur | speed | asset | source in | effects | nest"]
        for c in items:
            lines.append(f"{fmt(c['start'], 2)} | {c['track']} | {c['dur']:.2f}s | x{c['speed']:g} | {c['name']} | "
                         f"{fmt(c['src_in'], 1)} | {', '.join(c['effects'])} | {c['nest']}")
        (out / f"timeline_{minute:02d}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Done: {len(clips)} clips. Results in {out}")


if __name__ == "__main__":
    main()
