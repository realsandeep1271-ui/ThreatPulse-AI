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

## 🌟 What Makes This Bot Better?

| Feature | Standard CVE Trackers | Sandeep's Cyber Intel Bot |
|:---|:---|:---|
| **Noise Filtering** | Dumps 30,000+ useless CVEs/year | **Strict CISA KEV** (Only actively exploited in the wild) |
| **Exploit PoC Code** | ❌ No PoC links | **✅ Auto-searches GitHub for working exploits & repositories** |
| **Weaponization Odds** | ❌ Just basic CVSS score | **✅ FIRST.org EPSS Exploit Likelihood Score (%)** |
| **Hosting Cost** | Requires paid VPS / Docker server | **✅ 100% Free 24/7/365 via GitHub Actions** |
| **Ransomware Tracking** | ❌ None | **✅ Identifies associated ransomware campaigns** |

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
