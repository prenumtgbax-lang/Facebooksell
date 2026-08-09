import sqlite3
import os
import telebot
from telebot import types

# ==================== CONFIGURATION ====================
BOT_TOKEN = "888313009:AAHTmUPZ6vC8nR1_YjMui2DGCyTRgugIU"  # আপনার বট টোকেন দিন
ADMIN_ID = 6922048527  # আপনার টেলিগ্রাম নিউমেরিক ইউজার আইডি দিন
# =======================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0.0,
        total_deposit REAL DEFAULT 0.0,
        proxies_bought INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0
    )''')
    
    # Proxies Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS proxies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proxy_data TEXT,
        is_sold INTEGER DEFAULT 0
    )''')
    
    # Settings Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Default Settings
    default_settings = {
        'force_join_enabled': '0',
        'force_join_channel': '@BABY_CODER_1',
        'support_link': 'https://t.me/YourDomains',
        'bkash_num': '01700000000',
        'nagad_num': '01800000000',
        'binance_id': '12345678',
        'bkash_active': '1',
        'nagad_active': '1',
        'binance_active': '1',
        'usd_rate': '125.0',
        'min_deposit': '10.0',
        'proxy_price': '50.0'
    }
    
    for key, val in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
    conn.commit()
    conn.close()

init_db()

# DB Helper Functions
def get_setting(key):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else ""

def set_setting(key, value):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, username):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# Force Join Check
def check_force_join(user_id):
    if get_setting('force_join_enabled') == '0':
        return True
    channel = get_setting('force_join_channel')
    try:
        member = bot.get_chat_member(channel, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def force_join_markup():
    markup = types.InlineKeyboardMarkup()
    channel = get_setting('force_join_channel')
    link = f"https://t.me/{channel.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("📢 Join Channel / Group", url=link))
    markup.add(types.InlineKeyboardButton("✅ Joined / Verify", callback_data="check_joined"))
    return markup

# Main Keyboard Menu
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Buy Proxy"),
        types.KeyboardButton("💳 Wallet"),
        types.KeyboardButton("📥 Deposit"),
        types.KeyboardButton("🎧 Support")
    )
    return markup

