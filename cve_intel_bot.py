import os
import json
import urllib.request
import urllib.parse
import sys
import datetime
import xml.etree.ElementTree as ET

# ================= CONFIGURATION =================
# Secrets and Chat IDs are loaded securely from Environment Variables / GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not TELEGRAM_BOT_TOKEN:
    # Try reading from local .env if available
    pass

CISA_KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
THN_RSS_URL = "https://feeds.feedburner.com/TheHackersNews"
SANS_ISC_RSS_URL = "https://isc.sans.edu/rssfeed.xml"
GHSA_API_URL = "https://api.github.com/advisories?per_page=10"
NUCLEI_ADDITIONS_URL = "https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/.new-additions"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_cves.json")
SEEN_GHSA_FILE = os.path.join(BASE_DIR, "seen_ghsa.json")
SEEN_NEWS_FILE = os.path.join(BASE_DIR, "seen_news.json")
SEEN_NUCLEI_FILE = os.path.join(BASE_DIR, "seen_nuclei.json")
CISA_LOCAL_CACHE = os.path.join(BASE_DIR, "cisa_kev_cache.json")
STATE_FILE = os.path.join(BASE_DIR, "bot_state.json")

# ================= GEMINI PRO AI ENGINE =================
def ask_gemini_pro(prompt: str, system_instruction: str = None) -> str:
    """Queries Google Gemini Pro/Flash API for deep exploit reasoning and Q&A."""
    key = os.getenv("GEMINI_API_KEY", "").strip() or GEMINI_API_KEY
    if not key:
        return ""

    for model_name in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_json = json.loads(resp.read().decode())
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            continue
    return ""

def generate_ai_threat_breakdown(title: str, summary: str, context: str = "threat intel") -> str:
    """Generates a 3-bullet elite offensive hacker breakdown using Gemini Pro."""
    sys_prompt = (
        "You are an elite offensive security researcher and top 1% bug bounty hunter. "
        "Summarize the vulnerability/threat in exactly 3 sharp bullet points with emojis:\n"
        "• 🎯 Target & Bug Class: (service name & bug category)\n"
        "• ⚡ Exploit TTPs: (how attackers exploit or chain it)\n"
        "• 🛡️ Hunter/Defender Action: (concrete recon or defense tip)\n"
        "Write in crisp Hinglish/English. Keep under 70 words. No boilerplate."
    )
    user_prompt = f"Threat Title: {title}\nSummary: {summary}\nContext: {context}"
    return ask_gemini_pro(user_prompt, sys_prompt)

# ================= TELEGRAM API HELPERS =================
def send_telegram_message(message: str, chat_id: str = None, reply_to_id: int = None):
    """Sends a formatted markdown message to Telegram with auto-retry."""
    import time
    target_chat = chat_id or TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")
    if not target_chat:
        print("[-] Telegram Send Error: No TELEGRAM_CHAT_ID provided.")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_to_id:
        payload["reply_to_message_id"] = reply_to_id

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "CyberIntelBot/3.0"})

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            print(f"[-] Telegram Send Attempt {attempt} Error: {e}")
            time.sleep(2)
    return None

# ================= STATE MANAGEMENT =================
def load_bot_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_update_id": 0,
        "last_tip_date": "",
        "last_news_date": "",
        "last_tool_date": "",
        "last_extension_date": ""
    }

def save_bot_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[-] Failed to save bot state: {e}")

