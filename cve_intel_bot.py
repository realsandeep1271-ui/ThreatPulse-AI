import os
import json
import urllib.request
import urllib.parse
import sys
import datetime
import xml.etree.ElementTree as ET

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8786341409:AAHySbQU0xWdYi0HEqFdBo31xp_3Z9tuCK0")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004461177482")  # Supergroup

CISA_KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
THN_RSS_URL = "https://feeds.feedburner.com/TheHackersNews"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_cves.json")
CISA_LOCAL_CACHE = os.path.join(BASE_DIR, "cisa_kev_cache.json")
STATE_FILE = os.path.join(BASE_DIR, "bot_state.json")

# ================= TELEGRAM API HELPERS =================
def send_telegram_message(message: str, chat_id: str = TELEGRAM_CHAT_ID, reply_to_id: int = None):
    """Sends a formatted markdown message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_to_id:
        payload["reply_to_message_id"] = reply_to_id

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "CyberIntelBot/2.5"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[-] Telegram Send Error: {e}")
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

# ================= 4. CORPORATE & GLOBAL CYBER NEWS =================
def fetch_latest_cyber_news():
    req = urllib.request.Request(THN_RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    news_items = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.fromstring(resp.read())
            channel = tree.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:3]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    clean_desc = desc.split("<")[0].strip() if desc else ""
                    news_items.append({
                        "title": title,
                        "link": link,
                        "desc": clean_desc[:250] + "..." if len(clean_desc) > 250 else clean_desc
                    })
    except Exception as e:
        print(f"[-] News Fetch Error: {e}")
    return news_items

def format_news_alert(news_item: dict):
    return (
        f"⚡ *GLOBAL & CORPORATE THREAT INTELLIGENCE NEWS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚨 *Headline:* {news_item['title']}\n\n"
        f"📝 *Executive Summary:*\n{news_item['desc']}\n\n"
        f"🔗 *Full Official Investigation:*\n[{news_item['link']}]({news_item['link']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Cyber Threat News*"
    )

# ================= 5. CISA KEV & CVE CORE =================
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
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/2.5"})
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
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/2.5"})
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

def format_cve_alert(cve_item: dict, pocs: list, epss: str):
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
        f"{poc_text}\n"
        f"🛠️ *Required Defensive Action:*\n{action}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Cyber Threat Intel Bot*"
    )
    return alert

# ================= 6. INTERACTIVE STUDENT COMMAND HANDLER =================
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
                f"🤖 *Cyber Threat Intel Bot — Student Command Menu*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Hi {msg.get('from', {}).get('first_name', 'Hacker')}! You can query me using these commands:\n\n"
                f"📌 `/cve <keyword>` — Search latest exploited CVEs (e.g. `/cve windows` or `/cve apple`)\n"
                f"🛠️ `/tool <keyword>` — Discover top trending hacker tools (e.g. `/tool osint`)\n"
                f"🧩 `/extension` — Get today's top hacker browser extension\n"
                f"🎯 `/tip` — Get today's 1-Minute Bug Bounty Trick\n"
                f"⚡ `/news` — Breaking corporate & cyber news in 60 seconds\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👨‍💻 *Created by Sandeep Yadav (@realsandeep1271-ui)*"
            )
            send_telegram_message(help_text, chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/tip", "/bounty"]:
            idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
            tip = BUG_BOUNTY_TIPS[idx]
            send_telegram_message(format_bug_bounty_tip(tip), chat_id=chat_id, reply_to_id=msg_id)

        elif cmd in ["/extension", "/ext"]:
            idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
            ext = HACKER_EXTENSIONS[idx]
            send_telegram_message(format_extension_alert(ext), chat_id=chat_id, reply_to_id=msg_id)

        elif cmd == "/news":
            news = fetch_latest_cyber_news()
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
                send_telegram_message(format_cve_alert(item, pocs, epss), chat_id=chat_id, reply_to_id=msg_id)
            else:
                send_telegram_message(f"🔍 No CISA exploited CVE found matching `{query}`.", chat_id=chat_id, reply_to_id=msg_id)

    save_bot_state(state)

# ================= MULTI-TRACK DAILY DISPATCH ENGINE =================
def run_sync(test_mode=False):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    state = load_bot_state()

    print("[*] Processing interactive student commands...")
    process_interactive_commands()

    # 1. TRACK: REAL-TIME CISA CVE RADAR
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
            send_telegram_message("✅ *24/7 Multi-Track Threat Intel Engine Active!* Baseline established.")
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
                alert_msg = format_cve_alert(item, pocs, epss)
                send_telegram_message(alert_msg)
                if not test_mode:
                    seen_ids.add(cve_id)

            if not test_mode:
                with open(SEEN_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_ids), f)
                print("[+] Updated seen_cves.json successfully.")
        else:
            print("[+] No new CVEs detected right now.")

    # 2. TRACK: DAILY BUG BOUNTY TRICK (Guaranteed Daily Drop)
    if state.get("last_tip_date") != today_str:
        print("[*] Broadcasting Daily Bug Bounty Trick...")
        idx = datetime.datetime.now().day % len(BUG_BOUNTY_TIPS)
        tip = BUG_BOUNTY_TIPS[idx]
        send_telegram_message(format_bug_bounty_tip(tip))
        state["last_tip_date"] = today_str
        save_bot_state(state)
        print("[+] Daily Bug Bounty trick sent!")

    # 3. TRACK: DAILY HACKER BROWSER EXTENSION
    if state.get("last_extension_date") != today_str:
        print("[*] Broadcasting Daily Hacker Browser Extension...")
        idx = datetime.datetime.now().day % len(HACKER_EXTENSIONS)
        ext = HACKER_EXTENSIONS[idx]
        send_telegram_message(format_extension_alert(ext))
        state["last_extension_date"] = today_str
        save_bot_state(state)
        print("[+] Daily Hacker Extension sent!")

    # 4. TRACK: CORPORATE & GLOBAL CYBER NEWS
    if state.get("last_news_date") != today_str:
        print("[*] Broadcasting Corporate Threat & Cyber News...")
        news = fetch_latest_cyber_news()
        if news:
            send_telegram_message(format_news_alert(news[0]))
            state["last_news_date"] = today_str
            save_bot_state(state)
            print("[+] Corporate Cyber News sent!")

if __name__ == "__main__":
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
