import json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
weekday = now.weekday()  # Mon=0
if weekday not in (0,1,2):
    raise SystemExit("Runs only Monday-Wednesday")

# Free Google News RSS search restricted to Reuters.
q = urllib.parse.quote("site:reuters.com Reuters")
url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    xml = r.read()
root = ET.fromstring(xml)

items=[]
for item in root.findall(".//item"):
    title=(item.findtext("title") or "").strip()
    link=(item.findtext("link") or "").strip()
    pub=(item.findtext("pubDate") or "").strip()
    source=item.find("source")
    source_name=(source.text or "") if source is not None else ""
    if "Reuters" not in title and "Reuters" not in source_name:
        continue
    title=re.sub(r"\s+-\s+Reuters\s*$","",title)
    items.append({"title":title,"link":link,"published":pub,"source":"Reuters"})
    if len(items)>=12: break

# This zero-cost workflow deliberately does not invent AI summaries.
# It archives current Reuters candidates; the site exposes them as source links.
data_dir=Path("data"); data_dir.mkdir(exist_ok=True)
week=f"{now.isocalendar().year}-W{now.isocalendar().week:02d}"
path=data_dir/f"{week}.json"
if path.exists():
    data=json.loads(path.read_text(encoding="utf-8"))
else:
    data={"week":week,"days":{}}
day=["monday","tuesday","wednesday"][weekday]
data["days"][day]={"updated_at":now.isoformat(),"articles":items}
data["last_updated"]=now.isoformat()
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
(data_dir/"latest.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(items)} Reuters candidates to {path}")
