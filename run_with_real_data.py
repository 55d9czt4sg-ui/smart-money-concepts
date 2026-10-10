#!/usr/bin/env python3
"""
Execute Top Quant v1.0 with REAL QuantWheel market data (no mock data).

This script:
1. Screens SPX 500 + NDX 100 for candidates matching core four filters
2. Fetches live GEX heatmap data for each candidate
3. Feeds real positioning data into top_quant_runner.py
4. Produces ranked board with actual market positioning
"""

import json
import asyncio
from typing import List, Tuple

# These will be provided by the Claude environment via MCP
# When called from Claude, these functions are available

async def fetch_real_candidates() -> List[Tuple[str, float, dict]]:
    """
    Screen SPX 500 + NDX 100 with core four filters.
    Returns: [(ticker, spot, positioning_dict), ...]
    """
    print("\n" + "="*80)
    print("SCREENING: SPX 500 + NDX 100 (Core Four Filters)")
    print("="*80)

    try:
        # Call QuantWheel screening with relaxed filters (no putWallMove requirement)
        screen_response = await mcp__QUANTWHEEL__screen_gex_tickers(
            anchor="WEEKLY",
            gamma="positive",
            vanna="positive",
            putWallDistPctMin=-3,
            putWallDistPctMax=3,
            gammaBuildup5dPctMin=0,  # Rising
            vannaBullBearRatioMin=2.0,
            rvivMin=1.00,
            rvivMax=1.50,
            dailyChangePctMin=-1,
            dailyChangePctMax=2,
            limit=25
        )

        if not screen_response or screen_response.get("total") == 0:
            print("  ⚠ Screening returned no candidates. Using top major indices as fallback.")
            return await fetch_major_indices()

        print(f"  ✓ Found {screen_response.get('total', 0)} candidates")

        # Extract tickers and fetch detailed positioning data
        candidates = []
        tickers = screen_response.get("data", [])

        print(f"\n  Fetching GEX heatmap for {len(tickers)} candidates...")
        for row in tickers[:10]:  # Limit to top 10 to avoid quota exhaustion
            ticker = row.get("ticker")
            if not ticker:
                continue

            print(f"    → {ticker}...", end=" ", flush=True)

            try:
                # Fetch quote
                quote_resp = await mcp__QUANTWHEEL__get_stock_quote(ticker=ticker)
                spot = quote_resp.get("price", 0)

                # Fetch GEX heatmap
                gex_resp = await mcp__QUANTWHEEL__get_gex_heatmap(ticker=ticker)

                # Extract weekly (anchor) positioning
                positioning_dict = {
                    "gamma": gex_resp.get("netGamma", 0),
                    "vanna": gex_resp.get("netVanna", 0),
                    "vanna_bb": gex_resp.get("vannaBullBearRatio", 1.0),
                    "put_wall": gex_resp.get("putWallLevel", 0),
                    "call_wall": gex_resp.get("callWallLevel", 0),
                    "max_bull": gex_resp.get("maxBullLevel", 0),
                    "gamma_flip": gex_resp.get("gammaFlipLevel", 0),
                    "put_wall_move_today": gex_resp.get("putWallDirection", "Flat"),
                    "call_wall_move_today": gex_resp.get("callWallDirection", "Flat"),
                }

                candidates.append((ticker, spot, positioning_dict))
                print(f"✓ (γ: {positioning_dict['gamma']:,.0f}, spot: ${spot:.2f})")

            except Exception as e:
                print(f"✗ Error: {e}")
                continue

        if not candidates:
            print("\n  ⚠ Failed to fetch positioning data. Using major indices as fallback.")
            return await fetch_major_indices()

        return candidates

    except Exception as e:
        print(f"  ✗ Screening failed: {e}")
        print("  → Falling back to major indices")
        return await fetch_major_indices()


async def fetch_major_indices() -> List[Tuple[str, float, dict]]:
    """
    Fallback: fetch positioning for major indices (QQQ, SPY, IWM).
    """
    print("\n  Fetching major indices positioning (fallback)...")
    tickers = ["QQQ", "SPY", "IWM"]
    candidates = []

    for ticker in tickers:
        try:
            quote_resp = await mcp__QUANTWHEEL__get_stock_quote(ticker=ticker)
            spot = quote_resp.get("price", 0)

            gex_resp = await mcp__QUANTWHEEL__get_gex_heatmap(ticker=ticker)

            positioning_dict = {
                "gamma": gex_resp.get("netGamma", 0),
                "vanna": gex_resp.get("netVanna", 0),
                "vanna_bb": gex_resp.get("vannaBullBearRatio", 1.0),
                "put_wall": gex_resp.get("putWallLevel", 0),
                "call_wall": gex_resp.get("callWallLevel", 0),
                "max_bull": gex_resp.get("maxBullLevel", 0),
                "gamma_flip": gex_resp.get("gammaFlipLevel", 0),
                "put_wall_move_today": gex_resp.get("putWallDirection", "Flat"),
                "call_wall_move_today": gex_resp.get("callWallDirection", "Flat"),
            }

            candidates.append((ticker, spot, positioning_dict))
            print(f"    ✓ {ticker} @ ${spot:.2f} (γ: {positioning_dict['gamma']:,.0f})")

        except Exception as e:
            print(f"    ✗ {ticker}: {e}")
            continue

    return candidates


async def main():
    """Main execution: fetch real data → run framework."""

    # Fetch real candidates
    real_candidates = await fetch_real_candidates()

    if not real_candidates:
        print("\n✗ Failed to fetch any real data. Cannot proceed.")
        return

    print(f"\n✓ Fetched {len(real_candidates)} real candidates with live positioning data")
    print("\nPassing real data into Top Quant framework...")

    # Import the framework
    import sys
    sys.path.insert(0, '/home/user/smart-money-concepts')
    import top_quant_runner

    # Monkey-patch the mock data to use real data
    def phase_b_with_real_data():
        """Replace Phase B with real data."""
        print("  → Using REAL QuantWheel data (no mock data)")
        results = []
        for ticker, spot, data in real_candidates:
            pos = top_quant_runner.PositioningData(**data)
            results.append((ticker, spot, pos))
        return results

    # Patch the function
    top_quant_runner.phase_b_quantwheel_screen = phase_b_with_real_data

    # Run the framework
    print("\n")
    top_quant_runner.run_top_quant()


if __name__ == "__main__":
    asyncio.run(main())
