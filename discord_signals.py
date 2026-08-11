# discord_signals.py — Discord webhook signal dispatcher for ICT Kill Zone trades

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(__file__), 'sent_signals.json')
WEBHOOK_FILE = os.path.join(os.path.dirname(__file__), 'discord_webhook.txt')


def get_webhook_url() -> str:
    # 1. Environment variable
    url = os.environ.get('DISCORD_WEBHOOK_URL', '').strip()
    if url:
        return url
    # 2. Local config file
    if os.path.exists(WEBHOOK_FILE):
        with open(WEBHOOK_FILE, 'r', encoding='utf-8') as f:
            url = f.read().strip()
            if url:
                return url
    return ''


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'sent_entries': [], 'sent_outcomes': []}


def save_state(state: dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def send_webhook(webhook_url: str, payload: dict) -> bool:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'meegol-ict-backtester/1.0',
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        print(f"  [DISCORD WARN] Webhook failed ({e.code}): {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  [DISCORD WARN] Webhook connection error: {e}")
    return False


def dispatch_trade_alerts(trades: list, webhook_url: str = None):
    url = webhook_url or get_webhook_url()
    if not url:
        return

    state = load_state()
    sent_entries = set(state.get('sent_entries', []))
    sent_outcomes = set(state.get('sent_outcomes', []))

    for t in trades:
        trade_key = f"{t['symbol']}_{t['entry_time']}_{t['entry']}"

        # 1. Send Entry Alert if not already sent
        if trade_key not in sent_entries:
            is_long = t['direction'] == 'LONG'
            color = 0x8ec07c if is_long else 0xfb4934
            side_icon = "▲ LONG" if is_long else "▼ SHORT"

            embed = {
                "title": f"🚨 NEW TRADE ENTRY: {t['symbol']} ({side_icon})",
                "description": f"**Setup:** {t['reason']}",
                "color": color,
                "fields": [
                    {"name": "Symbol", "value": f"`{t['symbol']}`", "inline": True},
                    {"name": "Direction", "value": f"`{t['direction']}`", "inline": True},
                    {"name": "Entry Time", "value": f"`{t['entry_time']}`", "inline": True},
                    {"name": "Entry Price", "value": f"**{t['entry']}**", "inline": True},
                    {"name": "Stop Loss (-1R)", "value": f"`{t['sl']}`", "inline": True},
                    {"name": "Target TP (+4R)", "value": f"`{t['tp']}`", "inline": True},
                    {"name": "Risk (pts)", "value": f"`{t['risk_pts']} pts`", "inline": True},
                    {"name": "Target R:R", "value": "`1:4`", "inline": True},
                    {"name": "BE Protection", "value": "`Active @ +1.5R`", "inline": True},
                ],
                "footer": {"text": "meegol-backtest · ICT Kill Zone Live Signal Engine"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            payload = {"embeds": [embed]}
            if send_webhook(url, payload):
                print(f"  [DISCORD OK] Sent ENTRY alert for {t['symbol']} {t['entry_time']}")
                sent_entries.add(trade_key)

        # 2. Send Outcome Alert if trade is closed and outcome not already sent
        outcome = t.get('outcome')
        if outcome and trade_key in sent_entries and trade_key not in sent_outcomes:
            is_win = outcome == 'WIN'
            is_be = outcome == 'BE'
            color = 0xb8bb26 if is_win else (0xfabd2f if is_be else 0xfb4934)
            outcome_icon = "🏆 WIN (+4.0R)" if is_win else ("🛡️ BREAKEVEN (+0.0R)" if is_be else "❌ STOP LOSS (-1.0R)")

            pnl_str = f"+{t['pnl_r']}R" if t['pnl_r'] > 0 else f"{t['pnl_r']}R"

            embed = {
                "title": f"🏁 TRADE CLOSED: {t['symbol']} → {outcome_icon}",
                "description": f"Trade entry from `{t['entry_time']}` has hit its resolution.",
                "color": color,
                "fields": [
                    {"name": "Symbol", "value": f"`{t['symbol']}`", "inline": True},
                    {"name": "Direction", "value": f"`{t['direction']}`", "inline": True},
                    {"name": "Outcome", "value": f"**{outcome}**", "inline": True},
                    {"name": "Entry Price", "value": f"`{t['entry']}`", "inline": True},
                    {"name": "Exit Price", "value": f"**{t['exit']}**", "inline": True},
                    {"name": "P&L (R Multiples)", "value": f"**{pnl_str}**", "inline": True},
                    {"name": "Exit Time", "value": f"`{t['exit_time']}`", "inline": True},
                    {"name": "Cumulative R", "value": f"`+{t.get('cumulative_r', 0.0)}R`", "inline": True},
                ],
                "footer": {"text": "meegol-backtest · ICT Kill Zone Live Signal Engine"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            payload = {"embeds": [embed]}
            if send_webhook(url, payload):
                print(f"  [DISCORD OK] Sent OUTCOME alert for {t['symbol']} ({outcome})")
                sent_outcomes.add(trade_key)

    # Save updated state
    state['sent_entries'] = list(sent_entries)
    state['sent_outcomes'] = list(sent_outcomes)
    save_state(state)
