import os
import json
import urllib.request
import urllib.parse
import sys
import datetime
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

# ================= CONFIGURATION =================
# Secrets and Chat IDs are loaded securely from Environment Variables / GitHub Secrets
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8786341409:AAFS1fCRC8uoeK6FhD7-pqLqoHIlVwSs5GY").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004315340178").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

CISA_KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
THN_RSS_URL = "https://feeds.feedburner.com/TheHackersNews"
SANS_ISC_RSS_URL = "https://isc.sans.edu/rssfeed.xml"
GHSA_API_URL = "https://api.github.com/advisories?per_page=15&sort=published&direction=desc"
NUCLEI_ADDITIONS_URL = "https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/main/.new-additions"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_cves.json")
SEEN_GHSA_FILE = os.path.join(BASE_DIR, "seen_ghsa.json")
SEEN_NEWS_FILE = os.path.join(BASE_DIR, "seen_news.json")
SEEN_NUCLEI_FILE = os.path.join(BASE_DIR, "seen_nuclei.json")
SEEN_BOUNTIES_FILE = os.path.join(BASE_DIR, "seen_bounties.json")
SEEN_PROGRAMS_FILE = os.path.join(BASE_DIR, "seen_programs.json")
H1_REPORTS_CSV_URL = "https://raw.githubusercontent.com/reddelexc/hackerone-reports/master/data.csv"
CHAOS_PROGRAMS_URL = "https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/dist/data.json"
BUGCROWD_DATA_URL = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/master/data/bugcrowd_data.json"
CISA_LOCAL_CACHE = os.path.join(BASE_DIR, "cisa_kev_cache.json")
STATE_FILE = os.path.join(BASE_DIR, "bot_state.json")

# ================= GEMINI PRO AI ENGINE =================
def ask_gemini_pro(prompt: str, system_instruction: str = None) -> str:
    """Queries Google Gemini Pro/Flash API for deep exploit reasoning and Q&A."""
    key = os.getenv("GEMINI_API_KEY", "").strip() or GEMINI_API_KEY
    if not key:
        return ""

    for model_name in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro", "gemini-pro-latest", "gemini-1.5-flash", "gemini-2.0-flash"]:
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
        "• ⚡ Attack Mechanics: (vulnerable parameter, flow, or logic flaw)\n"
        "• 🛡️ Safe Verification & Audit: (safe defensive curl or version check, e.g. curl -s -I / target version check, or patch mitigation)\n"
        "Write in crisp Hinglish/English. Keep under 75 words. Strictly defensive and educational. No boilerplate."
    )
    user_prompt = f"Threat Title: {title}\nSummary: {summary}\nContext: {context}"
    return ask_gemini_pro(user_prompt, sys_prompt)

# ================= TELEGRAM API HELPERS =================
def send_telegram_message(message, chat_id: str = None, reply_to_id: int = None, reply_markup: dict = None):
    """Sends a formatted markdown message to Telegram with auto-retry and inline button support."""
    import time
    if isinstance(message, (tuple, list)):
        if len(message) > 1 and reply_markup is None:
            reply_markup = message[1]
        message = message[0]

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
    if reply_markup:
        payload["reply_markup"] = reply_markup

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "CyberIntelBot/3.0"})

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            print(f"[-] Telegram Send Attempt {attempt} Error: {e}")
            # If markdown parse failed (HTTP 400), fallback to plain text so message is never lost!
            if "400" in str(e) and "parse_mode" in payload:
                del payload["parse_mode"]
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "CyberIntelBot/3.0"})
            time.sleep(2)
    return None

