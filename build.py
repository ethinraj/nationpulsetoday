#!/usr/bin/env python3
"""NationPulse Today static site builder.

Reads every edition JSON in content/editions/, writes the full site to ./site/.
The newest edition becomes the homepage; older stories stay live and appear in
section pages and the archive. No third-party dependencies.

Usage:  python3 build.py
"""
import html, json, os, shutil, glob
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
DOMAIN = "nationpulsetoday.com"
SITE = "NationPulse Today"
TAGLINE = "Desh ki dhadkan, har din"

SECTIONS = [
    ("india", "India & Politics"),
    ("world", "World & Geopolitics"),
    ("business", "Business & Economy"),
    ("tse", "Tech, Sports & Entertainment"),
]
SEC_NAME = dict(SECTIONS)
SEC_SHORT = {"india": "India", "world": "World", "business": "Business", "tse": "Tech · Sports · Ent"}

e = lambda s: html.escape(str(s), quote=True)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = ["Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar"]


def fmt_dt(dt):
    h = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{dt.day} {MONTHS[dt.month-1]} {dt.year}, {h}:{dt.minute:02d} {ampm} IST"


def fmt_day(dt):
    return f"{DAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month-1]} {dt.year}"


LOGO = """<svg width="46" height="46" viewBox="0 0 46 46" aria-hidden="true"><rect width="46" height="46" rx="6" fill="#c8211b"/><polyline points="5,25 14,25 18,14 24,34 29,19 32,25 41,25" fill="none" stroke="#fff" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/></svg>"""

BAND_SVG = {
    "india": '<svg viewBox="0 0 400 180" preserveAspectRatio="none"><polyline points="0,110 70,110 95,60 125,150 150,85 170,110 400,110" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="3"/><circle cx="330" cy="50" r="70" fill="rgba(255,255,255,.06)"/></svg>',
    "world": '<svg viewBox="0 0 400 180" preserveAspectRatio="none"><circle cx="300" cy="90" r="80" fill="none" stroke="rgba(255,255,255,.3)" stroke-width="2"/><ellipse cx="300" cy="90" rx="35" ry="80" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="2"/><line x1="220" y1="90" x2="380" y2="90" stroke="rgba(255,255,255,.25)" stroke-width="2"/></svg>',
    "business": '<svg viewBox="0 0 400 180" preserveAspectRatio="none"><polyline points="0,150 60,130 110,140 170,95 220,110 280,60 340,75 400,30" fill="none" stroke="rgba(255,255,255,.4)" stroke-width="3"/><g fill="rgba(255,255,255,.08)"><rect x="40" y="120" width="26" height="60"/><rect x="90" y="100" width="26" height="80"/><rect x="140" y="80" width="26" height="100"/></g></svg>',
    "tse": '<svg viewBox="0 0 400 180" preserveAspectRatio="none"><circle cx="310" cy="80" r="46" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="3"/><path d="M280 60 q30 20 60 0 M280 100 q30 -20 60 0" fill="none" stroke="rgba(255,255,255,.3)" stroke-width="2"/><rect x="40" y="40" width="90" height="60" rx="6" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="2"/></svg>',
}


def band(sec, label):
    cls = "" if sec == "india" else f" {sec}"
    return f'<div class="band{cls}">{BAND_SVG.get(sec, "")}<span class="tag">{e(label)}</span></div>'


