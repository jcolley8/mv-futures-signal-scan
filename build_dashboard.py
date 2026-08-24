#!/usr/bin/env python3
"""
MV Futures Signal Scan — dashboard builder.

Usage:  python3 build_dashboard.py signals.json dashboard.html

Reads the cumulative signal corpus (signals.json) and emits a fully
self-contained HTML dashboard. No external dependencies, no network calls.

LOGO: if a file named logo.svg / logo.png / logo.jpg sits next to this script,
it is embedded as a data URL in the header. Otherwise a typographic MV VENTURES
lockup is used. Drop the real asset in and re-run — nothing else changes.

Palette: MV Ventures brand — #000000, #21355B (solid + frosted), #C8C8C8, #FFFFFF.
Magnitude is encoded on a single navy ramp derived from #21355B (sequential,
one hue, light->dark), never on rainbow or arbitrary categorical hues.
"""
import json, sys, os, base64

SRC = sys.argv[1] if len(sys.argv) > 1 else "signals.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "dashboard.html"
HERE = os.path.dirname(os.path.abspath(SRC)) or "."

data = json.load(open(SRC))
signals = data["signals"]
signals.sort(key=lambda s: (s.get("first_seen", ""), s.get("source_date", "")), reverse=True)

EPI = {
    "E-Educational":   ("E",  "Educational"),
    "P-Political":     ("P",  "Political"),
    "I-Environmental": ("I",  "Interaction w/ Environment"),
    "S-Social":        ("S",  "Social"),
    "T-Technological": ("T",  "Technological"),
    "EC-Economic":     ("Ec", "Economic"),
    "ME-Moral/Ethical":("ME", "Moral / Ethical"),
}
SECTORS = data.get("sectors") or [
    "Education", "AI & Cognition", "Labor & Economy", "Climate, Civic & Society",
    "Gaming, VR, AR & Virtual Worlds", "Neuroscience & Psychology",
    "Behavioral Health & Wellness", "Demographics & Migration", "Biotechnology",
    "Robotics & Fabrication", "Wildcards & Periphery"]

# ---- logo ---------------------------------------------------------------
def _embed(fn):
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        return None
    mime = "image/svg+xml" if fn.endswith(".svg") else ("image/jpeg" if fn.endswith((".jpg", ".jpeg")) else "image/png")
    return f'data:{mime};base64,' + base64.b64encode(open(p, "rb").read()).decode()

def _prepare_logo_from_source():
    """If a raw brand PNG/JPG (logo-src.*) is present, derive logo.png (white
    knocked out to transparency) and logo-dark.png (light-on-dark variant).
    Lets the repo carry the original brand asset and build both variants here."""
    src = next((os.path.join(HERE, f) for f in
                ("logo-src.png", "logo-src.jpg", "logo-src.jpeg")
                if os.path.exists(os.path.join(HERE, f))), None)
    if not src or os.path.exists(os.path.join(HERE, "logo.png")):
        return
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(src).convert("RGBA")
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if r > 242 and g > 242 and b > 242:
                px[x, y] = (r, g, b, 0)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    im.thumbnail((150, 150), Image.LANCZOS)
    im = im.quantize(colors=32, method=Image.FASTOCTREE).convert("RGBA")
    im.save(os.path.join(HERE, "logo.png"), optimize=True)
    d = im.copy(); dp = d.load()
    for y in range(d.size[1]):
        for x in range(d.size[0]):
            r, g, b, a = dp[x, y]
            if a == 0:
                continue
            dp[x, y] = (143, 163, 206, a) if b - r > 22 else (255, 255, 255, a)
    d = d.quantize(colors=32, method=Image.FASTOCTREE).convert("RGBA")
    d.save(os.path.join(HERE, "logo-dark.png"), optimize=True)

_prepare_logo_from_source()

LOGO_HTML = ('<div class="lockup"><span class="mv">MV</span>'
             '<span class="vt">VENTURES</span></div>')
_light = next((u for u in (_embed(f) for f in ("logo.svg", "logo.png", "logo.jpg", "logo.jpeg")) if u), None)
_dark = next((u for u in (_embed(f) for f in ("logo-dark.svg", "logo-dark.png")) if u), None)
# fallback: pre-encoded data URLs kept alongside the corpus (survives between sessions)
_ld = os.path.join(HERE, "logo-data.json")
if not _light and os.path.exists(_ld):
    _j = json.load(open(_ld))
    _light, _dark = _j.get("logo"), _j.get("logo_dark")