# ================= STATE MANAGEMENT =================
def load_bot_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                if "last_broadcast_time" not in state:
                    state["last_broadcast_time"] = 0
                return state
        except Exception:
            pass
    return {
        "last_update_id": 0,
        "last_broadcast_time": 0,
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
    msg = (
        f"🎯 *DAILY BUG BOUNTY TIP OF THE DAY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Topic:* `{tip['title']}`\n\n"
        f"💡 *The Technique:*\n{tip['trick']}\n\n"
        f"⚡ *Potential Impact:* `{tip['impact']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *ThreatPulse-AI Bug Bounty Playbook*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🧠 Ask AI Mentor About This", "url": "https://t.me/sandeep_cve_alert_bot"}]
        ]
    }
    return msg, markup

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
    msg = (
        f"🧩 *MUST-HAVE HACKER BROWSER EXTENSION*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Extension:* `{ext['name']}`\n"
        f"🌐 *Platform:* `{ext['browser']}`\n\n"
        f"📖 *Why Every Hacker Needs It:*\n{ext['desc']}\n\n"
        f"🔗 *Download & Install:*\n[{ext['url']}]({ext['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *ThreatPulse-AI Web Pentest Arsenal*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": f"🧩 Install {ext['name'][:22]}", "url": ext["url"]}]
        ]
    }
    return msg, markup

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
    msg = (
        f"🛠️ *TRENDING HACKER TOOL RADAR*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Tool:* `{tool['name']}`\n"
        f"⭐ *Stars:* {tool['stars']} | 💻 *Language:* `{tool['lang']}`\n\n"
        f"📖 *What it does:*\n{tool['desc']}\n\n"
        f"🔗 *GitHub Repository:*\n[{tool['url']}]({tool['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *ThreatPulse-AI Hacker Arsenal*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "⭐ GitHub Repo", "url": tool["url"]}]
        ]
    }
    return msg, markup

# ================= 4. REAL-TIME MULTI-SOURCE CYBER NEWS (PURZA 1) =================
def fetch_multi_source_cyber_news():
    feeds = [
        {"source": "The Hacker News", "url": THN_RSS_URL},
        {"source": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/"},
        {"source": "SANS Internet Storm Center", "url": SANS_ISC_RSS_URL},
        {"source": "SecurityAffairs (CTI)", "url": "https://securityaffairs.com/feed"},
        {"source": "KrebsOnSecurity", "url": "https://krebsonsecurity.com/feed/"},
        {"source": "Cisco Talos Intelligence", "url": "https://blog.talosintelligence.com/rss/"}
    ]
    all_news = []
    for f in feeds:
        try:
            req = urllib.request.Request(f["url"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
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

    msg = (
        f"⚡ *REAL-TIME CYBER THREAT RADAR*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Source:* `{news_item['source']}`\n"
        f"🚨 *Headline:* {news_item['title']}\n\n"
        f"📝 *Summary:*\n{news_item['desc']}\n\n"
        f"{ai_section}"
        f"🔗 *Full Investigation:* [Read Official Source]({news_item['link']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *ThreatPulse-AI Threat Radar*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": f"📖 Read Full on {news_item['source'][:18]}", "url": news_item["link"]}],
            [{"text": "🧠 Ask AI Mentor", "url": "https://t.me/sandeep_cve_alert_bot"}]
        ]
    }
    return msg, markup

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
    msg = (
        f"🎯 *NEW NUCLEI SCANNER TEMPLATE ADDED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Template:* `{tmpl['path']}`\n\n"
        f"⚡ *Instant Scan Command:*\n"
        f"`{tmpl['cmd']}`\n\n"
        f"🔗 *View YAML on GitHub:*\n"
        f"[{tmpl['path']}]({tmpl['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *ThreatPulse-AI Automation*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🔥 View Template YAML", "url": tmpl["url"]}]
        ]
    }
    return msg, markup

