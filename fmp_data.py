"""
Financial Modeling Prep (FMP) data fetcher for historical OHLC data and current price.

Fetches 1-month of historical OHLC data for SPX and formats as CSV with latest closing price.
"""

import requests
from datetime import datetime, timedelta, timezone
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def fetch_spx_ohlc_csv(api_key: str, days: int = 30) -> Tuple[str, float]:
    """
    Fetch historical OHLC data for SPX from FMP API and return as CSV format with latest price.
    
    Parameters:
        api_key (str): Financial Modeling Prep API key.
        days (int): Number of days of historical data to fetch (default: 30).
    
    Returns:
        Tuple[str, float]: CSV-formatted OHLC data with headers and latest closing price.
        
    Raises:
        requests.exceptions.RequestException: If FMP API request fails.
        ValueError: If API response is invalid or missing required data.
    """
    symbol = "^GSPC"  # SPX ticker for FMP
    
    try:
        # FMP stable historical price endpoint (full version)
        url = "https://financialmodelingprep.com/stable/historical-price-eod/full"
        to_date = datetime.now(timezone.utc).date()
        from_date = to_date - timedelta(days=max(days * 2, 45))
        params = {
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "apikey": api_key,
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Stable endpoint returns data as a list directly
        if isinstance(data, list):
            historical = data
        elif isinstance(data, dict) and "historical" in data:
            # Fallback for older endpoint format
            historical = data["historical"]
        else:
            raise ValueError(
                f"Unexpected FMP API response structure. "
                f"Response type: {type(data)}"
            )
        
        if not historical:
            raise ValueError(
                f"No historical data returned from FMP for symbol {symbol}"
            )
        
        # Sort by date ascending (oldest first)
        historical = sorted(historical, key=lambda x: x["date"])
        
        # Limit to requested number of days (FMP may return more)
        if len(historical) > days:
            historical = historical[-days:]
        
        # Get latest closing price (last record)
        latest_close = float(historical[-1].get("close", 0))
        
        # Format as CSV
        csv_lines = ["Date,Open,High,Low,Close"]
        
        for record in historical:
            date = record.get("date", "")
            # Full endpoint returns OHLC fields
            open_price = record.get("open", 0)
            high_price = record.get("high", 0)
            low_price = record.get("low", 0)
            close_price = record.get("close", 0)
            
            csv_lines.append(
                f"{date},{open_price:.2f},{high_price:.2f},{low_price:.2f},{close_price:.2f}"
            )
        
        csv_data = "\n".join(csv_lines)
        logger.info(
            f"Successfully fetched {len(historical)} days of SPX OHLC data from FMP. "
            f"Latest close: ${latest_close:.2f}"
        )
        
        return csv_data, latest_close
        
    except requests.exceptions.Timeout:
        logger.error("FMP API request timed out after 30 seconds")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"FMP API returned HTTP error: {e.response.status_code} - {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"FMP API request failed: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse FMP API response: {e}")
        raise