# last resort: lift the embedded logos out of any previously-built dashboard HTML
# in this folder (e.g. yesterday's file, or the staged Cowork artifact).
if not _light:
    import glob, re
    cands = sorted(glob.glob(os.path.join(HERE, "*.html")), key=os.path.getmtime, reverse=True)
    for c in cands:
        try:
            txt = open(c, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        m = re.search(r'class="logo logo-light" src="(data:image/[^"]+)"', txt)
        if m:
            _light = m.group(1)
            m2 = re.search(r'class="logo logo-dark" src="(data:image/[^"]+)"', txt)
            _dark = m2.group(1) if m2 else None
            break
if _light:
    LOGO_HTML = f'<img class="logo logo-light" src="{_light}" alt="MV Ventures">'
    if _dark:
        LOGO_HTML += f'<img class="logo logo-dark" src="{_dark}" alt="">'

import datetime
payload = {"meta": {**{k: v for k, v in data.items() if k not in ("signals",)},
                    "built_at": datetime.date.today().isoformat()},
           "signals": signals}

TPL = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="A standing horizon scan of the signals, trends, and drivers shaping the future of teaching, learning, and schooling. Published by MV Ventures.">
<title>MV Futures Signal Scan</title>
<style>
:root{
  color-scheme: light;
  --page:#FFFFFF; --surface:#FFFFFF; --raised:#FFFFFF;
  --frost:rgba(33,53,91,0.045); --frost-2:rgba(33,53,91,0.075);
  --ink:#000000; --ink-2:#21355B; --muted:#757575;
  --rule:#C8C8C8; --hair:rgba(0,0,0,0.12); --track:#E8E8E8;
  --navy:#21355B; --navy-ink:#FFFFFF;
  --n100:#E6E9F0; --n200:#C6CDDC; --n300:#9BA6BF; --n400:#6E7C9D;
  --n500:#45577E; --n600:#21355B; --n700:#16223B;
  --lik-actual:#21355B;      --lik-actual-ink:#FFFFFF;
  --lik-probable:#45577E;    --lik-probable-ink:#FFFFFF;
  --lik-plausible:#6E7C9D;   --lik-plausible-ink:#FFFFFF;
  --lik-possible:#9BA6BF;    --lik-possible-ink:#000000;
  --lik-preposterous:#C6CDDC;--lik-preposterous-ink:#000000;
  --tint:33,53,91;
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --page:#000000; --surface:rgba(255,255,255,0.045); --raised:rgba(255,255,255,0.07);
  --frost:rgba(33,53,91,0.42); --frost-2:rgba(33,53,91,0.55);
  --ink:#FFFFFF; --ink-2:#C8C8C8; --muted:#9A9A9A;
  --rule:rgba(255,255,255,0.16); --hair:rgba(255,255,255,0.14); --track:rgba(255,255,255,0.11);
  --navy:#8FA3CE; --navy-ink:#000000;
  --n100:#16223B; --n200:#21355B; --n300:#45577E; --n400:#6E7C9D;
  --n500:#9BA6BF; --n600:#C6CDDC; --n700:#E6E9F0;
  --lik-actual:#DCE3F2;      --lik-actual-ink:#000000;
  --lik-probable:#B6C2DE;    --lik-probable-ink:#000000;
  --lik-plausible:#8FA3CE;   --lik-plausible-ink:#000000;
  --lik-possible:#6A7CA8;    --lik-possible-ink:#FFFFFF;
  --lik-preposterous:#45577E;--lik-preposterous-ink:#FFFFFF;
  --tint:143,163,206;
}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1360px;margin:0 auto;padding:26px 24px 80px}

/* header */
header.top{display:flex;justify-content:space-between;align-items:flex-start;gap:28px;flex-wrap:wrap;
  padding-bottom:20px;border-bottom:2px solid var(--navy);margin-bottom:24px}
.brandrow{display:flex;align-items:flex-start;gap:18px}
.logo{width:66px;height:auto;flex:none;margin-top:3px}
.logo-dark{display:none}
:root[data-theme="dark"] .logo-light{display:none}
:root[data-theme="dark"] .logo-dark{display:block}
.lockup{display:flex;flex-direction:column;align-items:center;gap:3px;flex:none;
  border:2px solid var(--navy);padding:8px 10px;margin-top:2px}
.lockup .mv{font-size:24px;font-weight:800;letter-spacing:.02em;color:var(--navy);line-height:1}
.lockup .vt{font-size:7.5px;font-weight:700;letter-spacing:.34em;color:var(--ink);
  text-indent:.34em;line-height:1}
h1{font-size:27px;margin:0 0 6px;letter-spacing:-.015em;font-weight:680}
.sub{color:var(--ink-2);font-size:14px;margin:0;max-width:66ch}
.stamp{font-size:12.5px;color:var(--muted);margin-top:8px;font-variant-numeric:tabular-nums}
.toggle{background:var(--frost);border:1px solid var(--rule);border-radius:6px;color:var(--ink-2);
  padding:7px 13px;font-size:13px;cursor:pointer;font-family:inherit;white-space:nowrap;font-weight:550}
.toggle:hover{color:var(--ink);border-color:var(--navy)}

.stale{background:var(--frost-2);border:1px solid var(--navy);border-left:4px solid var(--navy);
  border-radius:8px;padding:12px 16px;margin-bottom:18px;font-size:13.5px;color:var(--ink)}
.stale b{color:var(--navy)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin-bottom:30px}
.tile{background:var(--frost);border:1px solid var(--hair);border-radius:8px;padding:14px 16px}
.tile .v{font-size:30px;font-weight:680;letter-spacing:-.02em;line-height:1.15;color:var(--navy)}
.tile .k{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-top:2px}

h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.11em;color:var(--navy);
  margin:36px 0 6px;font-weight:700}
