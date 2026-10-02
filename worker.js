// =====================================================================
// 👑 THREATPULSE-AI™ AUTONOMOUS OMNI-RADAR ENGINE (V3.0)
// Round-Robin Multi-Stream Telemetry (Zero Tech Leaks / 100% Proprietary)
// =====================================================================

const TELEGRAM_BOT_TOKEN = "8786341409:AAFS1fCRC8uoeK6FhD7-pqLqoHIlVwSs5GY";
const TELEGRAM_CHAT_ID = "-1004315340178";

export default {
  // Triggered every 5 minutes 24/7 by Cloudflare Cron Trigger (*/5 * * * *)
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runOmniThreatRadar(env));
  },

  // Manual Trigger & Health Check
  async fetch(request, env, ctx) {
    await runOmniThreatRadar(env);
    return new Response("👑 ThreatPulse-AI Omni-Radar V3 Active", { status: 200 });
  }
};

// ================= FAIR MULTI-TRACK DISPATCHER (NO STARVATION) =================
// Rotates across tracks every 5 minutes so EVERY category gets fresh coverage!
async function runOmniThreatRadar(env) {
  let trackIdx = 0;
  if (env.RADAR_KV) {
    const saved = await env.RADAR_KV.get("ACTIVE_TRACK_INDEX");
    if (saved !== null) trackIdx = parseInt(saved, 10) || 0;
  }

  const tracks = [
    { name: "Bugcrowd Live Radar", fn: checkBugcrowdLive },
    { name: "Today 2026 Zero-Days", fn: checkGhsaZeroDays },
    { name: "H1 Disclosed Bounties", fn: checkH1DisclosedBounties },
    { name: "CISA KEV 2026 Exploits", fn: checkCisaKnownExploits },
    { name: "Breaking Threat News", fn: checkBreakingThreatNews }
  ];

  // Try current track first; if no new items, smoothly fallback to next tracks
  for (let i = 0; i < tracks.length; i++) {
    const current = (trackIdx + i) % tracks.length;
    const sent = await tracks[current].fn(env);
    if (sent) {
      const nextIdx = (current + 1) % tracks.length;
      if (env.RADAR_KV) {
        await env.RADAR_KV.put("ACTIVE_TRACK_INDEX", nextIdx.toString());
      }
      return;
    }
  }
}

