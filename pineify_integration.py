#!/usr/bin/env python3
"""
Pineify Integration for Top Quant v1.0 — Phase 4

Options flow confirmation layer:
- Scan for bullish/bearish options flow alerts
- Calculate flow score (bullish activity ratio)
- Confirm or contradict positioning setup

This validates that institutional flow is consistent with QuantWheel positioning.
"""

from typing import Optional


async def get_options_flow_confirmation(ticker: str, timeframe: str = "1d") -> Optional[dict]:
    """
    Fetch recent options flow data from Pineify for a single ticker.

    Calls mcp__PINEIFY__find-options-flow-alerts to get bullish/bearish flow alerts,
    then calculates a flow score indicating the ratio of bullish to total alerts.
    """
    try:
        # Fetch options flow alerts from Pineify
        flow_resp = await mcp__PINEIFY__find_options_flow_alerts(
            symbols=[ticker],
            limit=20
        )

        if not flow_resp or not hasattr(flow_resp, 'data') or not flow_resp.data:
            return None

        # Extract bullish and bearish alerts
        alerts = flow_resp.data if isinstance(flow_resp.data, list) else [flow_resp.data]

        bullish_alerts = [a for a in alerts if a.get("direction", "").lower() == "bullish"]
        bearish_alerts = [a for a in alerts if a.get("direction", "").lower() == "bearish"]

        total = len(bullish_alerts) + len(bearish_alerts)

        if total == 0:
            return {
                "bullish_count": 0,
                "bearish_count": 0,
                "flow_score": 0.5,  # Neutral if no data
                "recent_volume": 0,
                "flow_direction": "neutral"
            }

        flow_score = len(bullish_alerts) / total
        total_premium = sum(a.get("premium_usd", 0) for a in alerts)

        return {
            "bullish_count": len(bullish_alerts),
            "bearish_count": len(bearish_alerts),
            "flow_score": flow_score,
            "recent_volume": total_premium,
            "flow_direction": "bullish" if flow_score > 0.5 else "bearish" if flow_score < 0.5 else "neutral"
        }
    except Exception as e:
        print(f"Error fetching flow for {ticker}: {e}")
        return None


async def validate_flow_confirmation(ticker: str, positioning_direction: str = "bullish") -> str:
    """
    Assess if recent options flow confirms the positioning setup.

    Args:
        ticker: Stock symbol
        positioning_direction: Expected direction from QuantWheel ("bullish" or "bearish")

    Returns:
        "Confirmed" (flow agrees), "Neutral" (mixed), or "Contradicts" (flow opposes)
    """
    print(f"\n  [PHASE D4] Flow Confirmation for {ticker}...")

    flow_data = await get_options_flow_confirmation(ticker)

    if not flow_data:
        print(f"    ⚠ Flow data unavailable, using neutral confirmation")
        return "Neutral"

    flow_score = flow_data.get("flow_score", 0.5)

    # Determine confirmation based on flow score alignment
    if positioning_direction == "bullish":
        if flow_score > 0.65:
            print(f"    ✓ Flow Confirms (bullish: {flow_score:.1%})")
            return "Confirmed"
        elif flow_score > 0.40:
            print(f"    ~ Flow Neutral (mixed: {flow_score:.1%})")
            return "Neutral"
        else:
            print(f"    ✗ Flow Contradicts (bearish: {flow_score:.1%})")
            return "Contradicts"
    else:  # bearish positioning
        if flow_score < 0.35:
            print(f"    ✓ Flow Confirms (bearish: {flow_score:.1%})")
            return "Confirmed"
        elif flow_score < 0.60:
            print(f"    ~ Flow Neutral (mixed: {flow_score:.1%})")
            return "Neutral"
        else:
            print(f"    ✗ Flow Contradicts (bullish: {flow_score:.1%})")
            return "Contradicts"


# ============================================================================
# SYNC WRAPPER
# ============================================================================

def validate_flow_confirmation_sync(
    ticker: str,
    positioning_direction: str = "bullish"
) -> str:
    """Synchronous wrapper for validate_flow_confirmation()."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            validate_flow_confirmation(ticker, positioning_direction)
        )
    except RuntimeError:
        return asyncio.run(
            validate_flow_confirmation(ticker, positioning_direction)
        )
    except Exception as e:
        print(f"Error during flow confirmation: {e}")
        return "Neutral"


if __name__ == "__main__":
    print("Pineify Integration for Top Quant v1.0")
    print("=" * 60)
    print("\nPhase D4: Options Flow Confirmation")
    print("\nTo integrate into top_quant_runner.py:")
    print("  1. from pineify_integration import validate_flow_confirmation_sync")
    print("  2. In phase_d_monthly_confirmation() or phase_e_flashalpha_confirmation():")
    print("     flow_status = validate_flow_confirmation_sync(ticker, 'bullish')")
    print("\nSee API_INTEGRATION_GUIDE.md for implementation details.")
