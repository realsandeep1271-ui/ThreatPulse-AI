# 🛡️ 24/7 Cyber Threat Intelligence & GitHub PoC Alert Bot

An automated, serverless Cybersecurity Threat Intelligence (CTI) engine that monitors actively exploited zero-day and 1-day vulnerabilities, predicts real-world weaponization likelihood, searches for working GitHub Proof-of-Concept (PoC) exploit scripts, and broadcasts instant real-time alerts to Telegram.

Developed by **Sandeep Yadav** ([@realsandeep1271-ui](https://github.com/realsandeep1271-ui)) — *Security Researcher & Offensive Engineer*.

---

## ⚡ Key Highlights & Architecture

```
                  ┌─────────────────────────────────────────┐
                  │          CISA KEV Feed (US Govt)        │
                  │  (Known Exploited Vulnerabilities JSON) │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    GitHub Actions (24/7 Serverless)     │
                  │        Runs every 1 hour (cron)         │
                  └────────────────────┬────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                         ▼                           ▼
            ┌────────────────────────┐  ┌────────────────────────┐
            │   FIRST.org EPSS API   │  │    GitHub Search API   │
            │(Exploit Likelihood %)  │  │(Live Working PoC Code) │
            └────────────┬───────────┘  └────────────┬───────────┘
                         │                           │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │        Telegram Broadcast Bot           │
                  │  (Instant Alerts with Clickable PoCs)   │
                  └─────────────────────────────────────────┘
```

---

## 🌟 8 Powerhouse Features (Top 1% Elite Edition)

| Feature | Description | Target Audience | Trigger |
|:---|:---|:---|:---|
| **1. ⚡ Day-1 Zero-Days (GHSA)** | Early-warning pre-disclosure advisories before CISA KEV adds them | Top 1% Bug Hunters | Automated Every 30 Mins |
| **2. 🎯 Nuclei Scanner Templates** | Ready-to-run `nuclei -t cves/` YAML links for 10,000-subdomain scans | Elite Bounty Hunters | With every CVE & `/nuclei` |
| **3. 🔬 Root-Cause Patch Diffs** | Direct GitHub commit diff links (`+` and `-` lines) to analyze code fixes | Reverse Engineers | With every CVE/GHSA |
| **4. 🚨 CISA Zero-Day & 1-Day Radar** | Live exploited bugs + FIRST EPSS likelihood + GitHub PoC exploit links | Red & Blue Teams | Automated Every 30 Mins |
| **5. 🎯 1-Minute Bug Bounty Playbook** | High-impact real-world bypasses (403, IDOR, SSRF, CORS, OAuth) | Pentesters & Hunters | Daily & on `/tip` command |
| **6. 🧩 Hacker Browser Extensions** | Must-have extensions (HackTools, FoxyProxy, Wappalyzer, Cookie-Editor) | Web Pentesters | Daily & on `/extension` |
| **7. 🛠️ Trending Hacker Arsenal** | GitHub search for trending open-source red-team & pentest repositories | Security Researchers | Quiet-day rotation & on `/tool` |
| **8. ⚡ Cyber News in 60 Seconds** | Breaking cybersecurity headlines curated from live RSS feeds | All Infosec Peers | Breaking updates & on `/news` |

---

## 🎮 Interactive Command Menu (In Telegram)

Students & Researchers can interact with the bot in any group, channel, or direct message:

- `/0day` — Trigger latest Day-1 Pre-Disclosure Advisories (GHSA Zero-Days)
- `/nuclei <cve>` — Check ready-made Nuclei scanner template (e.g. `/nuclei CVE-2026-0545`)
- `/cve <keyword>` — Search latest exploited vulnerabilities (e.g. `/cve windows`, `/cve apple`)
- `/tool <keyword>` — Discover top trending hacker tools on GitHub (e.g. `/tool osint`, `/tool recon`)
- `/extension` — Get today's top hacker browser extension
- `/tip` — Receive today's 1-Minute Bug Bounty Trick
- `/news` — Breaking cyber threat news in 60 seconds
- `/help` — Display the full interactive menu

---

## 🚀 Telegram Alert Preview

```text
🚨 NEW CISA EXPLOITED VULNERABILITY ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 CVE ID: CVE-2026-86950
🏢 Vendor & Product: Apple — Multiple Products
⚠️ Vulnerability: Apple Multiple Products Memory Corruption Flaw
📅 Date Added: 2026-09-29 | Due: 2026-10-19

📖 Summary:
Apple iOS, iPadOS, and macOS contain a memory corruption flaw that allows arbitrary code execution.

📊 Threat Intelligence Metrics:
• Ransomware Use: Unknown
• EPSS Exploit Likelihood: 88.5% (Critical Threat)

🔥 Public GitHub PoC Exploits Found:
1. [user/CVE-2026-86950-exploit](https://github.com/) ⭐ 42
2. [researcher/apple-poc-rce](https://github.com/) ⭐ 15

🛠️ Required Defensive Action:
Apply vendor updates immediately.
━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ Sandeep's Cyber Threat Intel Bot
```

---

## 🛠️ How to Deploy

1. Fork or clone this repository:
   ```bash
   git clone https://github.com/realsandeep1271-ui/cve-intelligence-bot.git
   ```
2. Configure your Telegram credentials in `cve_intel_bot.py`:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Enable GitHub Actions in your repository:
   - Go to **Actions** tab → Enable workflows.
   - The bot will run automatically every 1 hour!

---

## 📜 License & Ethics

Distributed under the **MIT License**. This tool is intended for defensive security teams, SOC analysts, and cybersecurity researchers to rapidly patch known exploited vulnerabilities.