# ================= 4B. HACKERONE DISCLOSED BOUNTIES & BUGCROWD RADAR (PURZA 4) =================
def fetch_hackerone_disclosed_bounties():
    """Fetches recently disclosed paid bounty reports from HackerOne using fast range request."""
    import csv, io
    reports = []
    req = urllib.request.Request(
        H1_REPORTS_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-35000"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read().decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                if not row:
                    continue
                link = (row.get("link") or "").strip()
                bounty_str = (row.get("bounty") or "0").strip()
                try:
                    bounty_val = float(bounty_str)
                except ValueError:
                    bounty_val = 0.0

                if link and bounty_val > 0:
                    reports.append({
                        "program": (row.get("program") or "Unknown").strip(),
                        "title": (row.get("title") or "No Title").strip(),
                        "link": f"https://{link}" if not link.startswith("http") else link,
                        "bounty": bounty_val,
                        "vuln_type": (row.get("vuln_type") or "Security Vulnerability").strip()
                    })
    except Exception as e:
        print(f"[-] Disclosed Bounties Fetch Error: {e}")
    return reports

def format_bounty_report_alert(report: dict):
    bounty_usd = f"${report['bounty']:,.0f}"
    bounty_inr = f"₹{int(report['bounty'] * 85):,}"
    ai_breakdown = generate_ai_threat_breakdown(report['title'], f"Paid {bounty_usd} on {report['program']}", context="Bug Bounty Disclosed Writeup")
    ai_block = ""
    if ai_breakdown:
        ai_block = f"🧠 *Gemini Pro Bounty Analysis:*\n{ai_breakdown}\n\n"

    msg = (
        f"💰 *HACKERONE DISCLOSED BOUNTY PAYOUT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 *Target Company:* `{report['program']}`\n"
        f"💵 *Bounty Paid:* `{bounty_usd}` *(~{bounty_inr})*\n"
        f"⚠️ *Bug Class:* `{report['vuln_type']}`\n\n"
        f"📝 *Disclosed Report:* {report['title']}\n\n"
        f"{ai_block}"
        f"🔗 *Read Full Disclosed Report & POC:*\n[{report['link']}]({report['link']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Cyber Threat Intelligence*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "💵 View Disclosed Report & PoC", "url": report["link"]}]
        ]
    }
    return msg, markup

def fetch_latest_bounty_programs():
    """Fetches public bug bounty programs from Bugcrowd (live scraper feed) and HackerOne."""
    programs = []

    # 1. LIVE BUGCROWD PROGRAMS FEED (Updated every 30 mins)
    try:
        req_bc = urllib.request.Request(BUGCROWD_DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_bc, timeout=15) as r:
            bc_data = json.loads(r.read().decode("utf-8"))
            for p in bc_data:
                p_url = p.get("url", "")
                if not p_url:
                    continue
                max_pay = p.get("max_payout") or 0
                targets = p.get("targets", {}).get("in_scope", [])
                programs.append({
                    "name": p.get("name", "Bugcrowd Program").strip(),
                    "url": p_url,
                    "platform": "Bugcrowd",
                    "bounty": bool(max_pay > 0),
                    "max_payout": max_pay,
                    "safe_harbor": p.get("safe_harbor", "standard"),
                    "domains_count": len(targets)
                })
    except Exception as e:
        print(f"[-] Bugcrowd Live Feed Error: {e}")

    # 2. HACKERONE PROGRAMS FEED (Chaos / Public Bounties)
    try:
        req_h1 = urllib.request.Request(CHAOS_PROGRAMS_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_h1, timeout=12) as r:
            chaos_data = json.loads(r.read().decode())
            for p in chaos_data.get("programs", []):
                url = p.get("url", "")
                if "hackerone.com" in url:
                    programs.append({
                        "name": p.get("name"),
                        "url": url,
                        "platform": "HackerOne",
                        "bounty": p.get("bounty", False),
                        "max_payout": 0,
                        "safe_harbor": "standard",
                        "domains_count": len(p.get("domains", []))
                    })
    except Exception as e:
        print(f"[-] HackerOne Programs Fetch Error: {e}")

    return programs

