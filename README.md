# 🛡️ 24/7 AI-Powered Cyber Threat Intelligence & Bug Bounty Engine

An autonomous, serverless Cybersecurity Threat Intelligence (CTI) & Bounty Reconnaissance engine powered by **Google Gemini Pro**. The system continuously monitors actively exploited zero-day vulnerabilities, predicts exploit weaponization likelihood, checks ready-to-run Nuclei scanner templates, fetches patch commit diffs, ingests real-time threat news from THN & SANS ISC, and tracks live **HackerOne disclosed bounty payouts** and **Bugcrowd programs** with instant Telegram broadcast and interactive AI mentoring.

Developed by **Sandeep Yadav** ([@realsandeep1271-ui](https://github.com/realsandeep1271-ui)) — *Security Researcher & Offensive Engineer*.

---

## ⚡ Key Highlights & Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Multi-Source Ingestion Telemetry         │
                    │   CISA KEV | GHSA Zero-Days | THN | SANS ISC | H1 Payouts│
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │           GitHub Actions (24/7 Cloud Serverless)       │
                    │                  Runs every 30 Mins (cron)             │
                    └───────────────────────────┬────────────────────────────┘
                                                │
            ┌───────────────────────────────────┼───────────────────────────────────┐
            │                                   │                                   │
            ▼                                   ▼                                   ▼
┌────────────────────────┐          ┌────────────────────────┐          ┌────────────────────────┐
│   FIRST.org EPSS API   │          │  ProjectDiscovery      │          │   Google Gemini Pro    │
│ (Exploit Probability)  │          │  (Nuclei YAML Scanners)│          │   (AI Threat Reasoning)│
└───────────┬────────────┘          └───────────┬────────────┘          └───────────┬────────────┘
            │                                   │                                   │
            └───────────────────────────────────┼───────────────────────────────────┘
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               Telegram Intelligence Bot                │
                    │   • Real-Time Threat Alerts with Clickable PoCs        │
                    │   • HackerOne Disclosed Payouts ($ & ₹)                │
                    │   • Interactive AI Mentor (/ask <question>)            │
                    └────────────────────────────────────────────────────────┘
```

---

## 🌟 10 Powerhouse Engine Features (Top 1% Elite Edition)

| Feature | Description | Target Audience | Trigger Mode |
|:---|:---|:---|:---|
| **1. 🧠 Gemini Pro AI Threat Engine** | Generates 3-bullet offensive summaries: Root cause, Exploit TTPs, and Hunter Action items | Red Teams & Hunters | Automated on every alert & `/ask` |
| **2. 💰 HackerOne Bounty Payout Tracker** | Real-time tracking of who received bounties, company target, dollar & rupee payouts, and PoC links | Bug Bounty Hunters | Continuous Stream & `/bounty` |
| **3. 🎯 Bugcrowd & H1 New Programs Radar** | Instant alerts whenever a company launches or expands a public bug bounty program | Recon Hunters | Continuous Stream & `/program` |
| **4. ⚡ Day-1 Zero-Days (GHSA)** | Early-warning pre-disclosure advisories before CISA KEV indexes them | Elite 0-Day Hunters | Automated Every 30 Mins & `/0day` |
| **5. 🎯 Nuclei Scanner Template Radar** | Ready-to-run `nuclei -t cves/` YAML links and newly added ProjectDiscovery community templates | Automation Hunters | Real-time & `/nuclei` |
| **6. 🔬 Root-Cause Patch Diffs** | Direct GitHub commit diff links (`+` and `-` lines) to analyze code fixes and bypasses | Vulnerability Researchers | Attached to CVE alerts |
| **7. 📡 Real-Time Multi-Source Cyber Stream** | Breaking cybersecurity headlines curated from **The Hacker News** and **SANS Internet Storm Center** | Infosec Community | Continuous Stream & `/news` |
| **8. 🚨 CISA Zero-Day & 1-Day Radar** | Actively exploited CVEs + FIRST EPSS likelihood metrics + Live GitHub PoC exploit links | SOC Analysts & Pentesters | Automated Every 30 Mins & `/cve` |
| **9. 🎯 1-Minute Bug Bounty Playbook** | High-impact real-world bypasses (403 Forbidden, IDOR, SSRF, CORS, OAuth token theft) | Web Pentesters | Daily Drop & `/tip` |
| **10. 🧩 Hacker Browser Extensions** | Handpicked extensions (HackTools, FoxyProxy, Wappalyzer, Cookie-Editor) | Application Testers | Daily Drop & `/extension` |

---

## 🎮 Interactive Telegram Command Menu

Members can interact with the bot in any group, channel, or direct message:

- `🧠 /ask <query>` — Ask Gemini Pro any hacking, recon, or bug bounty question!
- `💰 /bounty` — View latest HackerOne disclosed bounty payout with amount & writeup
- `🎯 /program <target>` — Search active HackerOne & Bugcrowd targets (e.g. `/program shopify`)
- `⚡ /0day` — Trigger latest Day-1 Pre-Disclosure Advisories (GHSA Zero-Days)
- `🎯 /nuclei <cve>` — Check ready-made Nuclei scanner template (e.g. `/nuclei CVE-2026-0545`)
- `📌 /cve <keyword>` — Search latest exploited vulnerabilities (e.g. `/cve windows`, `/cve apple`)
- `🛠️ /tool <keyword>` — Discover top trending hacker tools on GitHub (e.g. `/tool osint`, `/tool recon`)
- `🧩 /extension` — Get today's top hacker browser extension
- `🎯 /tip` — Receive today's 1-Minute Bug Bounty Trick
- `⚡ /news` — Breaking corporate & cyber news stream in real time
- `🤖 /help` — Display the full interactive menu

---

## 🚀 Live Telegram Alert Previews

### 1. HackerOne Disclosed Payout Alert
```text
💰 HACKERONE DISCLOSED BOUNTY PAYOUT
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Target Company: 8x8
💵 Bounty Paid: $3,000 (~₹2,55,000)
⚠️ Bug Class: Deserialization Vulnerability
📝 Disclosed Report: connect.8x8.com Automation Builder RCE

🧠 Gemini Pro Bounty Analysis:
• 🎯 Target: Webhook Automation Builder
• ⚡ Attack Vector: Java object deserialization leading to remote code execution.
• 🛡️ Hunter Tip: Test custom integrations accepting serialized base64 data.

🔗 Read Full Disclosed Report & POC:
https://hackerone.com/reports/3861550
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 Sandeep's Bug Bounty Hunter Radar
```

### 2. Day-1 Zero-Day Pre-Disclosure Alert
```text
⚡ DAY-1 ZERO-DAY PRE-DISCLOSURE RADAR (GHSA)
━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 ID: GHSA-chx6-46f5-w4vp | CVE: CVE-2026-12227
🚨 Severity: CRITICAL (Pre-KEV Early Alert)

📖 Vulnerability Summary:
Unauthenticated Remote Code Execution in Core Network API.

🎯 Ready-to-Scan Nuclei Template:
🔗 https://github.com/projectdiscovery/nuclei-templates/blob/main/http/cves/2026/CVE-2026-12227.yaml
💻 nuclei -t cves/2026/CVE-2026-12227.yaml -l targets.txt

🔬 Root-Cause Patch Diff Link:
🔗 https://github.com/vendor/repo/commit/7a8f9c

🔗 Full Security Advisory:
https://github.com/advisories/GHSA-chx6-46f5-w4vp
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 Sandeep's Top 1% Hacker Radar
```

---

## 🔒 Enterprise OPSEC & Security Model

This project adheres to strict Zero-Trust Operational Security (OPSEC):
- **Zero Hardcoded Secrets:** All tokens and API keys are isolated within **GitHub Repository Secrets**:
  - `GEMINI_API_KEY` — Google Gemini Pro API authentication
  - `TELEGRAM_BOT_TOKEN` — Telegram Bot API credential
  - `TELEGRAM_CHAT_ID` — Targeted broadcast channel/group ID
- **State Deduplication:** State machines (`seen_cves.json`, `seen_ghsa.json`, `seen_news.json`, `seen_bounties.json`, `seen_programs.json`) prevent duplicate noise and guarantee 100% signal delivery.

---

## 📜 License & Ethics

Distributed under the **MIT License**. This tool is engineered strictly for authorized security research, defensive threat modeling, and bug bounty hunting within official program scopes.

Designed with ❤️ by **Sandeep Yadav** ([@realsandeep1271-ui](https://github.com/realsandeep1271-ui)).