# ================= 1. BUG BOUNTY PLAYBOOK TIPS =================
BUG_BOUNTY_TIPS = [
    {
        "title": "403 Forbidden Authorization Bypass via Headers",
        "trick": "Agar target website par `/admin` ya sensitive endpoint par `403 Forbidden` mile, toh ye headers inject karo:\n\n• `X-Forwarded-For: 127.0.0.1`\n• `X-Original-URL: /admin`\n• `X-Rewrite-URL: /admin`\n• `X-Custom-IP-Authorization: 127.0.0.1`\n\nWAFs internal loopback samajh kar allow kar dete hain!",
        "impact": "Authentication / Authorization Bypass (Critical P1)"
    },
    {
        "title": "IDOR Parameter Tampering with Numeric vs JSON",
        "trick": "Agar application `GET /api/user/101` block kar rahi hai, toh parameter type change karo:\n\n1. `GET /api/user?id=102`\n2. `POST /api/user` with JSON `{\"id\": [102]}`\n3. `GET /api/user/101.json`\n\nBackend type confusion se doosre user ka data khul jata hai!",
        "impact": "Insecure Direct Object Reference (P1/P2)"
    },
    {
        "title": "SSRF Cloud Metadata Exfiltration",
        "trick": "Agar target par PDF generator, URL preview, ya Webhook URL input mile, toh cloud metadata query test karo:\n\n• AWS: `http://169.254.169.254/latest/meta-data/iam/security-credentials/`\n• GCP: `http://metadata.google.internal/computeMetadata/v1/` (Header: `Metadata-Flavor: Google`)\n• DigitalOcean: `http://169.254.169.254/metadata/v1.json`",
        "impact": "Full Cloud Account Takeover (Critical P1)"
    },
    {
        "title": "CORS Misconfiguration Account Takeover",
        "trick": "Request me `Origin: https://evil.com` ya `Origin: null` bhej kar dekho.\nAgar response me ye headers aayein:\n\n`Access-Control-Allow-Origin: https://evil.com`\n`Access-Control-Allow-Credentials: true`\n\nToh victim ke private sessions aur dashboard data ko chura sakte ho!",
        "impact": "Cross-Origin Data Theft (Medium/High)"
    },
    {
        "title": "Hidden Sensitive Git/Env Exposure",
        "trick": "Subdomain recon ke baad ye sensitive endpoints automate karo:\n\n• `/.git/config` ya `/.git/HEAD`\n• `/.env`\n• `/swagger.json` ya `/v2/api-docs`\n• `/actuator/env` (Spring Boot Actuator)\n\nInse aksar live DB passwords aur AWS keys leak hoti hain!",
        "impact": "Sensitive Information Disclosure (P1/P2)"
    },
    {
        "title": "Open Redirect to OAuth Token Hijacking",
        "trick": "Agar kisi login portal me `redirect_uri=https://target.com/callback` ho, toh try karo:\n\n• `redirect_uri=https://target.com.evil.com`\n• `redirect_uri=https://target.com/callback@evil.com`\n• `redirect_uri=https://target.com/callback/..;/evil.com`\n\nVictim ka OAuth token sidha aapke controlled server par dump ho jata hai!",
        "impact": "One-Click Account Takeover (Critical P1)"
    }
]

def format_bug_bounty_tip(tip: dict):
    return (
        f"🎯 *DAILY BUG BOUNTY TIP OF THE DAY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Topic:* `{tip['title']}`\n\n"
        f"💡 *The Technique:*\n{tip['trick']}\n\n"
        f"⚡ *Potential Impact:* `{tip['impact']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Bug Bounty Playbook*"
    )

# ================= 2. HACKER BROWSER EXTENSIONS & TOOLS =================
HACKER_EXTENSIONS = [
    {
        "name": "HackTools (All-in-One Web Pentesting Extension)",
        "browser": "Chrome & Firefox",
        "desc": "Web pentesting ke liye one-click reverse shells, SQLi payloads, XSS polyglots, base64 encoder/decoder sab browser me provide karta hai.",
        "url": "https://github.com/LasCC/Hack-Tools"
    },
    {
        "name": "FoxyProxy Standard",
        "browser": "Chrome & Firefox",
        "desc": "Burp Suite, OWASP ZAP, aur Tor ke beech instant 1-click proxy switching ke liye duniya ka sabse zaroori pentesting add-on.",
        "url": "https://getfoxyproxy.org/"
    },
    {
        "name": "Wappalyzer / WhatRuns",
        "browser": "Chrome & Firefox",
        "desc": "Website par kaun sa CMS (WordPress, Joomla), Web Framework (React, Django), backend server (Nginx, Apache), aur programming language chal rahi hai, instant reveal karta hai.",
        "url": "https://www.wappalyzer.com/"
    },
    {
        "name": "Cookie-Editor",
        "browser": "Chrome & Firefox",
        "desc": "Session cookies ko manually edit, add, delete ya import/export karne ke liye best tool — Auth Bypass aur Session Hijacking testing me mandatory hai.",
        "url": "https://cookie-editor.cgagnier.ca/"
    },
    {
        "name": "DotGit (Exposed .git Finder)",
        "browser": "Chrome & Firefox",
        "desc": "Jab aap kisi website ko browse karte ho, yeh automatically check karta hai ki kya website par `/.git/` folder expose hai, aur source code download karne ka alert deta hai.",
        "url": "https://github.com/davtur19/DotGit"
    },
    {
        "name": "ModHeader (Modify HTTP Headers)",
        "browser": "Chrome & Firefox",
        "desc": "Browser se direct custom headers (jaise `X-Forwarded-For`, `Authorization: Bearer`, `Custom-Token`) inject karke request bhejne ke liye sabse fast extension.",
        "url": "https://modheader.com/"
    }
]

