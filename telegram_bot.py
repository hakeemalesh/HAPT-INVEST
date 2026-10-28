import os
os.environ["TELEGRAM_BOT_TOKEN"] = "8740075368:AAFQ29GbkZvVhO01SePMnzYyDh-s-NZcM0Q"

import logging
from telegram.error import NetworkError, TimedOut

async def global_error_handler(update, context):
    if isinstance(context.error, (NetworkError, TimedOut)):
        logging.warning("⚠️ Network latency detected. Reconnecting automatically...")
    else:
        logging.error(f"Engine Exception: {context.error}")
import os
import logging
from dotenv import load_dotenv, find_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import strategy_engine

load_dotenv(find_dotenv())
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Core Multi-Market Watchlist
WATCHLIST = [
    "NVDA", "AAPL", "TSLA", "MSFT", "AMD",  # US Market
    "SHEL.L", "AZN.L", "LLOY.L", "BP.L"     # London Stock Exchange
]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("NVDA (US)", callback_data="scan_NVDA"), InlineKeyboardButton("AAPL (US)", callback_data="scan_AAPL")],
        [InlineKeyboardButton("TSLA (US)", callback_data="scan_TSLA"), InlineKeyboardButton("MSFT (US)", callback_data="scan_MSFT")],
        [InlineKeyboardButton("Shell (LSE)", callback_data="scan_SHEL.L"), InlineKeyboardButton("AstraZeneca (LSE)", callback_data="scan_AZN.L")],
        [InlineKeyboardButton("Lloyds (LSE)", callback_data="scan_LLOY.L"), InlineKeyboardButton("BP (LSE)", callback_data="scan_BP.L")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "⚡ HAPT INVEST MASTER INTERFACE ⚡\n"
        "• Background Watchlist Scanner: ACTIVE (15m Interval)\n"
        "• Markets Configured: US Equities & London Stock Exchange\n"
        "• Confluence Filter: ACTIVE\n\n"
        "Select an asset below for immediate manual scan:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    if context.job_queue:
        current_jobs = context.job_queue.get_jobs_by_name("watchlist_scanner")
        if not current_jobs:
            context.job_queue.run_repeating(
                scheduled_scan,
                interval=900,
                first=10,
                chat_id=user_id,
                name="watchlist_scanner"
            )

async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    for symbol in WATCHLIST:
        try:
            result = strategy_engine.run_engine(symbol)
            if result:
                await context.bot.send_message(chat_id=chat_id, text=result)
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data.replace("scan_", "")
    
    result = strategy_engine.run_engine(symbol)
    if result:
        await query.message.reply_text(result)
    else:
        await query.message.reply_text(f"⚠️ Scan completed for {symbol}: No setup detected.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN missing from .env!")
        return

    logger.info("🚀 HAPT INVEST Master Engine Initialized. Polling started...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.run_polling()

if __name__ == "__main__":
    main()


