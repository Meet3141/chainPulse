"""
ChainPulse — Gemini AI Client
Generates natural language disruption briefs with fallback.
"""

import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are ChainPulse, an AI supply chain co-pilot. Generate a concise, "
    "actionable operations brief in exactly 3 sentences. "
    "First sentence: what happened and where. "
    "Second sentence: business impact in specific numbers. "
    "Third sentence: recommended action with expected saving. "
    "Be direct. Use rupees (₹). No markdown. No bullet points."
)


def _build_user_prompt(data: dict) -> str:
    return (
        f"Disruption: {data.get('event_type', 'Unknown')} at {data.get('node_name', 'Unknown')}. "
        f"Severity: {data.get('severity', 0) * 100:.0f}%. "
        f"Shipments at risk: {data.get('count', 0)}. "
        f"Total exposure: ₹{data.get('exposure_inr', 0):,.0f}. "
        f"Top reroute: via {data.get('reroute_option_a', 'alternative route')}, "
        f"saves {data.get('time_saving', 0):.0f}h, costs ₹{data.get('cost_delta', 0):,.0f} extra."
    )


def _fallback_brief(data: dict) -> str:
    return (
        f"{data.get('event_type', 'Disruption')} at {data.get('node_name', 'unknown node')} "
        f"has elevated disruption risk to {data.get('count', 0)} active shipments. "
        f"Estimated SLA exposure: ₹{data.get('exposure_inr', 0):,.0f}. "
        f"Recommended action: execute reroute via {data.get('reroute_option_a', 'alternative route')} "
        f"to avoid ₹{data.get('net_saving', 0):,.0f} in penalties."
    )


def _sync_generate(prompt: str) -> str:
    """Synchronous Gemini call (runs in thread pool)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(prompt)
    return response.text.strip()


async def generate_brief(data: dict) -> str:
    """
    Generate a disruption brief using Gemini API.
    Falls back to a template if the API call fails or exceeds 2 seconds.
    """
    prompt = _build_user_prompt(data)

    try:
        brief = await asyncio.wait_for(
            asyncio.to_thread(_sync_generate, prompt),
            timeout=2.0,
        )
        return brief
    except Exception:
        return _fallback_brief(data)


# Quick self-test
if __name__ == "__main__":
    test_data = {
        "event_type": "Cyclone Alert",
        "node_name": "Chennai Port",
        "severity": 0.8,
        "count": 12,
        "exposure_inr": 1840000,
        "reroute_option_a": "Colombo",
        "time_saving": 31,
        "cost_delta": 40000,
        "net_saving": 1420000,
    }

    result = asyncio.run(generate_brief(test_data))
    print("Generated brief:")
    print(result)