h2 + .h2sub{font-size:13px;color:var(--muted);margin:0 0 14px;max-width:80ch}
.panel{background:var(--surface);border:1px solid var(--hair);border-radius:10px;padding:18px 20px}

/* critical uncertainties */
.cus{display:grid;gap:12px}
.cu{background:var(--frost);border:1px solid var(--hair);border-left:4px solid var(--navy);
  border-radius:8px;padding:16px 20px}
.cu-head{display:flex;gap:14px;align-items:baseline;cursor:pointer}
.cu-num{font-size:12px;font-weight:800;color:var(--navy);letter-spacing:.08em;flex:none;
  font-variant-numeric:tabular-nums;padding-top:2px}
.cu h3{font-size:17.5px;margin:0;font-weight:640;letter-spacing:-.01em;line-height:1.32;flex:1}
.cu-toggle{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;flex:none}
.cu-stamp{font-size:11.5px;color:var(--muted);margin-top:7px;line-height:1.45}
.cu-stamp b{color:var(--ink-2);font-weight:650}
.cu-stamp i{font-style:normal;color:var(--navy);font-weight:700}
.cu-q{margin:10px 0 0;font-size:13.5px;color:var(--ink-2)}
.cu-body{margin-top:14px;display:none}
.cu.open .cu-body{display:block}
.poles{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:stretch;margin:4px 0 14px}
.pole{background:var(--surface);border:1px solid var(--hair);border-radius:6px;padding:11px 13px;font-size:13px}
.pole b{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--navy);margin-bottom:4px;font-weight:700}
.axis{display:flex;align-items:center;color:var(--rule);font-size:20px;padding:0 2px}
.cu-body h4{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  margin:0 0 6px;font-weight:700}
.cu-body p.why{font-size:13.5px;color:var(--ink);margin:0 0 14px}
.watch{margin:0 0 14px;padding-left:18px;font-size:13px;color:var(--ink-2)}
.watch li{margin:4px 0}
.culinks{display:flex;flex-wrap:wrap;gap:6px}
.culinks button{background:var(--surface);border:1px solid var(--hair);border-radius:4px;
  font-size:11.5px;color:var(--ink-2);padding:4px 8px;cursor:pointer;font-family:inherit;text-align:left}
.culinks button:hover{border-color:var(--navy);color:var(--ink)}

/* scenario */
.scn{background:var(--frost);border:1px solid var(--hair);border-top:4px solid var(--navy);
  border-radius:8px;padding:22px 24px}
.scn-top{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}
.scn-year{font-size:11px;font-weight:800;letter-spacing:.12em;color:var(--navy);
  border:1px solid var(--navy);border-radius:3px;padding:3px 8px;flex:none}
.scn h3{font-size:23px;margin:0;font-weight:660;letter-spacing:-.015em}
.scn-axis{font-size:11.5px;color:var(--muted);margin:0 0 14px;letter-spacing:.02em}
.scn-premise{font-size:15px;line-height:1.6;margin:0 0 20px;color:var(--ink);max-width:78ch}
.personas{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-bottom:18px}
.persona{background:var(--surface);border:1px solid var(--hair);border-radius:6px;padding:14px 16px}
.persona .r{font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--navy);
  font-weight:750;margin-bottom:2px}
.persona .n{font-size:13.5px;font-weight:650;margin-bottom:7px;color:var(--ink)}
.persona p{font-size:13px;line-height:1.52;color:var(--ink-2);margin:0}
.scn-tension{border-left:3px solid var(--navy);padding:2px 0 2px 14px;margin:0 0 18px;
  font-size:14px;line-height:1.55;color:var(--ink);max-width:80ch}
.scn-tension b{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;
  color:var(--navy);margin-bottom:4px;font-weight:750}
.scn-foot{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding-top:16px;
  border-top:1px solid var(--hair)}
@media(max-width:760px){.scn-foot{grid-template-columns:1fr}}
.scn-foot h4{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);
  margin:0 0 7px;font-weight:700}
.scn-foot ul{margin:0;padding-left:17px;font-size:13px;color:var(--ink-2)}
.scn-foot li{margin:5px 0;line-height:1.45}
.scn-foot .curef{display:block;font-size:12.5px;color:var(--ink-2);margin:6px 0;line-height:1.4}
.scn-foot .curef b{color:var(--ink);font-weight:640}
.scn-foot .curef em{color:var(--muted);font-style:normal;display:block;font-size:12px;margin-top:1px}
.scn-arch{margin-top:12px}
.scn-arch summary{cursor:pointer;font-size:12.5px;color:var(--muted);padding:8px 0}
.scn-arch summary:hover{color:var(--ink)}
.scn-arch .scn{margin-top:10px}

/* matrix */
table.mx{width:100%;border-collapse:separate;border-spacing:3px;font-size:13px}
table.mx th{font-weight:700;color:var(--navy);text-align:left;padding:6px 10px;font-size:11px;
  text-transform:uppercase;letter-spacing:.09em}
table.mx th.col{text-align:center}
table.mx td{background:var(--surface);border:1px solid var(--hair);border-radius:6px;padding:10px;
  vertical-align:top;min-width:150px;cursor:pointer}
