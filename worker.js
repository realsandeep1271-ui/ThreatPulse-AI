// =====================================================================
// 👑 THREATPULSE-AI™ AUTONOMOUS THREAT TELEMETRY ENGINE
// Edge Radar Worker - Stealth Mode (Zero Tech Leaks / 100% Proprietary)
// =====================================================================

const TELEGRAM_BOT_TOKEN = "8786341409:AAFS1fCRC8uoeK6FhD7-pqLqoHIlVwSs5GY";
const TELEGRAM_CHAT_ID = "-1004461177482";

export default {
  // Triggered every 5 minutes 24/7 by Cloudflare Cron Trigger (*/5 * * * *)
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runOmniThreatRadar(env));
  },

  // Manual Trigger & Health Check
  async fetch(request, env, ctx) {
    await runOmniThreatRadar(env);
    return new Response("👑 ThreatPulse-AI Radar Engine Active", { status: 200 });
  }
};

// ================= MASTER RADAR ORCHESTRATOR =================
async function runOmniThreatRadar(env) {
  // PRIORITY 1: Early Zero-Day Advisories & Unpatched CVEs (GHSA)
  if (await checkGhsaZeroDays(env)) return;

  // PRIORITY 2: Actively Exploited In-The-Wild Zero-Days (CISA KEV)
  if (await checkCisaKnownExploits(env)) return;

  // PRIORITY 3: Live Bugcrowd Bug Bounty Programs
  if (await checkBugcrowdLive(env)) return;

  // PRIORITY 4: Live HackerOne Disclosed Bounty Payouts
  if (await checkH1DisclosedBounties(env)) return;

  // PRIORITY 5: Breaking Global Cyber Threat & Zero-Day News
  await checkBreakingThreatNews(env);
}

// ================= TRACK 1: DAY-1 ZERO DAYS & UNPATCHED CVES =================
async function checkGhsaZeroDays(env) {
  const url = "https://api.github.com/advisories?per_page=10";
  try {
    const res = await fetch(url, { headers: { "User-Agent": "ThreatPulseRadar/2.0" } });
    if (!res.ok) return false;
    const advisories = await res.json();

    for (const adv of advisories) {
      const sev = (adv.severity || "HIGH").toUpperCase();
      // Monitor Critical, High, and Medium vulnerabilities
      if (sev !== "CRITICAL" && sev !== "HIGH" && sev !== "MEDIUM") continue;

      const ghsaId = adv.ghsa_id;
      const key = `ghsa:${ghsaId}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const cveId = adv.cve_id || "CVE Pending / Day-1 Zero-Day";
      const rawSummary = adv.summary || "Security Vulnerability Advisory";
      const summary = cleanText(rawSummary);
      const pkg = ((adv.vulnerabilities && adv.vulnerabilities[0]?.package?.name) || "Global Component");
      const affected = cleanText(pkg);
      
      const patched = (adv.vulnerabilities && adv.vulnerabilities[0]?.patched_versions)
        ? `Fixed in: \`${cleanText(adv.vulnerabilities[0].patched_versions)}\``
        : "⚠️ *No Patch Available (Zero-Day)*";

      const text = `🚨 *THREATPULSE EARLY ZERO-DAY TELEMETRY*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 *Advisory:* \`${ghsaId}\`
⚡ *CVE Mapping:* \`${cveId}\`
🔥 *Severity:* \`${sev}\`
📦 *Affected Target:* \`${affected}\`
🛡️ *Patch Status:* ${patched}

📝 *Vulnerability Overview:*
${summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Proprietary Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "⚡ View Advisory Intel & Advisory", url: adv.html_url }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 604800 });
      }
      return true;
    }
  } catch (err) {
    console.error("GHSA Radar Error:", err);
  }
  return false;
}

// ================= TRACK 2: ACTIVELY WEAPONIZED ZERO-DAYS (CISA KEV) =================
async function checkCisaKnownExploits(env) {
  const url = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json";
  try {
    const res = await fetch(url, { headers: { "User-Agent": "ThreatPulseRadar/2.0" } });
    if (!res.ok) return false;
    const data = await res.json();
    const vulns = data.vulnerabilities || [];
    // Check the most recently added known exploited zero days
    const recent = vulns.slice(-10).reverse();

    for (const v of recent) {
      const cveId = v.cveID;
      const key = `cisa:${cveId}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const vendor = cleanText(v.vendorProject || "Target Vendor");
      const product = cleanText(v.product || "Target Product");
      const vulnName = cleanText(v.vulnerabilityName || "Active Exploit in the Wild");
      const action = cleanText(v.requiredAction || "Apply vendor mitigation immediately.");
      const dueDate = v.dueDate || "Immediate Action";

      const text = `🔥 *ACTIVE ZERO-DAY EXPLOITED IN WILD (CISA KEV)*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 *CVE:* \`${cveId}\`
🏢 *Vendor / Product:* \`${vendor} - ${product}\`
⚠️ *Threat:* \`${vulnName}\`
🚨 *Weaponization:* Actively Weaponized In The Wild

🛡️ *Required Remediation Action:*
${action}

⏳ *Federal Action Due Date:* \`${dueDate}\`
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Proprietary Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "🔍 NVD Vulnerability Analysis", url: `https://nvd.nist.gov/vuln/detail/${cveId}` }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 2592000 });
      }
      return true;
    }
  } catch (err) {
    console.error("CISA KEV Radar Error:", err);
  }
  return false;
}