def format_extension_alert(ext: dict):
    return (
        f"🧩 *MUST-HAVE HACKER BROWSER EXTENSION*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Extension:* `{ext['name']}`\n"
        f"🌐 *Platform:* `{ext['browser']}`\n\n"
        f"📖 *Why Every Hacker Needs It:*\n{ext['desc']}\n\n"
        f"🔗 *Download & Install:*\n[{ext['url']}]({ext['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Web Pentest Arsenal*"
    )

# ================= 3. TRENDING HACKER TOOLS RADAR =================
def fetch_trending_hacker_tools(keyword="security"):
    query = urllib.parse.quote(f"topic:{keyword} stars:>400")
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page=3"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/vnd.github.v3+json"
    })
    tools = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                tools.append({
                    "name": item.get("full_name"),
                    "desc": item.get("description") or "No description provided.",
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count", 0),
                    "lang": item.get("language") or "General"
                })
    except Exception as e:
        print(f"[-] Trending Tools Fetch Error: {e}")
    return tools

def format_tool_alert(tool: dict):
    return (
        f"🛠️ *TRENDING HACKER TOOL RADAR*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Tool:* `{tool['name']}`\n"
        f"⭐ *Stars:* {tool['stars']} | 💻 *Language:* `{tool['lang']}`\n\n"
        f"📖 *What it does:*\n{tool['desc']}\n\n"
        f"🔗 *GitHub Repository:*\n[{tool['url']}]({tool['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Hacker Arsenal Radar*"
    )

