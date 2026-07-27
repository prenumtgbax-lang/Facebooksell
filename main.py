import os
import json
import random
import string
import logging
import asyncio
import io
from datetime import datetime

import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

# ==============================================================================
# ⚙️ CONFIGURATION & FILE PATHS
# ==============================================================================

TOKEN = "8996063667:AAHaWei-z3SAemIWVBAtHxIDY1nkQQhgGqI"  # Replace with your Bot Token
ADMIN_ID = 6922048527          # Default Admin ID

# Database Storage Files
USER_DATA_FILE = "zarya_users.json"
CONFIG_FILE = "zarya_config.json"
SELL_DATA_FILE = "zarya_sells.json"
WITHDRAW_DATA_FILE = "zarya_withdraws.json"
BANNED_USERS_FILE = "zarya_banned.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 🌟 EMOJI MAPPING & HELPER FUNCTIONS
# ==============================================================================

EMOJI_MAP = {
    "balance": "6073556477824472025",
    "facebook": "5454340696183943190",
    "refer": "5266965772869053171",
    "leaderboard": "6244762094810436779",
    "support": "6176713668059732008",
    "my_report": "5409041938106031080",
    "admin": "6246674660927215020",
    "withdraw": "6084884131945125425",
    "arrow": "6084459299550009766",
    "fire": "6084757039567868626",
    "top": "6084818723888173207",
    "24h": "5211065583805673493",
    "delete": "5341319525142905998",
    "cross": "5341718759532938160",
    "sit": "5409162914449858605",
    "cup": "6235422679835350879",
    "star": "6336639073133794426",
    "date": "6336848409839801489",
    "pin": "6111410240807245099",
    "money": "6111799373434197692",
    "danger": "6109451886044124125",
    "1": "6109152797406532734",
    "2": "6109321250318849544",
    "3": "6109218153923876294",
    "link": "6111396350883010682",
    "king": "6311888503751843904",
    "diamond": "6086778199637756507",
    "bkash": "6237975191784266396",
    "nagad": "6235336389647407554",
    "binance": "6237610939902858402",
    "gift": "6071123877067494706",
    "dollar": "5893473283696759404",
    "mic": "6237568428316562386",
    "premium": "6246919169120408471",
    "done": "6082468062517270284",
    "coin": "6183763603473044358",
    "vip": "6109355038826567130",
    "notification": "6053142399482339205",
    "search": "6053117952528493140",
    "id": "6338935574967098253",
    "100%": "6053175754198358605",
    "ok": "6314082948572256406",
    "upp": "6312314362644143742",
    "world": "6314138297815803150",
    "like": "6314553256081103478",
    "ck": "6314471909400519173"
}

def EI(key: str) -> str:
    return EMOJI_MAP.get(key, "6109355038826567130")

def ET(key: str) -> str:
    return f"<tg-emoji emoji-id='{EI(key)}'>✨</tg-emoji>"

FIRST_NAMES = ["John", "Alex", "David", "Michael", "Rahim", "Tanvir", "Shakib", "Robert", "James", "William", "Daniel", "Hasan", "Arfan", "Mahmud"]
LAST_NAMES = ["Smith", "Johnson", "Ahmed", "Khan", "Williams", "Brown", "Jones", "Hossain", "Chowdhury", "Rahman", "Taylor", "Davis"]

def get_random_name():
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)

# ==============================================================================
# 🛠️ TELEGRAM KEYBOARD MONKEY-PATCH COMPATIBILITY LAYER
# ==============================================================================

try:
    telegram.KeyboardButton("test", style="primary", icon_custom_emoji_id="123")
except TypeError:
    _orig_kb_init = telegram.KeyboardButton.__init__
    def _new_kb_init(self, *args, **kwargs):
        kwargs.pop('style', None)
        kwargs.pop('icon_custom_emoji_id', None)
        _orig_kb_init(self, *args, **kwargs)
    telegram.KeyboardButton.__init__ = _new_kb_init

    _orig_ikb_init = telegram.InlineKeyboardButton.__init__
    def _new_ikb_init(self, *args, **kwargs):
        kwargs.pop('style', None)
        kwargs.pop('icon_custom_emoji_id', None)
        _orig_ikb_init(self, *args, **kwargs)
    telegram.InlineKeyboardButton.__init__ = _new_ikb_init