def format_bounty_program_alert(prog: dict):
    max_pay = prog.get("max_payout", 0)
    if max_pay and max_pay > 0:
        reward = f"Cash Bounties up to ${max_pay:,.0f} (~₹{int(max_pay * 85):,})"
    elif prog.get("bounty"):
        reward = "Cash Bounties ($$$)"
    else:
        reward = "Hall of Fame / Swag (VDP)"

    safe_h = str(prog.get("safe_harbor", "standard")).capitalize()
    targets_label = "targets" if prog["platform"] == "Bugcrowd" else "domains"

    msg = (
        f"🎯 *NEW BUG BOUNTY PROGRAM LAUNCHED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 *Company:* `{prog['name']}`\n"
        f"🌐 *Platform:* `{prog['platform']}`\n"
        f"💵 *Bounty Rewards:* `{reward}`\n"
        f"🛡️ *Safe Harbor:* `{safe_h}`\n"
        f"🎯 *In-Scope Target Assets:* `{prog['domains_count']} {targets_label}`\n\n"
        f"🔗 *Official Program Scope & Rules:*\n[{prog['url']}]({prog['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Cyber Threat Intelligence*"
    )
    btn_text = f"🎯 View {prog['platform']} Scope & Rules"
    markup = {
        "inline_keyboard": [
            [{"text": btn_text, "url": prog["url"]}]
        ]
    }
    return msg, markup

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
            f"💻 `nuclei -t cves/ -u https://target.com`\n"
        )
    else:
        nuclei_text = "\n🎯 *Nuclei Template:* Community YAML in progress.\n"

    patch_text = ""
    if adv.get("patch_url"):
        patch_text = f"\n🔬 *Root-Cause Patch Diff Link:*\n🔗 {adv['patch_url']}\n"

    ai_breakdown = generate_ai_threat_breakdown(f"{adv['ghsa_id']} ({adv['cve_id']})", clean_summary, context="GHSA 0-Day Advisory")
    ai_block = ""
    if ai_breakdown:
        ai_block = f"\n🧠 *Gemini Pro Zero-Day Analysis:*\n{ai_breakdown}\n"

    msg = (
        f"⚡ *DAY-1 ZERO-DAY PRE-DISCLOSURE RADAR (GHSA)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *ID:* `{adv['ghsa_id']}` | *CVE:* `{adv['cve_id']}`\n"
        f"🚨 *Severity:* `{adv['severity']}` (Pre-KEV Early Alert)\n\n"
        f"📖 *Vulnerability Summary:*\n{clean_summary}\n"
        f"{ai_block}"
        f"{nuclei_text}"
        f"{patch_text}\n"
        f"🔗 *Full Security Advisory:*\n{adv['url']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *ThreatPulse-AI Day-1 Radar*"
    )

    buttons = []
    row1 = [{"text": "⚡ GHSA Advisory", "url": adv["url"]}]
    if adv.get("patch_url"):
        row1.append({"text": "🔬 Root Patch Diff", "url": adv["patch_url"]})
    buttons.append(row1)

    if nuclei_info:
        buttons.append([{"text": "🎯 Scan Nuclei", "url": nuclei_info["template_url"]}])

    return msg, {"inline_keyboard": buttons}

# ================= 6. CISA KEV & CVE CORE (PURZA 2 & PURZA 3) =================
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

def analyze_poc_safety(poc: dict) -> dict:
    """
    Purza 2: Exploit Radar Honeypot Scanner
    Inspects GitHub PoC repo name, description, and metadata for malware honeypots.
    """
    desc = (poc.get("desc") or "").lower()
    name = (poc.get("name") or "").lower()
    honeypot_triggers = [
        ".exe", ".zip", "password:", "archive.zip", "telegram.me",
        "keylogger", "stealer", "token grabber", "discord.gg", "mediafire", "mega.nz"
    ]
    is_suspicious = any(term in desc or term in name for term in honeypot_triggers)
    if is_suspicious:
        return {
            "status": "🚨 MALWARE HONEYPOT RISK",
            "warning": "Suspicious binary/archive payload indicated. Do NOT execute on host system!",
            "is_safe": False
        }
    return {
        "status": "🛡️ COMMUNITY POC (SANDBOX RECOMMENDED)",
        "warning": "Standard source repo. Always verify in an isolated VM.",
        "is_safe": True
    }

