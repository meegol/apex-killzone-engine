import os
import json
import pytz
from datetime import datetime

ET = pytz.timezone('America/New_York')
UTC = pytz.utc

def generate_api_data():
    base_dir = os.path.dirname(__file__)
    src_json_path = os.path.join(base_dir, 'website', 'src', 'data', 'forwardTest.json')

    if not os.path.exists(src_json_path):
        raise FileNotFoundError(f"Source data file not found at {src_json_path}")

    with open(src_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    raw_trades = data.get('all_trades', [])
    parsed_trades = []

    for t in raw_trades:
        entry_time_str = t.get('entry_time', '')
        iso_timestamp = None
        dt_utc = None

        if entry_time_str:
            try:
                clean_time_str = entry_time_str.replace(' ET', '').strip()
                dt_naive = datetime.strptime(clean_time_str, '%Y-%m-%d %H:%M')
                dt_et = ET.localize(dt_naive)
                dt_utc = dt_et.astimezone(UTC)
                iso_timestamp = dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            except Exception:
                pass

        if not iso_timestamp:
            date_str = t.get('date', '2026-01-01')
            iso_timestamp = f"{date_str}T00:00:00Z"
            dt_utc = datetime.strptime(f"{date_str} 00:00", '%Y-%m-%d %H:%M').replace(tzinfo=UTC)

        symbol = t.get('symbol', 'NQ=F')
        direction = str(t.get('direction', '')).lower()
        outcome = str(t.get('outcome', '')).lower()

        if outcome == 'win':
            result = 'win'
        elif outcome == 'loss':
            result = 'loss'
        elif outcome == 'be':
            result = 'breakeven'
        elif outcome == 'eod_close':
            result = 'eod_close'
        else:
            result = outcome

        trade_record = {
            'timestamp': iso_timestamp,
            '_dt_utc': dt_utc,
            'date': t.get('date'),
            'instrument': symbol,
            'direction': direction,
            'entry_price': t.get('entry'),
            'stop_price': t.get('sl'),
            'target_price': t.get('tp'),
            'exit_price': t.get('exit'),
            'risk_pts': t.get('risk_pts'),
            'realized_r': float(t.get('pnl_r', 0.0)),
            'result': result,
            'setup': t.get('trigger'),
            'trigger': t.get('trigger'),
            'confirmation': t.get('confirmation'),
            'reason': t.get('reason'),
            'bars_held': t.get('bars_held'),
            'be_active': t.get('be_active', False),
            'rr_target': t.get('rr_target', 4.0),
            'entry_time': t.get('entry_time'),
            'exit_time': t.get('exit_time')
        }

        parsed_trades.append(trade_record)

    # Sort strictly chronologically by UTC timestamp
    parsed_trades.sort(key=lambda x: (x['_dt_utc'], x['instrument']))

    # Assign clean, unique, sequential trade IDs after chronological sorting
    api_trades = []
    for idx, t in enumerate(parsed_trades, 1):
        clean_sym = t['instrument'].replace('=', '').replace('^', '')
        trade_id = f"trade-{clean_sym}-{idx:04d}"
        
        # Remove internal helper key
        t_copy = dict(t)
        del t_copy['_dt_utc']
        t_copy['id'] = trade_id

        # Re-order keys nicely
        ordered_trade = {
            'id': trade_id,
            'timestamp': t_copy['timestamp'],
            'date': t_copy['date'],
            'instrument': t_copy['instrument'],
            'direction': t_copy['direction'],
            'entry_price': t_copy['entry_price'],
            'stop_price': t_copy['stop_price'],
            'target_price': t_copy['target_price'],
            'exit_price': t_copy['exit_price'],
            'risk_pts': t_copy['risk_pts'],
            'realized_r': t_copy['realized_r'],
            'result': t_copy['result'],
            'setup': t_copy['setup'],
            'trigger': t_copy['trigger'],
            'confirmation': t_copy['confirmation'],
            'reason': t_copy['reason'],
            'bars_held': t_copy['bars_held'],
            'be_active': t_copy['be_active'],
            'rr_target': t_copy['rr_target'],
            'entry_time': t_copy['entry_time'],
            'exit_time': t_copy['exit_time']
        }
        api_trades.append(ordered_trade)

    instruments = sorted(list(set(t['instrument'] for t in api_trades if t.get('instrument'))))
    dates = [t['date'] for t in api_trades if t.get('date')]
    date_from = min(dates) if dates else ""
    date_to = max(dates) if dates else ""

    now_utc = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

    api_payload = {
        'source': 'apex-killzone-engine',
        'version': 1,
        'generated_at': now_utc,
        'total_trades': len(api_trades),
        'instruments': instruments,
        'date_range': {
            'from': date_from,
            'to': date_to
        },
        'trades': api_trades
    }

    # Write to public/api/trades.json
    public_api_dir = os.path.join(base_dir, 'website', 'public', 'api')
    os.makedirs(public_api_dir, exist_ok=True)
    public_json_path = os.path.join(public_api_dir, 'trades.json')
    with open(public_json_path, 'w', encoding='utf-8') as f:
        json.dump(api_payload, f, indent=2)
    print(f"  [OK] Saved API JSON to {public_json_path}")

    # Write to docs/api/trades.json
    docs_api_dir = os.path.join(base_dir, 'docs', 'api')
    os.makedirs(docs_api_dir, exist_ok=True)
    docs_json_path = os.path.join(docs_api_dir, 'trades.json')
    with open(docs_json_path, 'w', encoding='utf-8') as f:
        json.dump(api_payload, f, indent=2)
    print(f"  [OK] Saved API JSON to {docs_json_path}")

    return api_payload

if __name__ == '__main__':
    generate_api_data()