# ==================== HANDLERS ====================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    register_user(user_id, username)
    
    user = get_user(user_id)
    if user and user[5] == 1:
        bot.send_message(user_id, "🚫 <b>You are banned from using this bot.</b>")
        return

    if not check_force_join(user_id):
        bot.send_message(
            user_id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join our official channel/group to use this bot.",
            reply_markup=force_join_markup()
        )
        return

    bot.send_message(
        user_id,
        f"👋 <b>Welcome {message.from_user.first_name}!</b>\n\nChoose an option from the menu below:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def check_joined_callback(call):
    if check_force_join(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ <b>Verification successful! Welcome.</b>", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ You have not joined yet! Please join first.", show_alert=True)

# ----------------- MENU BUTTONS -----------------

@bot.message_handler(func=lambda m: m.text == "🎧 Support")
def support_btn(message):
    supp = get_setting('support_link')
    bot.send_message(message.chat.id, f"🎧 <b>Customer Support:</b>\n\nContact us here: {supp}")

@bot.message_handler(func=lambda m: m.text == "💳 Wallet")
def wallet_btn(message):
    user = get_user(message.from_user.id)
    if not user: return
    
    msg = (
        f"💳 <b>Your Wallet Info</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user[0]}</code>\n"
        f"💰 <b>Balance:</b> <code>{user[2]:.2f} BDT</code>\n"
        f"📥 <b>Total Deposited:</b> <code>{user[3]:.2f} BDT</code>\n"
        f"🛒 <b>Total Proxies Bought:</b> <code>{user[4]}</code>"
    )
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "📥 Deposit")
def deposit_btn(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    if get_setting('bkash_active') == '1':
        buttons.append(types.InlineKeyboardButton("📱 bKash", callback_data="dep_bkash"))
    if get_setting('nagad_active') == '1':
        buttons.append(types.InlineKeyboardButton("📱 Nagad", callback_data="dep_nagad"))
    if get_setting('binance_active') == '1':
        buttons.append(types.InlineKeyboardButton("🟡 Binance (Pay/USDT)", callback_data="dep_binance"))
        
    markup.add(*buttons)
    min_dep = get_setting('min_deposit')
    usd_rate = get_setting('usd_rate')
    
    msg = (
        f"📥 <b>Deposit Money</b>\n\n"
        f"📌 <b>Minimum Deposit:</b> <code>{min_dep} BDT</code>\n"
        f"💱 <b>Binance Dollar Rate:</b> <code>1 USD = {usd_rate} BDT</code>\n\n"
        f"Select your payment method below:"
    )
    bot.send_message(message.chat.id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dep_"))
def deposit_method_selected(call):
    method = call.data.split("_")[1]
    msg = bot.send_message(call.from_user.id, "💵 <b>Enter Deposit Amount (in BDT):</b>")
    bot.register_next_step_handler(msg, process_deposit_amount, method)

def process_deposit_amount(message, method):
    try:
        amount = float(message.text)
        min_dep = float(get_setting('min_deposit'))
        if amount < min_dep:
            bot.send_message(message.chat.id, f"❌ Minimum deposit amount is <b>{min_dep} BDT</b>. Try again.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount! Please enter numbers only.")
        return

    usd_rate = float(get_setting('usd_rate'))
    
    if method == "bkash":
        num = get_setting('bkash_num')
        instructions = f"Send <b>{amount:.2f} BDT</b> (Personal Send Money) to:\n<code>{num}</code>"
    elif method == "nagad":
        num = get_setting('nagad_num')
        instructions = f"Send <b>{amount:.2f} BDT</b> (Personal Send Money) to:\n<code>{num}</code>"
    else: # binance
        usd_amount = amount / usd_rate
        bin_id = get_setting('binance_id')
        instructions = (
            f"Send <b>${usd_amount:.2f} USDT</b> (Equivalent to {amount:.2f} BDT @ Rate {usd_rate})\n"
            f"Binance Pay ID: <code>{bin_id}</code>"
        )

    msg = (
        f"<b>Payment Information ({method.upper()})</b>\n\n"
        f"{instructions}\n\n"
        f"➡️ <b>Please send your Transaction ID (TrxID) now:</b>"
    )
    sent = bot.send_message(message.chat.id, msg)
    bot.register_next_step_handler(sent, process_trx_id, method, amount)

def process_trx_id(message, method, amount):
    trx_id = message.text
    sent = bot.send_message(message.chat.id, "📸 Now send a <b>Screenshot / Payment Proof Image</b>:")
    bot.register_next_step_handler(sent, process_payment_pic, method, amount, trx_id)

def process_payment_pic(message, method, amount, trx_id):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Invalid photo! Payment process cancelled. Please start over.")
        return

    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Send Notification to Admin
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}_{amount}")
    )
    
    caption = (
        f"📥 <b>New Deposit Request!</b>\n\n"
        f"👤 <b>User:</b> @{username} (<code>{user_id}</code>)\n"
        f"💳 <b>Method:</b> {method.upper()}\n"
        f"💰 <b>Amount:</b> <code>{amount:.2f} BDT</code>\n"
        f"🆔 <b>Trx ID:</b> <code>{trx_id}</code>"
    )
    
    bot.send_photo(ADMIN_ID, photo_id, caption=caption, reply_markup=admin_markup)
    bot.send_message(user_id, "✅ <b>Payment submitted successfully!</b>\nPlease wait for admin approval.")

# Admin Deposit Approve/Reject
@bot.callback_query_handler(func=lambda call: call.data.startswith("app_") or call.data.startswith("rej_"))
def admin_deposit_action(call):
    action, uid, amt = call.data.split("_")
    uid = int(uid)
    amt = float(amt)
    
    if action == "app":
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ?, total_deposit = total_deposit + ? WHERE user_id=?", (amt, amt, uid))
        conn.commit()
        conn.close()
        
        bot.edit_message_caption(f"{call.message.caption}\n\n✅ <b>STATUS: APPROVED</b>", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, f"🎉 <b>Deposit Approved!</b>\n<code>{amt:.2f} BDT</code> has been added to your balance.")
    else:
        bot.edit_message_caption(f"{call.message.caption}\n\n❌ <b>STATUS: REJECTED</b>", call.message.chat.id, call.message.message_id)
        bot.send_message(uid, f"❌ <b>Deposit Rejected!</b>\nYour deposit request for <code>{amt:.2f} BDT</code> was rejected.")

