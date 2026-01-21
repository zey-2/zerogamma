"""
Telegram messaging module for sending market analysis to group chat.

Uses python-telegram-bot to post formatted analysis results.
"""

import asyncio
import html
import logging
import re

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def _send_message_async(
    bot_token: str,
    chat_id_int: int,
    message: str,
    message_thread_id: int | None = None,
) -> None:
    """
    Send a Telegram message asynchronously.

    Parameters:
        bot_token (str): Telegram bot token.
        chat_id_int (int): Telegram chat ID as integer.
        message (str): Message text to send.
        message_thread_id (int | None): Telegram topic (message thread) ID.
    """
    async with Bot(token=bot_token) as bot:
        await bot.send_message(
            chat_id=chat_id_int,
            text=message,
            parse_mode="HTML",
            message_thread_id=message_thread_id,
        )


def send_to_telegram(
    bot_token: str,
    chat_id: str,
    message: str,
    message_thread_id: str | None = None,
) -> bool:
    """
    Send formatted message to Telegram group chat.
    
    Parameters:
        bot_token (str): Telegram bot token.
        chat_id (str): Telegram group chat ID (can be negative for groups).
        message (str): Message text to send.
        message_thread_id (str | None): Telegram topic (message thread) ID.
    
    Returns:
        bool: True if message sent successfully, False otherwise.
    """
    try:
        # Parse chat ID (handle negative group chat IDs)
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            logger.error(f"Invalid chat ID format: {chat_id}")
            return False

        # Parse topic ID (optional)
        topic_id_int = None
        if message_thread_id:
            try:
                topic_id_int = int(message_thread_id)
            except ValueError:
                logger.error(
                    f"Invalid message_thread_id format: {message_thread_id}"
                )
                return False

        # Send message (async API)
        try:
            asyncio.run(
                _send_message_async(
                    bot_token,
                    chat_id_int,
                    message,
                    message_thread_id=topic_id_int,
                )
            )
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                _send_message_async(
                    bot_token,
                    chat_id_int,
                    message,
                    message_thread_id=topic_id_int,
                )
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
    timestamp = __import__("datetime").datetime.now().strftime(
        "%Y-%m-%d"
    )
    formatted_analysis = _normalize_analysis_for_telegram(analysis)

    message = (
        f"<b>{symbol} Market Analysis</b>\n"
        f"<i>{timestamp}</i>\n\n"
        f"<b>Current Price:</b> ${current_price:.2f}\n"
        f"<b>Zero Gamma Level:</b> ${zero_gamma_level:.2f}\n\n"
        f"<b>Analysis:</b>\n"
        f"{formatted_analysis}"
    )
    
    return message


def _normalize_analysis_for_telegram(text: str) -> str:
    """
    Normalize analysis text for Telegram HTML parse mode.

    Converts Markdown bold to HTML bold, preserves bullets, and escapes
    unsupported HTML characters to avoid formatting issues.

    Parameters:
        text (str): Raw analysis text from OpenRouter.

    Returns:
        str: Telegram-safe HTML text.
    """
    escaped = html.escape(text)
    lines = escaped.splitlines()
    normalized_lines = [_convert_line(line) for line in lines]
    return "\n".join(normalized_lines).strip()


def _convert_line(line: str) -> str:
    """
    Convert a single line to Telegram-safe HTML.

    Parameters:
        line (str): Escaped text line.

    Returns:
        str: Converted line with bullets and bold formatting.
    """
    stripped = line.lstrip()
    bullet_prefixes = ("* ", "- ")
    if stripped.startswith(bullet_prefixes):
        content = stripped[2:].strip()
        return f"• {_convert_bold_markdown(content)}"
    return _convert_bold_markdown(line)


def _convert_bold_markdown(text: str) -> str:
    """
    Convert Markdown bold markers to Telegram HTML bold tags.

    Parameters:
        text (str): Escaped text containing Markdown bold markers.

    Returns:
        str: Text with Markdown bold converted to HTML.
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
