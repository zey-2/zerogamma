"""
OpenRouter API integration for market analysis using xiaomi/mimo-v2-flash model.

Sends zero gamma level and SPX OHLC data to OpenRouter for AI-powered analysis.
"""

import json
import logging

import requests

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

    Return ONLY a JSON object with these fields:
    {{
        "zero_gamma_significance": "string",
        "trend": "string",
        "implications": ["string", "string", "string"]
    }}

    Constraints:
    - Max 120 words total across all fields
    - Use short, direct sentences
    - No headers, no extra keys, no Markdown
    - The implications array should contain 2-4 short bullets"""
        
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
            "max_tokens": 250,
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
        
        formatted = _format_structured_analysis(analysis)
        logger.info("Successfully received analysis from OpenRouter")
        return formatted
        
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


def _format_structured_analysis(analysis: str) -> str:
    """
    Format JSON analysis into a concise, labeled text block.

    Parameters:
        analysis (str): Raw JSON string from OpenRouter.

    Returns:
        str: Concise text with Markdown bold labels and bullets.

    Raises:
        ValueError: If JSON is invalid or missing required fields.
    """
    try:
        payload = json.loads(analysis)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenRouter returned invalid JSON") from exc

    zero_gamma = payload.get("zero_gamma_significance")
    trend = payload.get("trend")
    implications = payload.get("implications")

    if not isinstance(zero_gamma, str) or not zero_gamma.strip():
        raise ValueError("Missing or invalid zero_gamma_significance")
    if not isinstance(trend, str) or not trend.strip():
        raise ValueError("Missing or invalid trend")
    if not isinstance(implications, list) or not implications:
        raise ValueError("Missing or invalid implications list")

    bullet_lines = []
    for item in implications:
        if not isinstance(item, str) or not item.strip():
            continue
        bullet_lines.append(f"- {item.strip()}")

    if not bullet_lines:
        raise ValueError("Implications list contained no valid items")

    formatted = (
        f"**Zero Gamma**: {zero_gamma.strip()}\n"
        f"**Trend**: {trend.strip()}\n"
        f"**Implications**:\n"
        f"{chr(10).join(bullet_lines)}"
    )
    return formatted
