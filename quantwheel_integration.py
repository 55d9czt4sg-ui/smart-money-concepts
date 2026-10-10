#!/usr/bin/env python3
"""
QuantWheel API Integration Layer for Top Quant v1.0

This module provides helper functions to call QuantWheel APIs and fetch
positioning data for SPX 500 + NDX 100 candidates.

To use this in top_quant_runner.py:
1. Import: from quantwheel_integration import screen_spx_ndx_for_top_quant
2. In phase_b_quantwheel_screen(), call: candidates = await screen_spx_ndx_for_top_quant()
3. Fall back to mock data if QuantWheel is unavailable

NOTE: These functions are stubs showing the API call structure.
In production, replace the TODO sections with actual MCP tool calls.
"""

import asyncio
import json
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PositioningSnapshot:
    """QuantWheel positioning data for a single ticker."""
    ticker: str
    spot: float
    gamma: float  # Net GEX (positive = dealer short gamma)
    vanna: float  # Vanna value
    vanna_bb: float  # Vanna bull/bear ratio
    put_wall: float
    call_wall: float
    max_bull: float
    gamma_flip: float
    put_wall_move_today: str  # "Up" | "Down" | "Flat"
    call_wall_move_today: str
    expiration: str  # "Weekly" anchor


async def get_gex_heatmap_for_ticker(ticker: str, expiration: str = "Weekly") -> Optional[PositioningSnapshot]:
    """
    Fetch GEX positioning data from QuantWheel for a single ticker.
    """
    try:
        # Call QuantWheel APIs via MCP
        response = await mcp__QUANTWHEEL__get_gex_heatmap(
            symbol=ticker,
            expiration=expiration
        )

        quote = await mcp__QUANTWHEEL__get_stock_quote(symbol=ticker)

        return PositioningSnapshot(
            ticker=ticker,
            spot=quote.get("last_price", quote.get("price", 0)),
            gamma=response.get("gamma", 0),
            vanna=response.get("vanna", 0),
            vanna_bb=response.get("vanna_bull_bear_ratio", 1.0),
            put_wall=response.get("put_wall_level", 0),
            call_wall=response.get("call_wall_level", 0),
            max_bull=response.get("max_bull_level", 0),
            gamma_flip=response.get("gamma_flip_level", 0),
            put_wall_move_today=response.get("put_wall_direction", "Flat"),
            call_wall_move_today=response.get("call_wall_direction", "Flat"),
            expiration=expiration
        )
    except Exception as e:
        print(f"Error fetching GEX for {ticker}: {e}")
        return None


async def screen_gex_tickers(
    markets: List[str] = ["SPX 500", "NDX 100"],
    expiration: str = "Weekly"
) -> List[str]:
    """
    Screen SPX 500 + NDX 100 for candidates passing core four filters.

    Filters:
    - Gamma: Positive
    - Vanna: Positive
    - Put Wall distance: 0–3% from spot
    - Gamma buildup 5d: Rising
    - Put Wall move today: Up
    - Vanna B/B ratio: minimum 2.0x
    - RV/IV range: 1.00–1.50
    - Daily price move: -1% to +2%
    - IV trend: Declining
    """
    try:
        # Call QuantWheel screener with core four filters
        response = await mcp__QUANTWHEEL__screen_gex_tickers(
            markets=markets,
            filters={
                "gamma_type": "positive",
                "vanna_type": "positive",
                "put_wall_distance_min": 0,
                "put_wall_distance_max": 3,
                "gamma_buildup_5d": "rising",
                "put_wall_move": "up",
                "vanna_bull_bear_min": 2.0,
                "rv_iv_min": 1.00,
                "rv_iv_max": 1.50,
                "daily_move_min": -1,
                "daily_move_max": 2,
                "iv_status": "declining"
            },
            expiration=expiration
        )

        return response.get("tickers", []) if isinstance(response, dict) else response
    except Exception as e:
        print(f"Error screening QuantWheel: {e}")
        return []


async def screen_spx_ndx_for_top_quant(
    expiration: str = "Weekly"
) -> List[Tuple[str, float, dict]]:
    """
    Complete workflow: Screen SPX 500 + NDX 100, then fetch positioning data.

    Returns list of (ticker, spot, positioning_dict) tuples ready for phase_b.

    Steps:
    1. Call screen_gex_tickers() to get 20–50 candidate tickers
    2. For each ticker, call get_gex_heatmap_for_ticker() to fetch positioning
    3. Return formatted list matching phase_b_quantwheel_screen() output format
    """
    print("\n[QUANTWHEEL INTEGRATION] Screening SPX 500 + NDX 100...")

    # Step 1: Screen for core four candidates
    candidate_tickers = await screen_gex_tickers(expiration=expiration)

    if not candidate_tickers:
        print("  Warning: No candidates found via QuantWheel API")
        print("  Falling back to mock data for testing")
        return []

    print(f"  Found {len(candidate_tickers)} candidates passing core four filters")

    # Step 2: Fetch positioning data for each
    candidates_with_data = []
    for ticker in candidate_tickers:
        snap = await get_gex_heatmap_for_ticker(ticker, expiration)
        if snap:
            # Convert PositioningSnapshot to dict format matching phase_b
            positioning_dict = {
                "gamma": snap.gamma,
                "vanna": snap.vanna,
                "vanna_bb": snap.vanna_bb,
                "put_wall": snap.put_wall,
                "call_wall": snap.call_wall,
                "max_bull": snap.max_bull,
                "gamma_flip": snap.gamma_flip,
                "put_wall_move_today": snap.put_wall_move_today,
                "call_wall_move_today": snap.call_wall_move_today,
            }
            candidates_with_data.append((snap.ticker, snap.spot, positioning_dict))

    if not candidates_with_data:
        print("  Warning: Failed to fetch positioning data")
        return []

    print(f"  ✓ Fetched positioning for {len(candidates_with_data)} candidates")
    return candidates_with_data


# ============================================================================
# SYNCHRONOUS WRAPPER (for use in sync context)
# ============================================================================

def screen_spx_ndx_sync(expiration: str = "Weekly") -> List[Tuple[str, float, dict]]:
    """
    Synchronous wrapper for screen_spx_ndx_for_top_quant().

    Use this in top_quant_runner.py instead of the async version.
    """
    try:
        # Try async execution
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(screen_spx_ndx_for_top_quant(expiration))
    except RuntimeError:
        # No event loop running; create one
        return asyncio.run(screen_spx_ndx_for_top_quant(expiration))
    except Exception as e:
        print(f"Error during QuantWheel integration: {e}")
        return []


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("QuantWheel Integration Layer for Top Quant v1.0")
    print("=" * 60)
    print("\nTo integrate into top_quant_runner.py:")
    print("  1. from quantwheel_integration import screen_spx_ndx_sync")
    print("  2. In phase_b_quantwheel_screen():")
    print("     candidates_raw = screen_spx_ndx_sync()")
    print("     if not candidates_raw:")
    print("         # Fall back to mock data")
    print("         candidates_raw = [...mock data...]")
    print("\nCurrent Status: TODO - awaiting QuantWheel API implementation")
    print("\nSee API_INTEGRATION_GUIDE.md for full details.")