# ================= 4. REAL-TIME MULTI-SOURCE CYBER NEWS =================
def fetch_multi_source_cyber_news():
    feeds = [
        {"source": "The Hacker News", "url": THN_RSS_URL},
        {"source": "SANS Internet Storm Center", "url": SANS_ISC_RSS_URL}
    ]
    all_news = []
    for f in feeds:
        try:
            req = urllib.request.Request(f["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                tree = ET.fromstring(resp.read())
                channel = tree.find("channel")
                if channel is not None:
                    for item in channel.findall("item")[:4]:
                        title = item.find("title").text if item.find("title") is not None else ""
                        link = item.find("link").text if item.find("link") is not None else ""
                        desc = item.find("description").text if item.find("description") is not None else ""
                        clean_desc = desc.split("<")[0].strip() if desc else ""
                        if title and link:
                            all_news.append({
                                "source": f["source"],
                                "title": title.strip(),
                                "link": link.strip(),
                                "desc": clean_desc[:280] + "..." if len(clean_desc) > 280 else clean_desc
                            })
        except Exception as e:
            print(f"[-] News Fetch Error ({f['source']}): {e}")
    return all_news

def format_news_alert(news_item: dict):
    ai_breakdown = generate_ai_threat_breakdown(news_item['title'], news_item['desc'], context=news_item['source'])
    ai_section = ""
    if ai_breakdown:
        ai_section = f"🧠 *Gemini Pro Threat Breakdown:*\n{ai_breakdown}\n\n"

    return (
        f"⚡ *REAL-TIME CYBER THREAT RADAR*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Source:* `{news_item['source']}`\n"
        f"🚨 *Headline:* {news_item['title']}\n\n"
        f"📝 *Summary:*\n{news_item['desc']}\n\n"
        f"{ai_section}"
        f"🔗 *Full Investigation:* [Read Official Source]({news_item['link']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Cyber Threat Radar*"
    )

def fetch_latest_nuclei_additions():
    """Fetches real-time newly published Nuclei templates from ProjectDiscovery."""
    templates = []
    try:
        req = urllib.request.Request(NUCLEI_ADDITIONS_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            lines = [l.strip() for l in resp.read().decode().splitlines() if l.strip()]
            for line in lines[-8:]:
                templates.append({
                    "path": line,
                    "url": f"https://github.com/projectdiscovery/nuclei-templates/blob/main/{line}",
                    "cmd": f"nuclei -t {line} -l targets.txt"
                })
    except Exception as e:
        print(f"[-] Nuclei Additions Fetch Error: {e}")
    return templates

def format_nuclei_new_template_alert(tmpl: dict):
    return (
        f"🎯 *NEW NUCLEI SCANNER TEMPLATE ADDED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Template:* `{tmpl['path']}`\n\n"
        f"⚡ *Instant Scan Command:*\n"
        f"`{tmpl['cmd']}`\n\n"
        f"🔗 *View YAML on GitHub:*\n"
        f"[{tmpl['path']}]({tmpl['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Top 1% Bug Hunter Automation*"
    )

# ================= 5. TOP 1% ELITE HACKER ARSENAL =================
def check_nuclei_template(cve_id: str):
    """Checks if ProjectDiscovery Nuclei Template exists for this CVE."""
    if not cve_id or not cve_id.startswith("CVE-"):
        return None
    try:
        parts = cve_id.split("-")
        year = parts[1]
        raw_url = f"https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/http/cves/{year}/{cve_id}.yaml"
        req = urllib.request.Request(raw_url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                return {
                    "template_url": f"https://github.com/projectdiscovery/nuclei-templates/blob/main/http/cves/{year}/{cve_id}.yaml",
                    "command": f"nuclei -t http/cves/{year}/{cve_id}.yaml -u https://target.com"
                }
    except Exception:
        pass
    return None

def find_patch_commit_diffs(cve_id: str):
    """Searches GitHub for developer fix / security patch commits."""
    query = urllib.parse.quote(f"{cve_id} fix OR patch")
    url = f"https://api.github.com/search/commits?q={query}&sort=committer-date&order=desc&per_page=2"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/vnd.github.cloak-preview+json"
    })
    diffs = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                diffs.append({
                    "msg": item.get("commit", {}).get("message", "").split("\n")[0][:80],
                    "url": item.get("html_url"),
                    "repo": item.get("repository", {}).get("full_name")
                })
    except Exception:
        pass
    return diffs

def fetch_ghsa_early_advisories():
    """Fetches Day-1 Zero-Days from GitHub Security Advisories before CISA KEV adds them."""
    req = urllib.request.Request(GHSA_API_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/vnd.github.v3+json"
    })
    advisories = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            for item in data:
                # Prioritize Critical and High
                sev = item.get("severity", "unknown").lower()
                cve = item.get("cve_id") or "Pending CVE"
                ghsa = item.get("ghsa_id")
                summary = item.get("summary") or "No summary provided."
                html_url = item.get("html_url")
                refs = item.get("references", [])
                
                # Extract commit diff if present in references
                patch_url = None
                for r in refs:
                    if "/commit/" in r or "/pull/" in r:
                        patch_url = r
                        break

                advisories.append({
                    "ghsa_id": ghsa,
                    "cve_id": cve,
                    "severity": sev.upper(),
                    "summary": summary,
                    "url": html_url,
                    "patch_url": patch_url
                })
    except Exception as e:
        print(f"[-] GHSA Fetch Error: {e}")
    return advisories

def format_ghsa_alert(adv: dict, nuclei_info: dict = None):
    # Sanitize markdown in summary to prevent Telegram 400 Bad Request
    clean_summary = adv['summary'].replace("_", "\\_").replace("*", "\\*").replace("[", "(").replace("]", ")").replace("`", "'")
    nuclei_text = ""
    if nuclei_info:
        nuclei_text = (
            f"\n🎯 *Ready-to-Scan Nuclei Template:*\n"
            f"🔗 [{nuclei_info['template_url']}]({nuclei_info['template_url']})\n"
            f"💻 `nuclei -t cves/ -u https://target.com`\n"
        )
    else:
        nuclei_text = "\n🎯 *Nuclei Template:* Community YAML in progress.\n"

    patch_text = ""
    if adv.get("patch_url"):
        patch_text = f"\n🔬 *Root-Cause Patch Diff Link:*\n🔗 {adv['patch_url']}\n"

    return (
        f"⚡ *DAY-1 ZERO-DAY PRE-DISCLOSURE RADAR (GHSA)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *ID:* `{adv['ghsa_id']}` | *CVE:* `{adv['cve_id']}`\n"
        f"🚨 *Severity:* `{adv['severity']}` (Pre-KEV Early Alert)\n\n"
        f"📖 *Vulnerability Summary:*\n{clean_summary}\n"
        f"{nuclei_text}"
        f"{patch_text}\n"
        f"🔗 *Full Security Advisory:*\n{adv['url']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Sandeep's Top 1% Hacker Radar*"
    )

# ================= 6. CISA KEV & CVE CORE =================
def fetch_cisa_kev():
    urls = [
        "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                with open(CISA_LOCAL_CACHE, "w", encoding="utf-8") as cf:
                    json.dump(data, cf)
                return data
        except Exception:
            pass

    if os.path.exists(CISA_LOCAL_CACHE):
        try:
            with open(CISA_LOCAL_CACHE, "r", encoding="utf-8") as cf:
                return json.load(cf)
        except Exception:
            pass
    return None

def find_github_pocs(cve_id: str):
    query = urllib.parse.quote(f"{cve_id} exploit")
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/3.0"})
    pocs = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                pocs.append({
                    "name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count", 0)
                })
    except Exception:
        pass
    return pocs

def fetch_epss_score(cve_id: str):
    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            epss_data = data.get("data", [])
            if epss_data:
                score = float(epss_data[0].get("epss", 0)) * 100
                percentile = float(epss_data[0].get("percentile", 0)) * 100
                return f"{score:.1f}% (Percentile: {percentile:.1f}%)"
    except Exception:
        pass
    return "Not Available"

def format_cve_alert(cve_item: dict, pocs: list, epss: str, nuclei_info: dict = None, patch_diffs: list = None):
    cve_id = cve_item.get("cveID", "Unknown")
    vendor = cve_item.get("vendorProject", "Unknown")
    product = cve_item.get("product", "Unknown")
    name = cve_item.get("vulnerabilityName", "Unknown")
    date_added = cve_item.get("dateAdded", "N/A")
    desc = cve_item.get("shortDescription", "No description provided.")
    action = cve_item.get("requiredAction", "Apply updates per vendor instructions.")
    due_date = cve_item.get("dueDate", "N/A")
    ransomware = cve_item.get("knownRansomwareCampaignUse", "Unknown")

    poc_text = ""
    if pocs:
        poc_text = "\n*🔥 Public GitHub PoC Exploits Found:*\n"
        for idx, p in enumerate(pocs, 1):
            poc_text += f"{idx}. [{p['name']}]({p['url']}) ⭐ {p['stars']}\n"
    else:
        poc_text = "\n*🔍 GitHub PoC:* No public exploit repo indexed yet.\n"

    nuclei_text = ""
    if nuclei_info:
        nuclei_text = (
            f"\n🎯 *Top 1% Scanner Template (Nuclei YAML):*\n"
            f"🔗 [{nuclei_info['template_url']}]({nuclei_info['template_url']})\n"
            f"💻 `{nuclei_info['command']}`\n"
        )

    patch_text = ""
    if patch_diffs:
        patch_text = "\n🔬 *Root-Cause Patch Commit Diffs:*\n"
        for idx, pd in enumerate(patch_diffs[:2], 1):
            patch_text += f"{idx}. [{pd['repo']}: {pd['msg']}]({pd['url']})\n"

    alert = (
        f"🚨 *NEW CISA EXPLOITED VULNERABILITY ALERT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *CVE ID:* `{cve_id}`\n"
        f"🏢 *Vendor & Product:* {vendor} — {product}\n"
        f"⚠️ *Vulnerability:* {name}\n"
        f"📅 *Date Added:* {date_added} | *Due:* {due_date}\n\n"
        f"📖 *Summary:*\n{desc}\n\n"
        f"📊 *Threat Intelligence Metrics:*\n"
        f"• *Ransomware Use:* `{ransomware}`\n"
        f"• *EPSS Exploit Likelihood:* `{epss}`\n"
        f"{poc_text}"
        f"{nuclei_text}"
        f"{patch_text}\n"
        f"🛠️ *Required Defensive Action:*\n{action}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Cyber Threat Intel Bot*"
    )
    return alert

# ================= 7. INTERACTIVE STUDENT COMMAND HANDLER =================
def process_interactive_commands():
    state = load_bot_state()
    offset = state.get("last_update_id", 0) + 1
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return

    updates = data.get("result", [])
    if not updates:
        return

    kev_data = fetch_cisa_kev()
    vulns = kev_data.get("vulnerabilities", []) if kev_data else []

    for u in updates:
        up_id = u.get("update_id", 0)
        state["last_update_id"] = max(state.get("last_update_id", 0), up_id)

        msg = u.get("message", {})
        text = msg.get("text", "").strip()
        chat_id = msg.get("chat", {}).get("id")
        msg_id = msg.get("message_id")

        if not text or not chat_id:
            continue

        cmd = text.split()[0].lower()
        args = text[len(cmd):].strip()

        if cmd in ["/help", "/start", "/menu"]:
            help_text = (
                f"🤖 *Cyber Threat Intel Bot — Elite Command Menu*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Hi {msg.get('from', {}).get('first_name', 'Hacker')}! You can query me using these commands:\n\n"
                f"🧠 `/ask <question>` — Ask Gemini Pro any hacking, bug bounty, or exploit doubt!\n"
                f"📌 `/cve <keyword>` — Search latest exploited CVEs (e.g. `/cve windows` or `/cve apple`)\n"
                f"⚡ `/0day` — Day-1 Pre-Disclosure Advisories (GHSA Zero-Days)\n"
                f"🎯 `/nuclei <cve>` — Check ready-made Nuclei scanner template\n"
                f"🛠️ `/tool <keyword>` — Discover top trending hacker tools (e.g. `/tool osint`)\n"
                f"🧩 `/extension` — Get today's top hacker browser extension\n"
                f"🎯 `/tip` — Get today's 1-Minute Bug Bounty Trick\n"
                f"⚡ `/news` — Breaking corporate & cyber news stream\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 *Engineered by Sandeep Yadav (@realsandeep1271-ui)*"
            )
            send_telegram_message(help_text, chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/ask", "/ai", "/mentor"]:
            query = args.strip()
            if not query:
                reply = "❓ *Usage:* `/ask <aapka doubt>`\n_Example:_ `/ask CORS misconfiguration se account takeover kaise karein?`"
            else:
                ai_answer = ask_gemini_pro(
                    query,
                    system_instruction="You are an elite offensive security mentor and top 1% bug bounty hunter. Answer clearly, accurately, and practically in Hinglish/English with code/command snippets where applicable."
                )
                if ai_answer:
                    reply = f"🤖 *Gemini Pro Cyber Mentor:*\n\n{ai_answer}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🛡️ *AI Threat Intel Engine*"
                else:
                    reply = "⚠️ *Gemini Pro AI:* Key initializing. Please ensure `GEMINI_API_KEY` is added to GitHub Secrets!"
            send_telegram_message(reply, chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/0day":
            advs = fetch_ghsa_early_advisories()
            if advs:
                send_telegram_message(format_ghsa_alert(advs[0]), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message("🔍 No new Day-1 advisories at this moment.", chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/nuclei":
            cve_target = args.upper().strip() if args else "CVE-2026-0545"
            n_info = check_nuclei_template(cve_target)
            if n_info:
                reply = (
                    f"🎯 *Nuclei Template Found for {cve_target}:*\n"
                    f"🔗 [{n_info['template_url']}]({n_info['template_url']})\n\n"
                    f"💻 *Run Command:*\n`{n_info['command']}`"
                )
            else:
                reply = f"🔍 No official Nuclei YAML template indexed yet for `{cve_target}`."
            send_telegram_message(reply, chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/tip", "/bounty"]:
            idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
            tip = BUG_BOUNTY_TIPS[idx]
            send_telegram_message(format_bug_bounty_tip(tip), chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/extension", "/ext"]:
            idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
            ext = HACKER_EXTENSIONS[idx]
            send_telegram_message(format_extension_alert(ext), chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/news":
            news = fetch_multi_source_cyber_news()
            if news:
                send_telegram_message(format_news_alert(news[0]), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message("⚠️ No news updates right now.", chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/tool":
            search_term = args if args else "security"
            tools = fetch_trending_hacker_tools(search_term)
            if tools:
                send_telegram_message(format_tool_alert(tools[0]), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message(f"🔍 No trending tools found for `{search_term}`.", chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/cve":
            query = args.lower() if args else "2026"
            matched = [v for v in vulns if query in v.get("cveID", "").lower() or query in v.get("vendorProject", "").lower() or query in v.get("product", "").lower()]
            matched.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
            if matched:
                item = matched[0]
                cve_id = item.get("cveID")
                pocs = find_github_pocs(cve_id)
                epss = fetch_epss_score(cve_id)
                nuclei_info = check_nuclei_template(cve_id)
                patch_diffs = find_patch_commit_diffs(cve_id)
                send_telegram_message(format_cve_alert(item, pocs, epss, nuclei_info, patch_diffs), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message(f"🔍 No CISA exploited CVE found matching `{query}`.", chat_id=chat_id, reply_to_id=msg_id)

    save_bot_state(state)

# ================= MULTI-TRACK DAILY DISPATCH ENGINE =================
def run_sync(test_mode=False):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    state = load_bot_state()

    print("[*] Processing interactive student commands...")
    process_interactive_commands()

    # 1. TRACK: REAL-TIME CISA CVE RADAR (WITH NUCLEI & PATCH DIFF ENRICHMENT)
    print("[*] Checking CISA KEV Exploited Vulnerabilities...")
    kev_data = fetch_cisa_kev()
    if kev_data and "vulnerabilities" in kev_data:
        vulns = kev_data["vulnerabilities"]
        all_cve_ids = [v["cveID"] for v in vulns if "cveID" in v]

        seen_ids = set()
        if os.path.exists(SEEN_FILE):
            try:
                with open(SEEN_FILE, "r", encoding="utf-8") as f:
                    seen_ids = set(json.load(f))
            except Exception:
                seen_ids = set()

        if not seen_ids and not test_mode:
            print(f"[*] First run: Storing {len(all_cve_ids)} existing CVEs as baseline...")
            with open(SEEN_FILE, "w", encoding="utf-8") as f:
                json.dump(all_cve_ids, f)
            send_telegram_message("✅ *24/7 Top 1% Threat Intel Engine Active!* Baseline established.")
            return

        if test_mode:
            cves_2026 = [v for v in vulns if "CVE-2026-" in v.get("cveID", "")]
            cves_2026.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
            new_cves = [cves_2026[0]] if cves_2026 else [vulns[-1]]
        else:
            new_cves = [v for v in vulns if v.get("cveID") and v["cveID"] not in seen_ids]
            new_cves.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)

        if new_cves:
            print(f"[!] Broadcasting {len(new_cves)} new CVE alert(s)...")
            for item in new_cves[:2]:
                cve_id = item.get("cveID")
                pocs = find_github_pocs(cve_id)
                epss = fetch_epss_score(cve_id)
                nuclei_info = check_nuclei_template(cve_id)
                patch_diffs = find_patch_commit_diffs(cve_id)
                alert_msg = format_cve_alert(item, pocs, epss, nuclei_info, patch_diffs)
                res = send_telegram_message(alert_msg)
                if not test_mode and res:
                    seen_ids.add(cve_id)

            if not test_mode:
                with open(SEEN_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_ids), f)
                print("[+] Updated seen_cves.json successfully.")
        else:
            print("[+] No new CVEs detected right now.")

    # 2. TRACK: DAY-1 EARLY WARNING (GHSA ZERO-DAYS)
    seen_ghsa = set()
    if os.path.exists(SEEN_GHSA_FILE):
        try:
            with open(SEEN_GHSA_FILE, "r", encoding="utf-8") as f:
                seen_ghsa = set(json.load(f))
        except Exception:
            seen_ghsa = set()

    print("[*] Checking GitHub Security Advisories (Day-1 0-Days)...")
    advs = fetch_ghsa_early_advisories()
    new_advs = [a for a in advs if a["ghsa_id"] not in seen_ghsa and a["severity"] in ["CRITICAL", "HIGH"]]
    if new_advs:
        print(f"[!] Broadcasting {len(new_advs)} new GHSA Day-1 Zero-Day(s)...")
        for a in new_advs[:2]:
            n_info = check_nuclei_template(a.get("cve_id"))
            res = send_telegram_message(format_ghsa_alert(a, n_info))
            if res:
                seen_ghsa.add(a["ghsa_id"])
        with open(SEEN_GHSA_FILE, "w", encoding="utf-8") as gf:
            json.dump(list(seen_ghsa), gf)

    # 3. TRACK: DAILY BUG BOUNTY TRICK (Guaranteed Daily Drop)
    if state.get("last_tip_date") != today_str:
        print("[*] Broadcasting Daily Bug Bounty Trick...")
        idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
        tip = BUG_BOUNTY_TIPS[idx]
        res = send_telegram_message(format_bug_bounty_tip(tip))
        if res:
            state["last_tip_date"] = today_str
            save_bot_state(state)
            print("[+] Daily Bug Bounty trick sent!")
        else:
            print("[-] Daily Bug Bounty trick failed to send (will retry next cycle).")

    # 4. TRACK: DAILY HACKER BROWSER EXTENSION
    if state.get("last_extension_date") != today_str:
        print("[*] Broadcasting Daily Hacker Browser Extension...")
        idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
        ext = HACKER_EXTENSIONS[idx]
        res = send_telegram_message(format_extension_alert(ext))
        if res:
            state["last_extension_date"] = today_str
            save_bot_state(state)
            print("[+] Daily Hacker Extension sent!")
        else:
            print("[-] Daily Hacker Extension failed to send (will retry next cycle).")

    # 5. TRACK: REAL-TIME CONTINUOUS CYBER THREAT RADAR (THN + SANS ISC)
    seen_news = set()
    if os.path.exists(SEEN_NEWS_FILE):
        try:
            with open(SEEN_NEWS_FILE, "r", encoding="utf-8") as nf:
                seen_news = set(json.load(nf))
        except Exception:
            seen_news = set()

    print("[*] Checking Real-Time Cyber News Feeds (THN & SANS ISC)...")
    all_news = fetch_multi_source_cyber_news()
    new_news = [n for n in all_news if n["link"] not in seen_news]
    if new_news:
        print(f"[!] Broadcasting {len(new_news)} new Breaking Cyber News story/stories...")
        for item in new_news[:2]:
            res = send_telegram_message(format_news_alert(item))
            if res:
                seen_news.add(item["link"])
        with open(SEEN_NEWS_FILE, "w", encoding="utf-8") as nf:
            json.dump(list(seen_news), nf)
        print("[+] Updated seen_news.json successfully.")
    else:
        print("[+] No new Cyber News stories right now.")

    # 6. TRACK: PROJECTDISCOVERY NUCLEI TEMPLATE ADDITIONS RADAR
    seen_nuclei = set()
    if os.path.exists(SEEN_NUCLEI_FILE):
        try:
            with open(SEEN_NUCLEI_FILE, "r", encoding="utf-8") as nuc_f:
                seen_nuclei = set(json.load(nuc_f))
        except Exception:
            seen_nuclei = set()

    print("[*] Checking ProjectDiscovery Nuclei Template Additions...")
    n_additions = fetch_latest_nuclei_additions()
    new_n_additions = [t for t in n_additions if t["path"] not in seen_nuclei]
    if new_n_additions:
        print(f"[!] Broadcasting {len(new_n_additions)} new Nuclei Template(s)...")
        for tmpl in new_n_additions[:2]:
            res = send_telegram_message(format_nuclei_new_template_alert(tmpl))
            if res:
                seen_nuclei.add(tmpl["path"])
        with open(SEEN_NUCLEI_FILE, "w", encoding="utf-8") as nuc_f:
            json.dump(list(seen_nuclei), nuc_f)
        print("[+] Updated seen_nuclei.json successfully.")
    else:
        print("[+] No new Nuclei templates added right now.")

if __name__ == "__main__":
    if "--0day" in sys.argv:
        advs = fetch_ghsa_early_advisories()
        if advs:
            n_info = check_nuclei_template(advs[0].get("cve_id"))
            send_telegram_message(format_ghsa_alert(advs[0], n_info))
            print("[+] Sent GHSA 0-Day Alert")
        sys.exit(0)

    if "--nuclei" in sys.argv:
        n_info = check_nuclei_template("CVE-2026-0545")
        if n_info:
            reply = f"🎯 *Nuclei Scanner Template:*\n`{n_info['command']}`\n🔗 {n_info['template_url']}"
            send_telegram_message(reply)
            print("[+] Sent Nuclei Alert")
        sys.exit(0)

    if "--extension" in sys.argv:
        idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
        send_telegram_message(format_extension_alert(HACKER_EXTENSIONS[idx]))
        print("[+] Sent Extension Alert")
        sys.exit(0)

    if "--tip" in sys.argv:
        idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
        send_telegram_message(format_bug_bounty_tip(BUG_BOUNTY_TIPS[idx]))
        print("[+] Sent Bug Bounty Tip")
        sys.exit(0)

    if "--news" in sys.argv:
        news = fetch_latest_cyber_news()
        if news:
            send_telegram_message(format_news_alert(news[0]))
            print("[+] Sent Cyber News")
        sys.exit(0)

    is_test = "--test" in sys.argv
    run_sync(test_mode=is_test)