# ----------------- BUY PROXY -----------------

@bot.message_handler(func=lambda m: m.text == "🛒 Buy Proxy")
def buy_proxy_btn(message):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM proxies WHERE is_sold = 0")
    stock = cursor.fetchone()[0]
    conn.close()
    
    price = float(get_setting('proxy_price'))
    
    if stock == 0:
        bot.send_message(message.chat.id, "❌ <b>Out of stock!</b> Please try again later.")
        return

    msg = bot.send_message(
        message.chat.id,
        f"🛒 <b>Buy Proxy</b>\n\n"
        f"💵 <b>Price per unit:</b> <code>{price:.2f} BDT</code>\n"
        f"📦 <b>Available Stock:</b> <code>{stock}</code>\n\n"
        f"➡️ <i>Enter the quantity you want to buy:</i>"
    )
    bot.register_next_step_handler(msg, process_buy_proxy)

def process_buy_proxy(message):
    try:
        qty = int(message.text)
        if qty <= 0: raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid quantity enter a positive number!")
        return

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM proxies WHERE is_sold = 0")
    stock = cursor.fetchone()[0]
    
    if qty > stock:
        bot.send_message(message.chat.id, f"❌ Not enough stock! Current stock is {stock}.")
        conn.close()
        return

    price = float(get_setting('proxy_price'))
    total_cost = qty * price
    user = get_user(message.from_user.id)
    
    if user[2] < total_cost:
        bot.send_message(message.chat.id, f"❌ <b>Insufficient Balance!</b>\nTotal Cost: <code>{total_cost:.2f} BDT</code>\nYour Balance: <code>{user[2]:.2f} BDT</code>")
        conn.close()
        return

    # Deduct balance & Fetch unique proxies
    cursor.execute("SELECT id, proxy_data FROM proxies WHERE is_sold = 0 LIMIT ?", (qty,))
    proxies = cursor.fetchall()
    
    p_ids = [p[0] for p in proxies]
    p_lines = "\n".join([p[1] for p in proxies])
    
    cursor.execute(f"UPDATE proxies SET is_sold = 1 WHERE id IN ({','.join(['?']*len(p_ids))})", p_ids)
    cursor.execute("UPDATE users SET balance = balance - ?, proxies_bought = proxies_bought + ? WHERE user_id = ?", (total_cost, qty, message.from_user.id))
    
    conn.commit()
    conn.close()

    # Deliver Proxies as Text/File
    bot.send_message(message.chat.id, f"🎉 <b>Purchase Successful!</b>\nAmount Paid: <code>{total_cost:.2f} BDT</code>\n\n<b>Your Proxies:</b>\n<code>{p_lines}</code>")

# ==================== ADMIN PANEL ====================

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
        types.InlineKeyboardButton("👤 User Mgmt", callback_data="adm_users"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"),
        types.InlineKeyboardButton("⚙️ Payment Settings", callback_data="adm_pay"),
        types.InlineKeyboardButton("📤 Upload Proxy", callback_data="adm_proxy"),
        types.InlineKeyboardButton("🔗 Support/Channel Link", callback_data="adm_links")
    )
    bot.send_message(message.chat.id, "🛠️ <b>Admin Control Panel</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_") and call.from_user.id == ADMIN_ID)