table.mx td:hover{border-color:var(--navy)}
table.mx td.empty{background:transparent;border-style:dashed;cursor:default}
table.mx td.empty .cellcount{color:var(--muted)}
table.mx td.empty:hover{border-color:var(--hair)}
table.mx td.rowhead{background:transparent;border:none;font-weight:700;color:var(--ink);
  white-space:nowrap;padding:10px 12px 10px 0;width:1%;cursor:default}
table.mx td.rowhead small{display:block;font-weight:400;color:var(--muted);font-size:11.5px}
.cellcount{font-size:21px;font-weight:680;font-variant-numeric:tabular-nums;line-height:1.1;color:var(--navy)}
.cellitems{margin:6px 0 0;padding:0;list-style:none;font-size:12px;color:var(--ink-2)}
.cellitems li{margin:3px 0;line-height:1.35}
.cellitems a{text-decoration:none;border-bottom:1px solid var(--rule)}
.cellitems a:hover{border-bottom-color:currentColor}
.mx-legend{font-size:12px;color:var(--muted);margin-top:10px}

/* distribution bars */
.dists{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}
.bar-row{display:grid;grid-template-columns:minmax(94px,auto) 1fr auto;gap:10px;align-items:center;
  margin:7px 0;font-size:13px}
.bar-row .lbl{color:var(--ink-2);white-space:nowrap}
.bar-track{display:block;background:var(--track);border-radius:3px;height:11px;overflow:hidden}
.bar-fill{display:block;height:100%;border-radius:0 3px 3px 0;min-width:3px}
.bar-row .n{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:650;min-width:2ch;text-align:right}

/* filters */
.filters{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:10px 0 18px;
  position:sticky;top:0;background:var(--page);padding:12px 0;z-index:5;border-bottom:1px solid var(--rule)}
.fgroup{display:flex;gap:5px;align-items:center;flex-wrap:wrap}
.fgroup>.glabel{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-right:2px;font-weight:600}
.chip{border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);border-radius:999px;
  padding:5px 11px;font-size:12.5px;cursor:pointer;font-family:inherit;white-space:nowrap}
.chip:hover{border-color:var(--navy);color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--navy);color:var(--navy-ink);border-color:var(--navy);font-weight:600}
input.search{border:1px solid var(--rule);background:var(--surface);color:var(--ink);border-radius:6px;
  padding:7px 11px;font-size:13px;font-family:inherit;min-width:200px;flex:1}
input.search::placeholder{color:var(--muted)}
.count{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums}

/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:14px}
.card{background:var(--surface);border:1px solid var(--hair);border-radius:8px;padding:16px 18px;
  border-left:4px solid var(--likbg);display:flex;flex-direction:column}
.card h3{font-size:16px;margin:0 0 8px;line-height:1.32;font-weight:640;letter-spacing:-.006em}
.sectorname{font-size:10.5px;color:var(--navy);font-weight:750;letter-spacing:.09em;
  text-transform:uppercase;margin-bottom:6px}
.meta{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;align-items:center}
.pill{font-size:11px;border-radius:3px;padding:2.5px 7px;font-weight:650;letter-spacing:.02em;white-space:nowrap}
.pill.lik{background:var(--likbg);color:var(--likink)}
.pill.hz{border:1px solid var(--rule);color:var(--ink-2)}
.pill.hz3{border-color:var(--navy);color:var(--navy);font-weight:750}
.pill.tl{background:var(--track);color:var(--ink-2)}
.pill.ty{border:1px solid var(--hair);color:var(--muted);text-transform:uppercase;font-size:10px;letter-spacing:.08em}
.pill.new{background:var(--navy);color:var(--navy-ink)}
.epi{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 10px}
.epi span{font-size:10.5px;border:1px solid var(--hair);color:var(--ink-2);border-radius:3px;
  padding:2px 6px;letter-spacing:.03em}
.epi span b{color:var(--navy);font-weight:800}
.card p{margin:0 0 9px;font-size:13.5px;color:var(--ink-2);line-height:1.5}
.sowhat{border-left:2px solid var(--navy);padding-left:11px;margin:2px 0 12px !important;
  color:var(--ink) !important;font-size:13.5px}
.sowhat b{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--navy);
  display:block;margin-bottom:3px;font-weight:700}
.src{margin-top:auto;padding-top:10px;border-top:1px solid var(--hair);font-size:12px;color:var(--muted);
  display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.src a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--navy);font-weight:600}
.src a:hover{border-bottom-width:2px}
.src .sd{font-variant-numeric:tabular-nums;white-space:nowrap}

/* table view */
table.full{width:100%;border-collapse:collapse;font-size:12.5px}
table.full th{text-align:left;padding:8px 10px;border-bottom:2px solid var(--navy);color:var(--navy);
  font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;position:sticky;top:0;background:var(--page)}
table.full td{padding:8px 10px;border-bottom:1px solid var(--hair);vertical-align:top;color:var(--ink-2)}
table.full td.t{color:var(--ink);font-weight:560;min-width:230px}
table.full a{color:var(--ink)}
.hidden{display:none !important}
footer{margin-top:46px;padding-top:18px;border-top:2px solid var(--navy);font-size:12.5px;
  color:var(--muted);max-width:88ch}
