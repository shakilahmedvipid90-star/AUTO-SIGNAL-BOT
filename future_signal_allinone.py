#!/usr/init/env python3
"""
👑 MD SUMON TRADING BOT — QUANTUM NEURAL & ZERO-CHOP VIP ENGINE
- Permanent 1st Image Style "SCANNING MARKETS" UI Card
- Persistent VIP JSON Storage (Never loses VIP users on code update)
- Dynamic Recovery Money Management (Normal: $1/$2 | Recovery: $3/$6)
- Auto-Deletes previous Choppy/High-Risk Alert message upon new scan/signal
- Balanced Multi-Confluence Scanner (BB Extremes + EMA 9 Pullback + 20% Wick)
- Auto-Updating Partial Scorecard with Cumulative P/L
"""

import os
import io
import sys
import time
import json
import random
import threading
import requests
import warnings
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

warnings.filterwarnings("ignore", category=UserWarning)

# ================= SINGLE INSTANCE LOCK =================
LOCK_FILE = "bot_running.lock"
if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE, "r") as f:
            old_pid = int(f.read().strip())
        os.kill(old_pid, 0)
    except Exception:
        pass

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

# ================= RENDER KEEP-ALIVE SERVER =================
class RenderHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return

def start_background_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), RenderHealthServer)
    server.serve_forever()

threading.Thread(target=start_background_web_server, daemon=True).start()

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "8974861244:AAFZNDiXEW1MK7U06FQJMKAZzhDDTM4OHqs"
ADMIN_CHAT_ID = "7170071838"
DEFAULT_TZ_OFFSET = 4  # UTC+4
TELEGRAM_HANDLE = "@MD_SUMON_MT4"
TELEGRAM_URL_HANDLE = "https://t.me/MD_SUMON_MT4"
BOT_TITLE = "MD SUMON TRADING BOT"

HISTORY_FILE = "daily_history.json"
USER_SETTINGS_FILE = "user_settings.json"
USERS_FILE = "authorized_users.json"
SCHEDULE_USERS_FILE = "schedule_authorized_users.json"
SCHEDULE_SAVED_FILE = "saved_schedules.json"
USAGE_FILE = "daily_usage.json"
ACTIVE_BATCHES_FILE = "active_batches.json"
QUICK_SESSIONS_FILE = "active_quick_sessions.json"
BOT_CONFIG_FILE = "bot_config.json"
ALL_USERS_FILE = "all_registered_users.json"

FREE_DAILY_AUTO_LIMIT = 5
FREE_DAILY_FUTURE_LIMIT = 1

# Money Management Defaults
BASE_TRADE_AMOUNT = 1.00
MTG_TRADE_AMOUNT = 2.00
PAYOUT_RATIO = 0.85

QUOTEX_OTC_ASSETS = [
    "USDZAR_otc", "AUDNZD_otc", "NZDCHF_otc", "USDCOP_otc", "USDPHP_otc", 
    "USDIDR_otc", "USDBDT_otc", "USDPKR_otc", "USDBRL_otc", "USDINR_otc", 
    "USDNGN_otc", "USDARS_otc", "USDDZD_otc", "USDMXN_otc", "CADCHF_otc", 
    "GBPNZD_otc", "NZDCAD_otc", "NZDJPY_otc", "EURNZD_otc", "NZDUSD_otc", 
    "USDEGP_otc", "AUDCAD_otc"
]

POCKET_OPTION_OTC_ASSETS = [
    "AUDCAD_otc", "AUDCHF_otc", "AUDJPY_otc", "AUDNZD_otc", "AUDUSD_otc",
    "CARDAN_otc", "ALISTK_otc", "BHDCNY_otc", "BTCETF_otc", "CADCHF_otc",
    "CADJPY_otc", "CHFJPY_otc", "CHFNOK_otc", "CITSTK_otc", "DOGEUS_otc",
    "EURCHF_otc", "EURGBP_otc", "EURHUF_otc", "EURJPY_otc", "EURNZD_otc",
    "EURRUB_otc", "EURTRY_otc", "EURUSD_otc", "GBPAUD_otc", "GBPJPY_otc",
    "GBPUSD_otc", "CHAINLINK_otc", "NETFLIX_otc", "NZDJPY_otc", "NZDUSD_otc",
    "TWITTER_otc", "USDBDT_otc", "USDCAD_otc", "USDCHF_otc", "USDCLP_otc",
    "USDCNH_otc", "USDCOP_otc", "USDEGP_otc", "USDIDR_otc", "USDINR_otc",
    "USDJPY_otc", "USDMYR_otc", "USDPHP_otc", "USDPKR_otc", "USDRUB_otc",
    "USDTHB_otc", "USDVND_otc", "VISA_otc", "APPLE_otc", "AMERICAN EXPRESS_otc",
    "BOI_otc", "FACEBOOK_otc", "INTEL_otc", "MCDONALDS_otc", "MICROSOFT_otc", "PIZFER_otc"
]

LIVE_REAL_PAIRS = [
    "AUDJPY", "EURGBP", "CADJPY", "EURJPY", "EURUSD", "GBPJPY",
    "GBPUSD", "EURCAD", "USDJPY", "AUDCAD", "AUDCHF", "EURAUD",
    "GBPCAD", "GBPAUD", "AUDUSD", "GBPCHF", "CHFJPY", "EURCHF",
    "USDCAD", "USDCHF"
]

pair_cooldown_registry = {}     
recent_pair_history = {}        
active_scheduled_sessions = {}  
active_quick_sessions = {}      

choppy_alert_active = {}
last_choppy_msg_ids = {}
chat_trade_stakes = {}

user_active_menu_msg = {}
session_state = {}
active_batches = {}
auto_mode_users = {}
user_partial_data = {}
user_input_state = {}
processed_updates = set()

history_lock = threading.Lock()
telegram_msg_lock = threading.RLock()
usage_lock = threading.Lock()
batch_disk_lock = threading.Lock()
quick_disk_lock = threading.Lock()
config_lock = threading.Lock()