def admin_callbacks(call):
    data = call.data
    
    if data == "adm_stats":
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM proxies WHERE is_sold = 1")
        sold_p = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM proxies WHERE is_sold = 0")
        stock_p = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_deposit) FROM users")
        total_dep = cursor.fetchone()[0] or 0.0
        conn.close()
        
        msg = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"📦 Stock Proxies: <code>{stock_p}</code>\n"
            f"🛒 Sold Proxies: <code>{sold_p}</code>\n"
            f"💰 Total Deposits: <code>{total_dep:.2f} BDT</code>"
        )
        bot.send_message(call.from_user.id, msg)

    elif data == "adm_users":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕/➖ Modify Balance", callback_data="adm_mod_bal"),
            types.InlineKeyboardButton("🚫 Ban/Unban", callback_data="adm_ban"),
            types.InlineKeyboardButton("🔍 User Status", callback_data="adm_chk_usr")
        )
        bot.send_message(call.from_user.id, "👤 <b>User Management System</b>", reply_markup=markup)

    elif data == "adm_mod_bal":
        msg = bot.send_message(call.from_user.id, "Send User ID and Amount to add/subtract:\nFormat: <code>USER_ID AMOUNT</code>\nExample: <code>123456789 100</code> or <code>123456789 -50</code>")
        bot.register_next_step_handler(msg, process_adm_bal)

    elif data == "adm_ban":
        msg = bot.send_message(call.from_user.id, "Send User ID to Toggle Ban/Unban Status:")
        bot.register_next_step_handler(msg, process_adm_ban)

    elif data == "adm_chk_usr":
        msg = bot.send_message(call.from_user.id, "Send User ID to check status:")
        bot.register_next_step_handler(msg, process_adm_chk)

    elif data == "adm_bc":
        msg = bot.send_message(call.from_user.id, "Send text or photo (with caption) to broadcast to ALL users:")
        bot.register_next_step_handler(msg, process_adm_bc)

    elif data == "adm_pay":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Set bKash Number", callback_data="set_bkash"),
            types.InlineKeyboardButton("Set Nagad Number", callback_data="set_nagad"),
            types.InlineKeyboardButton("Set Binance ID", callback_data="set_binance"),
            types.InlineKeyboardButton("Set USD Rate", callback_data="set_rate"),
            types.InlineKeyboardButton("Set Min Deposit", callback_data="set_mindep"),
            types.InlineKeyboardButton("Toggle Payment Methods", callback_data="toggle_pay")
        )
        bot.send_message(call.from_user.id, "⚙️ <b>Payment System Settings</b>", reply_markup=markup)

    elif data == "adm_proxy":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📄 Upload TXT File", callback_data="up_txt"),
            types.InlineKeyboardButton("📝 Add Manually", callback_data="up_manual"),
            types.InlineKeyboardButton("🏷️ Set Proxy Price", callback_data="set_px_price")
        )
        bot.send_message(call.from_user.id, "📦 <b>Proxy Management</b>", reply_markup=markup)

    elif data == "adm_links":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Set Support Link", callback_data="set_supp_link"),
            types.InlineKeyboardButton("Set Channel Username", callback_data="set_chan_link"),
            types.InlineKeyboardButton("Toggle Force Join ON/OFF", callback_data="toggle_fj")
        )
        bot.send_message(call.from_user.id, "🔗 <b>Support & Channel Settings</b>", reply_markup=markup)

# Admin Action Processors
def process_adm_bal(message):
    try:
        uid, amt = message.text.split()
        uid = int(uid)
        amt = float(amt)
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, uid))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Updated balance for User <code>{uid}</code> by <code>{amt} BDT</code>")
    except Exception:
        bot.send_message(message.chat.id, "❌ Invalid input format.")

def process_adm_ban(message):
    try:
        uid = int(message.text)
        user = get_user(uid)
        if not user:
            bot.send_message(message.chat.id, "❌ User not found.")
            return
        new_status = 0 if user[5] == 1 else 1
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_status, uid))
        conn.commit()
        conn.close()
        status_txt = "Banned" if new_status == 1 else "Unbanned"
        bot.send_message(message.chat.id, f"✅ User <code>{uid}</code> is now <b>{status_txt}</b>.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Invalid User ID.")

def process_adm_chk(message):
    try:
        uid = int(message.text)
        u = get_user(uid)
        if u:
            bot.send_message(message.chat.id, f"👤 <b>User Info:</b>\nID: <code>{u[0]}</code>\nUsername: @{u[1]}\nBalance: <code>{u[2]} BDT</code>\nDeposits: <code>{u[3]} BDT</code>\nBought: <code>{u[4]}</code>\nBanned: <code>{u[5]}</code>")
        else:
            bot.send_message(message.chat.id, "❌ User not found.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Invalid ID.")

def process_adm_bc(message):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    count = 0
    for u in users:
        try:
            if message.photo:
                bot.send_photo(u[0], message.photo[-1].file_id, caption=message.caption or "")
            else:
                bot.send_message(u[0], message.text)
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ Broadcast completed! Sent to {count} users.")

