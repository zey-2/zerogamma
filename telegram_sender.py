"""
Telegram messaging module for sending market analysis to group chat.

Uses python-telegram-bot to post formatted analysis results.
"""

from telegram import Bot
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)


def send_to_telegram(
    bot_token: str,
    chat_id: str,
    message: str,
) -> bool:
    """
    Send formatted message to Telegram group chat.
    
    Parameters:
        bot_token (str): Telegram bot token.
        chat_id (str): Telegram group chat ID (can be negative for groups).
        message (str): Message text to send.
    
    Returns:
        bool: True if message sent successfully, False otherwise.
    """
    try:
        bot = Bot(token=bot_token)
        
        # Parse chat ID (handle negative group chat IDs)
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            logger.error(f"Invalid chat ID format: {chat_id}")
            return False
        
        # Send message
        bot.send_message(
            chat_id=chat_id_int,
            text=message,
            parse_mode="HTML",
        )
        
        logger.info(f"Successfully sent message to Telegram chat {chat_id}")
        return True
        
    except TelegramError as e:
        logger.error(f"Telegram API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending Telegram message: {e}")
        return False


def format_analysis_message(
    zero_gamma_level: float,
    analysis: str,
    current_price: float,
    symbol: str = "SPX",
) -> str:
    """
    Format analysis results for Telegram message.
    
    Parameters:
        zero_gamma_level (float): Zero gamma strike price.
        analysis (str): Market analysis text from OpenRouter.
        current_price (float): Current market price of symbol.
        symbol (str): Stock symbol being analyzed.
    
    Returns:
        str: Formatted HTML message for Telegram.
    """
    timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        f"<b>{symbol} Market Analysis</b>\n"
        f"<i>{timestamp}</i>\n\n"
        f"<b>Current Price:</b> ${current_price:.2f}\n"
        f"<b>Zero Gamma Level:</b> ${zero_gamma_level:.2f}\n\n"
        f"<b>Analysis:</b>\n"
        f"{analysis}"
    )
    
    return message