footer b{color:var(--ink-2)}
@media print{.filters,.toggle{display:none}.card,.cu{break-inside:avoid}.cu-body{display:block}}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div class="brandrow">
    __LOGO__
    <div>
      <h1>MV Futures Signal Scan</h1>
      <p class="sub">A standing horizon scan of the weak signals, strong signals, trends, and drivers most likely to shape the future of teaching, learning, and schooling — classified by likelihood of impact, EPISTEME domain, and Three Horizons.</p>
      <p class="stamp" id="stamp"></p>
    </div>
  </div>
  <button class="toggle" id="themeBtn" type="button">Dark mode</button>
</header>

<div id="stale"></div>
<div class="tiles" id="tiles"></div>

<h2>Critical uncertainties</h2>
<p class="h2sub">The five forces surfacing from this scan that are both <b>highly uncertain</b> in how they resolve and <b>highly consequential regardless of which way they go</b>. These are the axes worth building scenarios on. Click any card to open it.</p>
<div class="cus" id="cus"></div>

<h2>Today's scenario</h2>
<p class="h2sub">A short, plausible future built by crossing two of the critical uncertainties above and letting them resolve one particular way — then asking what an ordinary week feels like from inside it. Not a prediction. A rehearsal.</p>
<div id="scenario"></div>

<h2>Horizon &times; timeline map</h2>
<p class="h2sub">Rows are Three Horizons; columns are years until material impact on schools. Click a cell to filter the entries below it.</p>
<div class="panel">
  <table class="mx" id="matrix"></table>
  <p class="mx-legend">Cell shading scales with density. Titles link to the original source.</p>
</div>

<h2>Distributions</h2>
<div class="panel dists" id="dists"></div>

<h2>Signals, trends &amp; drivers</h2>
<div class="filters" id="filters"></div>
<div class="cards" id="cards"></div>
<div id="tableview" class="panel hidden" style="overflow:auto;max-height:80vh"></div>

<footer>
  <p><b>How to read this.</b> <b>Likelihood of impact</b> — <i>actual</i>: already happening and measurable now; <i>probable</i>: strong evidence it will land; <i>plausible</i>: credible pathway; <i>possible</i>: conceivable but speculative; <i>preposterous</i>: low-probability, high-impact wildcard worth tracking anyway. <b>EPISTEME</b> — <b>E</b>ducational · <b>P</b>olitical · <b>I</b>nteraction with environment (ecological and environmental forces bearing on schools) · <b>S</b>ocial · <b>T</b>echnological · <b>E</b>conomic · <b>M</b>oral/<b>E</b>thical. <b>Horizon</b> — H1: continuation of the status quo; H2: disruptive innovation; H3: complete transformation of how we do things.</p>
  <p>Every entry links to its original source for verification and use. Sources are limited to peer-reviewed journals, preprint servers, government and intergovernmental agencies, university research centers, survey organizations, think tanks, analyst and industry reports, editorially-governed news and trade press, and signal-bearing product or marketing material. No blogs.</p>
</footer>
</div>

<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
const DATA = JSON.parse(document.getElementById('payload').textContent);
const S = DATA.signals, META = DATA.meta, CUS = META.critical_uncertainties || [];
const LIK = ['actual','probable','plausible','possible','preposterous'];
const TLS = ['0-2','3-6','7-10'];
const HZ  = [1,2,3];
const HZL = {1:'H1 · Status quo',2:'H2 · Disruptive',3:'H3 · Transformative'};
const SECTORS = __SECTORS__;
const EPI = __EPI__;
const esc = t => String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const byId = {}; S.forEach(s=>byId[s.id]=s);

document.getElementById('stamp').textContent =
  'Last refreshed ' + META.last_updated + ' · scan #' + META.scan_count +
  ' · ' + S.length + ' entries under watch · refreshes daily at 12:00 PM ET';

(function(){
  const lu = META.last_updated, bt = META.built_at;
  if(!lu || !bt) return;
  const age = Math.round((Date.parse(bt+'T00:00:00Z') - Date.parse(lu+'T00:00:00Z'))/86400000);
  if(age >= 2) document.getElementById('stale').innerHTML =
    `<div class="stale"><b>This scan is ${age} days old.</b> The last successful scan was ${lu}; ` +
    `this page was rebuilt on ${bt}. The daily scan may be failing — the signals and scenario below ` +
    `are still accurate as of ${lu}, but nothing new has been added since.</div>`;
})();

const isNew = s => s.first_seen === META.last_updated;
const tiles = [
  [S.length,'Under watch'],
  [S.filter(isNew).length,'New this scan'],
  [CUS.length,'Critical uncertainties'],
  [S.filter(s=>s.horizon===3).length,'Horizon 3'],
  [S.filter(s=>s.likelihood==='actual').length,'Already actual'],
  [S.filter(s=>s.timeline==='0-2').length,'Landing in 0–2 yrs'],
  [S.filter(s=>['possible','preposterous'].includes(s.likelihood)).length,'Wildcards'],
];
document.getElementById('tiles').innerHTML = tiles.map(([v,k])=>
  `<div class="tile"><div class="v">${v}</div><div class="k">${k}</div></div>`).join('');

