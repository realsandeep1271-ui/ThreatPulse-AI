// ================= THREATPULSE-AI PROPRIETARY RADAR =================
// Autonomous Threat Telemetry Engine - Stealth Mode (Zero Tech Leaks)

const TELEGRAM_BOT_TOKEN = "8786341409:AAFS1fCRC8uoeK6FhD7-pqLqoHIlVwSs5GY";
const TELEGRAM_CHAT_ID = "-1004461177482";

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runLiveRadar(env));
  },

  async fetch(request, env, ctx) {
    await runLiveRadar(env);
    return new Response("ThreatPulse Radar OK", { status: 200 });
  }
};

async function runLiveRadar(env) {
  // Priority 1: Check GHSA Zero-Days first
  const sentGhsa = await checkGhsaZeroDays(env);
  if (sentGhsa) return; // Strict Pacing: Only 1 broadcast per cycle!

  // Priority 2: Check Bugcrowd & HackerOne Programs Live
  await checkNewBountyPrograms(env);
}

// ================= TRACK 1: GHSA DAY-1 ZERO DAYS =================
async function checkGhsaZeroDays(env) {
  const url = "https://api.github.com/advisories?per_page=5";
  try {
    const res = await fetch(url, { headers: { "User-Agent": "ThreatPulseRadar/1.0" } });
    if (!res.ok) return false;
    const advisories = await res.json();

    for (const adv of advisories) {
      const sev = (adv.severity || "").toUpperCase();
      if (sev !== "CRITICAL" && sev !== "HIGH") continue;

      const ghsaId = adv.ghsa_id;
      const key = `ghsa:${ghsaId}`;

      let seen = false;
      if (env.RADAR_KV) {
        seen = await env.RADAR_KV.get(key);
      }
      if (seen) continue;

      const cveId = adv.cve_id || "CVE Pending";
      const summary = adv.summary || "Security Advisory";
      const affected = (adv.vulnerabilities && adv.vulnerabilities[0]?.package?.name) || "Unknown Package";

      const text = `🚨 *THREATPULSE EARLY ZERO-DAY TELEMETRY*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 *Advisory:* \`${ghsaId}\`
⚡ *CVE Mapping:* \`${cveId}\`
🔥 *Severity:* \`${sev}\`
📦 *Affected Component:* \`${affected}\`

📝 *Intel Summary:*
${summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Proprietary Intelligence*`;

      const markup = {
        inline_keyboard: [
          [{ text: "⚡ View Advisory Details", url: adv.html_url }]
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

// ================= TRACK 2: BUGCROWD & HACKERONE BOUNTY RADAR =================
async function checkNewBountyPrograms(env) {
  // 1. LIVE BUGCROWD RADAR (Direct Scraped Feed updated every 30m)
  try {
    const bcRes = await fetch("https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/master/data/bugcrowd_data.json", {
      headers: { "User-Agent": "ThreatPulseRadar/1.0" }
    });
    if (bcRes.ok) {
      const bcData = await bcRes.json();
      
      let knownBc = null;
      if (env.RADAR_KV) {
        knownBc = await env.RADAR_KV.get("KNOWN_BUGCROWD_URLS", "json");
      }

      // If first run, baseline all existing Bugcrowd programs
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

          const text = `🎯 *NEW BUG BOUNTY PROGRAM LAUNCHED*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Company:* \`${prog.name}\`
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
          return true; // Sent 1 fresh program!
        }
      }
    }
  } catch (err) {
    console.error("Bugcrowd Live Radar Error:", err);
  }

  // 2. HACKERONE / CHAOS SCOPES
  try {
    const h1Res = await fetch("https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/dist/data.json", {
      headers: { "User-Agent": "ThreatPulseRadar/1.0" }
    });
    if (h1Res.ok) {
      const data = await h1Res.json();
      const programs = (data.programs || []).filter(p => (p.url || "").includes("hackerone.com"));

      for (const prog of programs) {
        const pUrl = prog.url;
        if (!pUrl) continue;
        const key = `prog_h1:${pUrl}`;

        let seen = false;
        if (env.RADAR_KV) {
          seen = await env.RADAR_KV.get(key);
        }
        if (seen) continue;

        const reward = prog.bounty ? "Cash Bounties ($$$)" : "Hall of Fame / Swag";
        const domains = (prog.domains || []).length;

        const text = `🎯 *NEW BUG BOUNTY PROGRAM LAUNCHED*
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *Company:* \`${prog.name}\`
🌐 *Platform:* \`HackerOne\`
💵 *Rewards:* \`${reward}\`
🎯 *Scope Size:* \`${domains} target domains\`

🔗 *Official Program Scope & Rules:*
[${pUrl}](${pUrl})
━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 *ThreatPulse-AI Bug Bounty Radar*`;

        const markup = {
          inline_keyboard: [
            [{ text: "🎯 View HackerOne Scope & Rules", url: pUrl }]
          ]
        };

        await sendTelegram(text, markup);

        if (env.RADAR_KV) {
          await env.RADAR_KV.put(key, "seen", { expirationTtl: 604800 });
        }
        return true;
      }
    }
  } catch (err) {
    console.error("H1 Scope Radar Error:", err);
  }

  return false;
}

// ================= TELEGRAM DISPATCHER =================
async function sendTelegram(text, markup) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const body = {
    chat_id: TELEGRAM_CHAT_ID,
    text: text,
    parse_mode: "Markdown",
    disable_web_page_preview: true,
    reply_markup: markup
  };

  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}
