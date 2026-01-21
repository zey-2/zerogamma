#!/usr/bin/env python3
"""
Main orchestration script for zerogamma analysis pipeline.

Fetches zero gamma level from SpotGamma, retrieves SPX OHLC data from FMP,
analyzes via OpenRouter, and sends results to Telegram.

Usage:
    python send_analysis.py
    
Environment Variables Required:
    - FMP_API_KEY: Financial Modeling Prep API key
    - OPENROUTER_API_KEY: OpenRouter API key
    - TELEGRAM_BOT_TOKEN: Telegram bot token
    - TELEGRAM_CHAT_ID: Telegram group chat ID
"""

import argparse
import base64
import hashlib
import hmac
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from config import get_config
from fmp_data import fetch_spx_ohlc_csv
from openrouter_analysis import analyze_with_openrouter
from telegram_sender import send_to_telegram, format_analysis_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("zerogamma_analysis.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# SpotGamma configuration
DEFAULT_SYM = "SPX"
LEVELS_URL = "https://api.spotgamma.com/v2/levelsBySym?sym={sym}"
JWT_SECRET = "secretKeyValue"


@dataclass(frozen=True)
class ZeroGammaLevel:
    """
    Data class for zero gamma level information from SpotGamma API.
    
    Attributes:
        sym: Stock symbol.
        trade_date: ISO format date string from API.
        zero_g_strike: Zero gamma strike price level.
        source_url: URL of the API endpoint queried.
    """
    sym: str
    trade_date: str
    zero_g_strike: float
    source_url: str


def _b64url(data: bytes) -> str:
    """
    Encode bytes to URL-safe base64 without padding.
    
    Parameters:
        data: Bytes to encode.
        
    Returns:
        str: Base64-encoded string.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwt_hs256(payload: Dict[str, Any], secret: str) -> str:
    """
    Create HS256-signed JWT token.
    
    Parameters:
        payload: JWT payload dictionary.
        secret: Secret key for signing.
        
    Returns:
        str: Signed JWT token.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = dict(payload)
    payload.setdefault("iat", int(time.time()))

    header_part = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")

    signature = hmac.new(
        secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


def fetch_zerogamma_level(*, sym: str, timeout_s: int = 30) -> ZeroGammaLevel:
    """
    Fetch zero gamma level from SpotGamma API.
    
    Parameters:
        sym: Stock symbol (default: SPX).
        timeout_s: Request timeout in seconds.
        
    Returns:
        ZeroGammaLevel: Zero gamma level data.
        
    Raises:
        requests.exceptions.RequestException: If API request fails.
        ValueError: If API response is invalid.
    """
    token = _jwt_hs256({}, JWT_SECRET)

    url = LEVELS_URL.format(sym=sym)
    
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "x-json-web-token": token,
            },
            timeout=timeout_s,
        )
        resp.raise_for_status()

        data = resp.json()
        if not isinstance(data, list) or not data:
            raise ValueError("Unexpected response shape (expected non-empty list)")

        row = data[0]
        if "zero_g_strike" not in row:
            raise ValueError("Response missing 'zero_g_strike'")

        level = ZeroGammaLevel(
            sym=row.get("sym", sym),
            trade_date=row.get("trade_date", ""),
            zero_g_strike=float(row["zero_g_strike"]),
            source_url=url,
        )
        
        logger.info(
            f"Successfully fetched zero gamma level for {sym}: "
            f"${level.zero_g_strike:.2f}"
        )
        return level
        
    except requests.exceptions.Timeout:
        logger.error(f"SpotGamma API request timed out after {timeout_s} seconds")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"SpotGamma API returned HTTP error: {e.response.status_code}"
        )
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"SpotGamma API request failed: {e}")
        raise
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse SpotGamma API response: {e}")
        raise


def run_analysis_pipeline(
    fmp_key: str,
    openrouter_key: str,
    telegram_token: str,
    telegram_chat_id: str,
    symbol: str = DEFAULT_SYM,
) -> bool:
    """
    Execute complete analysis pipeline.
    
    Fetches zero gamma level → SPX OHLC data → OpenRouter analysis →
    Telegram notification.
    
    Parameters:
        fmp_key: FMP API key.
        openrouter_key: OpenRouter API key.
        telegram_token: Telegram bot token.
        telegram_chat_id: Telegram group chat ID.
        symbol: Stock symbol to analyze.
        
    Returns:
        bool: True if pipeline completed, False if any step failed.
    """
    try:
        # Step 1: Fetch zero gamma level
        logger.info(f"Step 1: Fetching zero gamma level for {symbol}...")
        zero_gamma_level = fetch_zerogamma_level(sym=symbol)
        
        # Step 2: Fetch SPX OHLC data (includes latest closing price)
        logger.info("Step 2: Fetching SPX OHLC data from FMP...")
        ohlc_csv, current_price = fetch_spx_ohlc_csv(api_key=fmp_key, days=30)
        
        # Step 3: Get OpenRouter analysis
        logger.info("Step 3: Analyzing data with OpenRouter...")
        analysis = analyze_with_openrouter(
            api_key=openrouter_key,
            zero_gamma_level=zero_gamma_level.zero_g_strike,
            ohlc_csv=ohlc_csv,
            symbol=symbol,
        )
        
        # Step 4: Send to Telegram
        logger.info("Step 4: Sending analysis to Telegram...")
        message = format_analysis_message(
            zero_gamma_level=zero_gamma_level.zero_g_strike,
            analysis=analysis,
            current_price=current_price,
            symbol=symbol,
        )
        
        success = send_to_telegram(
            bot_token=telegram_token,
            chat_id=telegram_chat_id,
            message=message,
        )
        
        if success:
            logger.info("Pipeline completed successfully")
            return True
        else:
            logger.warning(
                "Pipeline completed but Telegram notification failed "
                "(error logged, skipping as configured)"
            )
            return True  # Pipeline succeeded, Telegram failure is non-critical
        
    except Exception as e:
        logger.error(f"Pipeline failed at step: {e}", exc_info=True)
        return False


def main():
    """
    Main entry point. Parse arguments and execute analysis pipeline.
    """
    parser = argparse.ArgumentParser(
        description="ZeroGamma analysis pipeline with OpenRouter and Telegram integration"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=DEFAULT_SYM,
        help=f"Stock symbol to analyze (default: {DEFAULT_SYM})",
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("Starting zerogamma analysis pipeline")
        logger.info("=" * 60)
        
        # Load configuration from environment
        config = get_config()
        
        # Run pipeline
        success = run_analysis_pipeline(
            fmp_key=config["FMP_API_KEY"],
            openrouter_key=config["OPENROUTER_API_KEY"],
            telegram_token=config["TELEGRAM_BOT_TOKEN"],
            telegram_chat_id=config["TELEGRAM_CHAT_ID"],
            symbol=args.symbol,
        )
        
        logger.info("=" * 60)
        if success:
            logger.info("Pipeline execution completed successfully")
            sys.exit(0)
        else:
            logger.error("Pipeline execution failed")
            sys.exit(1)
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
