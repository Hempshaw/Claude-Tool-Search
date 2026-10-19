# Weekly Free AI Tools for Claude: Discord digest (free version)

Every Monday this searches GitHub for new open-source projects built for Claude:
MCP servers, Claude Code plugins and skills, and apps using the Claude API. It ranks
them by stars, skips anything it has already posted, and sends the top 8 to a Discord
channel as cards.

It costs nothing to run. There's no AI step and no API key to pay for. GitHub's
search API, GitHub Actions and Discord webhooks are all free for this.

## Files

```
digest.py                              the script
requirements.txt                       Python packages
.github/workflows/weekly-digest.yml    the weekly schedule (must be at this exact path)
seen_tools.json                        created automatically after the first run
```

## Setup (about 5 minutes)

1. **Discord webhook.** In your server: channel settings → Integrations → Webhooks →
   New Webhook → pick the channel → Copy Webhook URL.
2. **GitHub repo.** Create a new repo and upload these files, keeping the
   `.github/workflows/` folder structure. A public repo gets unlimited free Actions minutes.
   A private one works too and uses only a few minutes of the free monthly allowance.
3. **Secret.** In the repo: Settings → Secrets and variables → Actions → New repository secret.
   Name it `DISCORD_WEBHOOK_URL` and paste the webhook URL. That's the only secret you need.
4. **Test it.** Actions tab → "Weekly AI tools digest" → Run workflow. A post should
   appear in your channel within a minute.

## Testing locally

```bash
pip install -r requirements.txt
DRY_RUN=1 python digest.py      # prints the Discord message instead of posting
```

## Tweaks

- **Schedule:** edit the `cron` line. GitHub uses UTC, and scheduled runs can be a few
  minutes late at busy times.
- **Too much noise or too little?** Set `MIN_STARS` (default 20) or `LOOKBACK_DAYS`
  (default 30) as env vars in the workflow's "Build and post digest" step.
- **Number of picks:** change `MAX_TOOLS` in `digest.py` (max 10, Discord's embed limit).
- **What it searches for:** edit the `SEARCHES` list in `digest.py`. It uses GitHub's
  search syntax, e.g. `topic:claude-code` or `"some phrase" in:name,description`.
- **Reset repeats:** delete `seen_tools.json`.

## Good to know

- Card text comes from each repo's own description, so quality varies.
- Ranking by stars favours popular projects over quietly useful ones.
- It only finds GitHub projects, not free tiers of commercial tools.
- GitHub pauses scheduled workflows in repos with no activity for 60 days. The weekly
  commit of `seen_tools.json` normally keeps it active. If it ever stops, re-enable it
  from the Actions tab.

Keep your webhook URL secret: anyone who has it can post to your channel.