def find_github_pocs(cve_id: str):
    query = urllib.parse.quote(f"{cve_id} exploit")
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/3.0"})
    pocs = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                poc_obj = {
                    "name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count", 0),
                    "desc": item.get("description") or ""
                }
                poc_obj["safety"] = analyze_poc_safety(poc_obj)
                pocs.append(poc_obj)
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
        poc_text = "\n*🔥 Public GitHub PoC Exploits & Safety Radar:*\n"
        for idx, p in enumerate(pocs, 1):
            safety_label = p.get("safety", {}).get("status", "🛡️ COMMUNITY POC")
            poc_text += f"{idx}. [{p['name']}]({p['url']}) ⭐ {p['stars']}\n   ↳ {safety_label}\n"
    else:
        poc_text = "\n*🔍 GitHub PoC:* No public exploit repo indexed yet.\n"

    nuclei_text = ""
    if nuclei_info:
        nuclei_text = (
            f"\n🎯 *Top 1% Scanner Template (Nuclei YAML):*\n"
            f"💻 `{nuclei_info['command']}`\n"
        )

    patch_text = ""
    if patch_diffs:
        patch_text = "\n🔬 *Root-Cause Patch Commit Diffs:*\n"
        for idx, pd in enumerate(patch_diffs[:2], 1):
            patch_text += f"{idx}. [{pd['repo']}: {pd['msg']}]({pd['url']})\n"

    # AI breakdown with safe verification & audit command
    ai_breakdown = generate_ai_threat_breakdown(f"{cve_id} - {name}", desc, context=f"{vendor} {product}")
    ai_block = ""
    if ai_breakdown:
        ai_block = f"\n🧠 *Gemini Pro Vulnerability Intelligence:*\n{ai_breakdown}\n"

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
        f"{ai_block}"
        f"{poc_text}"
        f"{nuclei_text}"
        f"{patch_text}\n"
        f"🛠️ *Required Defensive Action:*\n{action}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *ThreatPulse-AI Intelligence Engine*"
    )

    buttons = []
    row1 = []
    if nuclei_info:
        row1.append({"text": "🎯 Scan Nuclei", "url": nuclei_info["template_url"]})
    if patch_diffs:
        row1.append({"text": "🔬 View Patch", "url": patch_diffs[0]["url"]})
    if row1:
        buttons.append(row1)

    row2 = [{"text": "📖 Official NVD", "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"}]
    if pocs:
        row2.append({"text": "🔥 Top PoC Repo", "url": pocs[0]["url"]})
    buttons.append(row2)

    return alert, {"inline_keyboard": buttons}