# Payment & Settings Callbacks
@bot.callback_query_handler(func=lambda call: call.data in ["set_bkash", "set_nagad", "set_binance", "set_rate", "set_mindep", "toggle_pay", "up_txt", "up_manual", "set_px_price", "set_supp_link", "set_chan_link", "toggle_fj"])
def sub_admin_settings(call):
    data = call.data
    
    if data == "set_bkash":
        msg = bot.send_message(call.from_user.id, "Enter new bKash Number:")
        bot.register_next_step_handler(msg, lambda m: set_setting('bkash_num', m.text) or bot.send_message(m.chat.id, "✅ bKash number updated!"))
    elif data == "set_nagad":
        msg = bot.send_message(call.from_user.id, "Enter new Nagad Number:")
        bot.register_next_step_handler(msg, lambda m: set_setting('nagad_num', m.text) or bot.send_message(m.chat.id, "✅ Nagad number updated!"))
    elif data == "set_binance":
        msg = bot.send_message(call.from_user.id, "Enter new Binance Pay ID:")
        bot.register_next_step_handler(msg, lambda m: set_setting('binance_id', m.text) or bot.send_message(m.chat.id, "✅ Binance ID updated!"))
    elif data == "set_rate":
        msg = bot.send_message(call.from_user.id, "Enter 1 USD rate in BDT (e.g. 125):")
        bot.register_next_step_handler(msg, lambda m: set_setting('usd_rate', m.text) or bot.send_message(m.chat.id, "✅ USD Rate updated!"))
    elif data == "set_mindep":
        msg = bot.send_message(call.from_user.id, "Enter Minimum Deposit amount (BDT):")
        bot.register_next_step_handler(msg, lambda m: set_setting('min_deposit', m.text) or bot.send_message(m.chat.id, "✅ Min deposit updated!"))
    elif data == "toggle_pay":
        bk = '0' if get_setting('bkash_active') == '1' else '1'
        set_setting('bkash_active', bk)
        bot.send_message(call.from_user.id, f"✅ Payment status toggled!")
    elif data == "set_px_price":
        msg = bot.send_message(call.from_user.id, "Enter price per proxy in BDT:")
        bot.register_next_step_handler(msg, lambda m: set_setting('proxy_price', m.text) or bot.send_message(m.chat.id, "✅ Proxy price updated!"))
    elif data == "set_supp_link":
        msg = bot.send_message(call.from_user.id, "Enter Support Telegram Link/Username:")
        bot.register_next_step_handler(msg, lambda m: set_setting('support_link', m.text) or bot.send_message(m.chat.id, "✅ Support link updated!"))
    elif data == "set_chan_link":
        msg = bot.send_message(call.from_user.id, "Enter Force Join Channel Username (e.g. @mychannel):")
        bot.register_next_step_handler(msg, lambda m: set_setting('force_join_channel', m.text) or bot.send_message(m.chat.id, "✅ Channel username updated!"))
    elif data == "toggle_fj":
        curr = '0' if get_setting('force_join_enabled') == '1' else '1'
        set_setting('force_join_enabled', curr)
        status = "ENABLED" if curr == '1' else "DISABLED"
        bot.send_message(call.from_user.id, f"✅ Force Join is now <b>{status}</b>.")
    elif data == "up_manual":
        msg = bot.send_message(call.from_user.id, "Send Proxies (1 Proxy per line):")
        bot.register_next_step_handler(msg, process_proxy_upload_text)
    elif data == "up_txt":
        msg = bot.send_message(call.from_user.id, "Please upload a `.txt` file containing proxies (1 Proxy per line):")
        bot.register_next_step_handler(msg, process_proxy_upload_file)

def process_proxy_upload_text(message):
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if not lines:
        bot.send_message(message.chat.id, "❌ No text found.")
        return
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    for l in lines:
        cursor.execute("INSERT INTO proxies (proxy_data) VALUES (?)", (l,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Successfully added <b>{len(lines)}</b> proxies!")

def process_proxy_upload_file(message):
    if not message.document:
        bot.send_message(message.chat.id, "❌ Please upload a TXT file!")
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    lines = [line.strip() for line in downloaded.decode('utf-8').splitlines() if line.strip()]
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    for l in lines:
        cursor.execute("INSERT INTO proxies (proxy_data) VALUES (?)", (l,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Successfully uploaded <b>{len(lines)}</b> proxies from file!")

# Start Polling
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