// ================= TRACK 3: LIVE BUGCROWD PROGRAM RADAR =================
async function checkBugcrowdLive(env) {
  try {
    const bcRes = await fetch("https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/master/data/bugcrowd_data.json", {
      headers: { "User-Agent": "ThreatPulseRadar/2.0" }
    });
    if (bcRes.ok) {
      const bcData = await bcRes.json();
      
      let knownBc = null;
      if (env.RADAR_KV) {
        knownBc = await env.RADAR_KV.get("KNOWN_BUGCROWD_URLS", "json");
      }

      // Initialize baseline on first run
      if (!knownBc || !Array.isArray(knownBc)) {
        const allUrls = bcData.map(p => p.url).filter(Boolean);
        if (env.RADAR_KV) {
          await env.RADAR_KV.put("KNOWN_BUGCROWD_URLS", JSON.stringify(allUrls));
        }
      } else {
        const knownSet = new Set(knownBc);
        for (const prog of bcData) {
          const pUrl = prog.url;
          if (!pUrl || knownSet.has(pUrl)) continue;

          // Found a brand-new Bugcrowd program!
          const maxPay = (prog.max_payout && prog.max_payout > 0)
            ? `Cash Bounties up to $${prog.max_payout.toLocaleString()}`
            : "Hall of Fame / Swag (VDP)";
          const safeHarbor = String(prog.safe_harbor || "Standard").toUpperCase();
          const inScopeCount = (prog.targets && prog.targets.in_scope) ? prog.targets.in_scope.length : 0;
          const progName = cleanText(prog.name || "Bugcrowd Program");

          const text = `🎯 *NEW BUG BOUNTY PROGRAM LAUNCHED*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Company:* \`${progName}\`
🌐 *Platform:* \`Bugcrowd\`
💵 *Bounty Rewards:* \`${maxPay}\`
🛡️ *Safe Harbor:* \`${safeHarbor}\`
🎯 *In-Scope Target Assets:* \`${inScopeCount} targets\`

🔗 *Official Program Scope & Rules:*
[${pUrl}](${pUrl})
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Bug Bounty Radar*`;

          const markup = {
            inline_keyboard: [
              [{ text: "🎯 View Bugcrowd Scope & Rules", url: pUrl }]
            ]
          };

          await sendTelegram(text, markup);

          knownBc.push(pUrl);
          if (env.RADAR_KV) {
            await env.RADAR_KV.put("KNOWN_BUGCROWD_URLS", JSON.stringify(knownBc));
          }
          return true;
        }
      }
    }
  } catch (err) {
    console.error("Bugcrowd Live Radar Error:", err);
  }
  return false;
}

