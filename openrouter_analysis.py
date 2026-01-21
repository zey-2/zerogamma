"""
OpenRouter API integration for market analysis using xiaomi/mimo-v2-flash model.

Sends zero gamma level and SPX OHLC data to OpenRouter for AI-powered analysis.
"""

import requests
import logging

logger = logging.getLogger(__name__)


def analyze_with_openrouter(
    api_key: str,
    zero_gamma_level: float,
    ohlc_csv: str,
    symbol: str = "SPX",
) -> str:
    """
    Send zero gamma level and OHLC data to OpenRouter for market analysis.
    
    Parameters:
        api_key (str): OpenRouter API key.
        zero_gamma_level (float): Zero gamma strike price level from SpotGamma.
        ohlc_csv (str): CSV-formatted OHLC data (Date,Open,High,Low,Close).
        symbol (str): Stock symbol being analyzed (default: SPX).
    
    Returns:
        str: Analysis text from xiaomi/mimo-v2-flash model.
        
    Raises:
        requests.exceptions.RequestException: If OpenRouter API request fails.
        ValueError: If API response is invalid or missing analysis.
    """
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Construct analysis prompt with market context
        prompt = f"""Analyze the following market data for {symbol}:

Zero Gamma Level: ${zero_gamma_level:.2f}

Recent 30-Day OHLC Data:
{ohlc_csv}

Provide a concise market analysis covering:
1. Current zero gamma level significance
2. Trend analysis based on OHLC data
3. Key observations and trading implications

Keep analysis brief and actionable."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "xiaomi/mimo-v2-flash:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            raise ValueError(
                f"Unexpected OpenRouter API response structure. "
                f"Response keys: {list(data.keys())}"
            )
        
        analysis = data["choices"][0].get("message", {}).get("content", "")
        
        if not analysis:
            raise ValueError("OpenRouter returned empty analysis content")
        
        logger.info("Successfully received analysis from OpenRouter")
        return analysis
        
    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out after 60 seconds")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"OpenRouter API returned HTTP error: {e.response.status_code} - "
            f"{e.response.text}"
        )
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API request failed: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse OpenRouter API response: {e}")
        raise