def make_keyboard(kb_dict):
    if not kb_dict:
        return None
    if isinstance(kb_dict, (telegram.InlineKeyboardMarkup, telegram.ReplyKeyboardMarkup, telegram.ReplyKeyboardRemove)):
        return kb_dict
    if not isinstance(kb_dict, dict):
        return kb_dict

    if "inline_keyboard" in kb_dict:
        inline_rows = []
        for row in kb_dict["inline_keyboard"]:
            row_buttons = []
            for btn in row:
                kwargs = {}
                if "url" in btn: kwargs["url"] = btn["url"]
                if "callback_data" in btn: kwargs["callback_data"] = btn["callback_data"]
                if "style" in btn: kwargs["style"] = btn["style"]
                if "icon_custom_emoji_id" in btn: kwargs["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
                row_buttons.append(telegram.InlineKeyboardButton(text=btn["text"], **kwargs))
            inline_rows.append(row_buttons)
        return telegram.InlineKeyboardMarkup(inline_rows)

    if "keyboard" in kb_dict:
        rows = []
        for row in kb_dict["keyboard"]:
            row_buttons = []
            for btn in row:
                kwargs = {}
                if "style" in btn: kwargs["style"] = btn["style"]
                if "icon_custom_emoji_id" in btn: kwargs["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
                row_buttons.append(telegram.KeyboardButton(text=btn["text"], **kwargs))
            rows.append(row_buttons)
        return telegram.ReplyKeyboardMarkup(
            rows,
            resize_keyboard=kb_dict.get("resize_keyboard", True),
            one_time_keyboard=kb_dict.get("one_time_keyboard", False)
        )
    return kb_dict

_orig_send_message = telegram.Bot.send_message
async def _new_send_message(self, *args, **kwargs):
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = make_keyboard(kwargs["reply_markup"])
    return await _orig_send_message(self, *args, **kwargs)
telegram.Bot.send_message = _new_send_message

_orig_reply_text = telegram.Message.reply_text
async def _new_reply_text(self, *args, **kwargs):
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = make_keyboard(kwargs["reply_markup"])
    return await _orig_reply_text(self, *args, **kwargs)
telegram.Message.reply_text = _new_reply_text

_orig_edit_text = telegram.Message.edit_text
async def _new_edit_text(self, *args, **kwargs):
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = make_keyboard(kwargs["reply_markup"])
    return await _orig_edit_text(self, *args, **kwargs)
telegram.Message.edit_text = _new_edit_text

# ==============================================================================
# 📂 DATA PERSISTENCE HELPERS
# ==============================================================================

DEFAULT_CONFIG = {
    "admin_id": ADMIN_ID,
    "referral_reward": 1.0,
    "uid_pass_rate": 15.0,
    "uid_cookies_rate": 20.0,
    "uid_pass_default_pass": "ZaryaPass@123",
    "uid_cookies_default_pass": "ZaryaCook@998",
    "min_withdraw": 50.0,
    "bkash_active": True,
    "nagad_active": True,
    "binance_active": True,
    "sell_system_active": True,
    "uid_pass_active": True,
    "uid_cookies_active": True,
    "support_username": "@Niloy_Owner",
    "force_join_channels": []  # List of dicts: [{"chat_id": -100xxx, "link": "https://t.me/..."}]
}

def load_data(filename, default_val=None):
    if default_val is None:
        default_val = {}
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(default_val, f, indent=4)
        return default_val
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return default_val

def save_data(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_config():
    cfg = load_data(CONFIG_FILE, DEFAULT_CONFIG)
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    return cfg

def save_config(cfg):
    save_data(cfg, CONFIG_FILE)

def get_user(uid, name="User"):
    uid = str(uid)
    users = load_data(USER_DATA_FILE, {})
    if uid not in users:
        users[uid] = {
            "user_id": uid,
            "full_name": name,
            "balance": 0.0,
            "total_sell": 0,
            "approved_sell": 0,
            "rejected_sell": 0,
            "pending_sell": 0,
            "total_withdraw": 0.0,
            "referral_count": 0,
            "referrer_id": None,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(users, USER_DATA_FILE)
    return users[uid]

def update_user(uid, data):
    uid = str(uid)
    users = load_data(USER_DATA_FILE, {})
    if uid in users:
        users[uid].update(data)
        save_data(users, USER_DATA_FILE)

def is_admin(user_id):
    cfg = get_config()
    return int(user_id) == cfg.get("admin_id")

def is_user_banned(user_id):
    banned = load_data(BANNED_USERS_FILE, [])
    return str(user_id) in [str(x) for x in banned]

# ==============================================================================
# 🔐 FORCE JOIN CHECK SYSTEM
# ==============================================================================

async def check_force_join(bot, user_id):
    cfg = get_config()
    channels = cfg.get("force_join_channels", [])
    if not channels:
        return True
    for ch in channels:
        cid = ch.get("chat_id")
        if not cid: continue
        try:
            member = await bot.get_chat_member(chat_id=int(cid), user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logger.error(f"Error checking join status for {cid}: {e}")
            return False
    return True

async def prompt_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_config()
    channels = cfg.get("force_join_channels", [])
    inline_rows = []
    
    for i, ch in enumerate(channels, 1):
        link = ch.get("link", "https://t.me/")
        style = "primary" if i % 3 == 1 else ("success" if i % 3 == 2 else "danger")
        inline_rows.append([{
            "text": f"JOIN CHANNEL #{i}",
            "url": link,
            "style": style,
            "icon_custom_emoji_id": EI("link")
        }])
        
    inline_rows.append([{
        "text": "VERIFY JOINING",
        "callback_data": "check_join_status",
        "style": "success",
        "icon_custom_emoji_id": EI("ok")
    }])
    
    msg = (
        f"{ET('vip')} <b>MANDATORY CHANNELS JOIN REQUIRED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"You must join all of our official channels & groups to use <b>Zarya Accounts</b> services!\n\n"
        f"{ET('arrow')} Please join all channels below and click <b>VERIFY JOINING</b>."
    )
    
    kb = {"inline_keyboard": inline_rows}
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

# ==============================================================================
# 🎮 MAIN KEYBOARD & MENUS
# ==============================================================================

def build_main_keyboard(user_id):
    buttons = [
        [
            {"text": "Balance", "icon_custom_emoji_id": EI("balance"), "style": "primary"},
            {"text": "Facebook sell", "icon_custom_emoji_id": EI("facebook"), "style": "success"}
        ],
        [
            {"text": "Refer", "icon_custom_emoji_id": EI("refer"), "style": "primary"},
            {"text": "Leaderboard", "icon_custom_emoji_id": EI("leaderboard"), "style": "danger"}
        ],
        [
            {"text": "Support", "icon_custom_emoji_id": EI("support"), "style": "success"},
            {"text": "My Report", "icon_custom_emoji_id": EI("my_report"), "style": "primary"}
        ]
    ]
    if is_admin(user_id):
        buttons.append([
            {"text": "Admin Panel", "icon_custom_emoji_id": EI("admin"), "style": "danger"}
        ])
    return {"keyboard": buttons, "resize_keyboard": True}

async def show_main_menu(update_obj, context):
    user = update_obj.effective_user
    uid = user.id
    get_user(uid, user.full_name)

    if not await check_force_join(context.bot, uid):
        await prompt_force_join(update_obj, context)
        return

    msg = (
        f"{ET('vip')} <b>Welcome {user.full_name} to Zarya Accounts!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"The most reliable platform to sell Facebook Accounts dynamically and earn instant money!\n\n"
        f"{ET('fire')} Select an option from the menu below to get started."
    )
    kb = build_main_keyboard(uid)
    
    if hasattr(update_obj, 'message') and update_obj.message:
        await update_obj.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
    elif hasattr(update_obj, 'callback_query') and update_obj.callback_query:
        await update_obj.callback_query.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

# ==============================================================================
# 🚀 START & MESSAGE HANDLER
# ==============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    
    if is_user_banned(uid):
        await update.message.reply_text(f"{ET('cross')} <b>YOUR ACCOUNT IS BANNED BY ADMIN.</b>", parse_mode=ParseMode.HTML)
        return

    users = load_data(USER_DATA_FILE, {})
    is_new = str(uid) not in users

    u_data = get_user(uid, user.full_name)

    # Referral handling
    args = context.args
    if args and is_new:
        try:
            ref_id = str(args[0])
            if ref_id != str(uid) and ref_id in users:
                cfg = get_config()
                reward = cfg.get("referral_reward", 1.0)
                
                # Reward Referrer
                ref_user = users[ref_id]
                ref_user["balance"] += reward
                ref_user["referral_count"] += 1
                save_data(users, USER_DATA_FILE)
                
                u_data["referrer_id"] = ref_id
                save_data(users, USER_DATA_FILE)
                
                # Notify Referrer
                notif = (
                    f"{ET('gift')} <b>NEW REFERRAL REWARD!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{ET('vip')} Invited User: <b>{user.full_name}</b> (<code>{uid}</code>)\n"
                    f"{ET('coin')} Bonus Credited: <code>+৳{reward:.2f} BDT</code>"
                )
                try:
                    await context.bot.send_message(chat_id=int(ref_id), text=notif, parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Failed to notify referrer {ref_id}: {e}")
        except Exception as e:
            logger.error(f"Referral error: {e}")

    if not await check_force_join(context.bot, uid):
        await prompt_force_join(update, context)
        return

    await show_main_menu(update, context)

# ==============================================================================
# 💬 BUTTON INTERACTION & FLOW LOGIC
# ==============================================================================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text.strip()
    
    if is_user_banned(uid):
        await update.message.reply_text(f"{ET('cross')} <b>YOUR ACCOUNT IS BANNED BY ADMIN.</b>", parse_mode=ParseMode.HTML)
        return

    if not await check_force_join(context.bot, uid):
        await prompt_force_join(update, context)
        return

    cfg = get_config()
    u_data = get_user(uid, user.full_name)
    state = context.user_data.get("state")

    # Cancel Handling
    if text == "Cancel":
        context.user_data.clear()
        await update.message.reply_text("Action Cancelled.", reply_markup=build_main_keyboard(uid), parse_mode=ParseMode.HTML)
        return

    # 1. BALANCE BUTTON
    if text == "Balance":
        context.user_data.clear()
        msg = (
            f"{ET('balance')} <b>ACCOUNT BALANCE OVERVIEW</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ET('coin')} <b>Total Balance:</b> <code>৳{u_data['balance']:.2f} BDT</code>\n"
            f"{ET('withdraw')} <b>Total Withdraw:</b> <code>৳{u_data['total_withdraw']:.2f} BDT</code>\n\n"
            f"{ET('facebook')} <b>Total Sells:</b> <code>{u_data['total_sell']}</code>\n"
            f"{ET('done')} <b>Approved:</b> <code>{u_data['approved_sell']}</code>\n"
            f"{ET('cross')} <b>Rejected:</b> <code>{u_data['rejected_sell']}</code>"
        )
        kb = {"inline_keyboard": [[
            {"text": "WITHDRAW", "callback_data": "start_withdraw", "style": "success", "icon_custom_emoji_id": EI("withdraw")}
        ]]}
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # 2. FACEBOOK SELL BUTTON
    elif text == "Facebook sell":
        context.user_data.clear()
        if not cfg.get("sell_system_active", True):
            await update.message.reply_text(f"{ET('danger')} <b>Facebook sell system is currently disabled by Admin.</b>", parse_mode=ParseMode.HTML)
            return
            
        rate_pass = cfg.get("uid_pass_rate", 15.0)
        rate_cook = cfg.get("uid_cookies_rate", 20.0)
        
        kb = {
            "keyboard": [
                [
                    {"text": f"UID & Pass (৳{rate_pass:.0f})", "style": "primary", "icon_custom_emoji_id": EI("facebook")},
                    {"text": f"UID & Cookies (৳{rate_cook:.0f})", "style": "success", "icon_custom_emoji_id": EI("ck")}
                ],
                [{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}]
            ],
            "resize_keyboard": True
        }
        
        msg = f"{ET('fire')} <b>Select Facebook Account Type To Sell:</b>"
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # UID & PASS CHOSEN
    elif text.startswith("UID & Pass"):
        if not cfg.get("uid_pass_active", True):
            await update.message.reply_text(f"{ET('cross')} <b>UID & Pass sell option is currently offline.</b>", parse_mode=ParseMode.HTML)
            return
        
        fn, ln = get_random_name()
        default_pass = cfg.get("uid_pass_default_pass", "ZaryaPass@123")
        rate = cfg.get("uid_pass_rate", 15.0)
        
        context.user_data["sell_temp"] = {
            "type": "UID_PASS",
            "fn": fn,
            "ln": ln,
            "pass": default_pass,
            "price": rate
        }
        
        msg = (
            f"{ET('facebook')} <b>FACEBOOK UID & PASSWORD SELL DETAILS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ET('pin')} <b>First Name:</b> <code>{fn}</code>\n"
            f"{ET('pin')} <b>Last Name:</b> <code>{ln}</code>\n"
            f"{ET('key')} <b>Password:</b> <code>{default_pass}</code>\n"
            f"{ET('coin')} <b>Price:</b> <code>৳{rate:.2f} BDT</code>\n"
            f"{ET('24h')} <b>Report Time:</b> <code>12 Hours</code>\n\n"
            f"{ET('arrow')} Click <b>Submit Details</b> to submit your Facebook UID."
        )
        kb = {
            "keyboard": [
                [{"text": "Submit Details", "style": "success", "icon_custom_emoji_id": EI("ok")}],
                [{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}]
            ],
            "resize_keyboard": True
        }
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # UID & COOKIES CHOSEN
    elif text.startswith("UID & Cookies"):
        if not cfg.get("uid_cookies_active", True):
            await update.message.reply_text(f"{ET('cross')} <b>UID & Cookies sell option is currently offline.</b>", parse_mode=ParseMode.HTML)
            return
        
        fn, ln = get_random_name()
        default_pass = cfg.get("uid_cookies_default_pass", "ZaryaCook@998")
        rate = cfg.get("uid_cookies_rate", 20.0)
        
        context.user_data["sell_temp"] = {
            "type": "UID_COOKIES",
            "fn": fn,
            "ln": ln,
            "pass": default_pass,
            "price": rate
        }
        
        msg = (
            f"{ET('ck')} <b>FACEBOOK UID & COOKIES SELL DETAILS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ET('pin')} <b>First Name:</b> <code>{fn}</code>\n"
            f"{ET('pin')} <b>Last Name:</b> <code>{ln}</code>\n"
            f"{ET('key')} <b>Password:</b> <code>{default_pass}</code>\n"
            f"{ET('coin')} <b>Price:</b> <code>৳{rate:.2f} BDT</code>\n"
            f"{ET('24h')} <b>Report Time:</b> <code>12 Hours</code>\n\n"
            f"{ET('arrow')} Click <b>Submit Details</b> to proceed."
        )
        kb = {
            "keyboard": [
                [{"text": "Submit Details", "style": "success", "icon_custom_emoji_id": EI("ok")}],
                [{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}]
            ],
            "resize_keyboard": True
        }
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # SUBMIT DETAILS CLICKED
    elif text == "Submit Details":
        sell_temp = context.user_data.get("sell_temp")
        if not sell_temp:
            await update.message.reply_text("Session expired. Please select Facebook sell again.", reply_markup=build_main_keyboard(uid))
            return
            
        if sell_temp["type"] == "UID_PASS":
            context.user_data["state"] = "WAITING_UID_PASS_UID"
            kb = {"keyboard": [[{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}]], "resize_keyboard": True}
            await update.message.reply_text(f"{ET('id')} <b>Please send your Facebook Account UID:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            context.user_data["state"] = "WAITING_COOKIES_UID"
            kb = {"keyboard": [[{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}]], "resize_keyboard": True}
            await update.message.reply_text(f"{ET('id')} <b>Please send your Facebook Account UID:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # 3. REFER BUTTON
    elif text == "Refer":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={uid}"
        ref_reward = cfg.get("referral_reward", 1.0)
        
        msg = (
            f"{ET('refer')} <b>REFER & EARN PROGRAM</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ET('gift')} Earn <code>৳{ref_reward:.2f} BDT</code> for every valid friend you invite!\n\n"
            f"{ET('link')} <b>Your Referral Link:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"{ET('star')} <b>Your Total Referrals:</b> <code>{u_data['referral_count']}</code>\n"
            f"{ET('coin')} <b>Total Earned:</b> <code>৳{u_data['referral_count'] * ref_reward:.2f} BDT</code>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # 4. LEADERBOARD BUTTON
    elif text == "Leaderboard":
        users_all = load_data(USER_DATA_FILE, {})
        sorted_users = sorted(users_all.values(), key=lambda x: (x.get("approved_sell", 0) + x.get("referral_count", 0)), reverse=True)[:20]
        
        msg = f"{ET('leaderboard')} <b>TOP 20 LEADERBOARD</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        medals = [ET("king"), ET("star"), ET("cup"), ET("fire"), ET("vip")]
        
        for idx, u in enumerate(sorted_users, 1):
            icon = medals[idx-1] if idx <= len(medals) else ET("ok")
            name = u.get("full_name", "User")[:15]
            sells = u.get("approved_sell", 0)
            refs = u.get("referral_count", 0)
            msg += f"<b>{icon} #{idx} {name}</b> — Sells: <code>{sells}</code> | Refers: <code>{refs}</code>\n"
            
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # 5. MY REPORT BUTTON
    elif text == "My Report":
        sells_all = load_data(SELL_DATA_FILE, {})
        user_sells = [s for s in sells_all.values() if str(s.get("user_id")) == str(uid)]
        
        total = len(user_sells)
        approved = sum(1 for s in user_sells if s.get("status") == "APPROVED")
        rejected = sum(1 for s in user_sells if s.get("status") == "REJECTED")
        pending = sum(1 for s in user_sells if s.get("status") == "PENDING")
        
        msg = (
            f"{ET('my_report')} <b>MY SELL REPORT SUMMARY</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{ET('pin')} <b>Total Submitted:</b> <code>{total}</code>\n"
            f"{ET('done')} <b>Approved:</b> <code>{approved}</code>\n"
            f"{ET('cross')} <b>Rejected:</b> <code>{rejected}</code>\n"
            f"{ET('24h')} <b>Pending:</b> <code>{pending}</code>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # 6. SUPPORT BUTTON
    elif text == "Support":
        supp_usr = cfg.get("support_username", "@Niloy_Owner")
        msg = (
            f"{ET('support')} <b>LIVE SUPPORT CENTER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"For any queries or issues, please contact our support team:\n\n"
            f"{ET('mic')} <b>Official Support:</b> {supp_usr}"
        )
        kb = {"inline_keyboard": [[
            {"text": "CONTACT SUPPORT", "url": f"https://t.me/{supp_usr.replace('@','')}", "style": "primary", "icon_custom_emoji_id": EI("support")}
        ]]}
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # 7. ADMIN PANEL BUTTON
    elif text == "Admin Panel" and is_admin(uid):
        context.user_data.clear()
        await show_admin_panel(update, context)
        return

    # ==========================================================================
    # 🔄 STATE INPUT PROCESSING (FLOWS)
    # ==========================================================================

    # A. SUBMITTING UID & PASS
    if state == "WAITING_UID_PASS_UID":
        fb_uid = text.strip()
        sell_temp = context.user_data.get("sell_temp")
        
        sell_id = "".join(random.choices(string.digits, k=8))
        sells = load_data(SELL_DATA_FILE, {})
        
        sell_entry = {
            "sell_id": sell_id,
            "user_id": uid,
            "type": "UID_PASS",
            "first_name": sell_temp["fn"],
            "last_name": sell_temp["ln"],
            "password": sell_temp["pass"],
            "price": sell_temp["price"],
            "uid": fb_uid,
            "cookies": None,
            "status": "PENDING",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        sells[sell_id] = sell_entry
        save_data(sells, SELL_DATA_FILE)
        
        # Update user stats
        u_data["total_sell"] += 1
        u_data["pending_sell"] += 1
        update_user(uid, u_data)
        
        context.user_data.clear()
        
        await update.message.reply_text(
            f"{ET('done')} <b>Facebook UID & Pass Request Submitted Successfully!</b>\n"
            f"{ET('24h')} Request ID: <code>#{sell_id}</code> (Report time: 12 Hours)",
            reply_markup=build_main_keyboard(uid),
            parse_mode=ParseMode.HTML
        )
        
        # Alert Admin
        admin_id = cfg.get("admin_id", ADMIN_ID)
        adm_msg = (
            f"{ET('notification')} <b>NEW FACEBOOK SELL REQUEST (#{sell_id})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.full_name} (<code>{uid}</code>)\n"
            f"🏷️ <b>Type:</b> UID & Password\n"
            f"📌 <b>First Name:</b> <code>{sell_temp['fn']}</code>\n"
            f"📌 <b>Last Name:</b> <code>{sell_temp['ln']}</code>\n"
            f"🔑 <b>Password:</b> <code>{sell_temp['pass']}</code>\n"
            f"🆔 <b>UID:</b> <code>{fb_uid}</code>\n"
            f"💰 <b>Price:</b> <code>৳{sell_temp['price']:.2f} BDT</code>"
        )
        adm_kb = {"inline_keyboard": [[
            {"text": "APPROVE", "callback_data": f"app_sell_{sell_id}", "style": "success", "icon_custom_emoji_id": EI("ok")},
            {"text": "REJECT", "callback_data": f"rej_sell_{sell_id}", "style": "danger", "icon_custom_emoji_id": EI("delete")}
        ]]}
        try:
            await context.bot.send_message(chat_id=admin_id, text=adm_msg, reply_markup=adm_kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to alert admin: {e}")
        return

    # B. SUBMITTING COOKIES - STEP 1: UID
    elif state == "WAITING_COOKIES_UID":
        context.user_data["cookies_uid"] = text.strip()
        context.user_data["state"] = "WAITING_COOKIES_DATA"
        await update.message.reply_text(f"{ET('ck')} <b>Now, please send your Facebook Cookies data:</b>", parse_mode=ParseMode.HTML)
        return

    # B. SUBMITTING COOKIES - STEP 2: COOKIES
    elif state == "WAITING_COOKIES_DATA":
        cookies_data = text.strip()
        fb_uid = context.user_data.get("cookies_uid")
        sell_temp = context.user_data.get("sell_temp")
        
        sell_id = "".join(random.choices(string.digits, k=8))
        sells = load_data(SELL_DATA_FILE, {})
        
        sell_entry = {
            "sell_id": sell_id,
            "user_id": uid,
            "type": "UID_COOKIES",
            "first_name": sell_temp["fn"],
            "last_name": sell_temp["ln"],
            "password": sell_temp["pass"],
            "price": sell_temp["price"],
            "uid": fb_uid,
            "cookies": cookies_data,
            "status": "PENDING",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        sells[sell_id] = sell_entry
        save_data(sells, SELL_DATA_FILE)
        
        u_data["total_sell"] += 1
        u_data["pending_sell"] += 1
        update_user(uid, u_data)
        
        context.user_data.clear()
        
        await update.message.reply_text(
            f"{ET('done')} <b>Facebook UID & Cookies Request Submitted Successfully!</b>\n"
            f"{ET('24h')} Request ID: <code>#{sell_id}</code> (Report time: 12 Hours)",
            reply_markup=build_main_keyboard(uid),
            parse_mode=ParseMode.HTML
        )
        
        # Alert Admin
        admin_id = cfg.get("admin_id", ADMIN_ID)
        adm_msg = (
            f"{ET('notification')} <b>NEW FACEBOOK SELL REQUEST (#{sell_id})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.full_name} (<code>{uid}</code>)\n"
            f"🏷️ <b>Type:</b> UID & Cookies\n"
            f"📌 <b>First Name:</b> <code>{sell_temp['fn']}</code>\n"
            f"📌 <b>Last Name:</b> <code>{sell_temp['ln']}</code>\n"
            f"🔑 <b>Password:</b> <code>{sell_temp['pass']}</code>\n"
            f"🆔 <b>UID:</b> <code>{fb_uid}</code>\n"
            f"🍪 <b>Cookies:</b> <code>{cookies_data[:50]}...</code>\n"
            f"💰 <b>Price:</b> <code>৳{sell_temp['price']:.2f} BDT</code>"
        )
        adm_kb = {"inline_keyboard": [[
            {"text": "APPROVE", "callback_data": f"app_sell_{sell_id}", "style": "success", "icon_custom_emoji_id": EI("ok")},
            {"text": "REJECT", "callback_data": f"rej_sell_{sell_id}", "style": "danger", "icon_custom_emoji_id": EI("delete")}
        ]]}
        try:
            await context.bot.send_message(chat_id=admin_id, text=adm_msg, reply_markup=adm_kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to alert admin: {e}")
        return

    # C. WITHDRAWAL FLOW
    elif state == "WAITING_WITHDRAW_METHOD":
        method = text.upper()
        if method not in ["BKASH", "NAGAD", "BINANCE"]:
            await update.message.reply_text("Please select a valid payment method from the buttons below.")
            return
        
        context.user_data["withdraw_method"] = method
        context.user_data["state"] = "WAITING_WITHDRAW_AMOUNT"
        min_w = cfg.get("min_withdraw", 50.0)
        
        await update.message.reply_text(
            f"{ET('money')} <b>Enter withdraw amount (Min: ৳{min_w:.2f} BDT):</b>",
            parse_mode=ParseMode.HTML
        )
        return

    elif state == "WAITING_WITHDRAW_AMOUNT":
        try:
            amount = float(text)
        except:
            await update.message.reply_text("Please enter a valid numeric amount.")
            return

        min_w = cfg.get("min_withdraw", 50.0)
        if amount < min_w:
            await update.message.reply_text(f"{ET('danger')} Minimum withdrawal amount is <code>৳{min_w:.2f} BDT</code>.", parse_mode=ParseMode.HTML)
            return

        if amount > u_data["balance"]:
            await update.message.reply_text(f"{ET('danger')} Insufficient balance! Your active balance is <code>৳{u_data['balance']:.2f} BDT</code>.", parse_mode=ParseMode.HTML)
            return

        context.user_data["withdraw_amount"] = amount
        context.user_data["state"] = "WAITING_WITHDRAW_ACC"
        
        await update.message.reply_text(
            f"{ET('pin')} <b>Enter your {context.user_data['withdraw_method']} Account Number / Address:</b>",
            parse_mode=ParseMode.HTML
        )
        return

    elif state == "WAITING_WITHDRAW_ACC":
        acc_num = text.strip()
        method = context.user_data.get("withdraw_method")
        amount = context.user_data.get("withdraw_amount")
        
        wd_id = "".join(random.choices(string.digits, k=8))
        withdraws = load_data(WITHDRAW_DATA_FILE, {})
        
        wd_entry = {
            "withdraw_id": wd_id,
            "user_id": uid,
            "method": method,
            "amount": amount,
            "account_number": acc_num,
            "status": "PENDING",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        withdraws[wd_id] = wd_entry
        save_data(withdraws, WITHDRAW_DATA_FILE)
        
        # Deduct user balance immediately
        u_data["balance"] -= amount
        update_user(uid, u_data)
        
        context.user_data.clear()
        
        await update.message.reply_text(
            f"{ET('done')} <b>Withdrawal Request Submitted!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>Method:</b> {method}\n"
            f"💰 <b>Amount:</b> ৳{amount:.2f} BDT\n"
            f"📞 <b>Account:</b> {acc_num}\n"
            f"🆔 <b>Request ID:</b> #{wd_id}",
            reply_markup=build_main_keyboard(uid),
            parse_mode=ParseMode.HTML
        )
        
        # Alert Admin
        admin_id = cfg.get("admin_id", ADMIN_ID)
        adm_msg = (
            f"{ET('withdraw')} <b>NEW WITHDRAWAL REQUEST (#{wd_id})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.full_name} (<code>{uid}</code>)\n"
            f"🏷️ <b>Method:</b> {method}\n"
            f"💰 <b>Amount:</b> <code>৳{amount:.2f} BDT</code>\n"
            f"📞 <b>Account:</b> <code>{acc_num}</code>"
        )
        adm_kb = {"inline_keyboard": [[
            {"text": "APPROVE", "callback_data": f"app_wd_{wd_id}", "style": "success", "icon_custom_emoji_id": EI("ok")},
            {"text": "REJECT", "callback_data": f"rej_wd_{wd_id}", "style": "danger", "icon_custom_emoji_id": EI("delete")}
        ]]}
        try:
            await context.bot.send_message(chat_id=admin_id, text=adm_msg, reply_markup=adm_kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to alert admin of withdraw: {e}")
        return

    # ADMIN INPUT STATES
    if is_admin(uid):
        await handle_admin_input_states(update, context, state, text)

# ==============================================================================
# 🎛️ CALLBACK QUERY HANDLER
# ==============================================================================

async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    uid = user.id
    
    await query.answer()

    if data == "check_join_status":
        if await check_force_join(context.bot, uid):
            try:
                await query.message.delete()
            except:
                pass
            await show_main_menu(update, context)
        else:
            await query.answer("❌ You have not joined all mandatory channels yet!", show_alert=True)
        return

    # WITHDRAW START FROM BALANCE MENU
    elif data == "start_withdraw":
        cfg = get_config()
        u_data = get_user(uid)
        min_w = cfg.get("min_withdraw", 50.0)
        
        if u_data["balance"] < min_w:
            await query.answer(f"Minimum withdrawal requirement is ৳{min_w:.2f} BDT!", show_alert=True)
            return
            
        btn_rows = []
        if cfg.get("bkash_active", True):
            btn_rows.append([{"text": "BKASH", "style": "danger", "icon_custom_emoji_id": EI("bkash")}])
        if cfg.get("nagad_active", True):
            btn_rows.append([{"text": "NAGAD", "style": "primary", "icon_custom_emoji_id": EI("nagad")}])
        if cfg.get("binance_active", True):
            btn_rows.append([{"text": "BINANCE", "style": "success", "icon_custom_emoji_id": EI("binance")}])
            
        btn_rows.append([{"text": "Cancel", "style": "danger", "icon_custom_emoji_id": EI("delete")}])
        
        context.user_data["state"] = "WAITING_WITHDRAW_METHOD"
        kb = {"keyboard": btn_rows, "resize_keyboard": True}
        
        await context.bot.send_message(
            chat_id=uid,
            text=f"{ET('money')} <b>Select Withdrawal Payment Method:</b>",
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )
        return

    # ADMIN APPROVE SELL
    elif data.startswith("app_sell_"):
        if not is_admin(uid): return
        sell_id = data.replace("app_sell_", "")
        sells = load_data(SELL_DATA_FILE, {})
        
        if sell_id in sells and sells[sell_id]["status"] == "PENDING":
            s = sells[sell_id]
            s["status"] = "APPROVED"
            save_data(sells, SELL_DATA_FILE)
            
            # Credit User
            target_uid = str(s["user_id"])
            u = get_user(target_uid)
            u["balance"] += s["price"]
            u["approved_sell"] += 1
            if u["pending_sell"] > 0: u["pending_sell"] -= 1
            update_user(target_uid, u)
            
            await query.edit_message_text(f"✅ <b>Approved Sell Request #{sell_id}</b>", parse_mode=ParseMode.HTML)
            
            # Notify User
            notif = (
                f"{ET('done')} <b>FACEBOOK SELL APPROVED!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Request ID: <code>#{sell_id}</code>\n"
                f"Amount Credited: <code>+৳{s['price']:.2f} BDT</code>"
            )
            try:
                await context.bot.send_message(chat_id=int(target_uid), text=notif, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to notify user {target_uid}: {e}")
        return

    # ADMIN REJECT SELL
    elif data.startswith("rej_sell_"):
        if not is_admin(uid): return
        sell_id = data.replace("rej_sell_", "")
        sells = load_data(SELL_DATA_FILE, {})
        
        if sell_id in sells and sells[sell_id]["status"] == "PENDING":
            s = sells[sell_id]
            s["status"] = "REJECTED"
            save_data(sells, SELL_DATA_FILE)
            
            target_uid = str(s["user_id"])
            u = get_user(target_uid)
            u["rejected_sell"] += 1
            if u["pending_sell"] > 0: u["pending_sell"] -= 1
            update_user(target_uid, u)
            
            await query.edit_message_text(f"❌ <b>Rejected Sell Request #{sell_id}</b>", parse_mode=ParseMode.HTML)
            
            # Notify User
            notif = (
                f"{ET('cross')} <b>FACEBOOK SELL REJECTED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Request ID: <code>#{sell_id}</code>\n"
                f"Your Facebook ID sell request was not approved."
            )
            try:
                await context.bot.send_message(chat_id=int(target_uid), text=notif, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to notify user {target_uid}: {e}")
        return

    # ADMIN APPROVE WITHDRAW
    elif data.startswith("app_wd_"):
        if not is_admin(uid): return
        wd_id = data.replace("app_wd_", "")
        withdraws = load_data(WITHDRAW_DATA_FILE, {})
        
        if wd_id in withdraws and withdraws[wd_id]["status"] == "PENDING":
            w = withdraws[wd_id]
            w["status"] = "APPROVED"
            save_data(withdraws, WITHDRAW_DATA_FILE)
            
            target_uid = str(w["user_id"])
            u = get_user(target_uid)
            u["total_withdraw"] += w["amount"]
            update_user(target_uid, u)
            
            await query.edit_message_text(f"✅ <b>Approved Withdrawal #{wd_id}</b>", parse_mode=ParseMode.HTML)
            
            # Notify User
            notif = (
                f"{ET('done')} <b>WITHDRAWAL APPROVED!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Request ID: <code>#{wd_id}</code>\n"
                f"Amount: <code>৳{w['amount']:.2f} BDT</code>\n"
                f"Method: {w['method']}"
            )
            try:
                await context.bot.send_message(chat_id=int(target_uid), text=notif, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to notify user {target_uid}: {e}")
        return

    # ADMIN REJECT WITHDRAW
    elif data.startswith("rej_wd_"):
        if not is_admin(uid): return
        wd_id = data.replace("rej_wd_", "")
        withdraws = load_data(WITHDRAW_DATA_FILE, {})
        
        if wd_id in withdraws and withdraws[wd_id]["status"] == "PENDING":
            w = withdraws[wd_id]
            w["status"] = "REJECTED"
            save_data(withdraws, WITHDRAW_DATA_FILE)
            
            # Refund user balance
            target_uid = str(w["user_id"])
            u = get_user(target_uid)
            u["balance"] += w["amount"]
            update_user(target_uid, u)
            
            await query.edit_message_text(f"❌ <b>Rejected Withdrawal #{wd_id}</b>", parse_mode=ParseMode.HTML)
            
            # Notify User
            notif = (
                f"{ET('cross')} <b>WITHDRAWAL REJECTED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Request ID: <code>#{wd_id}</code>\n"
                f"Amount <code>৳{w['amount']:.2f} BDT</code> has been refunded to your account balance."
            )
            try:
                await context.bot.send_message(chat_id=int(target_uid), text=notif, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to notify user {target_uid}: {e}")
        return

    # ADMIN PANEL CALLBACK ACTIONS
    if is_admin(uid):
        await handle_admin_callbacks(update, context, data)

# ==============================================================================
# 👑 ADMIN PANEL & CONTROL SUITE
# ==============================================================================

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USER_DATA_FILE, {})
    sells = load_data(SELL_DATA_FILE, {})
    banned = load_data(BANNED_USERS_FILE, [])
    cfg = get_config()
    
    total_users = len(users)
    total_banned = len(banned)
    total_sells = len(sells)
    
    msg = (
        f"{ET('admin')} <b>ZARYA ACCOUNTS ADMIN DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{ET('vip')} <b>Total Users:</b> <code>{total_users}</code>\n"
        f"{ET('danger')} <b>Banned Users:</b> <code>{total_banned}</code>\n"
        f"{ET('facebook')} <b>Total ID Sells:</b> <code>{total_sells}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>UID&Pass Password:</b> <code>{cfg.get('uid_pass_default_pass')}</code>\n"
        f"🔑 <b>UID&Cookies Password:</b> <code>{cfg.get('uid_cookies_default_pass')}</code>\n"
        f"📢 <b>Force Join Channels:</b> <code>{len(cfg.get('force_join_channels', []))} Configured</code>"
    )
    
    kb = {"inline_keyboard": [
        [
            {"text": "ALL USERS FILE", "callback_data": "adm_users_file", "style": "primary", "icon_custom_emoji_id": EI("pin")},
            {"text": "BROADCAST SMS", "callback_data": "adm_broadcast", "style": "success", "icon_custom_emoji_id": EI("mic")}
        ],
        [
            {"text": "+ ADD BALANCE", "callback_data": "adm_add_bal", "style": "success", "icon_custom_emoji_id": EI("coin")},
            {"text": "- REMOVE BALANCE", "callback_data": "adm_rem_bal", "style": "danger", "icon_custom_emoji_id": EI("money")}
        ],
        [
            {"text": "FORCE JOIN SETTINGS", "callback_data": "adm_fj_menu", "style": "primary", "icon_custom_emoji_id": EI("link")},
            {"text": "REFERRAL REWARD", "callback_data": "adm_set_ref", "style": "primary", "icon_custom_emoji_id": EI("gift")}
        ],
        [
            {"text": "UID&PASS RATE", "callback_data": "adm_set_rate_up", "style": "primary", "icon_custom_emoji_id": EI("dollar")},
            {"text": "UID&COOKIES RATE", "callback_data": "adm_set_rate_cook", "style": "primary", "icon_custom_emoji_id": EI("dollar")}
        ],
        [
            {"text": "MIN WITHDRAW SET", "callback_data": "adm_set_min_wd", "style": "primary", "icon_custom_emoji_id": EI("withdraw")},
            {"text": "PAYMENT METHODS", "callback_data": "adm_toggle_pay", "style": "primary", "icon_custom_emoji_id": EI("bkash")}
        ],
        [
            {"text": "SELL SYSTEM TOGGLE", "callback_data": "adm_toggle_sell", "style": "primary", "icon_custom_emoji_id": EI("facebook")},
            {"text": "PASSWORDS SET", "callback_data": "adm_set_passes", "style": "primary", "icon_custom_emoji_id": EI("pin")}
        ],
        [
            {"text": "BAN / UNBAN USER", "callback_data": "adm_ban_menu", "style": "danger", "icon_custom_emoji_id": EI("delete")},
            {"text": "SCAN USER DETAILS", "callback_data": "adm_scan_user", "style": "primary", "icon_custom_emoji_id": EI("search")}
        ],
        [
            {"text": "SET HELPLINE ID", "callback_data": "adm_set_help", "style": "success", "icon_custom_emoji_id": EI("support")}
        ]
    ]}
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    query = update.callback_query
    cfg = get_config()
    
    if data == "adm_users_file":
        users = load_data(USER_DATA_FILE, {})
        sells = load_data(SELL_DATA_FILE, {})
        
        content = "ZARYA ACCOUNTS REGISTERED USERS DUMP\n"
        content += "========================================\n\n"
        for uid, u in users.items():
            content += f"ID: {uid} | Name: {u.get('full_name')} | Balance: ৳{u.get('balance'):.2f} | Sells: {u.get('approved_sell')} | Refers: {u.get('referral_count')}\n"
            
        f = io.BytesIO(content.encode('utf-8'))
        f.name = "All_Users_Report.txt"
        await context.bot.send_document(chat_id=query.from_user.id, document=f, caption="📊 Complete Registered Users Report")
        return

    elif data == "adm_broadcast":
        context.user_data["state"] = "ADM_WAITING_BROADCAST"
        await query.message.reply_text("<b>Enter broadcast message text to send to all users:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_add_bal":
        context.user_data["state"] = "ADM_WAITING_ADD_BAL_USER"
        await query.message.reply_text("<b>Enter User ID to credit balance to:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_rem_bal":
        context.user_data["state"] = "ADM_WAITING_REM_BAL_USER"
        await query.message.reply_text("<b>Enter User ID to debit balance from:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_ref":
        context.user_data["state"] = "ADM_WAITING_REF_RATE"
        await query.message.reply_text("<b>Enter new referral reward amount in BDT:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_rate_up":
        context.user_data["state"] = "ADM_WAITING_UP_RATE"
        await query.message.reply_text("<b>Enter new UID & Pass sell rate in BDT:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_rate_cook":
        context.user_data["state"] = "ADM_WAITING_COOK_RATE"
        await query.message.reply_text("<b>Enter new UID & Cookies sell rate in BDT:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_min_wd":
        context.user_data["state"] = "ADM_WAITING_MIN_WD"
        await query.message.reply_text("<b>Enter new minimum withdrawal amount in BDT:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_passes":
        context.user_data["state"] = "ADM_WAITING_PASS_TYPE"
        kb = {"inline_keyboard": [
            [{"text": "Set UID&Pass Password", "callback_data": "adm_pass_up"}, {"text": "Set UID&Cookies Password", "callback_data": "adm_pass_cook"}]
        ]}
        await query.message.reply_text("Select which system password to change:", reply_markup=kb)
        return

    elif data == "adm_pass_up":
        context.user_data["state"] = "ADM_WAITING_UP_PASS_VAL"
        await query.message.reply_text("Enter new default password for UID & Pass:")
        return

    elif data == "adm_pass_cook":
        context.user_data["state"] = "ADM_WAITING_COOK_PASS_VAL"
        await query.message.reply_text("Enter new default password for UID & Cookies:")
        return

    elif data == "adm_toggle_pay":
        cfg["bkash_active"] = not cfg.get("bkash_active", True)
        save_config(cfg)
        await query.answer(f"Bkash status set to: {cfg['bkash_active']}", show_alert=True)
        return

    elif data == "adm_toggle_sell":
        cfg["sell_system_active"] = not cfg.get("sell_system_active", True)
        save_config(cfg)
        await query.answer(f"Facebook Sell system set to: {cfg['sell_system_active']}", show_alert=True)
        return

    elif data == "adm_fj_menu":
        channels = cfg.get("force_join_channels", [])
        txt = "<b>Current Force Join Channels:</b>\n\n"
        for idx, ch in enumerate(channels, 1):
            txt += f"{idx}. Chat ID: <code>{ch.get('chat_id')}</code> | Link: {ch.get('link')}\n"
            
        kb = {"inline_keyboard": [
            [{"text": "+ ADD CHANNEL", "callback_data": "adm_fj_add"}, {"text": "CLEAR ALL CHANNELS", "callback_data": "adm_fj_clear"}]
        ]}
        await query.message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    elif data == "adm_fj_add":
        context.user_data["state"] = "ADM_WAITING_FJ_ID"
        await query.message.reply_text("<b>Send the Chat ID of the channel/group (e.g. -100xxxxxxx):</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_fj_clear":
        cfg["force_join_channels"] = []
        save_config(cfg)
        await query.answer("All Force Join channels removed!", show_alert=True)
        return

    elif data == "adm_ban_menu":
        context.user_data["state"] = "ADM_WAITING_BAN_ID"
        await query.message.reply_text("<b>Enter Telegram User ID to Ban/Unban:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_scan_user":
        context.user_data["state"] = "ADM_WAITING_SCAN_ID"
        await query.message.reply_text("<b>Enter Telegram User ID to scan details:</b>", parse_mode=ParseMode.HTML)
        return

    elif data == "adm_set_help":
        context.user_data["state"] = "ADM_WAITING_HELP_ID"
        await query.message.reply_text("<b>Enter new Helpline Username (e.g., @Niloy_Owner):</b>", parse_mode=ParseMode.HTML)
        return

async def handle_admin_input_states(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, text: str):
    cfg = get_config()
    
    if state == "ADM_WAITING_BROADCAST":
        context.user_data.clear()
        users = load_data(USER_DATA_FILE, {})
        await update.message.reply_text(f"Broadcasting to {len(users)} users...")
        count = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 <b>ANNOUNCEMENT</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}", parse_mode=ParseMode.HTML)
                count += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await update.message.reply_text(f"✅ Broadcast complete. Delivered to {count} users.")
        return

    elif state == "ADM_WAITING_ADD_BAL_USER":
        context.user_data["target_uid"] = text.strip()
        context.user_data["state"] = "ADM_WAITING_ADD_BAL_AMT"
        await update.message.reply_text("Enter amount to credit:")
        return

    elif state == "ADM_WAITING_ADD_BAL_AMT":
        try:
            amt = float(text)
            target = context.user_data.get("target_uid")
            u = get_user(target)
            u["balance"] += amt
            update_user(target, u)
            context.user_data.clear()
            await update.message.reply_text(f"✅ Added ৳{amt:.2f} BDT to User #{target}. New Balance: ৳{u['balance']:.2f} BDT.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        return

    elif state == "ADM_WAITING_REM_BAL_USER":
        context.user_data["target_uid"] = text.strip()
        context.user_data["state"] = "ADM_WAITING_REM_BAL_AMT"
        await update.message.reply_text("Enter amount to debit:")
        return

    elif state == "ADM_WAITING_REM_BAL_AMT":
        try:
            amt = float(text)
            target = context.user_data.get("target_uid")
            u = get_user(target)
            u["balance"] -= amt
            if u["balance"] < 0: u["balance"] = 0
            update_user(target, u)
            context.user_data.clear()
            await update.message.reply_text(f"✅ Debited ৳{amt:.2f} BDT from User #{target}. New Balance: ৳{u['balance']:.2f} BDT.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        return

    elif state == "ADM_WAITING_REF_RATE":
        try:
            cfg["referral_reward"] = float(text)
            save_config(cfg)
            context.user_data.clear()
            await update.message.reply_text(f"✅ Referral reward updated to ৳{cfg['referral_reward']:.2f} BDT.")
        except:
            await update.message.reply_text("Invalid amount.")
        return

    elif state == "ADM_WAITING_UP_RATE":
        try:
            cfg["uid_pass_rate"] = float(text)
            save_config(cfg)
            context.user_data.clear()
            await update.message.reply_text(f"✅ UID & Pass rate updated to ৳{cfg['uid_pass_rate']:.2f} BDT.")
        except:
            await update.message.reply_text("Invalid rate.")
        return

    elif state == "ADM_WAITING_COOK_RATE":
        try:
            cfg["uid_cookies_rate"] = float(text)
            save_config(cfg)
            context.user_data.clear()
            await update.message.reply_text(f"✅ UID & Cookies rate updated to ৳{cfg['uid_cookies_rate']:.2f} BDT.")
        except:
            await update.message.reply_text("Invalid rate.")
        return

    elif state == "ADM_WAITING_MIN_WD":
        try:
            cfg["min_withdraw"] = float(text)
            save_config(cfg)
            context.user_data.clear()
            await update.message.reply_text(f"✅ Minimum withdrawal updated to ৳{cfg['min_withdraw']:.2f} BDT.")
        except:
            await update.message.reply_text("Invalid threshold.")
        return

    elif state == "ADM_WAITING_UP_PASS_VAL":
        cfg["uid_pass_default_pass"] = text.strip()
        save_config(cfg)
        context.user_data.clear()
        await update.message.reply_text(f"✅ UID & Pass default password set to: <code>{cfg['uid_pass_default_pass']}</code>", parse_mode=ParseMode.HTML)
        return

    elif state == "ADM_WAITING_COOK_PASS_VAL":
        cfg["uid_cookies_default_pass"] = text.strip()
        save_config(cfg)
        context.user_data.clear()
        await update.message.reply_text(f"✅ UID & Cookies default password set to: <code>{cfg['uid_cookies_default_pass']}</code>", parse_mode=ParseMode.HTML)
        return

    elif state == "ADM_WAITING_FJ_ID":
        context.user_data["fj_id"] = text.strip()
        context.user_data["state"] = "ADM_WAITING_FJ_LINK"
        await update.message.reply_text("Send the Channel invite link (e.g. https://t.me/...):")
        return

    elif state == "ADM_WAITING_FJ_LINK":
        link = text.strip()
        cid = context.user_data.get("fj_id")
        channels = cfg.get("force_join_channels", [])
        channels.append({"chat_id": cid, "link": link})
        cfg["force_join_channels"] = channels
        save_config(cfg)
        context.user_data.clear()
        await update.message.reply_text("✅ Force join channel added successfully!")
        return

    elif state == "ADM_WAITING_BAN_ID":
        target = text.strip()
        banned = load_data(BANNED_USERS_FILE, [])
        if target in [str(x) for x in banned]:
            banned.remove(target)
            save_data(banned, BANNED_USERS_FILE)
            await update.message.reply_text(f"✅ User #{target} UNBANNED successfully.")
        else:
            banned.append(target)
            save_data(banned, BANNED_USERS_FILE)
            await update.message.reply_text(f"🚫 User #{target} BANNED successfully.")
        context.user_data.clear()
        return

    elif state == "ADM_WAITING_SCAN_ID":
        target = text.strip()
        u = get_user(target)
        msg = (
            f"🔍 <b>USER DETAILED SCAN REPORT (#{target})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name:</b> {u.get('full_name')}\n"
            f"💰 <b>Balance:</b> ৳{u.get('balance'):.2f} BDT\n"
            f"📦 <b>Total Sells:</b> {u.get('total_sell')}\n"
            f"✅ <b>Approved Sells:</b> {u.get('approved_sell')}\n"
            f"❌ <b>Rejected Sells:</b> {u.get('rejected_sell')}\n"
            f"👥 <b>Total Refers:</b> {u.get('referral_count')}\n"
            f"📅 <b>Joined Date:</b> {u.get('joined_date')}"
        )
        context.user_data.clear()
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    elif state == "ADM_WAITING_HELP_ID":
        cfg["support_username"] = text.strip()
        save_config(cfg)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Helpline ID set to {cfg['support_username']}")
        return

# ==============================================================================
# 🚀 MAIN APPLICATION ENTRY POINT
# ==============================================================================

def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback_queries))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    logger.info("⚡ Zarya Accounts Telegram Bot is online and listening...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