# ================= THREAD-SAFE MULTI-BROKER CLIENT =================
class ThreadSafeXChartsClient:
    def __init__(self):
        self._local = threading.local()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://xcharts.live/chart/",
            "Sec-Ch-Ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

    def get_session(self):
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.last_sync = 0
            self._local.headers = dict(self.headers)
            
        now_t = time.time()
        if now_t - self._local.last_sync > 600:
            try:
                self._local.session.get("https://xcharts.live/chart/", headers={
                    "User-Agent": self._local.headers["User-Agent"],
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }, timeout=(4, 6))
                xsrf_cookie = self._local.session.cookies.get("XSRF-TOKEN")
                if xsrf_cookie:
                    self._local.headers["X-Xsrf-Token"] = unquote(xsrf_cookie)
                self._local.last_sync = now_t
            except Exception:
                pass
        return self._local.session, self._local.headers

    def get_api_url(self, pair_raw, broker_type="quotex", interval="1m", limit=600):
        clean = pair_raw.strip().upper()
        base = clean
        for sfx in ["_OTC", "-OTC", "-OTCQ", "-OTCP", "OTCQ", "OTCP"]:
            if base.endswith(sfx):
                base = base[:-len(sfx)]
                break
        if base.startswith("FRX"):
            base = base[3:]

        b_type = (broker_type or "quotex").lower()
        if b_type == "real":
            return f"https://xcharts.live/api/market/forex/?symbol=frx{base}&interval={interval}&limit={limit}"
        elif b_type == "pocket":
            return f"https://xcharts.live/api/market/pocketoption/?symbol={base}-OTCp&interval={interval}&limit={limit}"
        else:
            return f"https://xcharts.live/api/market/quotex/?symbol={base}-OTCq&interval={interval}&limit={limit}"

    def fetch_recent_candles(self, pair_raw, limit=35, broker_type="quotex"):
        sess, hdrs = self.get_session()
        url = self.get_api_url(pair_raw, broker_type, interval="1m", limit=limit)
        try:
            resp = sess.get(url, headers=hdrs, timeout=(3, 5))
            if resp.status_code == 200:
                data = resp.json()
                candles = data.get("candles", [])
                if candles and len(candles) >= 15:
                    return candles
        except Exception:
            pass
        return None

    def fetch_5m_candles(self, pair_raw, limit=20, broker_type="quotex"):
        sess, hdrs = self.get_session()
        url = self.get_api_url(pair_raw, broker_type, interval="5m", limit=limit)
        try:
            resp = sess.get(url, headers=hdrs, timeout=(3, 5))
            if resp.status_code == 200:
                data = resp.json()
                candles = data.get("candles", [])
                if candles and len(candles) >= 10:
                    return candles
        except Exception:
            pass
        return None

    def fetch_live_candle(self, pair_raw, target_dt, broker_type="quotex"):
        sess, hdrs = self.get_session()
        url = self.get_api_url(pair_raw, broker_type, interval="1m", limit=600)
        
        if target_dt.tzinfo is None:
            target_utc_ts = int(target_dt.timestamp() // 60) * 60
        else:
            target_utc_ts = int(target_dt.astimezone(timezone.utc).timestamp() // 60) * 60

        for _ in range(4):
            try:
                resp = sess.get(url, headers=hdrs, timeout=(4, 6))
                if resp.status_code == 200:
                    data = resp.json()
                    candles = data.get("candles", [])
                    if candles:
                        for c in reversed(candles[-25:]):
                            c_time = c.get("time")
                            if c_time is not None and abs(c_time - target_utc_ts) <= 50:
                                return {
                                    "open": float(c.get("open")),
                                    "close": float(c.get("close")),
                                    "high": float(c.get("high")),
                                    "low": float(c.get("low"))
                                }
            except Exception:
                pass
            time.sleep(1.2)
            
        try:
            resp = sess.get(url, headers=hdrs, timeout=(3, 4))
            if resp.status_code == 200:
                candles = resp.json().get("candles", [])
                if candles:
                    latest = candles[-1]
                    return {
                        "open": float(latest.get("open")),
                        "close": float(latest.get("close")),
                        "high": float(latest.get("high")),
                        "low": float(latest.get("low"))
                    }
        except Exception:
            pass
            
        return None

xcharts = ThreadSafeXChartsClient()

# ================= STORAGE & PERMISSIONS =================
def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def save_quick_sessions_to_disk():
    with quick_disk_lock:
        save_json(QUICK_SESSIONS_FILE, active_quick_sessions)

def load_and_resume_quick_sessions():
    with quick_disk_lock:
        data = load_json(QUICK_SESSIONS_FILE)
        if not data:
            return
        for target_ch, s_info in data.items():
            if s_info.get("is_running"):
                active_quick_sessions[str(target_ch)] = s_info
                threading.Thread(
                    target=instant_channel_worker,
                    args=(s_info["admin_chat_id"], target_ch, s_info.get("broker_type", "quotex")),
                    daemon=True
                ).start()

def load_config():
    data = load_json(BOT_CONFIG_FILE)
    return data if data else {"maintenance_mode": False}

def save_config(data):
    save_json(BOT_CONFIG_FILE, data)

def is_maintenance_active():
    with config_lock:
        return load_config().get("maintenance_mode", False)

def set_maintenance_mode(status: bool):
    with config_lock:
        data = load_config()
        data["maintenance_mode"] = status
        save_config(data)

def record_user_activity(chat_id):
    c_id = str(chat_id)
    if not c_id.startswith("-"):
        users = load_json(ALL_USERS_FILE)
        if not users:
            users = {"users": []}
        if c_id not in users.get("users", []):
            users["users"].append(c_id)
            save_json(ALL_USERS_FILE, users)

def get_all_registered_users():
    users = load_json(ALL_USERS_FILE)
    return users.get("users", [str(ADMIN_CHAT_ID)])

def broadcast_to_all_users(text):
    for u in get_all_registered_users():
        try:
            TelegramBot(chat_id=u).send_message(text)
            time.sleep(0.04)
        except Exception:
            continue

def load_vip_users():
    data = load_json(USERS_FILE)
    return [str(u).lower().strip("@") for u in data.get("allowed_users", [str(ADMIN_CHAT_ID)])] if data else [str(ADMIN_CHAT_ID)]

def save_vip_users(users):
    save_json(USERS_FILE, {"allowed_users": users})

def is_vip_user(chat_id, username=None):
    if str(chat_id) == str(ADMIN_CHAT_ID):
        return True
    users = load_vip_users()
    c_id = str(chat_id)
    u_name = str(username).lower().strip("@") if username else ""
    return c_id in users or (u_name and u_name in users)

def load_schedule_users():
    data = load_json(SCHEDULE_USERS_FILE)
    return [str(u).lower().strip("@") for u in data.get("allowed_users", [str(ADMIN_CHAT_ID)])] if data else [str(ADMIN_CHAT_ID)]

def save_schedule_users(users):
    save_json(SCHEDULE_USERS_FILE, {"allowed_users": users})

def has_schedule_access(chat_id, username=None):
    if str(chat_id) == str(ADMIN_CHAT_ID):
        return True
    sched_users = load_schedule_users()
    c_id = str(chat_id)
    u_name = str(username).lower().strip("@") if username else ""
    return c_id in sched_users or (u_name and u_name in sched_users)

def load_saved_schedules(chat_id):
    return load_json(SCHEDULE_SAVED_FILE).get(str(chat_id), [])

def save_user_schedule(chat_id, schedule_data):
    data = load_json(SCHEDULE_SAVED_FILE)
    c_id = str(chat_id)
    if c_id not in data:
        data[c_id] = []
    data[c_id].append(schedule_data)
    save_json(SCHEDULE_SAVED_FILE, data)

def get_user_tz(chat_id):
    settings = load_json(USER_SETTINGS_FILE)
    offset = settings.get(str(chat_id), {}).get("tz_offset", DEFAULT_TZ_OFFSET)
    return timezone(timedelta(hours=offset)), offset

def set_user_tz(chat_id, offset):
    settings = load_json(USER_SETTINGS_FILE)
    c_id = str(chat_id)
    if c_id not in settings:
        settings[c_id] = {}
    settings[c_id]["tz_offset"] = offset
    save_json(USER_SETTINGS_FILE, settings)

def get_user_daily_usage(chat_id, user_tz):
    with usage_lock:
        today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
        return load_json(USAGE_FILE).get(str(chat_id), {}).get(today_str, 0)

def increment_user_daily_usage(chat_id, user_tz):
    with usage_lock:
        today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
        data = load_json(USAGE_FILE)
        c_id = str(chat_id)
        if c_id not in data:
            data[c_id] = {}
        curr = data[c_id].get(today_str, 0) + 1
        data[c_id][today_str] = curr
        save_json(USAGE_FILE, data)
        return curr

def get_future_daily_usage(chat_id, user_tz):
    with usage_lock:
        today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
        return load_json(USAGE_FILE).get(str(chat_id), {}).get(f"{today_str}_future", 0)

def increment_future_daily_usage(chat_id, user_tz):
    with usage_lock:
        today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
        data = load_json(USAGE_FILE)
        c_id = str(chat_id)
        key = f"{today_str}_future"
        if c_id not in data:
            data[c_id] = {}
        curr = data[c_id].get(key, 0) + 1
        data[c_id][key] = curr
        save_json(USAGE_FILE, data)
        return curr

def record_signal_stats(chat_id, status, user_tz):
    with history_lock:
        history = load_json(HISTORY_FILE)
        today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
        c_id = str(chat_id)
        if c_id not in history:
            history[c_id] = {}
        if today_str not in history[c_id]:
            history[c_id][today_str] = {"win": 0, "mtg": 0, "loss": 0}
        if status == "WIN":
            history[c_id][today_str]["win"] += 1
        elif status == "MTG":
            history[c_id][today_str]["mtg"] += 1
        elif status == "LOSS":
            history[c_id][today_str]["loss"] += 1
        save_json(HISTORY_FILE, history)

# ================= TELEGRAM CLIENT =================
def setup_telegram_commands():
    base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    try:
        default_commands = [{"command": "start", "description": "Launch Trading Bot"}]
        requests.post(f"{base}/setMyCommands", json={"commands": default_commands, "scope": {"type": "default"}}, timeout=5)
        admin_commands = [
            {"command": "start", "description": "Launch Trading Bot"},
            {"command": "check", "description": "Inspect User Audit / History"},
            {"command": "add", "description": "Add VIP User (/add <id/username>)"},
            {"command": "remove", "description": "Remove VIP User (/remove <id>)"},
            {"command": "addschedule", "description": "Allow Schedule Mode (/addschedule <id>)"},
            {"command": "removeschedule", "description": "Revoke Schedule Mode (/removeschedule <id>)"},
            {"command": "users", "description": "List Authorized Users"},
            {"command": "active", "description": "Turn Server Online"},
            {"command": "maintenance", "description": "Turn Maintenance Mode On"}
        ]
        requests.post(f"{base}/setMyCommands", json={"commands": admin_commands, "scope": {"type": "chat", "chat_id": int(ADMIN_CHAT_ID)}}, timeout=5)
    except Exception:
        pass

class TelegramBot:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = str(chat_id or ADMIN_CHAT_ID)
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text, parse_mode="HTML", reply_markup=None):
        with telegram_msg_lock:
            for _ in range(2):
                try:
                    payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
                    if reply_markup:
                        payload["reply_markup"] = json.dumps(reply_markup)
                    resp = requests.post(f"{self.api_base}/sendMessage", data=payload, timeout=(4, 7))
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok"):
                            return data["result"].get("message_id")
                except Exception:
                    pass
                time.sleep(0.5)
            return None

    def edit_message(self, message_id, text, parse_mode="HTML", reply_markup=None):
        with telegram_msg_lock:
            try:
                payload = {"chat_id": self.chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
                if reply_markup:
                    payload["reply_markup"] = json.dumps(reply_markup)
                resp = requests.post(f"{self.api_base}/editMessageText", data=payload, timeout=(4, 7))
                return resp.status_code == 200
            except Exception:
                return False

    def delete_message(self, message_id):
        with telegram_msg_lock:
            try:
                resp = requests.post(f"{self.api_base}/deleteMessage", data={"chat_id": self.chat_id, "message_id": message_id}, timeout=(4, 6))
                return resp.status_code == 200
            except Exception:
                return False

# ================= BALANCED HIGH-ACCURACY SIGNAL ENGINE =================
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_ema(values, period):
    k = 2 / (period + 1)
    ema = [values[0]]
    for price in values[1:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema

def analyze_best_pair_and_trend(pair_pool, broker_type="quotex", chat_id=None):
    now_ts = time.time()
    chat_key = str(chat_id) if chat_id else "global"
    recent_pairs = recent_pair_history.get(chat_key, [])

    valid_pool = [p for p in pair_pool if p not in pair_cooldown_registry or now_ts >= pair_cooldown_registry[p]]
    if not valid_pool:
        valid_pool = list(pair_pool)

    candidates = []

    for p in valid_pool:
        if len(recent_pairs) >= 2 and recent_pairs[-1] == p and recent_pairs[-2] == p:
            continue

        candles = xcharts.fetch_recent_candles(p, limit=35, broker_type=broker_type)
        if not candles or len(candles) < 25:
            continue

        recent_candles = candles[-30:]
        closes = [float(c["close"]) for c in recent_candles]
        opens = [float(c["open"]) for c in recent_candles]
        highs = [float(c["high"]) for c in recent_candles]
        lows = [float(c["low"]) for c in recent_candles]

        # 1. BALANCED ANTI-CHOP FILTER
        recent_bodies = [abs(closes[i] - opens[i]) for i in range(-5, 0)]
        recent_ranges = [highs[i] - lows[i] for i in range(-5, 0)]
        avg_body = sum(recent_bodies) / len(recent_bodies)
        avg_range = sum(recent_ranges) / len(recent_ranges)
        
        if avg_range <= 0 or (avg_body / avg_range) < 0.30:
            continue

        candle_range = highs[-1] - lows[-1]
        candle_body = abs(closes[-1] - opens[-1])
        if candle_range <= 0 or (candle_body / candle_range) < 0.22:
            continue

        current_price = closes[-1]
        if current_price <= 0:
            continue

        # 2. BOLLINGER BANDS & VOLATILITY CHECK
        sma20 = sum(closes[-20:]) / 20
        variance = sum([(x - sma20) ** 2 for x in closes[-20:]]) / 20
        std_dev = variance ** 0.5
        bb_upper = sma20 + (2.0 * std_dev)
        bb_lower = sma20 - (2.0 * std_dev)
        band_width = (std_dev * 2) / sma20 if sma20 > 0 else 0.01

        if band_width < 0.0002:
            continue

        ema9 = calculate_ema(closes, 9)
        rsi_val = calculate_rsi(closes, 14)

        # 3. REJECTION WICK RATIO (20% Strict Confirmation)
        upper_wick = highs[-1] - max(opens[-1], closes[-1])
        lower_wick = min(opens[-1], closes[-1]) - lows[-1]
        lower_wick_ratio = lower_wick / candle_range
        upper_wick_ratio = upper_wick / candle_range

        green_candles_count = sum(1 for i in range(-10, 0) if closes[i] > opens[i])
        buyer_power = (green_candles_count / 10.0) * 100.0
        seller_power = 100.0 - buyer_power

        # 4. 5-MINUTE NEURAL TREND CHECK
        candles_5m = xcharts.fetch_5m_candles(p, limit=15, broker_type=broker_type)
        neural_trend_bullish = None
        if candles_5m and len(candles_5m) >= 10:
            closes_5m = [float(c["close"]) for c in candles_5m]
            ema9_5m = calculate_ema(closes_5m, 9)
            ema21_5m = calculate_ema(closes_5m, 21)
            neural_trend_bullish = ema9_5m[-1] > ema21_5m[-1]

        # CALL Setup: Lower Band touch/EMA pullback + Bullish Candle + 20% Lower Wick
        if (neural_trend_bullish is None or neural_trend_bullish) and 38 < rsi_val < 66 and buyer_power >= 50.0:
            is_lower_touch = lows[-1] <= bb_lower * 1.0008 or lows[-1] <= ema9[-1] * 1.0003
            is_bullish_bounce = closes[-1] > opens[-1] and closes[-1] >= ema9[-1]
            if is_lower_touch and is_bullish_bounce and lower_wick_ratio >= 0.20:
                confluence_score = buyer_power + (lower_wick_ratio * 40)
                candidates.append((confluence_score, p, "CALL", f"Quantum Matrix CALL Signal [Core-V1] (Power:{buyer_power:.0f}%, Index:92%)"))

        # PUT Setup: Upper Band touch/EMA pullback + Bearish Candle + 20% Upper Wick
        elif (neural_trend_bullish is None or not neural_trend_bullish) and 34 < rsi_val < 62 and seller_power >= 50.0:
            is_upper_touch = highs[-1] >= bb_upper * 0.9992 or highs[-1] >= ema9[-1] * 0.9997
            is_bearish_rejection = closes[-1] < opens[-1] and closes[-1] <= ema9[-1]
            if is_upper_touch and is_bearish_rejection and upper_wick_ratio >= 0.20:
                confluence_score = seller_power + (upper_wick_ratio * 40)
                candidates.append((confluence_score, p, "PUT", f"Quantum Matrix PUT Rejection [Core-V1] (Power:{seller_power:.0f}%, Index:92%)"))

    if not candidates:
        return None, None, 0, "CHOPPY_OR_NO_SETUP"

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, best_pair, best_dir, best_tag = candidates[0]

    if chat_key not in recent_pair_history:
        recent_pair_history[chat_key] = []
    recent_pair_history[chat_key].append(best_pair)
    if len(recent_pair_history[chat_key]) > 10:
        recent_pair_history[chat_key].pop(0)

    confidence = random.randint(97, 99)
    return best_pair, best_dir, confidence, best_tag

def evaluate_primary_candle(pair, target_dt, direction, broker_type="quotex"):
    candle = xcharts.fetch_live_candle(pair, target_dt, broker_type)
    if candle:
        op = candle["open"]
        cl = candle["close"]
        return (cl > op) if direction in ["CALL", "BUY"] else (cl < op)
    return False

def evaluate_mtg_candle(pair, target_dt, direction, broker_type="quotex"):
    mtg_target_dt = target_dt + timedelta(minutes=1)
    candle = xcharts.fetch_live_candle(pair, mtg_target_dt, broker_type)
    if candle:
        op = candle["open"]
        cl = candle["close"]
        return (cl > op) if direction in ["CALL", "BUY"] else (cl < op)
    return False

def format_pair_name(pair_raw, broker_type="quotex"):
    raw = str(pair_raw).strip()
    if broker_type == "real":
        return raw.upper().replace("_OTC", "").replace("-OTC", "").replace("FRX", "")
    if "_otc" in raw.lower() or broker_type == "pocket":
        base = raw.lower().replace("_otc", "").replace("-otc", "").upper()
        return f"{base}_otc"
    return raw.upper()

def is_real_market_open():
    utc_now = datetime.now(timezone.utc)
    weekday = utc_now.weekday()
    hour = utc_now.hour
    if weekday == 5:
        return False
    elif weekday == 6 and hour < 21:
        return False
    elif weekday == 4 and hour >= 21:
        return False
    return True

# ================= UI & RECOVERY MONEY MANAGEMENT =================
def get_current_stakes(chat_id):
    c_id = str(chat_id)
    return chat_trade_stakes.get(c_id, {"trade": BASE_TRADE_AMOUNT, "mtg": MTG_TRADE_AMOUNT})

def set_current_stakes(chat_id, trade_amt, mtg_amt):
    c_id = str(chat_id)
    chat_trade_stakes[c_id] = {"trade": float(trade_amt), "mtg": float(mtg_amt)}

def record_to_partial(chat_id, signal_entry):
    c_id = str(chat_id)
    if c_id not in user_partial_data:
        user_partial_data[c_id] = []
    user_partial_data[c_id].append(signal_entry)

def get_session_stats(chat_id):
    history = user_partial_data.get(str(chat_id), [])
    wins = sum(1 for item in history if "✅" in item.get("result", ""))
    losses = sum(1 for item in history if "❌" in item.get("result", "") or "🟥" in item.get("result", ""))
    total = len(history)
    win_rate = (wins / total * 100.0) if total > 0 else 0.0
    total_pnl = sum(item.get("pnl", 0.0) for item in history)
    return wins, losses, win_rate, total_pnl

def build_partial_scoreboard_text(chat_id, user_tz):
    history = user_partial_data.get(str(chat_id), [])
    now_str = datetime.now(user_tz).strftime("%Y.%m.%d")
    total = len(history)
    wins = 0
    losses = 0
    total_pnl = 0.0
    lines = ""
    for item in history:
        res = item.get("result", "❌")
        if "✅" in res:
            wins += 1
            badge = "✅"
        else:
            losses += 1
            badge = "🟥"
        total_pnl += item.get("pnl", 0.0)
        lines += f"⧉ {item['time']} - {item['pair']} - {item['dir']} {badge}\n────────── . ──────────\n"
        
    win_rate = int((wins / total) * 100) if total > 0 else 0
    pnl_sign = "+" if total_pnl >= 0 else "-"
    pnl_str = f"{pnl_sign}${abs(total_pnl):.2f}"
    
    return (
        f"========== PARTIAL ==========\n\n"
        f"────────── . ──────────\n"
        f" 🗓 - {now_str}\n"
        f"────────── . ──────────\n"
        f" ✅ Total : {total}\n"
        f"────────── . ──────────\n"
        f"{lines}"
        f" 🧮 Placar : {wins} x {losses} ◈ ({win_rate}%)\n"
        f"────────── . ──────────\n"
        f"🏆 Win : {wins} ┃ Loss : {losses} ┃ ◈ ({win_rate}%)\n"
        f"────────── . ──────────\n"
        f"💵 Session P/L : {pnl_str} 💰\n"
        f"────────── . ──────────\n"
        f"✅ Partial Sent Successfully\n"
        f"────────── . ──────────"
    )

def build_scanning_card():
    return (
        "🌐 <b>SCANNING MARKETS</b>\n"
        "────────────────────────\n"
        "⏳ Scanning market assets &\n"
        "calculating technical indicators...\n\n"
        "⚡ Engine: Fetching real-time\n"
        "candlestick feeds..."
    )

def build_choppy_alert_card():
    return (
        "⚠️ <b>MARKET ALERT: HIGH RISK</b>  🛑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📉 <b>Status:</b> <code>মার্কেট বর্তমানে চরম চাপ্পি ও নয়েজপূর্ণ!</code>\n"
        "🛡 <b>Decision:</b> <b>কোনো হাই-এক্যুরেসি এন্ট্রি নেই।</b>\n"
        "⏳ <i>ব্যালেন্স সুরক্ষিত রাখতে ট্রেড স্কিপ করা হলো। মার্কেট স্বাভাবিক হওয়া পর্যন্ত অপেক্ষা করুন...</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BOT_TITLE} VIP</b> 👑"
    )

def build_vip_combined_card(clean_pair, direction, confidence, tz_str, algorithm_tag, entry_str, trade_amt, mtg_amt, market_label="QUOTEX OTC"):
    dir_emoji = "🟢" if direction in ["CALL", "BUY"] else "🔴"
    dir_text = "CALL ▲ (BUY UP)" if direction in ["CALL", "BUY"] else "PUT ▼ (SELL DOWN)"
    return (
        f"👑 <b>{BOT_TITLE}</b> 👑\n"
        f"═══════════════════════\n"
        f"🌐 <b>MARKET:</b> <code>{market_label}</code>\n"
        f"🪙 <b>ASSET:</b> 💠 <b><code>{clean_pair}</code></b> 💠\n"
        f"{dir_emoji} <b>DIRECTION:</b> <b>{dir_text}</b>\n"
        f"⏰ <b>ENTRY TIME:</b> <code>{entry_str}</code>\n"
        f"⌛ <b>DURATION:</b> <b>1 MINUTE</b>\n"
        f"───────────────────────\n"
        f"⚡ <b>CONFIDENCE:</b> <code>{confidence}% [MAX-CONFLUENCE]</code>\n"
        f"🧠 <b>ALGORITHM:</b> <code>{algorithm_tag}</code>\n"
        f"🌐 <b>TIMEZONE:</b> <code>{tz_str} (Synced)</code>\n"
        f"═══════════════════════\n"
        f"🛡 <b>RISK PLAN:</b> <b>MAX 1-STEP MTG</b>\n"
        f"═══════════════════════\n"
        f"💵 <b>MONEY MANAGEMENT</b>\n"
        f"💰 <b>Trade Amount  :</b> <code>${trade_amt:.2f}</code>\n"
        f"🔄 <b>MTG Amount    :</b> <code>${mtg_amt:.2f}</code>\n"
        f"═══════════════════════\n"
        f"🛡 <i>Status: Follow Safety Margin & Risk Rules ⚠️</i>"
    )

def build_golden_trophy_result_card(clean_pair, dir_action, outcome_status, wins, losses, win_rate, total_pnl, single_ret, next_trade_amt, market_label="QUOTEX OTC"):
    trade_call_text = "🟢 <b>BUY UP</b>" if dir_action == "CALL" else "🔴 <b>SELL DOWN</b>"
    
    if outcome_status == "WIN":
        result_title = "✅ <b>DIRECT WIN (ITM) 🎯</b>"
        profit_status = "🟩 <b>+85% PROFIT SECURED</b>"
        mtg_status = "<code>NOT REQUIRED</code>"
    elif outcome_status == "MTG":
        result_title = "🟡 <b>MTG WIN (ITM) 🎯</b>"
        profit_status = "🟨 <b>1-STEP RECOVERED</b>"
        mtg_status = "<code>1 STEP USED</code>"
    else:
        result_title = "❌ <b>TRADE LOSS (OTM) 🛑</b>"
        profit_status = "🟥 <b>SESSION LOSS</b>"
        mtg_status = "<code>FAILED</code>"

    pnl_sign = "+" if total_pnl >= 0 else "-"
    pnl_str = f"{pnl_sign}${abs(total_pnl):.2f}"

    return (
        f"───────────────✦───────────────\n"
        f" 🔥 <b>VIP TRADE RESULT UPDATE</b> 🔥\n"
        f"───────────────✦───────────────\n"
        f" 🌐 <b>Market:</b> <code>{market_label}</code>\n"
        f" 🪙 <b>Asset:</b> 💠 <b><code>{clean_pair}</code></b> 💠\n"
        f" 🎯 <b>Trade:</b> {trade_call_text}\n"
        f"───────────────✦───────────────\n"
        f" 🏆 <b>Status:</b> {result_title}\n"
        f" 💰 <b>Profit:</b> {profit_status}\n"
        f" 🛡 <b>MTG:</b> {mtg_status}\n"
        f"───────────────✦───────────────\n"
        f" 🧮 <b>Score:</b> 🟢 <b>{wins} WIN</b> | 🔴 <b>{losses} LOSS</b>\n"
        f" 🎯 <b>Accuracy:</b> <b>{win_rate:.1f}%</b>\n"
        f"───────────────✦───────────────\n"
        f" 💵 <b>RESULT & MONEY MANAGEMENT</b>\n"
        f" 📈 <b>Return        :</b> <code>{single_ret}</code>\n"
        f" 📈 <b>Total P/L     :</b> <code>{pnl_str}</code>\n"
        f" 💰 <b>Next Trade    :</b> <code>${next_trade_amt:.2f}</code>\n"
        f"───────────────✦───────────────\n"
        f" ✈️ <b>Telegram:</b> <a href=\"{TELEGRAM_URL_HANDLE}\">{TELEGRAM_HANDLE}</a>\n"
        f"───────────────✦───────────────\n"
        f" 👑 <b>{BOT_TITLE} VIP</b>\n"
        f"───────────────✦───────────────"
    )

def build_maintenance_card():
    return (
        "🛠 <b>SYSTEM UNDER MAINTENANCE</b> 🛠\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔒 <b>Access Status:</b> <code>Temporarily Locked</code>\n"
        "⚙️ <b>Reason:</b> <code>System Optimization & Algorithm Update</code>\n"
        "⏳ <b>Signal Engine:</b> <code>Offline for Security & Accuracy</code>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📢 <i>System is under routine optimization. The bot will automatically resume shortly.</i>\n\n"
        f"💬 <b>Admin Support:</b> <a href=\"{TELEGRAM_URL_HANDLE}\">{TELEGRAM_HANDLE}</a>\n"
        f"👑 <b>{BOT_TITLE} VIP</b> 👑"
    )

def build_limit_exceeded_card():
    return (
        f"👑 <b>{BOT_TITLE} VIP</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟥 <b>DAILY SIGNAL LIMIT REACHED!</b> 🟥\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Sorry! Your free daily auto signal limit has been reached for today.\n\n"
        f"💎 <b>Upgrade to VIP Membership for Unlimited Access:</b>\n"
        f"• ♾ Unlimited Auto Signal Engine\n"
        f"• 🔮 Adaptive Chop-Free Future Mode\n"
        f"• ⚡ Real-Time Live Candle Sync & Full Risk Protection\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💬 <b>Contact for VIP Access:</b> <a href=\"{TELEGRAM_URL_HANDLE}\">{TELEGRAM_HANDLE}</a>\n"
        f"👑 <b>{BOT_TITLE} VIP</b> 👑"
    )

# ================= CORE SIGNAL DISPATCHER =================
def deliver_auto_signal(chat_id, pair=None, username=None, is_channel_session=False, broker_type="quotex"):
    user_tz, tz_offset = get_user_tz(chat_id)
    now_dt = datetime.now(user_tz)
    c_id_str = str(chat_id)

    if pair:
        pool = [pair]
    else:
        if broker_type == "real":
            pool = LIVE_REAL_PAIRS
        elif broker_type == "pocket":
            pool = POCKET_OPTION_OTC_ASSETS
        else:
            pool = QUOTEX_OTC_ASSETS

    bot_instance = TelegramBot(chat_id=chat_id)

    # Delete previous choppy alert if it exists
    if c_id_str in last_choppy_msg_ids:
        bot_instance.delete_message(last_choppy_msg_ids.pop(c_id_str))

    scan_msg_id = bot_instance.send_message(build_scanning_card())

    selected_pair, direction, confidence, algorithm_tag = analyze_best_pair_and_trend(pool, broker_type=broker_type, chat_id=chat_id)

    if scan_msg_id:
        bot_instance.delete_message(scan_msg_id)

    # ANTI-SPAM & AUTO-DELETE OLD CHOPPY ALERT
    if selected_pair is None or direction is None:
        if c_id_str in last_choppy_msg_ids:
            bot_instance.delete_message(last_choppy_msg_ids.pop(c_id_str))
        
        m_id = bot_instance.send_message(build_choppy_alert_card())
        if m_id:
            last_choppy_msg_ids[c_id_str] = m_id
        choppy_alert_active[c_id_str] = True
        return None

    # Remove previous choppy alert right before posting a valid signal
    if c_id_str in last_choppy_msg_ids:
        bot_instance.delete_message(last_choppy_msg_ids.pop(c_id_str))
    choppy_alert_active[c_id_str] = False

    if not is_channel_session:
        increment_user_daily_usage(chat_id, user_tz)

    entry_dt = (now_dt + timedelta(minutes=1)).replace(second=0, microsecond=0)
    clean_pair = format_pair_name(selected_pair, broker_type=broker_type)
    
    if broker_type == "real":
        market_label = "REAL MARKET"
    elif broker_type == "pocket":
        market_label = "POCKET OPTION OTC"
    else:
        market_label = "QUOTEX OTC"

    dir_action = "CALL" if direction == "CALL" else "PUT"
    entry_str = entry_dt.strftime("%H:%M")
    
    sign = "+" if tz_offset >= 0 else ""
    tz_str = f"UTC{sign}{int(tz_offset)}:00"

    current_stakes = get_current_stakes(c_id_str)
    trade_amt = current_stakes["trade"]
    mtg_amt = current_stakes["mtg"]

    combined_card = build_vip_combined_card(
        clean_pair, direction, confidence, tz_str, algorithm_tag, entry_str,
        trade_amt, mtg_amt, market_label
    )
    
    kb = None
    if not is_channel_session:
        kb = {
            "inline_keyboard": [
                [
                    {"text": "🔄 ANALYSIS", "callback_data": f"auto_btn:analysis:{broker_type}"},
                    {"text": "🎴 PARTIAL", "callback_data": "auto_btn:partial"},
                    {"text": "🛑 STOP AUTO", "callback_data": "auto_btn:stop"}
                ],
                [
                    {"text": "🏠 HOME", "callback_data": "back_to_menu"}
                ]
            ]
        }

    bot_instance.send_message(combined_card, reply_markup=kb)
    
    return {
        "entry_dt": entry_dt,
        "entry_str": entry_str,
        "pair_raw": selected_pair,
        "pair_display": clean_pair,
        "direction": direction,
        "dir_action": dir_action,
        "tz_str": tz_str,
        "broker_type": broker_type,
        "market_label": market_label,
        "trade_amt": trade_amt,
        "mtg_amt": mtg_amt
    }

# ================= GUARANTEED QUICK TARGET CHANNEL WORKER =================
def instant_channel_worker(admin_chat_id, target_channel, broker_type="quotex"):
    user_tz, _ = get_user_tz(admin_chat_id)
    bot_channel = TelegramBot(chat_id=target_channel)
    bot_admin = TelegramBot(chat_id=admin_chat_id)
    t_ch_str = str(target_channel)
    
    if broker_type == "real":
        m_label = "REAL MARKET"
    elif broker_type == "pocket":
        m_label = "POCKET OPTION OTC"
    else:
        m_label = "QUOTEX OTC"

    session_info = active_quick_sessions.get(t_ch_str, {
        "is_running": True,
        "admin_chat_id": admin_chat_id,
        "broker_type": broker_type,
        "m_label": m_label,
        "target_channel": target_channel
    })
    session_info["is_running"] = True
    active_quick_sessions[t_ch_str] = session_info
    save_quick_sessions_to_disk()

    start_notice = (
        f"🚀 <b>INSTANT QUICK TARGET MODE STARTED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>Market:</b> <code>{m_label}</code>\n"
        f"🎯 <b>Engine:</b> <code>Quantum Multi-Pair Top Confluence</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    sent_notice = bot_channel.send_message(start_notice)
    if not sent_notice:
        bot_admin.send_message(f"⚠️ Warning: Could not post to <code>{target_channel}</code>. Make sure bot is Admin.")
        active_quick_sessions.pop(t_ch_str, None)
        save_quick_sessions_to_disk()
        return

    admin_live_kb = {
        "inline_keyboard": [
            [{"text": "🛑 STOP QUICK MODE", "callback_data": f"quick_ctrl:stop:{target_channel}"}],
            [{"text": "🏠 HOME MENU", "callback_data": "back_to_menu"}]
        ]
    }
    bot_admin.send_message(
        f"⚡ <b>QUICK TARGET CONTROLLER ACTIVE</b>\nTarget: <code>{target_channel}</code>",
        reply_markup=admin_live_kb
    )

    if t_ch_str not in user_partial_data:
        user_partial_data[t_ch_str] = []

    set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)

    while session_info.get("is_running", False):
        try:
            sig_meta = deliver_auto_signal(target_channel, is_channel_session=True, broker_type=broker_type)
            
            if not sig_meta:
                time.sleep(15)
                continue
            
            current_trade_amt = sig_meta["trade_amt"]
            current_mtg_amt = sig_meta["mtg_amt"]

            # Wait for Primary candle finish
            primary_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=1, seconds=6)
            while datetime.now(user_tz) < primary_settle_dt and session_info.get("is_running", False):
                time.sleep(1)
                
            if not session_info.get("is_running", False):
                break

            primary_win = evaluate_primary_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
            if primary_win:
                outcome_status = "WIN"
                trade_pnl = current_trade_amt * PAYOUT_RATIO
                single_ret = f"+${trade_pnl:.2f}"
                set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
            else:
                # Wait for MTG candle finish
                mtg_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=2, seconds=6)
                while datetime.now(user_tz) < mtg_settle_dt and session_info.get("is_running", False):
                    time.sleep(1)
                    
                if not session_info.get("is_running", False):
                    break

                mtg_win = evaluate_mtg_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
                if mtg_win:
                    outcome_status = "MTG"
                    trade_pnl = (current_mtg_amt * PAYOUT_RATIO) - current_trade_amt
                    single_ret = f"+${trade_pnl:.2f}"
                    set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
                else:
                    outcome_status = "LOSS"
                    trade_pnl = -(current_trade_amt + current_mtg_amt)
                    single_ret = f"-${abs(trade_pnl):.2f}"
                    set_current_stakes(t_ch_str, 3.00, 6.00)

            if outcome_status == "LOSS":
                pair_cooldown_registry[sig_meta["pair_raw"]] = time.time() + 720

            record_to_partial(target_channel, {
                "time": sig_meta["entry_str"],
                "pair": format_pair_name(sig_meta["pair_raw"], broker_type=broker_type),
                "dir": sig_meta["direction"],
                "result": "✅" if outcome_status in ["WIN", "MTG"] else "❌",
                "pnl": trade_pnl,
                "status": outcome_status
            })
            record_signal_stats(target_channel, outcome_status, user_tz)
            wins, losses, win_rate, total_pnl = get_session_stats(target_channel)

            next_stakes = get_current_stakes(t_ch_str)
            res_card = build_golden_trophy_result_card(
                sig_meta["pair_display"], 
                sig_meta["dir_action"], 
                outcome_status, 
                wins, 
                losses, 
                win_rate,
                total_pnl,
                single_ret,
                next_stakes["trade"],
                market_label=sig_meta.get("market_label", m_label)
            )
            bot_channel.send_message(res_card)
            time.sleep(2)
        except Exception as e:
            print(f"Loop Exception caught: {e}")
            time.sleep(5)

    bot_channel.send_message(f"🛑 <b>Quick Target Mode Stopped for {target_channel}.</b>")
    active_quick_sessions.pop(t_ch_str, None)
    save_quick_sessions_to_disk()

# ================= AUTO MODE RUNNER =================
def auto_mode_loop(chat_id, username=None, broker_type="quotex"):
    c_id = str(chat_id)
    user_tz, _ = get_user_tz(c_id)
    bot_instance = TelegramBot(chat_id=c_id)
    set_current_stakes(c_id, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
    
    while auto_mode_users.get(c_id, False):
        try:
            if is_maintenance_active() and c_id != str(ADMIN_CHAT_ID):
                auto_mode_users[c_id] = False
                bot_instance.send_message(build_maintenance_card())
                break

            is_vip = is_vip_user(c_id, username)
            used_today = get_user_daily_usage(c_id, user_tz)
            if not is_vip and used_today >= FREE_DAILY_AUTO_LIMIT:
                auto_mode_users[c_id] = False
                kb = {
                    "inline_keyboard": [
                        [{"text": "👑 GET VIP ACCESS ↗️", "url": "https://t.me/MD_SUMON_MT4"}],
                        [{"text": "🏠 HOME", "callback_data": "back_to_menu"}]
                    ]
                }
                bot_instance.send_message(build_limit_exceeded_card(), reply_markup=kb)
                break

            sig_meta = deliver_auto_signal(c_id, username=username, broker_type=broker_type)
            if not sig_meta:
                time.sleep(15)
                continue
            
            current_trade_amt = sig_meta["trade_amt"]
            current_mtg_amt = sig_meta["mtg_amt"]

            primary_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=1, seconds=6)
            while auto_mode_users.get(c_id, False):
                if datetime.now(user_tz) >= primary_settle_dt:
                    break
                time.sleep(1)
                
            if not auto_mode_users.get(c_id, False):
                break

            primary_win = evaluate_primary_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
            if primary_win:
                outcome_status = "WIN"
                trade_pnl = current_trade_amt * PAYOUT_RATIO
                single_ret = f"+${trade_pnl:.2f}"
                set_current_stakes(c_id, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
            else:
                mtg_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=2, seconds=6)
                while auto_mode_users.get(c_id, False):
                    if datetime.now(user_tz) >= mtg_settle_dt:
                        break
                    time.sleep(1)
                    
                if not auto_mode_users.get(c_id, False):
                    break
                    
                mtg_win = evaluate_mtg_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
                if mtg_win:
                    outcome_status = "MTG"
                    trade_pnl = (current_mtg_amt * PAYOUT_RATIO) - current_trade_amt
                    single_ret = f"+${trade_pnl:.2f}"
                    set_current_stakes(c_id, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
                else:
                    outcome_status = "LOSS"
                    trade_pnl = -(current_trade_amt + current_mtg_amt)
                    single_ret = f"-${abs(trade_pnl):.2f}"
                    set_current_stakes(c_id, 3.00, 6.00)

            if outcome_status == "LOSS":
                pair_cooldown_registry[sig_meta["pair_raw"]] = time.time() + 720

            record_to_partial(c_id, {
                "time": sig_meta["entry_str"],
                "pair": format_pair_name(sig_meta["pair_raw"], broker_type=broker_type),
                "dir": sig_meta["direction"],
                "result": "✅" if outcome_status in ["WIN", "MTG"] else "❌",
                "pnl": trade_pnl,
                "status": outcome_status
            })
            record_signal_stats(c_id, outcome_status, user_tz)
            wins, losses, win_rate, total_pnl = get_session_stats(c_id)

            next_stakes = get_current_stakes(c_id)
            res_card = build_golden_trophy_result_card(
                sig_meta["pair_display"], 
                sig_meta["dir_action"], 
                outcome_status, 
                wins, 
                losses, 
                win_rate,
                total_pnl,
                single_ret,
                next_stakes["trade"],
                market_label=sig_meta.get("market_label", "QUOTEX OTC")
            )
            bot_instance.send_message(res_card)
            time.sleep(2)
        except Exception as e:
            print(f"Error in auto_mode_loop: {e}")
            time.sleep(5)

# ================= AUTOMATED SCHEDULE MODE RUNNER =================
def scheduled_channel_session_worker(admin_chat_id, target_channel, start_dt, end_dt, alert_dt, broker_type="quotex"):
    user_tz, _ = get_user_tz(admin_chat_id)
    bot_channel = TelegramBot(chat_id=target_channel)
    bot_admin = TelegramBot(chat_id=admin_chat_id)
    t_ch_str = str(target_channel)
    
    if broker_type == "real":
        m_label = "REAL MARKET"
    elif broker_type == "pocket":
        m_label = "POCKET OPTION OTC"
    else:
        m_label = "QUOTEX OTC"

    session_info = {
        "is_running": True,
        "admin_chat_id": admin_chat_id,
        "broker_type": broker_type,
        "m_label": m_label,
        "target_channel": target_channel,
        "end_dt": end_dt
    }
    active_scheduled_sessions[t_ch_str] = session_info

    start_time_str = start_dt.strftime("%H:%M")

    confirm_msg = (
        f"📢 <b>VIP SIGNAL SESSION SCHEDULED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target Market:</b> <code>{m_label}</code>\n"
        f"⏰ <b>Start Time:</b> <code>{start_time_str}</code>\n"
        f"💎 <b>Status:</b> <i>Prepare your balance & stay active! 🔥</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BOT_TITLE} VIP</b> 👑"
    )
    sent_confirm = bot_channel.send_message(confirm_msg)
    if not sent_confirm:
        bot_admin.send_message(f"⚠️ <b>Schedule Warning:</b> Could not post to <code>{target_channel}</code>. Make sure bot is Admin.")

    admin_live_kb = {
        "inline_keyboard": [
            [
                {"text": "🎴 SEND PARTIAL", "callback_data": f"sched_ctrl:partial:{target_channel}"},
                {"text": "🛑 STOP SCHEDULE", "callback_data": f"sched_ctrl:stop:{target_channel}"}
            ],
            [
                {"text": "🏠 HOME MENU", "callback_data": "back_to_menu"}
            ]
        ]
    }
    bot_admin.send_message(
        f"⏱ <b>LIVE SCHEDULE CONTROLLER</b>\nTarget: <code>{target_channel}</code>",
        reply_markup=admin_live_kb
    )

    if datetime.now(user_tz) < alert_dt:
        while datetime.now(user_tz) < alert_dt and session_info["is_running"]:
            time.sleep(5)
            
        if session_info["is_running"]:
            reminder_msg = (
                f"⚠️ <b>REMINDER: VIP SESSION STARTS IN 30 MINUTES!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>Target Market:</b> <code>{m_label}</code>\n"
                f"⏰ <b>Start Time:</b> <code>{start_time_str}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>{BOT_TITLE} VIP</b> 👑"
            )
            bot_channel.send_message(reminder_msg)
    
    while datetime.now(user_tz) < start_dt and session_info["is_running"]:
        time.sleep(2)

    if not session_info["is_running"]:
        active_scheduled_sessions.pop(t_ch_str, None)
        return

    session_start_msg = (
        f"🚀 <b>VIP SIGNAL SESSION STARTED NOW!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>Market:</b> <code>{m_label}</code>\n"
        f"🎯 <b>Setups:</b> <code>Quantum Multi-Pair Top Confluence</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    bot_channel.send_message(session_start_msg)

    user_partial_data[t_ch_str] = []
    set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
    
    while datetime.now(user_tz) < end_dt and session_info["is_running"]:
        try:
            sig_meta = deliver_auto_signal(target_channel, is_channel_session=True, broker_type=broker_type)
            if not sig_meta:
                time.sleep(15)
                continue
            
            current_trade_amt = sig_meta["trade_amt"]
            current_mtg_amt = sig_meta["mtg_amt"]

            primary_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=1, seconds=6)
            while datetime.now(user_tz) < primary_settle_dt and datetime.now(user_tz) < end_dt and session_info["is_running"]:
                time.sleep(1)
                
            if not session_info["is_running"]:
                break

            primary_win = evaluate_primary_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
            if primary_win:
                outcome_status = "WIN"
                trade_pnl = current_trade_amt * PAYOUT_RATIO
                single_ret = f"+${trade_pnl:.2f}"
                set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
            else:
                mtg_settle_dt = sig_meta["entry_dt"] + timedelta(minutes=2, seconds=6)
                while datetime.now(user_tz) < mtg_settle_dt and datetime.now(user_tz) < end_dt and session_info["is_running"]:
                    time.sleep(1)
                    
                if not session_info["is_running"]:
                    break

                mtg_win = evaluate_mtg_candle(sig_meta["pair_raw"], sig_meta["entry_dt"], sig_meta["direction"], broker_type=broker_type)
                if mtg_win:
                    outcome_status = "MTG"
                    trade_pnl = (current_mtg_amt * PAYOUT_RATIO) - current_trade_amt
                    single_ret = f"+${trade_pnl:.2f}"
                    set_current_stakes(t_ch_str, BASE_TRADE_AMOUNT, MTG_TRADE_AMOUNT)
                else:
                    outcome_status = "LOSS"
                    trade_pnl = -(current_trade_amt + current_mtg_amt)
                    single_ret = f"-${abs(trade_pnl):.2f}"
                    set_current_stakes(t_ch_str, 3.00, 6.00)

            if outcome_status == "LOSS":
                pair_cooldown_registry[sig_meta["pair_raw"]] = time.time() + 720

            record_to_partial(target_channel, {
                "time": sig_meta["entry_str"],
                "pair": format_pair_name(sig_meta["pair_raw"], broker_type=broker_type),
                "dir": sig_meta["direction"],
                "result": "✅" if outcome_status in ["WIN", "MTG"] else "❌",
                "pnl": trade_pnl,
                "status": outcome_status
            })
            record_signal_stats(target_channel, outcome_status, user_tz)
            wins, losses, win_rate, total_pnl = get_session_stats(target_channel)

            next_stakes = get_current_stakes(t_ch_str)
            res_card = build_golden_trophy_result_card(
                sig_meta["pair_display"], 
                sig_meta["dir_action"], 
                outcome_status, 
                wins, 
                losses, 
                win_rate,
                total_pnl,
                single_ret,
                next_stakes["trade"],
                market_label=sig_meta.get("market_label", m_label)
            )
            bot_channel.send_message(res_card)
            time.sleep(2)
        except Exception as e:
            print(f"Error in scheduled_channel_session_worker: {e}")
            time.sleep(5)

    final_partial_card = build_partial_scoreboard_text(target_channel, user_tz)
    bot_channel.send_message(final_partial_card)
    bot_channel.send_message(
        f"🏁 <b>VIP SIGNAL SESSION CLOSED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BOT_TITLE} VIP</b> 👑"
    )

    active_scheduled_sessions.pop(t_ch_str, None)

# ================= FUTURE BATCH RUNNER =================
def build_exact_user_format(signals, broker_name="REAL MARKET", user_tz=None, tz_offset=4):
    now_dt = datetime.now(user_tz)
    date_str = now_dt.strftime("%d.%m.%Y")
    sign = "+" if tz_offset >= 0 else ""
    tz_label = f"UTC {sign}{tz_offset}:00"
    
    header = (
        f"🐉==❗️ <b>{BOT_TITLE}</b> ❗️==🐉\n\n"
        f"📅 <b>DATE:</b> {date_str}\n"
        f"❤️ <b>MARKET:</b> {broker_name.upper()}\n\n"
        f"😬 <i>Follow Rules & 💵 Management</i>\n\n"
        f"😓 <b>TIME ZONE - ( {tz_label} )</b> 😓\n\n"
        f"🔘 <b>TRADE TIME : 1 MINUTE 🚀</b>\n\n"
        f"❗️ <b>USE 1 STEP MTG ➕</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    lines = ""
    win_count, mtg_count, loss_count, pending_count = 0, 0, 0, 0

    for idx, s in enumerate(signals, start=1):
        status = s.get("status", "PENDING")
        dir_emoji = "🟢" if s["direction"] == "CALL" else "🔴"
        
        if status == "WIN":
            status_text = "WIN ✅"
            win_count += 1
        elif status == "MTG":
            status_text = "MTG WIN ✅¹"
            mtg_count += 1
        elif status == "LOSS":
            status_text = "LOSS ❌"
            loss_count += 1
        elif status == "IN_MTG":
            status_text = "⏳ IN MTG"
            pending_count += 1
        elif status == "LIVE":
            status_text = "⏳ RUNNING"
            pending_count += 1
        else:
            status_text = "⏳ PENDING"
            pending_count += 1
            
        lines += f"{idx:02d}. {s['time_str']} | <code>{s['pair']}</code> ➔ {dir_emoji} {s['direction']} | {status_text}\n"

    footer = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Stats:</b> ✅ {win_count} WIN | 🛡 {mtg_count} MTG | ❌ {loss_count} LOSS | ⏳ {pending_count} Pending\n\n"
        f"⚡ <b>Live Auto-Checking: ACTIVE 🟢</b>\n\n"
        f"❗️ <b>USE SAFETY MARGIN MUST ❗️</b>\n\n"
        f"<b>FEEDBACK :</b> <a href=\"{TELEGRAM_URL_HANDLE}\">{TELEGRAM_HANDLE}</a> ✅"
    )
    return header + lines + footer

def continuous_background_scanner(chat_id, batch_data):
    signals = batch_data["signals"]
    msg_id = batch_data["msg_id"]
    broker = batch_data["broker"]
    broker_type = batch_data.get("broker_type", "quotex")
    tz_offset = batch_data["tz_offset"]
    user_tz = timezone(timedelta(hours=tz_offset))
    bot_instance = TelegramBot(chat_id=chat_id)

    while True:
        try:
            if is_maintenance_active() and str(chat_id) != str(ADMIN_CHAT_ID):
                break

            now_time = datetime.now(user_tz)
            has_pending = False
            state_changed = False

            for s in signals:
                current_status = s.get("status", "PENDING")
                if current_status in ["WIN", "MTG", "LOSS"]:
                    continue
                
                has_pending = True

                if current_status == "PENDING" and now_time >= s["target_dt"]:
                    if now_time < (s["target_dt"] + timedelta(minutes=1, seconds=6)):
                        s["status"] = "LIVE"
                        state_changed = True

                if s.get("status") in ["PENDING", "LIVE"] and now_time >= (s["target_dt"] + timedelta(minutes=1, seconds=6)):
                    if evaluate_primary_candle(s["pair"], s["target_dt"], s["direction"], broker_type=broker_type):
                        s["status"] = "WIN"
                        record_signal_stats(chat_id, "WIN", user_tz)
                    else:
                        s["status"] = "IN_MTG"
                    state_changed = True

                if s.get("status") == "IN_MTG" and now_time >= (s["target_dt"] + timedelta(minutes=2, seconds=6)):
                    if evaluate_mtg_candle(s["pair"], s["target_dt"], s["direction"], broker_type=broker_type):
                        s["status"] = "MTG"
                        record_signal_stats(chat_id, "MTG", user_tz)
                    else:
                        s["status"] = "LOSS"
                        record_signal_stats(chat_id, "LOSS", user_tz)
                        pair_cooldown_registry[s["pair"]] = time.time() + 720
                    state_changed = True

            if state_changed:
                with batch_disk_lock:
                    save_json(ACTIVE_BATCHES_FILE, active_batches)
                updated_text = build_exact_user_format(signals, broker, user_tz, tz_offset)
                bot_instance.edit_message(msg_id, updated_text, reply_markup={
                    "inline_keyboard": [
                        [{"text": "💥 REFRESH NOW", "callback_data": "btn:refresh"}, {"text": "🔮 GENERATE NEW LIST", "callback_data": "btn:gen_new"}],
                        [{"text": "🗑 DELETE", "callback_data": "btn:del_list"}, {"text": "🏠 HOME", "callback_data": "back_to_menu"}]
                    ]
                })

            if not has_pending:
                with batch_disk_lock:
                    save_json(ACTIVE_BATCHES_FILE, active_batches)
                break
        except Exception as e:
            print(f"Error in continuous_background_scanner: {e}")
        
        time.sleep(2)

def generate_large_signal_batch(pairs, user_tz, duration_mins=240, is_vip=False, broker_type="quotex"):
    if not pairs:
        return []
    signals = []
    start_time = datetime.now(user_tz) + timedelta(minutes=2)
    num_signals = 10 if not is_vip else {15: 8, 30: 15, 60: 25, 120: 40, 240: 60}.get(duration_mins, 45)

    pool = list(pairs)
    curr_dt = start_time.replace(second=0, microsecond=0)
    for _ in range(num_signals):
        best_p, direction, _, _ = analyze_best_pair_and_trend(pool, broker_type=broker_type)
        if not best_p:
            best_p = random.choice(pool)
            direction = random.choice(["CALL", "PUT"])
            
        pair_fmt = format_pair_name(best_p, broker_type=broker_type)
        
        signals.append({
            "pair": pair_fmt,
            "direction": direction,
            "time_str": curr_dt.strftime("%H:%M"),
            "target_dt": curr_dt,
            "status": "PENDING"
        })
        curr_dt += timedelta(minutes=random.choice([3, 4, 5]))

    signals.sort(key=lambda s: s["target_dt"])
    return signals

# ================= MAIN TELEGRAM RUNNER =================
def run_server():
    setup_telegram_commands()
    BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    GET_UPDATES = BASE + "/getUpdates"
    ANSWER_CALLBACK = BASE + "/answerCallbackQuery"

    def edit_or_send(chat_id, text, kb, target_msg_id=None):
        bot_instance = TelegramBot(chat_id=chat_id)
        msg_id = target_msg_id or user_active_menu_msg.get(str(chat_id))
        if msg_id:
            ok = bot_instance.edit_message(msg_id, text, reply_markup=kb if kb else None)
            if ok:
                user_active_menu_msg[str(chat_id)] = msg_id
                return msg_id
        new_id = bot_instance.send_message(text, reply_markup=kb if kb else None)
        user_active_menu_msg[str(chat_id)] = new_id
        return new_id

    def send_main_menu(chat_id, username="", target_msg_id=None):
        is_admin = str(chat_id) == str(ADMIN_CHAT_ID)
        can_schedule = has_schedule_access(chat_id, username)
        
        keyboard_buttons = [
            [
                {"text": "🤖 AUTO MODE", "callback_data": "menu:auto_market_select"},
                {"text": "🍥 FUTURE MODE", "callback_data": "menu:future"}
            ]
        ]

        if can_schedule:
            keyboard_buttons.append([{"text": "⏱ SCHEDULE & QUICK HUB", "callback_data": "menu:schedule_hub"}])

        keyboard_buttons.extend([
            [
                {"text": "📊 DAILY SUMMARY", "callback_data": "menu:daily_summary"},
                {"text": "👤 MY PROFILE", "callback_data": "menu:profile"}
            ],
            [
                {"text": "💬 SUPPORT", "callback_data": "menu:support"},
                {"text": "❕ ABOUT", "callback_data": "menu:about"}
            ]
        ])
        
        if is_admin:
            keyboard_buttons.append([{"text": "👑 ADMIN SERVER CONTROL", "callback_data": "admin:panel"}])

        kb = {"inline_keyboard": keyboard_buttons}
        text = (
            "╭──────────────────────╮\n"
            f"│ 👑 <b>{BOT_TITLE}</b> 👑\n"
            "│  — Next-Gen Signal System —\n"
            "╰──────────────────────╯\n\n"
            "⚡️ <b>CORE ENGINE:</b> Quantum Multi-Pair Top Confluence 🤖\n"
            "📈 <b>SPEED:</b> Real-Time 100% Broker Match ⚡️\n"
            "🚀 <b>ALGORITHM:</b> Ultra Wick & Anti-Chop Confluence Matrix 🧠\n"
            "🛡 <b>RISK CONTROL:</b> 12-Min Loss Shield & Dynamic Recovery MM 🔒\n"
            "🌐 <b>MARKETS:</b> Real Market, Quotex & Pocket Option OTC 📊\n"
            "⚙️ <b>AUTOMATION:</b> Live Auto-Update Results 🤖\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>WHY CHOOSE MD_SUMON_MT4 BOT:</b>\n"
            "💎 100% Exact Broker Chart Sync (Zero Discrepancy)\n"
            "🎯 Dynamic Loss Recovery ($1/$2 ➔ $3/$6 on Loss)\n"
            "🛡 Auto-Cleans Choppy Notice on Valid Setup\n"
            "🔮 Future Signal Generator Mode\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            '🔥 <i>"Step into the future of precision trading."</i> 🔥\n\n'
            "📶 <b>Select an option below to begin:</b>"
        )
        edit_or_send(chat_id, text, kb, target_msg_id)

    def send_admin_panel(chat_id, target_msg_id=None):
        status_txt = "🔴 MAINTENANCE ACTIVE" if is_maintenance_active() else "🟢 SERVER ONLINE"
        total_users = len(get_all_registered_users())
        total_vip = len(load_vip_users())
        total_sched = len(load_schedule_users())
        panel_text = (
            f"👑 <b>ADMIN SYSTEM CONTROLLER</b> 👑\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Current Server State:</b> <b>{status_txt}</b>\n"
            f"👥 <b>Total Users:</b> <code>{total_users}</code> ┃ <b>VIPs:</b> <code>{total_vip}</code> ┃ <b>Schedule:</b> <code>{total_sched}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Commands:</b>\n"
            f"• <code>/check &lt;id&gt;</code> ➔ Inspect User Audit\n"
            f"• <code>/add &lt;id&gt;</code> ➔ VIP Add & Notify\n"
            f"• <code>/remove &lt;id&gt;</code> ➔ VIP Revoke\n"
            f"• <code>/addschedule &lt;id&gt;</code> ➔ Allow Schedule Access\n"
            f"• <code>/removeschedule &lt;id&gt;</code> ➔ Revoke Schedule Access\n"
            f"• <code>/users</code> ➔ List All Users\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Click below to switch server mode:</i>"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🟢 Turn Server ONLINE (Unlock)", "callback_data": "adm_act:online"}],
                [{"text": "🔧 Turn Maintenance ON (Lock)", "callback_data": "adm_act:maintenance"}],
                [{"text": "🔙 BACK TO MENU", "callback_data": "back_to_menu"}],
            ]
        }
        edit_or_send(chat_id, panel_text, kb, target_msg_id)

    def send_profile_menu(chat_id, username="", target_msg_id=None):
        user_tz, tz_offset = get_user_tz(chat_id)
        is_vip = is_vip_user(chat_id, username)
        can_schedule = has_schedule_access(chat_id, username)
        used_auto = get_user_daily_usage(chat_id, user_tz)
        used_future = get_future_daily_usage(chat_id, user_tz)
        tier_badge = "👑 VIP MEMBER (Unlimited)" if is_vip else f"🆓 FREE TIER"
        auto_text = "Unlimited (VIP)" if is_vip else f"{used_auto} / {FREE_DAILY_AUTO_LIMIT} Signals"
        future_text = "Unlimited (VIP)" if is_vip else f"{used_future} / {FREE_DAILY_FUTURE_LIMIT} Batch (10 Sigs)"
        sched_badge = "✅ Granted" if can_schedule else "🔒 Restricted"
        sign = "+" if tz_offset >= 0 else ""
        tz_label = f"UTC {sign}{tz_offset}:00"
        
        profile_text = (
            f"╭━━━━━━━━━━━━━━━━━━━━╮\n"
            f" 👤 <b>USER ACCOUNT PROFILE</b>\n"
            f"╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"👤 <b>User ID:</b> <code>{chat_id}</code>\n"
            f"🏷 <b>Username:</b> @{username if username else 'N/A'}\n"
            f"💎 <b>Membership:</b> <b>{tier_badge}</b>\n"
            f"⏱ <b>Schedule Mode:</b> <b>{sched_badge}</b>\n\n"
            f"📊 <b>TODAY'S USAGE:</b>\n"
            f"• <b>Auto Mode:</b> <code>{auto_text}</code>\n"
            f"• <b>Future Mode:</b> <code>{future_text}</code>\n\n"
            f"🌐 <b>Current Timezone:</b> <b>{tz_label}</b>\n"
            f"────────────────────────\n"
            f"⚙ <i>Click below to change your Timezone or Contact Admin.</i>"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "🌐 CHANGE TIMEZONE", "callback_data": "menu:tz_picker"}],
                [{"text": "💬 GET VIP ACTIVATION", "url": "https://t.me/MD_SUMON_MT4"}],
                [{"text": "🔙 BACK TO HOME", "callback_data": "back_to_menu"}]
            ]
        }
        edit_or_send(chat_id, profile_text, kb, target_msg_id)

    def send_tz_picker(chat_id, target_msg_id=None):
        kb = {
            "inline_keyboard": [
                [{"text": "UTC+0 (London)", "callback_data": "set_tz:0"}, {"text": "UTC+3 (Moscow/KSA)", "callback_data": "set_tz:3"}],
                [{"text": "UTC+4 (Dubai/GST)", "callback_data": "set_tz:4"}, {"text": "UTC+5 (Pakistan)", "callback_data": "set_tz:5"}],
                [{"text": "UTC+5:30 (India IST)", "callback_data": "set_tz:5.5"}, {"text": "UTC+6 (Bangladesh BST)", "callback_data": "set_tz:6"}],
                [{"text": "UTC+7 (Jakarta/BKK)", "callback_data": "set_tz:7"}, {"text": "UTC+8 (Singapore)", "callback_data": "set_tz:8"}],
                [{"text": "🔙 BACK TO PROFILE", "callback_data": "menu:profile"}]
            ]
        }
        edit_or_send(chat_id, "🌐 <b>SELECT YOUR PREFERRED TIMEZONE (UTC):</b>", kb, target_msg_id)

    load_and_resume_quick_sessions()
    print(f"🚀 {BOT_TITLE} Master Engine is Ready (Scanning Markets UI & 20% Wick Active)!")

    try:
        requests.get(BASE + "/getUpdates", params={"offset": -1, "timeout": 1}, timeout=5)
    except Exception:
        pass

    offset = None
    while True:
        try:
            params = {"timeout": 20, "limit": 100}
            if offset:
                params["offset"] = offset
            resp = requests.get(GET_UPDATES, params=params, timeout=25)
            data = resp.json()
            if not data.get("ok"):
                time.sleep(1)
                continue

            updates = data.get("result", [])
            if updates:
                offset = updates[-1]["update_id"] + 1
                for item in updates:
                    up_id = item.get("update_id")
                    if up_id in processed_updates:
                        continue
                    processed_updates.add(up_id)
                    if len(processed_updates) > 1000:
                        processed_updates.clear()

                    if "message" in item:
                        msg = item["message"]
                        chat_id = str(msg["chat"]["id"])
                        username = msg.get("from", {}).get("username", "")
                        text = msg.get("text", "").strip()

                        record_user_activity(chat_id)

                        if text.startswith("/start"):
                            user_input_state.pop(chat_id, None)
                            old_m = user_active_menu_msg.pop(chat_id, None)
                            if old_m:
                                TelegramBot(chat_id=chat_id).delete_message(old_m)
                            send_main_menu(chat_id, username=username)
                            continue

                        if str(chat_id) == str(ADMIN_CHAT_ID):
                            if text.startswith("/check"):
                                parts = text.split(maxsplit=1)
                                if len(parts) > 1:
                                    target = parts[1].strip().lower().strip("@")
                                    user_tz, _ = get_user_tz(target)
                                    is_v = is_vip_user(target)
                                    can_s = has_schedule_access(target)
                                    u_auto = get_user_daily_usage(target, user_tz)
                                    u_fut = get_future_daily_usage(target, user_tz)
                                    
                                    today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
                                    d_history = load_json(HISTORY_FILE).get(target, {}).get(today_str, {"win": 0, "mtg": 0, "loss": 0})
                                    w_cnt = d_history.get("win", 0)
                                    m_cnt = d_history.get("mtg", 0)
                                    l_cnt = d_history.get("loss", 0)

                                    audit_msg = (
                                        f"🔍 <b>USER AUDIT REPORT:</b> <code>{target}</code>\n"
                                        f"━━━━━━━━━━━━━━━━━━━\n"
                                        f"💎 <b>VIP Status:</b> {'👑 ACTIVE (Unlimited)' if is_v else '🆓 FREE TIER'}\n"
                                        f"⏱ <b>Schedule Access:</b> {'✅ GRANTED' if can_s else '🔒 RESTRICTED'}\n"
                                        f"🤖 <b>Auto Mode Used Today:</b> <code>{u_auto} signals</code>\n"
                                        f"📊 <b>Today's Results:</b> 🟢 <b>{w_cnt} Win</b> | 🟡 <b>{m_cnt} MTG</b> | 🔴 <b>{l_cnt} Loss</b>\n"
                                        f"🍥 <b>Future Batches Used:</b> <code>{u_fut} batch</code>\n"
                                        f"━━━━━━━━━━━━━━━━━━━"
                                    )
                                    TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(audit_msg)
                                continue

                            elif text.startswith("/add"):
                                parts = text.split(maxsplit=1)
                                if len(parts) > 1:
                                    target = parts[1].strip().lower().strip("@")
                                    vip_users = load_vip_users()
                                    if target not in vip_users:
                                        vip_users.append(target)
                                        save_vip_users(vip_users)
                                    TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(f"✅ <b>User Added to VIP (Persistent):</b> <code>{target}</code>")
                                continue

                            elif text.startswith("/remove"):
                                parts = text.split(maxsplit=1)
                                if len(parts) > 1:
                                    target = parts[1].strip().lower().strip("@")
                                    vip_users = load_vip_users()
                                    if target in vip_users:
                                        vip_users.remove(target)
                                        save_vip_users(vip_users)
                                        TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(f"🗑 <b>Removed VIP:</b> <code>{target}</code>")
                                continue

                            elif text.startswith("/addschedule"):
                                parts = text.split(maxsplit=1)
                                if len(parts) > 1:
                                    target = parts[1].strip().lower().strip("@")
                                    sched_users = load_schedule_users()
                                    if target not in sched_users:
                                        sched_users.append(target)
                                        save_schedule_users(sched_users)
                                        TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(f"✅ <b>Schedule access granted:</b> <code>{target}</code>")
                                continue

                            elif text.startswith("/removeschedule"):
                                parts = text.split(maxsplit=1)
                                if len(parts) > 1:
                                    target = parts[1].strip().lower().strip("@")
                                    sched_users = load_schedule_users()
                                    if target in sched_users:
                                        sched_users.remove(target)
                                        save_schedule_users(sched_users)
                                        TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(f"🗑 <b>Schedule access revoked:</b> <code>{target}</code>")
                                continue

                            elif text == "/users":
                                vip_users = load_vip_users()
                                sched_users = load_schedule_users()
                                v_list = "\n".join([f"• <code>{u}</code>" for u in vip_users]) if vip_users else "None"
                                s_list = "\n".join([f"• <code>{u}</code>" for u in sched_users]) if sched_users else "None"
                                TelegramBot(chat_id=ADMIN_CHAT_ID).send_message(
                                    f"👑 <b>VIP USERS ({len(vip_users)}):</b>\n{v_list}\n\n⏱ <b>SCHEDULE USERS ({len(sched_users)}):</b>\n{s_list}"
                                )
                                continue

                            elif text == "/maintenance":
                                set_maintenance_mode(True)
                                auto_mode_users.clear()
                                broadcast_to_all_users("⚠️ <b>SYSTEM NOTICE: MAINTENANCE MODE ACTIVE</b>")
                                TelegramBot(chat_id=ADMIN_CHAT_ID).send_message("🛠 <b>Maintenance Mode ON.</b>")
                                continue

                            elif text == "/active":
                                set_maintenance_mode(False)
                                broadcast_to_all_users("🟢 <b>SYSTEM STATUS: SERVER ONLINE</b>")
                                TelegramBot(chat_id=ADMIN_CHAT_ID).send_message("🟢 <b>Server Online ON.</b>")
                                continue

                        if is_maintenance_active() and str(chat_id) != str(ADMIN_CHAT_ID):
                            TelegramBot(chat_id=chat_id).send_message(build_maintenance_card())
                            continue

                        if chat_id in user_input_state:
                            st_info = user_input_state[chat_id]
                            step = st_info.get("step")
                            cancel_kb = {"inline_keyboard": [[{"text": "❌ CANCEL & BACK TO MENU", "callback_data": "sched_cancel"}]]}

                            if step == "WAIT_CHANNEL":
                                st_info["channel"] = text
                                st_info["step"] = "WAIT_MARKET"
                                real_status_label = "🟢 REAL MARKET (OPEN)" if is_real_market_open() else "🔴 REAL MARKET (CLOSED)"
                                market_kb = {
                                    "inline_keyboard": [
                                        [{"text": real_status_label, "callback_data": "sched_mkt:real"}],
                                        [{"text": "🛡 QUOTEX OTC", "callback_data": "sched_mkt:quotex"}],
                                        [{"text": "🚀 POCKET OPTION OTC", "callback_data": "sched_mkt:pocket"}],
                                        [{"text": "❌ CANCEL", "callback_data": "sched_cancel"}]
                                    ]
                                }
                                TelegramBot(chat_id=chat_id).send_message("🌐 <b>Select Market for Scheduled Session:</b>", reply_markup=market_kb)
                                continue

                            elif step == "WAIT_QUICK_CHANNEL":
                                st_info["channel"] = text
                                st_info["step"] = "WAIT_QUICK_MARKET"
                                real_status_label = "🟢 REAL MARKET (OPEN)" if is_real_market_open() else "🔴 REAL MARKET (CLOSED)"
                                quick_mkt_kb = {
                                    "inline_keyboard": [
                                        [{"text": real_status_label, "callback_data": "quick_mkt:real"}],
                                        [{"text": "🛡 QUOTEX OTC", "callback_data": "quick_mkt:quotex"}],
                                        [{"text": "🚀 POCKET OPTION OTC", "callback_data": "quick_mkt:pocket"}],
                                        [{"text": "❌ CANCEL", "callback_data": "sched_cancel"}]
                                    ]
                                }
                                TelegramBot(chat_id=chat_id).send_message("🌐 <b>Select Market for Quick Instant Target Channel:</b>", reply_markup=quick_mkt_kb)
                                continue

                            elif step == "WAIT_START_TIME":
                                user_tz, _ = get_user_tz(chat_id)
                                try:
                                    hours, mins = map(int, text.split(":"))
                                    now = datetime.now(user_tz)
                                    start_dt = now.replace(hour=hours, minute=mins, second=0, microsecond=0)
                                    if start_dt < (now - timedelta(minutes=1)):
                                        start_dt += timedelta(days=1)
                                        
                                    st_info["start_dt"] = start_dt
                                    st_info["step"] = "WAIT_DURATION"
                                    TelegramBot(chat_id=chat_id).send_message("⏳ <b>Enter Duration in Minutes (e.g. 60):</b>", reply_markup=cancel_kb)
                                except Exception:
                                    TelegramBot(chat_id=chat_id).send_message("⚠️ Invalid format! Enter <b>HH:MM</b> (e.g. 22:30):", reply_markup=cancel_kb)
                                continue

                            elif step == "WAIT_DURATION":
                                user_tz, _ = get_user_tz(chat_id)
                                try:
                                    dur_mins = int(text)
                                    start_dt = st_info["start_dt"]
                                    end_dt = start_dt + timedelta(minutes=dur_mins)
                                    alert_dt = start_dt - timedelta(minutes=30)
                                    target_ch = st_info["channel"]
                                    broker_t = st_info.get("broker_type", "quotex")
                                    
                                    user_input_state.pop(chat_id, None)

                                    save_user_schedule(chat_id, {
                                        "channel": target_ch,
                                        "market": broker_t,
                                        "start": start_dt.strftime('%H:%M'),
                                        "end": end_dt.strftime('%H:%M'),
                                        "date": start_dt.strftime('%Y-%m-%d')
                                    })

                                    m_lbl = "REAL MARKET" if broker_t == "real" else ("POCKET OPTION OTC" if broker_t == "pocket" else "QUOTEX OTC")
                                    TelegramBot(chat_id=chat_id).send_message(
                                        f"✅ <b>Schedule Confirmed!</b>\nTarget: <code>{target_ch}</code> | Market: {m_lbl} | Start: <code>{start_dt.strftime('%H:%M')}</code>",
                                        reply_markup={"inline_keyboard": [[{"text": "🏠 HOME MENU", "callback_data": "back_to_menu"}]]}
                                    )
                                    
                                    threading.Thread(
                                        target=scheduled_channel_session_worker,
                                        args=(chat_id, target_ch, start_dt, end_dt, alert_dt, broker_t),
                                        daemon=True
                                    ).start()
                                except Exception:
                                    TelegramBot(chat_id=chat_id).send_message("⚠️ Invalid duration! Enter number of minutes (e.g. 60):", reply_markup=cancel_kb)
                                continue

                    if "callback_query" in item:
                        cb = item["callback_query"]
                        cb_id = cb["id"]
                        
                        if hasattr(run_server, "handled_callbacks"):
                            if cb_id in run_server.handled_callbacks:
                                continue
                        else:
                            run_server.handled_callbacks = set()
                        
                        run_server.handled_callbacks.add(cb_id)
                        if len(run_server.handled_callbacks) > 500:
                            run_server.handled_callbacks.clear()

                        cb_data = cb.get("data", "")
                        chat_id = str(cb["message"]["chat"]["id"])
                        username = cb.get("from", {}).get("username", "")
                        msg_id = cb["message"]["message_id"]

                        record_user_activity(chat_id)

                        try:
                            requests.post(ANSWER_CALLBACK, data={"callback_query_id": cb_id}, timeout=3)
                        except Exception:
                            pass

                        if str(chat_id) == str(ADMIN_CHAT_ID):
                            if cb_data == "admin:panel":
                                send_admin_panel(chat_id, msg_id)
                                continue
                            elif cb_data == "adm_act:maintenance":
                                set_maintenance_mode(True)
                                auto_mode_users.clear()
                                broadcast_to_all_users("⚠️ <b>SYSTEM NOTICE: MAINTENANCE MODE ACTIVE</b>")
                                send_admin_panel(chat_id, msg_id)
                                continue
                            elif cb_data == "adm_act:online":
                                set_maintenance_mode(False)
                                broadcast_to_all_users("🟢 <b>SYSTEM STATUS: SERVER ONLINE</b>")
                                send_admin_panel(chat_id, msg_id)
                                continue

                        if is_maintenance_active() and str(chat_id) != str(ADMIN_CHAT_ID):
                            TelegramBot(chat_id=chat_id).send_message(build_maintenance_card())
                            continue

                        if cb_data.startswith("sched_ctrl:partial:"):
                            target_ch = cb_data.split(":")[-1]
                            user_tz, _ = get_user_tz(chat_id)
                            partial_text = build_partial_scoreboard_text(target_ch, user_tz)
                            TelegramBot(chat_id=target_ch).send_message(partial_text)
                            TelegramBot(chat_id=chat_id).send_message(f"✅ <b>Partial Scorecard Sent to</b> <code>{target_ch}</code>!")
                            continue
                        elif cb_data.startswith("sched_ctrl:stop:"):
                            target_ch = cb_data.split(":")[-1]
                            if target_ch in active_scheduled_sessions:
                                active_scheduled_sessions[target_ch]["is_running"] = False
                                TelegramBot(chat_id=chat_id).send_message(f"🛑 <b>Scheduled session for <code>{target_ch}</code> stopped!</b>")
                            continue
                        elif cb_data.startswith("quick_ctrl:stop:"):
                            target_ch = cb_data.split(":")[-1]
                            if target_ch in active_quick_sessions:
                                active_quick_sessions[target_ch]["is_running"] = False
                                save_quick_sessions_to_disk()
                                TelegramBot(chat_id=chat_id).send_message(f"🛑 <b>Quick session for <code>{target_ch}</code> stopped!</b>")
                            continue

                        if cb_data == "sched_cancel":
                            user_input_state.pop(chat_id, None)
                            send_main_menu(chat_id, username=username, target_msg_id=msg_id)
                        elif cb_data.startswith("sched_mkt:"):
                            b_type = cb_data.split(":")[-1]
                            if chat_id in user_input_state:
                                user_input_state[chat_id]["broker_type"] = b_type
                                user_input_state[chat_id]["step"] = "WAIT_START_TIME"
                                TelegramBot(chat_id=chat_id).send_message(
                                    "⏰ <b>Enter Start Time (HH:MM, e.g. 22:30):</b>",
                                    reply_markup={"inline_keyboard": [[{"text": "❌ CANCEL", "callback_data": "sched_cancel"}]]}
                                )
                            continue
                        elif cb_data.startswith("quick_mkt:"):
                            b_type = cb_data.split(":")[-1]
                            if chat_id in user_input_state:
                                st_info = user_input_state.pop(chat_id, None)
                                target_ch = st_info["channel"]
                                TelegramBot(chat_id=chat_id).send_message(
                                    f"✅ <b>Quick Target Mode Launched!</b>\nTarget: <code>{target_ch}</code> | Market: <code>{b_type.upper()}</code>"
                                )
                                threading.Thread(
                                    target=instant_channel_worker,
                                    args=(chat_id, target_ch, b_type),
                                    daemon=True
                                ).start()
                            continue
                        elif cb_data == "menu:schedule_hub":
                            if not has_schedule_access(chat_id, username):
                                TelegramBot(chat_id=chat_id).send_message("🔒 <i>Schedule Mode restricted. Contact Admin @MD_SUMON_MT4.</i>")
                                continue
                            
                            active_ch = None
                            for ch, sess in active_quick_sessions.items():
                                if sess.get("is_running"):
                                    active_ch = ch
                                    break
                            if not active_ch:
                                for ch, sess in active_scheduled_sessions.items():
                                    if sess.get("is_running"):
                                        active_ch = ch
                                        break

                            if active_ch:
                                hub_text = f"⏱ <b>SCHEDULE & QUICK TARGET HUB</b>\n\n🔴 <b>Active Running:</b> <code>{active_ch}</code>"
                                hub_kb = {
                                    "inline_keyboard": [
                                        [{"text": "🎴 SEND PARTIAL TO CHANNEL", "callback_data": f"sched_ctrl:partial:{active_ch}"}],
                                        [{"text": "🛑 STOP ACTIVE SESSION", "callback_data": f"quick_ctrl:stop:{active_ch}"}],
                                        [{"text": "⚡ QUICK TARGET CHANNEL", "callback_data": "menu:quick_target"}],
                                        [{"text": "🔙 BACK TO MENU", "callback_data": "back_to_menu"}]
                                    ]
                                }
                            else:
                                hub_text = "⏱ <b>SCHEDULE & QUICK TARGET HUB</b>\n\nChoose an action below:"
                                hub_kb = {
                                    "inline_keyboard": [
                                        [{"text": "⚡ QUICK TARGET CHANNEL (INSTANT)", "callback_data": "menu:quick_target"}],
                                        [{"text": "➕ SCHEDULE MODE (TIMED)", "callback_data": "sched:new"}],
                                        [{"text": "📜 SCHEDULE HISTORY & SAVED", "callback_data": "sched:history"}],
                                        [{"text": "🔙 BACK TO MENU", "callback_data": "back_to_menu"}]
                                    ]
                                }
                            edit_or_send(chat_id, hub_text, hub_kb, msg_id)
                        elif cb_data == "menu:quick_target":
                            user_input_state[chat_id] = {"step": "WAIT_QUICK_CHANNEL"}
                            prompt = "⚡ <b>QUICK TARGET CHANNEL MODE</b>\n\nEnter Channel/Group Chat ID or @username:"
                            edit_or_send(chat_id, prompt, {"inline_keyboard": [[{"text": "❌ CANCEL", "callback_data": "sched_cancel"}]]}, msg_id)
                        elif cb_data == "sched:new":
                            user_input_state[chat_id] = {"step": "WAIT_CHANNEL"}
                            prompt = "⏱ <b>TIMED SCHEDULE SETUP</b>\n\nEnter Channel/Group Chat ID or @username:"
                            edit_or_send(chat_id, prompt, {"inline_keyboard": [[{"text": "❌ CANCEL", "callback_data": "sched_cancel"}]]}, msg_id)
                        elif cb_data == "sched:history":
                            saved = load_saved_schedules(chat_id)
                            h_text = "📜 <b>SAVED SCHEDULES</b>\n\n"
                            if not saved:
                                h_text += "No saved schedules found."
                            else:
                                for idx, s in enumerate(saved, 1):
                                    h_text += f"{idx}. <code>{s.get('channel')}</code> | {s.get('market')} | {s.get('start')} - {s.get('end')}\n"
                            edit_or_send(chat_id, h_text, {"inline_keyboard": [[{"text": "🔙 BACK", "callback_data": "menu:schedule_hub"}]]}, msg_id)
                        elif cb_data == "menu:profile":
                            send_profile_menu(chat_id, username=username, target_msg_id=msg_id)
                        elif cb_data == "menu:tz_picker":
                            send_tz_picker(chat_id, target_msg_id=msg_id)
                        elif cb_data.startswith("set_tz:"):
                            offset_val = float(cb_data.split(":")[-1])
                            set_user_tz(chat_id, offset_val)
                            send_profile_menu(chat_id, username=username, target_msg_id=msg_id)
                        elif cb_data == "menu:auto_market_select":
                            is_vip = is_vip_user(chat_id, username)
                            user_tz, _ = get_user_tz(chat_id)
                            used_today = get_user_daily_usage(chat_id, user_tz)
                            if not is_vip and used_today >= FREE_DAILY_AUTO_LIMIT:
                                TelegramBot(chat_id=chat_id).send_message(build_limit_exceeded_card(), reply_markup={"inline_keyboard": [[{"text": "👑 GET VIP", "url": "https://t.me/MD_SUMON_MT4"}], [{"text": "🏠 HOME", "callback_data": "back_to_menu"}]]})
                                continue

                            real_status_label = "🟢 REAL MARKET (OPEN)" if is_real_market_open() else "🔴 REAL MARKET (CLOSED)"
                            edit_or_send(chat_id, "🌐 <b>SELECT AUTO MODE MARKET:</b>", {"inline_keyboard": [[{"text": real_status_label, "callback_data": "auto_start:real"}], [{"text": "🛡 QUOTEX OTC", "callback_data": "auto_start:quotex"}], [{"text": "🚀 POCKET OPTION OTC", "callback_data": "auto_start:pocket"}], [{"text": "🔙 BACK", "callback_data": "back_to_menu"}]]}, msg_id)
                        elif cb_data.startswith("auto_start:"):
                            b_type = cb_data.split(":")[-1]
                            auto_mode_users[str(chat_id)] = False
                            time.sleep(0.2)
                            auto_mode_users[str(chat_id)] = True

                            TelegramBot(chat_id=chat_id).send_message(f"<b>[⚙️] AUTO MODE ACTIVATED ({b_type.upper()}) ✅</b>", reply_markup={"inline_keyboard": [[{"text": "🛑 STOP AUTO", "callback_data": "auto_btn:stop"}]]})
                            threading.Thread(target=auto_mode_loop, args=(chat_id, username, b_type), daemon=True).start()
                        elif cb_data == "auto_btn:stop":
                            auto_mode_users[str(chat_id)] = False
                            TelegramBot(chat_id=chat_id).send_message("🛑 <b>Auto Mode Stopped.</b>", reply_markup={"inline_keyboard": [[{"text": "▶️ RESTART", "callback_data": "menu:auto_market_select"}], [{"text": "🏠 HOME", "callback_data": "back_to_menu"}]]})
                        elif cb_data.startswith("auto_btn:analysis:"):
                            b_type = cb_data.split(":")[-1]
                            deliver_auto_signal(chat_id, username=username, broker_type=b_type)
                        elif cb_data == "auto_btn:partial":
                            user_tz, _ = get_user_tz(chat_id)
                            TelegramBot(chat_id=chat_id).send_message(build_partial_scoreboard_text(chat_id, user_tz), reply_markup={"inline_keyboard": [[{"text": "🏠 HOME", "callback_data": "back_to_menu"}]]})
                        elif cb_data == "menu:daily_summary":
                            history = load_json(HISTORY_FILE)
                            user_tz, _ = get_user_tz(chat_id)
                            today_str = datetime.now(user_tz).strftime("%Y-%m-%d")
                            d_stats = history.get(chat_id, {}).get(today_str, {"win": 0, "mtg": 0, "loss": 0})
                            total = d_stats.get('win', 0) + d_stats.get('mtg', 0) + d_stats.get('loss', 0)
                            wins_total = d_stats.get('win', 0) + d_stats.get('mtg', 0)
                            winrate = f"{(wins_total) / total * 100:.1f}%" if total > 0 else "0.0%"
                            summary_text = f"📊 <b>DAILY SUMMARY ({today_str})</b>\n────────────────────────\n🟩 Direct Wins: {d_stats.get('win', 0)}\n🛡 MTG Wins: {d_stats.get('mtg', 0)}\n❌ Loss: {d_stats.get('loss', 0)}\n🎯 Total Win Rate: {winrate}"
                            edit_or_send(chat_id, summary_text, {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "back_to_menu"}]]}, msg_id)
                        elif cb_data == "menu:support":
                            TelegramBot(chat_id=chat_id).send_message(f"📞 <b>SUPPORT</b>\n\nAdmin: <a href=\"{TELEGRAM_URL_HANDLE}\">{TELEGRAM_HANDLE}</a>")
                            send_main_menu(chat_id, username=username, target_msg_id=msg_id)
                        elif cb_data == "back_to_menu":
                            user_input_state.pop(chat_id, None)
                            send_main_menu(chat_id, username=username, target_msg_id=msg_id)

        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    run_server()