// ================= TRACK 4: HACKERONE DISCLOSED BOUNTY PAYOUTS =================
async function checkH1DisclosedBounties(env) {
  try {
    const res = await fetch("https://raw.githubusercontent.com/reddelexc/hackerone-reports/master/data.csv", {
      headers: { "User-Agent": "ThreatPulseRadar/2.0", "Range": "bytes=0-15000" }
    });
    if (!res.ok && res.status !== 206) return false;
    const csvText = await res.text();
    const lines = csvText.split("\n");

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const parts = parseCsvLine(line);
      if (parts.length < 5) continue;

      const program = cleanText(parts[0] || "Target Company");
      const title = cleanText(parts[1] || "Disclosed Vulnerability Report");
      let link = (parts[2] || "").trim();
      if (!link) continue;
      if (!link.startsWith("http")) link = `https://${link}`;
      const bounty = parseFloat(parts[3] || "0");
      const vulnType = cleanText(parts[4] || "Security Flaw");

      if (bounty <= 0) continue;

      const key = `h1_rep:${link}`;
      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const bountyUsd = `$${bounty.toLocaleString()}`;
      const bountyInr = `₹${Math.round(bounty * 85).toLocaleString()}`;

      const text = `💰 *HACKERONE DISCLOSED BOUNTY PAYOUT*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Target Company:* \`${program}\`
💵 *Bounty Paid:* \`${bountyUsd}\` *(~${bountyInr})*
⚠️ *Bug Class:* \`${vulnType}\`

📝 *Disclosed Report:*
${title}

🔗 *Read Full Writeup & PoC:*
[${link}](${link})
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Bug Bounty Radar*`;

      const markup = {
        inline_keyboard: [
          [{ text: "💵 View Report & PoC", url: link }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 2592000 });
      }
      return true;
    }
  } catch (err) {
    console.error("H1 Disclosed Radar Error:", err);
  }
  return false;
}

// ================= TRACK 5: BREAKING GLOBAL CYBER THREAT NEWS =================
async function checkBreakingThreatNews(env) {
  try {
    const res = await fetch("https://feeds.feedburner.com/TheHackersNews", {
      headers: { "User-Agent": "ThreatPulseRadar/2.0" }
    });
    if (!res.ok) return false;
    const xml = await res.text();
    const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/g) || [];

    for (const item of itemMatches.slice(0, 5)) {
      const titleMatch = item.match(/<title>([\s\S]*?)<\/title>/);
      const linkMatch = item.match(/<link>([\s\S]*?)<\/link>/);

      if (!titleMatch || !linkMatch) continue;
      const rawTitle = titleMatch[1].replace(/<!\[CDATA\[(.*?)\]\]>/, "$1").trim();
      const rawLink = linkMatch[1].replace(/<!\[CDATA\[(.*?)\]\]>/, "$1").trim();

      const title = cleanText(rawTitle);
      const key = `news:${rawLink}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const text = `📰 *BREAKING CYBER THREAT ALERT*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 *Headline:*
${title}

⚡ *Source:* Global Cyber Threat Intelligence Feed

🔗 *Full Threat Analysis & IOCs:*
[${rawLink}](${rawLink})
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Proprietary Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "⚡ Read Full Incident Report", url: rawLink }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 604800 });
      }
      return true;
    }
  } catch (err) {
    console.error("News Radar Error:", err);
  }
  return false;
}

// ================= HELPER FUNCTIONS =================
function cleanText(str) {
  if (!str) return "";
  return str
    .replace(/[_*`\[\]()~>#+=|{}.!-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseCsvLine(line) {
  const result = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

// ================= TELEGRAM DISPATCHER (WITH AUTO-FALLBACK) =================
async function sendTelegram(text, markup) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const body = {
    chat_id: TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: "Markdown",
    disable_web_page_preview: true,
    reply_markup: markup
  };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    // If Markdown parsing fails with 400, fallback to plain text delivery immediately
    if (!res.ok) {
      delete body.parse_mode;
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
    }
  } catch (e) {
    console.error("Telegram Dispatch Error:", e);
  }
}
