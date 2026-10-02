import time
import os
import sys
import datetime
import cve_intel_bot

# Set up credentials safely
os.environ["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN", "8786341409:AAFS1fCRC8uoeK6FhD7-pqLqoHIlVwSs5GY")
os.environ["TELEGRAM_CHAT_ID"] = os.getenv("TELEGRAM_CHAT_ID", "-1004461177482")
cve_intel_bot.TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
cve_intel_bot.TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

print("==========================================================")
print("🛡️  SANDEEP'S HIGH-SPEED CYBER THREAT RADAR DAEMON  🛡️")
print("==========================================================")
print("[+] Mode: Real-Time Continuous Firehose (Every 90 Seconds)")
print("[+] Feeds: THN | SANS ISC | SecurityAffairs | Krebs | Talos | H1 | Nuclei")
print("[+] Press Ctrl + C anytime to stop.")
print("==========================================================")

while True:
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[*] [{now_str}] Scanning 5 CTI Feeds, GHSA, and Telegram...")
        cve_intel_bot.run_sync()
    except KeyboardInterrupt:
        print("\n[-] Stopped by user.")
        break
    except Exception as e:
        print(f"[-] Daemon Error: {e}")
    time.sleep(90)
