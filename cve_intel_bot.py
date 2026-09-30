import os
import json
import urllib.request
import urllib.parse
import sys

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8786341409:AAHySbQU0xWdYi0HEqFdBo31xp_3Z9tuCK0")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1004461177482")  # Supergroup

CISA_KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_cves.json")
CISA_LOCAL_CACHE = os.path.join(BASE_DIR, "cisa_kev_cache.json")

def send_telegram_message(message: str, chat_id: str = TELEGRAM_CHAT_ID):
    """Sends a formatted markdown message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "CyberIntelBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[-] Telegram Send Error: {e}")
        return None

def fetch_cisa_kev():
    """Fetches the latest CISA Known Exploited Vulnerabilities feed with multi-mirror support."""
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
        except Exception as e:
            print(f"[-] Fetch attempt failed for {u}: {e}")

    # Fallback to local cache if offline
    if os.path.exists(CISA_LOCAL_CACHE):
        print("[*] Using cached CISA KEV feed...")
        try:
            with open(CISA_LOCAL_CACHE, "r", encoding="utf-8") as cf:
                return json.load(cf)
        except Exception:
            pass
    return None

def find_github_pocs(cve_id: str):
    """Searches GitHub for open-source PoC exploits for the given CVE."""
    query = f"{cve_id} exploit"
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/1.0"})
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
    """Fetches the EPSS (Exploit Prediction Scoring System) probability score."""
    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "CyberIntelBot/1.0"})
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
    """Formats the alert message for Telegram with clean Markdown."""
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

def fetch_trending_hacker_tools():
    """Fetches trending open-source hacker & cybersecurity tools from GitHub."""
    query = urllib.parse.quote("topic:security stars:>500")
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
    """Formats the trending tool message for Telegram."""
    return (
        f"🛠️ *TRENDING HACKER TOOL OF THE DAY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 *Tool:* `{tool['name']}`\n"
        f"⭐ *Stars:* {tool['stars']} | 💻 *Language:* `{tool['lang']}`\n\n"
        f"📖 *What it does:*\n{tool['desc']}\n\n"
        f"🔗 *GitHub Repository:*\n[{tool['url']}]({tool['url']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *Sandeep's Hacker Arsenal Radar*"
    )

def run_sync(test_mode=False):
    """Main execution loop."""
    print("[*] Fetching latest CISA KEV feed...")
    kev_data = fetch_cisa_kev()
    if not kev_data or "vulnerabilities" not in kev_data:
        print("[-] Failed to load CISA feed.")
        return

    vulns = kev_data["vulnerabilities"]
    all_cve_ids = [v["cveID"] for v in vulns if "cveID" in v]

    # Load seen CVEs
    seen_ids = set()
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                seen_ids = set(json.load(f))
        except Exception:
            seen_ids = set()

    # If first run and not in test mode, establish baseline
    if not seen_ids and not test_mode:
        print(f"[*] First run: Storing {len(all_cve_ids)} existing CVEs as baseline...")
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(all_cve_ids, f)
        print("[+] Baseline stored. Subsequent runs will alert on newly added CVEs.")
        send_telegram_message("✅ *24/7 Cyber Threat Intel Bot Activated!* Baseline established with current CISA KEV records. Watching for newly added exploits!")
        return

    if test_mode:
        print("[*] TEST MODE: Selecting the freshest 2026 CVE...")
        cves_2026 = [v for v in vulns if "CVE-2026-" in v.get("cveID", "")]
        cves_2026.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
        new_cves = [cves_2026[0]] if cves_2026 else [vulns[-1]]
    else:
        new_cves = [v for v in vulns if v.get("cveID") and v["cveID"] not in seen_ids]
        new_cves.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)

    if not new_cves:
        print("[+] No new CVEs detected. Everything is up to date.")
        return

    print(f"[!] Detected {len(new_cves)} new CVE(s) to process!")

    for item in new_cves[:5]:  # Limit to 5 at a time to prevent flood
        cve_id = item.get("cveID")
        print(f"[*] Processing {cve_id}...")
        pocs = find_github_pocs(cve_id)
        epss = fetch_epss_score(cve_id)
        alert_msg = format_cve_alert(item, pocs, epss)

        send_telegram_message(alert_msg)
        print(f"[+] Alert sent for {cve_id}")

        if not test_mode:
            seen_ids.add(cve_id)

    if not test_mode:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_ids), f)
        print("[+] Updated seen_cves.json successfully.")

if __name__ == "__main__":
    if "--tool" in sys.argv:
        print("[*] Fetching trending hacker tools...")
        tools = fetch_trending_hacker_tools()
        if tools:
            msg = format_tool_alert(tools[0])
            send_telegram_message(msg)
            print(f"[+] Sent trending tool alert for {tools[0]['name']}")
        else:
            print("[-] No trending tools found.")
        sys.exit(0)

    is_test = "--test" in sys.argv
    run_sync(test_mode=is_test)
