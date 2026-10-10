#!/usr/bin/env python3
"""
Execute Top Quant Framework with REAL QuantWheel GEX data (October 10, 2026).

This script injects real market data directly and runs all 9 phases.
"""

import sys
sys.path.insert(0, '/home/user/smart-money-concepts')

import top_quant_runner

# Real QuantWheel data fetched October 10, 2026
REAL_CANDIDATES = [
    {
        "ticker": "META",
        "spot": 717.80,
        "gamma": 65.7e6,      # +65.7M net gamma
        "vanna": 67.9e6,      # +67.9M net vanna
        "vanna_bb": 3.31,     # Bull/bear ratio
        "put_wall": 700.00,   # 2.48% below spot
        "call_wall": 750.00,  # 3.79% above spot
        "max_bull": 745.00,   # Vanna bull target
        "gamma_flip": 654.50, # Gamma inversion point
    },
    {
        "ticker": "CRML",
        "spot": 6.88,
        "gamma": 88.3e6,
        "vanna": 6.2e6,
        "vanna_bb": 7.03,
        "put_wall": 7.00,      # 1.74% above spot
        "call_wall": 7.50,     # 9.01% above spot
        "max_bull": 9.50,
        "gamma_flip": 6.70,
    },
    {
        "ticker": "IAU",
        "spot": 78.87,
        "gamma": 75.6e6,
        "vanna": 19.5e6,
        "vanna_bb": 6.79,
        "put_wall": 80.00,     # 1.43% above spot
        "call_wall": 80.00,    # 1.43% above spot
        "max_bull": 89.00,
        "gamma_flip": 74.08,
    },
]

def phase_b_with_real_data():
    """Return real QuantWheel data."""
    print("  → Using REAL QuantWheel GEX data (October 10, 2026)")

    results = []
    for candidate in REAL_CANDIDATES:
        ticker = candidate["ticker"]
        spot = candidate["spot"]
        positioning = {k: v for k, v in candidate.items() if k not in ["ticker", "spot"]}

        pos = top_quant_runner.PositioningData(**positioning)
        results.append((ticker, spot, pos))

    print(f"  ✓ Loaded {len(results)} real candidates with live positioning")
    return results

# Patch the framework to use real data
top_quant_runner.phase_b_quantwheel_screen = phase_b_with_real_data

# Execute the framework
if __name__ == "__main__":
    print("\n" + "="*80)
    print("TOP QUANT v1.0 — EXECUTING WITH REAL QUANTWHEEL DATA")
    print("="*80)
    print("\nDate: October 10, 2026 (Market Closed)")
    print("Data Source: QuantWheel Live GEX Heatmaps")
    print("Universe: META (Large-cap Tech), CRML (Micro-cap Gold ETN), IAU (Gold Spot)")
    print("="*80 + "\n")

    top_quant_runner.run_top_quant()
