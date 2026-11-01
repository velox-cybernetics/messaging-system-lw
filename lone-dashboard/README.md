# Lone Wraps dashboard

Shows every message the bot takes in and every reply it sends, per channel, with a per-customer bot switch and a flag that emails the address in `FLAG_EMAIL`. Follow ups shows who the bot follows up with and when.

## Setup

1. In Vercel, open the `lone-dashboard` project, go to Storage, and connect a new Upstash for Redis database. Vercel adds `KV_REST_API_URL` and `KV_REST_API_TOKEN` to the project. If the keys come in named `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` instead, those work too.
2. Add these to the project's environment variables:
   - `DASH_PASSWORD`: the sign-in password
   - `RESEND_API_KEY`: from a resend.com account
   - `FLAG_EMAIL`: where flags go. Until a domain is verified in Resend, this has to be the address the Resend account signed up with.
3. Add the same database to the bot's `.env` in `messaging-system-lw`:
   ```
   DASH_REDIS_URL=<KV_REST_API_URL value>
   DASH_REDIS_TOKEN=<KV_REST_API_TOKEN value>
   ```
   Use the read/write token, not the read-only one. Restart the bot.
4. Deploy: `vercel --prod` from this folder.

Without the two `DASH_REDIS_*` keys the bot prints `DASHBOARD OFF` at startup and runs exactly as before.

## How it works

- The bot writes straight to the dashboard's own Upstash database (`helpers/state/dashboard.py`), on a background worker, so a slow or down dashboard never delays a reply.
- Counts are kept by hour of the day, day of the month, and month of the year, so Day, Week, Month and YTD on the Overview each read one or two keys. "Distinct" numbers count each customer once per hour, day, month and year.
- Only messages the system gets to answer count. A message from a customer who is switched off, on a channel that is switched off, or restricted (a person has the conversation, `restricted_{id}` in the bot) still shows in Messages but adds nothing to the Overview. Neither do the replies and hand-offs that follow it.
- While the bot runs it checks in every 5 minutes (`up_last`). The Overview shows "System offline" when no check-in came for 7 minutes.
- The Overview's Follow ups shows how many went out today in the shop's time, whichever range is picked. It counts `followups:sent`, so deleting a conversation takes its follow ups off it too.
- The pages poll `/api/pulse` every 15 seconds while visible (every 60 seconds after 5 minutes with no mouse or keyboard use) and reload only when something changed. Each poll is one database command and also carries the bot's last check-in, so "System running" stays current. The Overview and Follow ups reload at most every 30 seconds.
- Messages has three tabs: Forms (Meta and website form leads, plus anyone who texts in directly, since form leads are answered by text), Instagram and Messenger. The bot's `TABS` in `helpers/state/dashboard.py` sorts each channel into one. Each tab splits into System on and System off by the customer's own switch, worked out from the `off` set when the list loads, so switching someone moves them right away.
- Follow ups has one row per customer and one column per day, today and the 13 days before it plus tomorrow: a dot for each follow up that went out, a ring for the one picked to go out next. `src/followup.py` writes the night's picks (`followups:due`, one line per conversation, with when it goes out and which follow up in a row it is) and every follow up it sends (`followups:sent`). A customer who writes in before theirs goes out comes off the list right away. The end of the morning's send and the start of the night's pick clear anything left that was due, so a follow up called off at send time, or a morning the server missed, never stays listed. Someone switched off, or on a channel switched off, doesn't show as getting one, since the bot checks the switch before it sends. The pick and send hours are `PREP_HOUR` and `FOLLOWUP_HOUR` in `src/followup.py`; keep `api/follow-ups.ts` in step.
- On phones the tab bar at the bottom holds Overview and Messages. The Overview leaves out the bar chart and keeps the system status or booking rate and the totals, and Messages shows the list or one conversation at a time. Follow ups and System info only open on a computer.
- Switching a customer off adds them to the `off` set. The switch at the top of each tab's list adds the whole tab to `off_tabs` (Forms covers texts and both forms). The bot checks both sets in one request at the webhook, before answering, and before every send, so nothing goes out: no reply, no hold message, no typing bubble. Every check-in also copies both sets into the bot, so a switched-off customer or channel stays off through a bot restart or a dashboard outage.
- A pic gets 3 tries, 2 seconds apart, to be copied, since Instagram's link can fail for a moment right when the message lands. One that still fails shows as an Attachment link.
- Flagging emails the feedback, the bot's last reply, and the state that reply was written from.
- The trash button on a conversation deletes, after an are-you-sure, its thread, pic copies, summary, place in its tab, flag, saved reply state and its follow ups (sent and picked), and takes back everything it added to the Overview: its messages, replies, hand-offs and the distinct-customer counts it added. The bot keeps a ledger per conversation for this (`ledger:{id}` holds each count by hash and field, `ledger_sets:{id}` the customer sets it joined), and a count whose day, month or year has already aged out is skipped. The customer's switch stays. A new message from them starts a new conversation, with its Instagram or Messenger name looked up again, and so does a picked follow up the bot still sends.

## What is kept

| Data | Kept for |
| --- | --- |
| Threads (newest 500 entries each) | 1 year after the last message |
| Counts by day and by month | 400 days |
| Counts by year | 800 days |
| Copies of customer pics (1024px JPEG, about 60 to 110 KB each) | 30 days |
| Reply states for flag emails | 30 days |
| Each conversation's ledger of what it added to the counts | 800 days after its newest message |
| Follow ups that went out | 15 days |
| Follow ups picked for the morning | Until they go out or get called off |

Videos and links stay links. Instagram and Messenger links stop working after a while.

## Layout

- `public/html`, `public/css`: pages and styles
- `ts`: browser TypeScript, compiled into `public/js` by `npm run build`. Vercel runs it on deploy, so `public/js` is build output and stays out of git
- `api`: Vercel functions in TypeScript, `api/_helpers` is shared server code
- `npm run check` type-checks both