/* ---------- critical uncertainties ---------- */
function daysBetween(a,b){
  const ms = Date.parse(b+'T00:00:00Z') - Date.parse(a+'T00:00:00Z');
  return isNaN(ms) ? null : Math.round(ms/86400000);
}
function stamp(c){
  const today = META.last_updated;
  const age = c.first_identified ? daysBetween(c.first_identified, today) : null;
  const since = c.last_revised ? daysBetween(c.last_revised, today) : null;
  const bits = [];
  if(age !== null) bits.push(`<b>on the list ${age === 0 ? 'since today' : age + ' day' + (age===1?'':'s')}</b>`);
  if(since !== null) bits.push(since === 0 ? '<i class="fresh">revised today</i>'
                     : (since === 1 ? 'revised yesterday' : `unchanged for ${since} days`));
  if(c.status_note) bits.push(esc(c.status_note));
  return bits.join(' &middot; ');
}
document.getElementById('cus').innerHTML = CUS.map((c,i)=>`
  <section class="cu" id="${esc(c.id)}">
    <div class="cu-head" data-cu="${i}">
      <span class="cu-num">CU ${String(i+1).padStart(2,'0')}</span>
      <h3>${esc(c.title)}</h3>
      <span class="cu-toggle">open</span>
    </div>
    <div class="cu-stamp">${stamp(c)}</div>
    <p class="cu-q">${esc(c.question)}</p>
    <div class="cu-body">
      <h4>Why it matters regardless of outcome</h4>
      <p class="why">${esc(c.why_it_matters)}</p>
      <h4>The uncertainty axis</h4>
      <div class="poles">
        <div class="pole"><b>Pole A</b>${esc(c.pole_a)}</div>
        <div class="axis">&harr;</div>
        <div class="pole"><b>Pole B</b>${esc(c.pole_b)}</div>
      </div>
      <h4>What would tell you which way it is resolving</h4>
      <ul class="watch">${c.watch.map(w=>`<li>${esc(w)}</li>`).join('')}</ul>
      <h4>Underlying signals in this scan (${c.signals.length})</h4>
      <div class="culinks">${c.signals.filter(id=>byId[id]).map(id=>
        `<button type="button" data-sig="${esc(id)}">${esc(byId[id].title)}</button>`).join('')}</div>
    </div>
  </section>`).join('');

document.querySelectorAll('.cu-head').forEach(h=>h.addEventListener('click',()=>{
  const sec = h.closest('.cu'); const open = sec.classList.toggle('open');
  h.querySelector('.cu-toggle').textContent = open ? 'close' : 'open';
}));
document.querySelectorAll('.culinks button').forEach(b=>b.addEventListener('click',()=>{
  clearFilters(); state.q = byId[b.dataset.sig].title.toLowerCase();
  document.getElementById('q').value = byId[b.dataset.sig].title;
  render(); document.getElementById('cards').scrollIntoView({behavior:'smooth',block:'start'});
}));

/* ---------- scenario ---------- */
(function(){
  const SC = META.scenarios || [];
  const el = document.getElementById('scenario');
  if(!SC.length){ el.innerHTML = '<p style="color:var(--muted)">No scenario in this scan yet.</p>'; return; }
  const render = s => `
    <section class="scn">
      <div class="scn-top"><span class="scn-year">${esc(s.year)}</span><h3>${esc(s.title)}</h3></div>
      <p class="scn-axis">${esc(s.axis || '')}</p>
      <p class="scn-premise">${esc(s.premise)}</p>
      <div class="personas">${(s.personas||[]).map(p=>`
        <div class="persona"><div class="r">${esc(p.role)}</div><div class="n">${esc(p.name||'')}</div>
        <p>${esc(p.vignette)}</p></div>`).join('')}</div>
      <p class="scn-tension"><b>The tension</b>${esc(s.tension)}</p>
      <div class="scn-foot">
        <div><h4>Built from</h4>${(s.based_on||[]).map(b=>
          `<span class="curef"><b>${esc(b.title)}</b><em>${esc(b.pole||'')}</em></span>`).join('')}</div>
        <div><h4>Worth arguing about</h4><ul>${(s.provocations||[]).map(p=>
          `<li>${esc(p)}</li>`).join('')}</ul></div>
      </div>
    </section>`;
  el.innerHTML = render(SC[0]) + (SC.length>1 ? `
    <details class="scn-arch"><summary>${SC.length-1} earlier scenario${SC.length>2?'s':''} &mdash; open</summary>
    ${SC.slice(1).map(render).join('')}</details>` : '');
})();