// ================= TRACK 1: LIVE BUGCROWD PROGRAM RADAR =================
async function checkBugcrowdLive(env) {
  try {
    const res = await fetch("https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/master/data/bugcrowd_data.json", {
      headers: { "User-Agent": "ThreatPulseRadar/3.0" }
    });
    if (!res.ok) return false;
    const progs = await res.json();

    for (const prog of progs) {
      const pUrl = prog.url;
      if (!pUrl) continue;
      const key = `bc:${pUrl}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const progName = cleanText(prog.name || "Bugcrowd Target");
      const maxPay = (prog.max_payout && prog.max_payout > 0)
        ? `Cash Bounties up to $${prog.max_payout.toLocaleString()} (~₹${Math.round(prog.max_payout * 85).toLocaleString()})`
        : "Hall of Fame / Swag (VDP)";
      const safeHarbor = String(prog.safe_harbor || "Standard").toUpperCase();
      const inScopeCount = (prog.targets && prog.targets.in_scope) ? prog.targets.in_scope.length : 0;

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
👑 *Cyber Threat Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "🎯 View Bugcrowd Scope & Rules", url: pUrl }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 2592000 });
      }
      return true;
    }
  } catch (err) {
    console.error("Bugcrowd Radar Error:", err);
  }
  return false;
}

// ================= TRACK 2: TODAY'S DAY-1 ZERO-DAYS & 2026 CVES =================
async function checkGhsaZeroDays(env) {
  // Always query sorted by published descending for TODAY's brand-new CVEs!
  const url = "https://api.github.com/advisories?per_page=15&sort=published&direction=desc";
  try {
    const res = await fetch(url, { headers: { "User-Agent": "ThreatPulseRadar/3.0" } });
    if (!res.ok) return false;
    const advisories = await res.json();

    const currentYear = new Date().getFullYear().toString();

    for (const adv of advisories) {
      // Filter only current year (2026) advisories
      const pubDate = adv.published_at || "";
      if (!pubDate.startsWith(currentYear)) continue;

      const sev = (adv.severity || "HIGH").toUpperCase();
      const ghsaId = adv.ghsa_id;
      const key = `ghsa:${ghsaId}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const cveId = adv.cve_id || "CVE Pending / Day-1 Zero-Day";
      const summary = cleanText(adv.summary || "Security Vulnerability Advisory");
      const pkg = ((adv.vulnerabilities && adv.vulnerabilities[0]?.package?.name) || "Target Component");
      const affected = cleanText(pkg);
      
      const patched = (adv.vulnerabilities && adv.vulnerabilities[0]?.patched_versions)
        ? `Fixed in: \`${cleanText(adv.vulnerabilities[0].patched_versions)}\``
        : "⚠️ *No Patch Available (Day-1 Zero-Day)*";

      const text = `🚨 *EARLY ZERO-DAY TELEMETRY*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 *Advisory:* \`${ghsaId}\`
⚡ *CVE Mapping:* \`${cveId}\`
🔥 *Severity:* \`${sev}\`
📦 *Affected Target:* \`${affected}\`
🛡️ *Patch Status:* ${patched}

📝 *Vulnerability Overview:*
${summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *Cyber Threat Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "⚡ View Advisory Intel & Proof", url: adv.html_url }]
        ]
      };

      await sendTelegram(text, markup);

      if (env.RADAR_KV) {
        await env.RADAR_KV.put(key, "seen", { expirationTtl: 604800 });
      }
      return true;
    }
  } catch (err) {
    console.error("GHSA Zero-Day Error:", err);
  }
  return false;
}

// ================= TRACK 3: HACKERONE DISCLOSED BOUNTY PAYOUTS ($$$) =================
async function checkH1DisclosedBounties(env) {
  try {
    const res = await fetch("https://raw.githubusercontent.com/reddelexc/hackerone-reports/master/data.csv", {
      headers: { "User-Agent": "ThreatPulseRadar/3.0", "Range": "bytes=0-15000" }
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
      const bounty = parseFloat(parts[4] || "0");
      const vulnType = cleanText(parts[5] || "Security Vulnerability");

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
👑 *Cyber Threat Intelligence*`;

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

// ================= TRACK 4: ACTIVELY WEAPONIZED 2026 ZERO-DAYS (CISA KEV) =================
async function checkCisaKnownExploits(env) {
  const url = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json";
  try {
    const res = await fetch(url, { headers: { "User-Agent": "ThreatPulseRadar/3.0" } });
    if (!res.ok) return false;
    const data = await res.json();
    const vulns = data.vulnerabilities || [];

    // STRICT: Only 2026 CVEs & strictly sorted by dateAdded descending!
    const currentYear = new Date().getFullYear().toString();
    const vulns2026 = vulns.filter(v => (v.dateAdded || "").startsWith(currentYear) || (v.cveID || "").includes(currentYear));
    vulns2026.sort((a, b) => (b.dateAdded || "").localeCompare(a.dateAdded || ""));

    for (const v of vulns2026) {
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
🚨 *Weaponization:* Actively Weaponized In The Wild (2026)

🛡️ *Required Remediation Action:*
${action}

⏳ *Federal Action Due Date:* \`${dueDate}\`
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *Cyber Threat Intelligence*`;

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

// ================= TRACK 5: BREAKING GLOBAL CYBER THREAT NEWS =================
async function checkBreakingThreatNews(env) {
  try {
    const res = await fetch("https://feeds.feedburner.com/TheHackersNews", {
      headers: { "User-Agent": "ThreatPulseRadar/3.0" }
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
👑 *Cyber Threat Intelligence*`;

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