# ---------------------------------------------------------------- load data
def load_editions():
    eds = []
    for p in sorted(glob.glob(os.path.join(ROOT, "content", "editions", "*.json"))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        d["_id"] = os.path.splitext(os.path.basename(p))[0]
        d["_dt"] = datetime.fromisoformat(d["updated"])
        d["_date"] = d["_dt"].strftime("%Y-%m-%d")
        eds.append(d)
    eds.sort(key=lambda d: d["_dt"], reverse=True)
    return eds


def collect(eds):
    """Flatten all stories/editorials with URLs; newest first, de-duplicated by URL."""
    stories, editorials, seen = [], [], set()
    for ed in eds:
        dt, date = ed["_dt"], ed["_date"]
        le = ed.get("lead_editorial")
        if le:
            url = f"editorial/{date}/{le['slug']}.html"
            if url not in seen:
                seen.add(url)
                editorials.append(dict(le, url=url, dt=dt, sec=None, lead=True))
        for s in ed["sections"]:
            for st in s["stories"]:
                url = f"story/{date}/{st['slug']}.html"
                if url not in seen:
                    seen.add(url)
                    stories.append(dict(st, url=url, dt=dt, sec=s["id"]))
            ed_ = s.get("editorial")
            if ed_:
                url = f"editorial/{date}/{ed_['slug']}.html"
                if url not in seen:
                    seen.add(url)
                    editorials.append(dict(ed_, url=url, dt=dt, sec=s["id"], lead=False))
    return stories, editorials


# ---------------------------------------------------------------- chrome
def page(title, body, rel, active="", desc="", latest=None, canonical=""):
    full_title = f"{title} | {SITE}" if title != SITE else f"{SITE} — {TAGLINE}"
    desc = desc or "NationPulse Today: India, duniya, business, tech, sports aur entertainment ki taaza khabrein aur bebaak editorials — Hinglish mein."
    nav_items = [("index.html", "Home", "home")] + [
        (f"section/{sid}.html", SEC_SHORT[sid], sid) for sid, _ in SECTIONS
    ] + [("editorials.html", "Editorials", "editorials"), ("archive.html", "Archive", "archive")]
    nav = "".join(
        f'<li><a href="{rel}{href}"{" class=active" if key == active else ""}>{e(lbl)}</a></li>'
        for href, lbl, key in nav_items
    )
    upd = fmt_dt(latest["_dt"]) if latest else ""
    edname = latest.get("edition", "") if latest else ""
    today = fmt_day(latest["_dt"]) if latest else ""
    ticker = ""
    if latest and latest.get("ticker"):
        items = "".join(f"<span>{e(t)}</span>" for t in latest["ticker"])
        ticker = f'<div class="ticker"><div class="wrap"><span class="lbl">TAAZA</span><div class="track"><div class="move">{items}</div></div></div></div>'
    canon = f'<link rel="canonical" href="https://{DOMAIN}/{canonical}">' if canonical is not None else ""
    return f"""<!doctype html>
<html lang="hi-Latn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:site" content="@nationpulsetoday">
{canon}
<link rel="icon" href="data:image/svg+xml,{LOGO.replace('"', "'").replace('#', '%23')}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<div class="topbar"><div class="wrap"><span>{e(today)}</span><span>Updated: <b>{e(upd)}</b> · <button class="theme-btn" id="themeBtn" type="button">Light / Dark</button></span></div></div>
<header class="masthead"><div class="wrap">
  <a class="logo" href="{rel}index.html">{LOGO}<div><div class="name">NationPulse <span>Today</span></div><div class="tag">{TAGLINE}</div></div></a>
  <div class="edition-badge"><strong>{e(edname)}</strong>Subah 7 baje · Shaam 7 baje</div>
</div></header>
<nav class="main" aria-label="Sections"><ul>{nav}</ul></nav>
{ticker}
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
  <div class="cols">
    <div><div class="fname">NationPulse <span>Today</span></div><p>India aur duniya ki khabrein, saaf bhasha mein. Har khabar ke saath original source ka link — taaki aap khud jaanch sakein.</p></div>
    <div><h5>Sections</h5><ul>{"".join(f'<li><a href="{rel}section/{sid}.html">{e(n)}</a></li>' for sid, n in SECTIONS)}</ul></div>
    <div><h5>NationPulse</h5><ul><li><a href="{rel}about.html">About Us</a></li><li><a href="{rel}editorial-policy.html">Editorial Policy</a></li><li><a href="{rel}archive.html">Archive</a></li><li><a href="https://x.com/nationpulsetoday" rel="noopener" target="_blank">X / Twitter</a></li></ul></div>
  </div>
  <div class="legal">© {datetime.now().year} NationPulse Today. Khabrein publicly available reports par aadharit hain aur har article mein source link diya gaya hai. "Hamari Raay" columns opinion hain. Yeh site investment, legal ya medical salaah nahi deti.</div>
</div></footer>
<script>
(function(){{var r=document.documentElement,k="np-theme";try{{var s=localStorage.getItem(k);if(s)r.setAttribute("data-theme",s)}}catch(e){{}}
document.getElementById("themeBtn").addEventListener("click",function(){{var cur=r.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");var n=cur==="dark"?"light":"dark";r.setAttribute("data-theme",n);try{{localStorage.setItem(k,n)}}catch(e){{}}}});}})();
</script>
</body>
</html>
"""


def src_line(sources):
    if not sources:
        return ""
    names = ", ".join(e(s["name"].split(" — ")[0]) for s in sources[:2])
    return f'<div class="src">Source: {names}</div>'


def card(st, rel, wide=False):
    return f"""<article class="card{' wide' if wide else ''}"><span class="kicker">{e(SEC_SHORT[st['sec']])}</span>
<h3><a href="{rel}{st['url']}">{e(st['title'])}</a></h3><p>{e(st['summary'])}</p>{src_line(st.get('sources'))}</article>"""


def ed_box(ed, rel):
    first = ed["body"][0] if ed.get("body") else ""
    return f"""<aside class="ed-box"><span class="kicker">Hamari Raay · Editorial</span>
<h3><a href="{rel}{ed['url']}">{e(ed['title'])}</a></h3><p>{e(first)}</p><a class="more" href="{rel}{ed['url']}">Poora editorial padhein →</a></aside>"""


# ---------------------------------------------------------------- pages
def build_home(latest, stories, editorials):
    rel = ""
    date = latest["_date"]
    secs = {s["id"]: s for s in latest["sections"]}
    cur = [s for s in stories if s["dt"] == latest["_dt"]]
    top = cur[0]
    le = next((x for x in editorials if x.get("lead") and x["dt"] == latest["_dt"]), None)
    heads = "".join(
        f'<li><a href="{s["url"]}">{e(s["title"])}<small>{e(SEC_SHORT[s["sec"]])}</small></a></li>' for s in cur[1:7]
    )
    lead_html = ""
    if le:
        lead_html = f"""<div class="lead-ed"><span class="kicker">{e(le.get('kicker','Hamari Raay'))}</span>
<h2><a href="{le['url']}">{e(le['title'])}</a></h2><p>{e(le['summary'])}</p><a class="more" href="{le['url']}">Lead editorial padhein →</a></div>"""
    body = f"""<section class="hero">
  <div class="top-story">{band(top['sec'], 'Top Story')}<span class="kicker">{e(SEC_SHORT[top['sec']])}</span>
    <h1><a href="{top['url']}">{e(top['title'])}</a></h1><p class="dek">{e(top['summary'])}</p>{src_line(top.get('sources'))}</div>
  {lead_html}
  <div class="headlines"><h3>Aaj ki Badi Khabrein</h3><ol>{heads}</ol></div>
</section>"""
    for sid, name in SECTIONS:
        s = secs.get(sid)
        if not s:
            continue
        sst = [x for x in cur if x["sec"] == sid]
        if sid == top["sec"]:
            sst = [x for x in sst if x["url"] != top["url"]] or sst
        cards = "".join(card(x, rel, wide=(len(sst) == 1)) for x in sst)
        sed = next((x for x in editorials if x["sec"] == sid and x["dt"] == latest["_dt"]), None)
        body += f"""<section class="section" id="{sid}"><div class="sec-head"><h2>{e(name)}</h2><a href="section/{sid}.html">Sab dekhein →</a></div>
<div class="sec-grid"><div class="cards">{cards}</div>{ed_box(sed, rel) if sed else ''}</div></section>"""
    return page(SITE, body, rel, "home", latest=latest, canonical="")


def build_section(sid, latest, stories, editorials):
    rel = "../"
    items = [s for s in stories if s["sec"] == sid][:40]
    eds = [x for x in editorials if x["sec"] == sid][:6]
    lst = "".join(
        f'<div class="list-item"><span class="kicker">{e(fmt_dt(s["dt"]))}</span><h3><a href="{rel}{s["url"]}">{e(s["title"])}</a></h3><p>{e(s["summary"])}</p></div>'
        for s in items
    )
    side = "".join(ed_box(x, rel) for x in eds[:2])
    body = f"""<h1 class="page-title">{e(SEC_NAME[sid])}</h1><p class="page-sub">Is section ki taaza aur pichhli khabrein.</p>
<div class="sec-grid"><div>{lst}</div><div style="display:grid;gap:20px;align-self:start">{side}</div></div>"""
    return page(SEC_NAME[sid], body, rel, sid, latest=latest, canonical=f"section/{sid}.html")


def article_html(item, rel, latest, others, is_ed):
    sec_lbl = SEC_SHORT.get(item["sec"], "Editorial") if item["sec"] else "Lead Editorial"
    crumbs = f'<a href="{rel}index.html">Home</a> / ' + (
        f'<a href="{rel}editorials.html">Editorials</a>' if is_ed else f'<a href="{rel}section/{item["sec"]}.html">{e(SEC_NAME[item["sec"]])}</a>'
    )
    dek = item.get("summary", "")
    note = '<div class="opinion-note"><b>Opinion:</b> Yeh NationPulse Today ka editorial hai — tathyon par aadharit hamari raay, khabar nahi.</div>' if is_ed else ""
    paras = "".join(f"<p>{e(p)}</p>" for p in item.get("body", []))
    srcs = item.get("sources") or []
    src_html = ""
    if srcs:
        src_html = '<div class="sources"><h4>Sources</h4><ul>' + "".join(
            f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener nofollow">{e(s["name"])}</a></li>' for s in srcs
        ) + "</ul></div>"
    rel_html = ""
    if others:
        rel_html = '<div class="related"><h4>Aur padhein</h4><ul>' + "".join(
            f'<li><a href="{rel}{o["url"]}">{e(o["title"])}</a></li>' for o in others[:5]
        ) + "</ul></div>"
    kicker = "Hamari Raay · Editorial" if is_ed else sec_lbl
    body = f"""<article class="article"><div class="crumbs">{crumbs}</div><span class="kicker">{e(kicker)}</span>
<h1>{e(item['title'])}</h1>{f'<p class="dek">{e(dek)}</p>' if dek else ''}
<div class="byline"><span><b>NationPulse Today Desk</b></span><span>{e(fmt_dt(item['dt']))}</span></div>
{note}<div class="body">{paras}</div>{src_html}{rel_html}</article>"""
    return page(item["title"], body, rel, "editorials" if is_ed else (item["sec"] or ""), desc=dek or (item.get("body") or [""])[0][:155], latest=latest, canonical=item["url"])


def build_editorials(latest, editorials):
    rel = ""
    lst = "".join(
        f'<div class="list-item"><span class="kicker">{"Lead Editorial" if x.get("lead") else e(SEC_SHORT.get(x["sec"], ""))} · {e(fmt_dt(x["dt"]))}</span><h3><a href="{x["url"]}">{e(x["title"])}</a></h3><p>{e(x.get("summary") or x["body"][0])}</p></div>'
        for x in editorials[:60]
    )
    body = f'<div class="prose"><h1 class="page-title">Hamari Raay</h1><p class="page-sub">NationPulse Today ke editorials — tathyon par aadharit, bebaak raay.</p>{lst}</div>'
    return page("Editorials", body, rel, "editorials", latest=latest, canonical="editorials.html")


def build_archive(latest, eds, stories):
    rel = ""
    out = ""
    for ed in eds:
        its = [s for s in stories if s["dt"] == ed["_dt"]]
        if not its:
            continue
        out += f'<h2 style="font-family:var(--serif);margin:28px 0 4px">{e(fmt_day(ed["_dt"]))} — {e(ed.get("edition",""))}</h2>'
        out += "".join(
            f'<div class="list-item"><span class="kicker">{e(SEC_SHORT[s["sec"]])}</span><h3><a href="{s["url"]}">{e(s["title"])}</a></h3></div>'
            for s in its
        )
    body = f'<div class="prose"><h1 class="page-title">Archive</h1><p class="page-sub">Har edition ki saari khabrein.</p>{out}</div>'
    return page("Archive", body, rel, "archive", latest=latest, canonical="archive.html")


def build_static(latest):
    about = """<div class="prose"><h1 class="page-title">About NationPulse Today</h1>
<p>NationPulse Today ek independent digital news platform hai jo India aur duniya ki badi khabrein seedhi, saaf Hinglish mein pesh karta hai.</p>
<p>Hum din mein do baar — subah aur shaam — naya edition publish karte hain: India & Politics, World & Geopolitics, Business & Economy, aur Tech, Sports & Entertainment.</p>
<p>Har khabar ke neeche original reporting ka link hota hai. Har section ke saath ek <b>"Hamari Raay"</b> editorial hota hai, jo saaf taur par opinion ke roop mein label kiya jaata hai.</p>
<p>Follow karein: <a href="https://x.com/nationpulsetoday" style="color:var(--accent)">@nationpulsetoday</a></p></div>"""
    policy = """<div class="prose"><h1 class="page-title">Editorial Policy</h1>
<ul>
<li><b>Source-first:</b> Har news story publicly available, vishwasniya reports par aadharit hoti hai, aur un sources ke link article mein diye jaate hain.</li>
<li><b>News aur opinion alag:</b> "Hamari Raay" editorials opinion hain aur hamesha alag label ke saath chhapte hain.</li>
<li><b>AI-assisted production:</b> Content research aur drafting mein AI tools ka istemaal hota hai. Publication ki zimmedari NationPulse Today ki hai.</li>
<li><b>Aarop aur faisle:</b> Kisi par lage aaropon ko hum aarop hi likhte hain, saabit tathya nahi.</li>
<li><b>Corrections:</b> Galti dikhe to X par @nationpulsetoday ko batayein; sahi ki gayi jaankari article mein update ki jaayegi.</li>
<li><b>No financial advice:</b> Business coverage jaankari ke liye hai, nivesh salaah nahi.</li>
</ul></div>"""
    return (
        page("About Us", about, "", "", latest=latest, canonical="about.html"),
        page("Editorial Policy", policy, "", "", latest=latest, canonical="editorial-policy.html"),
    )


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    eds = load_editions()
    if not eds:
        raise SystemExit("No editions found")
    latest = eds[0]
    stories, editorials = collect(eds)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))

    write("index.html", build_home(latest, stories, editorials))
    for sid, _ in SECTIONS:
        write(f"section/{sid}.html", build_section(sid, latest, stories, editorials))
    for st in stories:
        others = [s for s in stories if s["sec"] == st["sec"] and s["url"] != st["url"]]
        write(st["url"], article_html(st, "../../", latest, others, False))
    for ed in editorials:
        others = [x for x in editorials if x["url"] != ed["url"]]
        write(ed["url"], article_html(ed, "../../", latest, others, True))
    write("editorials.html", build_editorials(latest, editorials))
    write("archive.html", build_archive(latest, eds, stories))
    a, p = build_static(latest)
    write("about.html", a)
    write("editorial-policy.html", p)
    write("CNAME", DOMAIN + "\n")
    write(".nojekyll", "")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: https://{DOMAIN}/sitemap.xml\n")
    urls = ["", "editorials.html", "archive.html", "about.html", "editorial-policy.html"] + \
        [f"section/{s}.html" for s, _ in SECTIONS] + [x["url"] for x in stories + editorials]
    sm = "".join(f"<url><loc>https://{DOMAIN}/{u}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    print(f"Built {len(stories)} stories, {len(editorials)} editorials from {len(eds)} edition(s) -> {OUT}")


if __name__ == "__main__":
    main()