# ================= 7. INTERACTIVE STUDENT COMMAND HANDLER =================
def process_interactive_commands():
    if not TELEGRAM_BOT_TOKEN:
        return
    state = load_bot_state()
    offset = state.get("last_update_id", 0) + 1
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=0"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return

    updates = data.get("result", [])
    if not updates:
        return

    for u in updates:
        up_id = u.get("update_id", 0)
        state["last_update_id"] = max(state.get("last_update_id", 0), up_id)

        msg = u.get("message", {})
        text = msg.get("text", "").strip()
        chat_id = msg.get("chat", {}).get("id")
        msg_id = msg.get("message_id")

        if not text or not chat_id:
            continue

        cmd = text.split()[0].lower().split("@")[0]
        args = text[len(text.split()[0]):].strip()

        if cmd in ["/help", "/start", "/menu"]:
            help_text = (
                f"🤖 *ThreatPulse-AI — Elite Cyber Intel & Bug Bounty Menu*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Hi {msg.get('from', {}).get('first_name', 'Hacker')}! You can query me using these commands:\n\n"
                f"🧠 `/ask <question>` — Ask Gemini Pro any hacking, bug bounty, or exploit doubt!\n"
                f"💰 `/bounty` — Latest HackerOne disclosed bounty payout & writeup\n"
                f"🎯 `/program <keyword>` — Search HackerOne/Bugcrowd bounty programs\n"
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
            menu_markup = {
                "inline_keyboard": [
                    [{"text": "🚀 ThreatPulse-AI GitHub", "url": "https://github.com/realsandeep1271-ui/ThreatPulse-AI"}]
                ]
            }
            send_telegram_message(help_text, chat_id=chat_id, reply_to_id=msg_id, reply_markup=menu_markup)

        elif cmd in ["/bounty", "/payout", "/disclosed"]:
            bounties = fetch_hackerone_disclosed_bounties()
            if bounties:
                send_telegram_message(format_bounty_report_alert(bounties[0]), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message("🔍 No disclosed bounty reports found right now.", chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/program", "/target", "/scope", "/bugcrowd"]:
            keyword = args.lower().strip()
            programs = fetch_latest_bounty_programs()
            if cmd == "/bugcrowd" and not keyword:
                keyword = "bugcrowd"
            if keyword:
                matched = [p for p in programs if keyword in p['name'].lower() or keyword in p['url'].lower()]
            else:
                matched = programs[:3]

            if matched:
                send_telegram_message(format_bounty_program_alert(matched[0]), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message(f"🔍 No bug bounty program found matching `{keyword}`.", chat_id=chat_id, reply_to_id=msg_id)

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
            kev_data = fetch_cisa_kev()
            vulns = kev_data.get("vulnerabilities", []) if kev_data else []
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

# ================= 8. PACED RATE-LIMITING DISPATCH ENGINE (PURZA 5) =================
# Enforces exact 30-minute pacing (1 msg / 30 min) to permanently eliminate alert fatigue
DISPATCH_INTERVAL_SECONDS = 1800  # 30 Minutes

def run_sync(test_mode=False, force=False):
    import time
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    state = load_bot_state()

    print("[*] Processing interactive student commands (instant execution)...")
    process_interactive_commands()

    # Rate Limiting & Pacing Check: Prevent message dumping (Harsh bhai feedback)
    last_broadcast = state.get("last_broadcast_time", 0)
    time_since_last = time.time() - last_broadcast

    if not test_mode and not force and time_since_last < DISPATCH_INTERVAL_SECONDS:
        rem_min = int((DISPATCH_INTERVAL_SECONDS - time_since_last) / 60)
        print(f"[*] Dispatcher Paced: Last broadcast was {int(time_since_last/60)}m ago. Next broadcast eligible in ~{rem_min}m. (Alert fatigue prevention: 1 msg / 30 min)")
        return

    candidates = []

    # 1. TRACK: DAY-1 GHSA ZERO-DAYS (Priority 100)
    seen_ghsa = set()
    if os.path.exists(SEEN_GHSA_FILE):
        try:
            with open(SEEN_GHSA_FILE, "r", encoding="utf-8") as gf:
                seen_ghsa = set(json.load(gf))
        except Exception:
            seen_ghsa = set()

    advs = fetch_ghsa_early_advisories()
    new_advs = [a for a in advs if a["ghsa_id"] not in seen_ghsa and a["severity"] in ["CRITICAL", "HIGH"]]
    for a in new_advs:
        def make_ghsa_entry(adv_item):
            def cb():
                seen_ghsa.add(adv_item["ghsa_id"])
                with open(SEEN_GHSA_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_ghsa), f)
            def fmt():
                n_info = check_nuclei_template(adv_item.get("cve_id"))
                return format_ghsa_alert(adv_item, n_info)
            return {
                "track": "GHSA Day-1 Zero-Day",
                "priority": 100,
                "title": f"{adv_item['ghsa_id']} ({adv_item['severity']})",
                "formatter": fmt,
                "commit_callback": cb
            }
        candidates.append(make_ghsa_entry(a))

    # 2. TRACK: CISA KEV EXPLOITED CVEs (Priority 90)
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
        else:
            new_cves = [v for v in vulns if v.get("cveID") and v["cveID"] not in seen_ids]
            new_cves.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
            for item in new_cves:
                def make_cve_entry(cve_item):
                    cid = cve_item.get("cveID")
                    def cb():
                        seen_ids.add(cid)
                        with open(SEEN_FILE, "w", encoding="utf-8") as f:
                            json.dump(list(seen_ids), f)
                    def fmt():
                        pocs = find_github_pocs(cid)
                        epss = fetch_epss_score(cid)
                        n_info = check_nuclei_template(cid)
                        diffs = find_patch_commit_diffs(cid)
                        return format_cve_alert(cve_item, pocs, epss, n_info, diffs)
                    return {
                        "track": "CISA KEV Exploited CVE",
                        "priority": 90,
                        "title": cid,
                        "formatter": fmt,
                        "commit_callback": cb
                    }
                candidates.append(make_cve_entry(item))

    # 3. TRACK: HACKERONE DISCLOSED BOUNTIES (Priority 80)
    seen_bounties = set()
    if os.path.exists(SEEN_BOUNTIES_FILE):
        try:
            with open(SEEN_BOUNTIES_FILE, "r", encoding="utf-8") as bf:
                seen_bounties = set(json.load(bf))
        except Exception:
            seen_bounties = set()

    bounties = fetch_hackerone_disclosed_bounties()
    new_bounties = [b for b in bounties if b["link"] not in seen_bounties]
    for rep in new_bounties:
        def make_bounty_entry(rep_item):
            def cb():
                seen_bounties.add(rep_item["link"])
                with open(SEEN_BOUNTIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_bounties), f)
            return {
                "track": "H1 Bounty Disclosed",
                "priority": 80,
                "title": f"${rep_item['bounty']:.0f} on {rep_item['program']}",
                "formatter": lambda: format_bounty_report_alert(rep_item),
                "commit_callback": cb
            }
        candidates.append(make_bounty_entry(rep))

    # 4. TRACK: MULTI-SOURCE BREAKING CYBER NEWS (Priority 70)
    seen_news = set()
    if os.path.exists(SEEN_NEWS_FILE):
        try:
            with open(SEEN_NEWS_FILE, "r", encoding="utf-8") as nf:
                seen_news = set(json.load(nf))
        except Exception:
            seen_news = set()

    all_news = fetch_multi_source_cyber_news()
    new_news = [n for n in all_news if n["link"] not in seen_news]
    for item in new_news:
        def make_news_entry(n_item):
            def cb():
                seen_news.add(n_item["link"])
                with open(SEEN_NEWS_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_news), f)
            return {
                "track": "Breaking Cyber News",
                "priority": 70,
                "title": n_item["title"][:50],
                "formatter": lambda: format_news_alert(n_item),
                "commit_callback": cb
            }
        candidates.append(make_news_entry(item))

    # 5. TRACK: NUCLEI TEMPLATE ADDITIONS (Priority 60)
    seen_nuclei = set()
    if os.path.exists(SEEN_NUCLEI_FILE):
        try:
            with open(SEEN_NUCLEI_FILE, "r", encoding="utf-8") as nuc_f:
                seen_nuclei = set(json.load(nuc_f))
        except Exception:
            seen_nuclei = set()

    n_additions = fetch_latest_nuclei_additions()
    new_n_additions = [t for t in n_additions if t["path"] not in seen_nuclei]
    for tmpl in new_n_additions:
        def make_nuc_entry(t_item):
            def cb():
                seen_nuclei.add(t_item["path"])
                with open(SEEN_NUCLEI_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_nuclei), f)
            return {
                "track": "New Nuclei Template",
                "priority": 60,
                "title": t_item["path"],
                "formatter": lambda: format_nuclei_new_template_alert(t_item),
                "commit_callback": cb
            }
        candidates.append(make_nuc_entry(tmpl))

    # 6. TRACK: BUG BOUNTY PROGRAMS / SCOPE (Priority 50)
    seen_programs = set()
    if os.path.exists(SEEN_PROGRAMS_FILE):
        try:
            with open(SEEN_PROGRAMS_FILE, "r", encoding="utf-8") as pf:
                seen_programs = set(json.load(pf))
        except Exception:
            seen_programs = set()

    programs = fetch_latest_bounty_programs()
    new_programs = [p for p in programs if p["url"] not in seen_programs]
    for prog in new_programs:
        def make_prog_entry(p_item):
            def cb():
                seen_programs.add(p_item["url"])
                with open(SEEN_PROGRAMS_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_programs), f)
            return {
                "track": "New Bounty Scope",
                "priority": 50,
                "title": p_item["name"],
                "formatter": lambda: format_bounty_program_alert(p_item),
                "commit_callback": cb
            }
        candidates.append(make_prog_entry(prog))

    # 7. TRACK: DAILY BUG BOUNTY PLAYBOOK TIP (Priority 40)
    if state.get("last_tip_date") != today_str:
        idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
        tip = BUG_BOUNTY_TIPS[idx]
        def tip_cb():
            state["last_tip_date"] = today_str
            save_bot_state(state)
        candidates.append({
            "track": "Daily Bounty Playbook Tip",
            "priority": 40,
            "title": tip["title"],
            "formatter": lambda: format_bug_bounty_tip(tip),
            "commit_callback": tip_cb
        })

    # 8. TRACK: DAILY HACKER EXTENSION (Priority 30)
    if state.get("last_extension_date") != today_str:
        idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
        ext = HACKER_EXTENSIONS[idx]
        def ext_cb():
            state["last_extension_date"] = today_str
            save_bot_state(state)
        candidates.append({
            "track": "Daily Hacker Extension",
            "priority": 30,
            "title": ext["name"],
            "formatter": lambda: format_extension_alert(ext),
            "commit_callback": ext_cb
        })

    # Test mode fallback candidate
    if test_mode and not candidates:
        if kev_data and "vulnerabilities" in kev_data:
            cves_2026 = [v for v in kev_data["vulnerabilities"] if "CVE-2026-" in v.get("cveID", "")]
            test_cve = cves_2026[0] if cves_2026 else kev_data["vulnerabilities"][-1]
            def fmt_test():
                cid = test_cve.get("cveID")
                pocs = find_github_pocs(cid)
                epss = fetch_epss_score(cid)
                nuclei_info = check_nuclei_template(cid)
                diffs = find_patch_commit_diffs(cid)
                return format_cve_alert(test_cve, pocs, epss, nuclei_info, diffs)
            candidates.append({
                "track": "Test Mode Dispatch",
                "priority": 999,
                "title": test_cve.get("cveID"),
                "formatter": fmt_test,
                "commit_callback": lambda: None
            })

    if not candidates:
        print("[+] All feeds monitored. No new threat alerts pending.")
        return

    # Sort descending by priority: highest severity alert goes first!
    candidates.sort(key=lambda x: x["priority"], reverse=True)
    selected = candidates[0]

    print(f"[!] Dispatching 1 paced alert: [{selected['track']}] {selected['title']} (Priority {selected['priority']})")
    formatted = selected["formatter"]()
    msg = formatted[0] if isinstance(formatted, (tuple, list)) else formatted
    markup = formatted[1] if isinstance(formatted, (tuple, list)) and len(formatted) > 1 else None

    res = send_telegram_message(msg, reply_markup=markup)
    if res:
        selected["commit_callback"]()
        state["last_broadcast_time"] = time.time()
        save_bot_state(state)
        print(f"[+] Alert broadcasted successfully! Remaining in queue: {len(candidates) - 1}. Next alert in 30 minutes.")
    else:
        print("[-] Telegram broadcast failed; item retained in queue for next cycle.")

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
        news = fetch_multi_source_cyber_news()
        if news:
            send_telegram_message(format_news_alert(news[0]))
            print("[+] Sent Cyber News")
        sys.exit(0)

    is_force = "--force" in sys.argv
    is_test = "--test" in sys.argv
    run_sync(test_mode=is_test, force=is_force)
