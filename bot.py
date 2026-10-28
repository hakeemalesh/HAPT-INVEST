# -*- coding: utf-8 -*-
import sqlite3
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = "8740075368:AAFQ29GbkZvVhO01SePMnzYyDh-s-NZcM0Q"
DB_PATH = "hapt_invest.db"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🦅 *HAPT INVEST | Institutional Command Endpoint*\n\n"
        "Available Commands:\n"
        "• /status - Check 72-hr Paper Trading Telemetry & System Health\n"
        "• /signals - List recent Grade A/A+ institutional alerts\n"
        "• /check <TICKER> - Run real-time volume & ATR analysis on any ticker\n"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT ticker) FROM signals")
        total_signals, unique_tickers = cursor.fetchone()
        conn.close()
        
        status_msg = (
            "📊 *HAPT INVEST | System Telemetry Status*\n\n"
            f"• *Status:* 🟢 ACTIVE (Paper Trading Mode)\n"
            f"• *Database:* Online (hapt_invest.db)\n"
            f"• *Total Signals Persisted:* {total_signals}\n"
            f"• *Unique Assets Tracked:* {unique_tickers}\n"
        )
    except Exception as e:
        status_msg = f"⚠️ Telemetry query error: {e}"
        
    await update.message.reply_text(status_msg, parse_mode="Markdown")

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, ticker, grade, confidence, price FROM signals ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            await update.message.reply_text("ℹ️ No signals recorded yet in telemetry database.")
            return

        msg = "🚨 *Recent Institutional Signals*\n\n"
        for r in rows:
            msg += f"• *{r[1]}* | {r[2]} ({r[3]}%) |  @ {r[0]}\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Telemetry query error: {e}")

async def check_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a ticker, e.g., /check NVDA or /check SHEL.L")
        return
        
    ticker = context.args[0].upper()
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="21d")
        if len(hist) < 21:
            await update.message.reply_text(f"Insufficient historical data for {ticker}.")
            return
            
        current = hist.iloc[-1]
        avg_vol = hist["Volume"].iloc[:-1].mean()
        rvol = current["Volume"] / avg_vol if avg_vol > 0 else 0
        
        tr = max(current['High'] - current['Low'], 
                 abs(current['High'] - hist['Close'].iloc[-2]), 
                 abs(current['Low'] - hist['Close'].iloc[-2]))
        prev_ranges = (hist['High'] - hist['Low']).iloc[-15:-1]
        atr_14 = prev_ranges.mean() if len(prev_ranges) > 0 else 1.0
        atr_expansion = tr / atr_14 if atr_14 > 0 else 1.0
        
        reply = (
            f"🔍 *Live Inspection: {ticker}*\n\n"
            f"• *Price:* \n"
            f"• *RVOL:* {rvol:.2f}x vs 20D Avg\n"
            f"• *ATR Range Expansion:* {atr_expansion:.2f}x\n"
        )
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error checking ticker {ticker}: {e}")

if __name__ == '__main__':
    print("Starting HAPT INVEST Interactive Bot (Segment 2)...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("signals", signals))
    app.add_handler(CommandHandler("check", check_ticker))
    app.run_polling()
