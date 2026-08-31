# ================= ১. মার্কেট স্ক্যানার কার্ড =================
def build_radar_scanner_card(clean_pair, confidence, tz_str, algorithm_tag="EMA 9/21 + RSI 14 + Reversal Flow"):
    return (
        f"<blockquote>👑 <b>{BOT_TITLE}</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>MARKET SCANNER ACTIVE</b>\n\n"
        f"⚡ <b>Target Pair:</b> <code>{clean_pair}</code>\n"
        f"🎯 <b>Confidence:</b> {confidence}% Ultra-High\n"
        f"🧠 <b>Algorithm:</b> {algorithm_tag}\n"
        f"🌐 <b>Server Zone:</b> {tz_str} (Live Sync)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <i>Locking best entry point...</i></blockquote>"
    )

# ================= ২. ট্রেড এক্সিকিউশন কার্ড =================
def build_execution_ticket_card(clean_pair, dir_action, entry_str):
    action_text = "CALL ▲ (BUY UP)" if dir_action == "CALL" else "PUT ▼ (SELL DOWN)"
    return (
        f"<blockquote>👑 <b>{BOT_TITLE}</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ASSET:</b> <code>{clean_pair}</code>\n"
        f"🟢 <b>ACTION:</b> <b>{action_text}</b>\n"
        f"⏰ <b>ENTRY:</b> {entry_str}\n"
        f"⌛ <b>EXPIRY:</b> <b>1 MINUTE</b>\n"
        f"🛡 <b>STRATEGY:</b> <b>MAX 1-STEP MTG</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>Wait for exact 00-second candle open</i></blockquote>"
    )

# ================= ৩. অফিসিয়াল রেজাল্ট কার্ড =================
def build_golden_trophy_result_card(clean_pair, dir_action, outcome_status, wins, losses, win_rate):
    trade_call_text = "🟢 <b>BUY UP</b>" if dir_action == "CALL" else "🔴 <b>SELL DOWN</b>"
    
    if outcome_status == "WIN":
        result_title = "✅ <b>DIRECT WIN (ITM) 🎯</b>"
        profit_status = "🟩 <b>+85% PROFIT SECURED</b>"
        mtg_status = "<b>NOT REQUIRED</b>"
    elif outcome_status == "MTG":
        result_title = "🟡 <b>MTG WIN (ITM) 🎯</b>"
        profit_status = "🟨 <b>1-STEP RECOVERED</b>"
        mtg_status = "<b>1 STEP USED</b>"
    else:
        result_title = "❌ <b>TRADE LOSS (OTM) 🛑</b>"
        profit_status = "🟥 <b>SESSION LOSS</b>"
        mtg_status = "<b>FAILED</b>"

    return (
        f"<blockquote>👑 <b>{BOT_TITLE}</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>OFFICIAL RESULT UPDATE</b> 🏆\n\n"
        f"🏛 <b>Broker:</b> QUOTEX OTC\n"
        f"🪙 <b>Asset:</b> <code>{clean_pair}</code>\n"
        f"🎯 <b>Trade:</b> {trade_call_text}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>RESULT:</b> {result_title}\n"
        f"📈 <b>Profit:</b> {profit_status}\n"
        f"🛡 <b>Martingale:</b> {mtg_status}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🧮 <b>TOTAL SCORE:</b> 🟢 <b>{wins} WIN</b> ┃ 🔴 <b>{losses} LOSS</b>\n"
        f"🎯 <b>ACCURACY:</b> <b>({win_rate:.1f}%)</b>\n"
        f"✈️ <b>TELEGRAM:</b> {TELEGRAM_HANDLE}\n"
        f"━━━━━━━━━━━━━━━━━━━</blockquote>"
    )

# ================= ৪. ফিউচার সিগন্যাল লিস্ট ফরম্যাট =================
def build_exact_user_format(signals, broker_name="REAL MARKET", user_tz=None, tz_offset=4):
    now_dt = datetime.now(user_tz)
    date_str = now_dt.strftime("%d.%m.%Y")
    sign = "+" if tz_offset >= 0 else ""
    tz_label = f"UTC {sign}{tz_offset}:00"
    
    header = (
        f"👑 <b>{BOT_TITLE}</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>DATE:</b> {date_str}\n"
        f"❤️ <b>MARKET:</b> {broker_name.upper()}\n\n"
        f"😬 <i>Follow Rules & 💵 Management</i>\n\n"
        f"😓 <b>TIME ZONE:</b> ( {tz_label} ) 😓\n"
        f"🔘 <b>TRADE TIME:</b> 1 MINUTE 🚀\n"
        f"❗️ <b>USE 1 STEP MTG ➕</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    lines = ""
    win_count = 0
    mtg_count = 0
    loss_count = 0
    pending_count = 0

    for idx, s in enumerate(signals, start=1):
        status = s.get("status", "PENDING")
        dir_emoji = "🟢" if s["direction"] == "CALL" else "🔴"
        
        if status == "WIN":
            status_text = "<b>WIN ✅</b>"
            win_count += 1
        elif status == "MTG":
            status_text = "<b>MTG ✅¹</b>"
            mtg_count += 1
        elif status == "LOSS":
            status_text = "<b>LOSS ❌</b>"
            loss_count += 1
        elif status == "IN_MTG":
            status_text = "<b>⏳ IN MTG</b>"
            pending_count += 1
        elif status == "LIVE":
            status_text = "<b>⏳ LIVE</b>"
            pending_count += 1
        else:
            status_text = "<b>⏳ PENDING</b>"
            pending_count += 1
            
        lines += f"{idx:02d}. {s['time_str']} ┃ <code>{s['pair']}</code> ➔ {dir_emoji} {s['direction']} ┃ {status_text}\n"

    footer = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Stats:</b> ✅ {win_count} WIN ┃ 🛡 {mtg_count} MTG ┃ ❌ {loss_count} LOSS ┃ ⏳ {pending_count} PENDING\n\n"
        f"⚡ <b>Quotex Live Auto-Checking: ACTIVE 🟢</b>\n\n"
        f"❗️ <b>USE SAFETY MARGIN MUST ❗️</b>\n\n"
        f"<b>FEEDBACK:</b> {TELEGRAM_HANDLE} ✅"
    )
    return header + lines + footer