/* ---------- matrix ---------- */
(function(){
  const cells = {}; let max = 0; const CAP = 7;
  HZ.forEach(h=>TLS.forEach(t=>{
    const list = S.filter(s=>s.horizon===h && s.timeline===t);
    cells[h+'|'+t] = list; if(list.length>max) max = list.length;
  }));
  const shade = n => n ? `rgba(var(--tint),${(0.05+0.20*(n/Math.max(max,1))).toFixed(3)})` : 'transparent';
  let html = '<thead><tr><th></th>' + TLS.map(t=>`<th class="col">${t} years</th>`).join('') + '</tr></thead><tbody>';
  HZ.forEach(h=>{
    html += `<tr><td class="rowhead">${HZL[h].split(' · ')[0]}<small>${HZL[h].split(' · ')[1]}</small></td>`;
    TLS.forEach(t=>{
      const list = cells[h+'|'+t], n = list.length;
      html += `<td class="${n?'':'empty'}" data-h="${h}" data-t="${t}" style="background:${shade(n)}">` +
        `<div class="cellcount">${n}</div>` +
        (n ? '<ul class="cellitems">' + list.slice(0,CAP).map(s=>
          `<li><a href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('') +
          (n>CAP ? `<li style="color:var(--muted)">+ ${n-CAP} more — click cell to filter</li>` : '') + '</ul>' : '') +
        '</td>';
    });
    html += '</tr>';
  });
  document.getElementById('matrix').innerHTML = html + '</tbody>';
  document.querySelectorAll('table.mx td[data-h]:not(.empty)').forEach(td=>{
    td.addEventListener('click', e=>{
      if(e.target.tagName === 'A') return;
      clearFilters();
      state.horizon.add(td.dataset.h); state.timeline.add(td.dataset.t);
      document.querySelectorAll('.chip[data-k]').forEach(b=>b.setAttribute('aria-pressed',
        (b.dataset.k==='horizon'&&b.dataset.v===td.dataset.h)||(b.dataset.k==='timeline'&&b.dataset.v===td.dataset.t)
        ? 'true':'false'));
      render();
      document.getElementById('cards').scrollIntoView({behavior:'smooth',block:'start'});
    });
  });
})();

/* ---------- distributions ---------- */
(function(){
  function block(title, rows, colorFn){
    const max = Math.max(...rows.map(r=>r[1]),1);
    return `<div><h3 style="font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--navy);margin:0 0 9px;font-weight:700">${title}</h3>` +
      rows.map(([lbl,n],i)=>`<div class="bar-row"><span class="lbl">${esc(lbl)}</span>` +
        `<span class="bar-track"><span class="bar-fill" style="width:${(n/max*100).toFixed(1)}%;background:${colorFn(lbl,i)}"></span></span>` +
        `<span class="n">${n}</span></div>`).join('') + '</div>';
  }
  const cnt=(arr,key)=>{const m={};arr.forEach(x=>{const k=key(x);(Array.isArray(k)?k:[k]).forEach(v=>m[v]=(m[v]||0)+1)});return m;};
  const lc=cnt(S,s=>s.likelihood), ec=cnt(S,s=>s.episteme), sc=cnt(S,s=>s.sector), tc=cnt(S,s=>s.type);
  document.getElementById('dists').innerHTML = [
    block('Likelihood of impact', LIK.map(l=>[l,lc[l]||0]), l=>'var(--lik-'+l+')'),
    block('EPISTEME domain', Object.keys(EPI).map(k=>[EPI[k][1],ec[k]||0]), ()=>'var(--n500)'),
    block('Sector of origin', SECTORS.map(s=>[s,sc[s]||0]), ()=>'var(--n400)'),
    block('Entry type', ['signal','trend','driver'].map(t=>[t,tc[t]||0]), ()=>'var(--n400)'),
  ].join('');
})();

/* ---------- filters + cards ---------- */
const state = {likelihood:new Set(),episteme:new Set(),horizon:new Set(),timeline:new Set(),
               sector:new Set(),type:new Set(),q:'',view:'cards'};
function clearFilters(){
  ['likelihood','episteme','horizon','timeline','sector','type'].forEach(k=>state[k].clear());
  state.q=''; const q=document.getElementById('q'); if(q) q.value='';
  document.querySelectorAll('.chip[data-k]').forEach(b=>b.setAttribute('aria-pressed','false'));
}
(function buildFilters(){
  const f = document.getElementById('filters');
  const g=(label,key,opts,fmt)=>`<div class="fgroup"><span class="glabel">${label}</span>` +
    opts.map(o=>`<button class="chip" type="button" data-k="${key}" data-v="${esc(o)}" aria-pressed="false">${esc(fmt?fmt(o):o)}</button>`).join('') + '</div>';
  f.innerHTML =
    g('Likelihood','likelihood',LIK) +
    g('EPISTEME','episteme',Object.keys(EPI), k=>EPI[k][0]+' · '+EPI[k][1]) +
    g('Horizon','horizon',['1','2','3'], h=>'H'+h) +
    g('Timeline','timeline',TLS, t=>t+' yr') +
    g('Sector','sector',SECTORS) +
    g('Type','type',['signal','trend','driver']) +
    `<input class="search" id="q" type="search" placeholder="Search titles, summaries, sources…">` +
    `<button class="chip" id="viewBtn" type="button">Table view</button>` +
    `<button class="chip" id="clearBtn" type="button">Clear</button>` +
    `<span class="count" id="count"></span>`;
  f.querySelectorAll('.chip[data-k]').forEach(b=>b.addEventListener('click',()=>{
    const set=state[b.dataset.k], v=b.dataset.v;
    if(set.has(v)){set.delete(v);b.setAttribute('aria-pressed','false');}
    else{set.add(v);b.setAttribute('aria-pressed','true');}
    render();
  }));
  document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value.toLowerCase();render();});
  document.getElementById('clearBtn').addEventListener('click',()=>{clearFilters();render();});
  document.getElementById('viewBtn').addEventListener('click',e=>{
    state.view = state.view==='cards'?'table':'cards';
    e.target.textContent = state.view==='cards'?'Table view':'Card view';
    render();
  });
})();

function match(s){
  if(state.likelihood.size && !state.likelihood.has(s.likelihood)) return false;
  if(state.horizon.size && !state.horizon.has(String(s.horizon))) return false;
  if(state.timeline.size && !state.timeline.has(s.timeline)) return false;
  if(state.sector.size && !state.sector.has(s.sector)) return false;
  if(state.type.size && !state.type.has(s.type)) return false;
  if(state.episteme.size && !s.episteme.some(e=>state.episteme.has(e))) return false;
  if(state.q){
    const hay=(s.title+' '+s.summary+' '+s.so_what+' '+s.source_name+' '+s.sector).toLowerCase();
    if(!hay.includes(state.q)) return false;
  }
  return true;
}
function card(s){
  return `<article class="card" style="--likbg:var(--lik-${s.likelihood});--likink:var(--lik-${s.likelihood}-ink)">
    <div class="sectorname">${esc(s.sector)}</div>
    <h3>${esc(s.title)}</h3>
    <div class="meta">
      <span class="pill lik">${s.likelihood}</span>
      <span class="pill hz${s.horizon===3?' hz3':''}">Horizon ${s.horizon}</span>
      <span class="pill tl">${s.timeline} yrs</span>
      <span class="pill ty">${s.type}</span>
      ${isNew(s)?'<span class="pill new">new</span>':''}
      ${s.sightings>1?`<span class="pill ty">seen ${s.sightings}&times;</span>`:''}
    </div>
    <div class="epi">${s.episteme.map(e=>`<span><b>${EPI[e]?EPI[e][0]:'?'}</b> ${EPI[e]?esc(EPI[e][1]):esc(e)}</span>`).join('')}</div>
    <p>${esc(s.summary)}</p>
    <p class="sowhat"><b>So what for schools</b>${esc(s.so_what)}</p>
    <div class="src">
      <a href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(s.source_name)} &nearr;</a>
      <span class="sd">${esc(s.source_type)} · ${esc(s.source_date)}</span>
    </div>
  </article>`;
}
function table(rows){
  return `<table class="full"><thead><tr>
    <th>Signal</th><th>Type</th><th>Likelihood</th><th>EPISTEME</th><th>Horizon</th><th>Timeline</th><th>Sector</th><th>Source</th><th>Date</th>
  </tr></thead><tbody>` + rows.map(s=>`<tr>
    <td class="t">${esc(s.title)}</td><td>${s.type}</td><td>${s.likelihood}</td>
    <td>${s.episteme.map(e=>EPI[e]?EPI[e][0]:e).join(', ')}</td>
    <td>H${s.horizon}</td><td>${s.timeline}</td><td>${esc(s.sector)}</td>
    <td><a href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(s.source_name)}</a></td>
    <td style="font-variant-numeric:tabular-nums">${esc(s.source_date)}</td></tr>`).join('') + '</tbody></table>';
}
function render(){
  const rows = S.filter(match);
  document.getElementById('count').textContent = rows.length + ' of ' + S.length + ' shown';
  const cards = document.getElementById('cards'), tv = document.getElementById('tableview');
  if(state.view==='cards'){
    cards.classList.remove('hidden'); tv.classList.add('hidden');
    cards.innerHTML = rows.length ? rows.map(card).join('')
      : '<p style="color:var(--muted)">No entries match those filters.</p>';
  } else {
    cards.classList.add('hidden'); tv.classList.remove('hidden');
    tv.innerHTML = table(rows);
  }
}
render();

const btn = document.getElementById('themeBtn');
if(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches){
  document.documentElement.dataset.theme='dark'; btn.textContent='Light mode';
}
btn.addEventListener('click',()=>{
  const d = document.documentElement.dataset.theme==='dark';
  document.documentElement.dataset.theme = d?'light':'dark';
  btn.textContent = d?'Dark mode':'Light mode';
});
</script>
</body>
</html>
"""

out = (TPL
       .replace("__PAYLOAD__", json.dumps(payload).replace("</", "<\\/"))
       .replace("__SECTORS__", json.dumps(SECTORS))
       .replace("__EPI__", json.dumps({k: list(v) for k, v in EPI.items()}))
       .replace("__LOGO__", LOGO_HTML))

open(OUT, "w").write(out)
print(f"wrote {OUT} — {len(signals)} signals, {len(data.get('critical_uncertainties',[]))} uncertainties, {len(out)} bytes")
