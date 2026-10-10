#!/usr/bin/env python3
"""
Top Quant v1.0 — Dealer positioning swing-trading framework.

Phase A–I execution pipeline:
  A: Market context (event risk, GEX regime)
  B: Weekly QuantWheel screen (SPX 500 + NDX 100, core four filters)
  C: Trajectory analysis (IV, gamma buildup, vanna B/B, wall migration)
  D: Monthly confirmation (weekly + monthly alignment)
  E: FlashAlpha GEX confirmation
  F: SMC structure validation (1D buyer control + 1H entry quality)
  G: Ranking & classification (6-component weighted model)
  H: Entry timing (nearest expiry context)
  I: Trade plan validation

Output: Formatted report with candidate classifications and ranked board.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict

# ============================================================================
# API INTEGRATION MARKERS
# ============================================================================
# NOTE: This framework integrates with:
#   - QuantWheel API (via MCP) for GEX screening and positioning data
#   - FlashAlpha API (via MCP) for independent GEX confirmation
#   - TradingView API (via MCP) for SMC structure validation
#   - Pineify API (via MCP) for flow confirmation layer
#   - Robinhood API (via MCP) for retail positioning context
#
# All API calls should be wrapped in try/except and return graceful
# error messages if APIs are unavailable.

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PositioningData:
    """Weekly options positioning snapshot."""
    gamma: float  # Net GEX (positive = dealer short gamma)
    vanna: float  # Vanna value
    vanna_bb: float  # Vanna bull/bear ratio
    put_wall: float
    call_wall: float
    max_bull: float
    gamma_flip: float
    vanna_flip: Optional[float] = None
    put_wall_move_today: Optional[str] = None  # "Up" | "Down" | "Flat"
    call_wall_move_today: Optional[str] = None


@dataclass
class TrajectoryMetrics:
    """Direction and acceleration of positioning."""
    iv_1d: float
    iv_5d: float
    gamma_buildup_5d: float  # Rising = positive
    gamma_buildup_accel: str  # "Rising" | "Flat" | "Deteriorating"
    vanna_bb_trajectory: str  # "Rising" | "Flat" | "Deteriorating"
    put_wall_trajectory: str  # "Up" | "Flat" | "Down"
    call_wall_trajectory: str  # "Up" | "Flat" | "Down"
    max_bull_trajectory: str  # "Up" | "Flat" | "Down"
    price_trend_4h: str  # "Bullish" | "Neutral" | "Bearish"
    price_trend_1d: str  # "Bullish" | "Neutral" | "Bearish"
    volume_accumulation: str  # "Rising" | "Normal" | "Declining"


@dataclass
class PositioningCalculations:
    """Positioning references (not guaranteed targets)."""
    upside_to_call_wall: float
    upside_to_max_bull: float
    downside_to_put_wall: float
    positioning_rr: float  # Upside / Downside


@dataclass
class SMCValidation:
    """Smart Money Concepts structural confirmation."""
    buyer_control_1d: str  # "Strong" | "Mixed" | "Weak"
    daily_demand_present: bool
    daily_supply_overhead: bool
    hour_1_setup: str  # "Bullish" | "Mixed" | "Bearish"
    liquidity_sweep_confirmation: bool
    entry_directly_into_supply: bool


@dataclass
class RankingScore:
    """Weighted 0–100 ranking."""
    gamma_buildup: float  # 30%
    vanna_strength: float  # 25%
    put_wall_behavior: float  # 15%
    positioning_rr: float  # 15%
    iv_contraction: float  # 10%
    price_volume: float  # 5%
    total: float


@dataclass
class Candidate:
    """Complete candidate record."""
    ticker: str
    spot: float
    weekly_positioning: PositioningData
    monthly_positioning: Optional[PositioningData]
    trajectory: TrajectoryMetrics
    positioning_calcs: PositioningCalculations
    smc: SMCValidation
    ranking: RankingScore
    runway: str  # "OPEN" | "COMPRESSED" | "BLOCKED"
    classification: str  # "A+ PRIME" | "A" | "WATCH" | "BREAKOUT" | "PASS"
    monthly_alignment: bool
    flashalpha_confirmation: str  # "Confirmed" | "Neutral" | "Contradicts"
    entry_condition: str
    invalidation_level: float
    first_target: float
    secondary_target: float
    event_risk: Optional[str] = None


# ============================================================================
# PHASE A: MARKET CONTEXT
# ============================================================================

def phase_a_market_context() -> dict:
    """
    Check scheduled event risk, broad GEX regime, market compression state.

    Returns dict with:
      - event_risk: "Major" | "Minor" | "None"
      - broad_regime: "Positive GEX" | "Negative GEX" | "Neutral"
      - market_state: "Compressed" | "Trending" | "Acceleration"
    """
    # Stub: In production, pull from economic calendar + GEX dashboard
    return {
        "event_risk": "Minor",
        "timestamp": datetime.now().isoformat(),
        "broad_regime": "Positive GEX",
        "market_state": "Compressed",
        "note": "October 10, 2026. Post-FOMC stabilization. VIX contracted. No major catalysts next 3d.",
    }


# ============================================================================
# PHASE B: WEEKLY QUANTWHEEL SCREEN
# ============================================================================

def phase_b_quantwheel_screen() -> list:
    """
    Run SPX 500 + NDX 100 with hard filters:
      - Anchor: Weekly
      - Gamma: Positive
      - Vanna: Positive
      - Put Wall distance from spot: 0–3%
      - Gamma buildup 5d: Rising
      - Put Wall move today: Up
      - Vanna bull/bear ratio: minimum 2.0x
      - RV/IV minimum: 1.00, maximum: 1.50
      - Daily price move minimum: -1%, maximum: +2%
      - IV confirmation: IV declining

    Returns list of (ticker, spot, positioning_data) tuples.

    QUANTWHEEL API INTEGRATION:
    This function should call QuantWheel's screen_gex_tickers tool:

      response = await mcp__QUANTWHEEL__screen_gex_tickers(
          screener="top-puts",  # or appropriate screener
          markets=["SPX 500", "NDX 100"],
          filters={
              "gamma_type": "positive",
              "vanna_type": "positive",
              "put_wall_distance": "0-3%",
              "gamma_buildup_5d": "rising",
              "put_wall_move": "up",
              "vanna_bb_min": 2.0,
              "rv_iv_min": 1.00,
              "rv_iv_max": 1.50,
              "daily_move_min": -1,
              "daily_move_max": 2,
              "iv_trend": "declining"
          }
      )

    For each ticker in response, call get_gex_heatmap or get_gex to fetch:
      - gamma (net GEX for Weekly expiry)
      - vanna (bull/bear ratio for Weekly)
      - put/call wall levels
      - gamma_flip and vanna_flip levels
      - wall move direction (today vs yesterday)
    """
    # Stub: In production, call QuantWheel API with these exact filters
    candidates_raw = [
        ("AAPL", 227.50, {
            "gamma": 12.5e6,
            "vanna": 2.3,
            "vanna_bb": 2.8,
            "put_wall": 225.00,
            "call_wall": 230.00,
            "max_bull": 235.00,
            "gamma_flip": 232.50,
            "put_wall_move_today": "Up",
            "call_wall_move_today": "Up",
        }),
        ("MSFT", 418.30, {
            "gamma": 8.7e6,
            "vanna": 1.9,
            "vanna_bb": 2.4,
            "put_wall": 415.00,
            "call_wall": 420.00,
            "max_bull": 425.00,
            "gamma_flip": 422.00,
            "put_wall_move_today": "Up",
            "call_wall_move_today": "Flat",
        }),
        ("QQQ", 425.80, {
            "gamma": 15.2e6,
            "vanna": 2.6,
            "vanna_bb": 3.1,
            "put_wall": 423.00,
            "call_wall": 428.00,
            "max_bull": 432.00,
            "gamma_flip": 430.00,
            "put_wall_move_today": "Up",
            "call_wall_move_today": "Up",
        }),
        ("SPY", 582.10, {
            "gamma": 11.3e6,
            "vanna": 2.1,
            "vanna_bb": 2.6,
            "put_wall": 580.00,
            "call_wall": 585.00,
            "max_bull": 590.00,
            "gamma_flip": 587.50,
            "put_wall_move_today": "Up",
            "call_wall_move_today": "Up",
        }),
    ]

    # Convert to PositioningData objects
    results = []
    for ticker, spot, data in candidates_raw:
        pos = PositioningData(**data)
        results.append((ticker, spot, pos))

    return results


# ============================================================================
# PHASE C: TRAJECTORY ANALYSIS
# ============================================================================

def phase_c_trajectory(ticker: str, positioning: PositioningData) -> TrajectoryMetrics:
    """
    Analyze direction and acceleration of:
      - 1D vs 5D IV contraction
      - Gamma buildup magnitude and acceleration
      - Vanna B/B trajectory
      - Put/Call/Max Bull wall migration
      - 4H and 1D price trend
      - Volume accumulation
    """
    # Stub: In production, query historical positioning data + price data

    # Synthetic trajectory based on ticker
    if ticker in ("QQQ", "AAPL"):
        return TrajectoryMetrics(
            iv_1d=16.2,
            iv_5d=17.1,
            gamma_buildup_5d=2.3e6,  # Rising
            gamma_buildup_accel="Rising",
            vanna_bb_trajectory="Rising",
            put_wall_trajectory="Up",
            call_wall_trajectory="Up",
            max_bull_trajectory="Up",
            price_trend_4h="Bullish",
            price_trend_1d="Bullish",
            volume_accumulation="Rising",
        )
    else:
        return TrajectoryMetrics(
            iv_1d=16.8,
            iv_5d=17.4,
            gamma_buildup_5d=1.8e6,  # Rising but slower
            gamma_buildup_accel="Flat",
            vanna_bb_trajectory="Flat",
            put_wall_trajectory="Flat",
            call_wall_trajectory="Up",
            max_bull_trajectory="Up",
            price_trend_4h="Neutral",
            price_trend_1d="Bullish",
            volume_accumulation="Normal",
        )


# ============================================================================
# PHASE D: MONTHLY CONFIRMATION
# ============================================================================

def phase_d_monthly_confirmation(
    ticker: str, weekly_positioning: PositioningData
) -> tuple:
    """
    Rerun on Monthly anchor. Compare gamma/vanna direction, wall migration,
    positioning structure migration.

    Returns (monthly_positioning_data, alignment_flag).
    """
    # Stub: Query QuantWheel with Monthly anchor

    # Synthetic monthly data (assume aligned for strong candidates)
    if ticker in ("QQQ", "AAPL", "SPY"):
        monthly = PositioningData(
            gamma=weekly_positioning.gamma * 0.9,  # Slightly lower but same direction
            vanna=weekly_positioning.vanna * 0.95,
            vanna_bb=weekly_positioning.vanna_bb * 0.98,
            put_wall=weekly_positioning.put_wall * 0.99,
            call_wall=weekly_positioning.call_wall * 1.01,
            max_bull=weekly_positioning.max_bull * 1.02,
            gamma_flip=weekly_positioning.gamma_flip * 1.01,
        )
        aligned = True
    else:
        monthly = PositioningData(
            gamma=weekly_positioning.gamma * 0.75,  # Diverging
            vanna=weekly_positioning.vanna * 0.80,
            vanna_bb=weekly_positioning.vanna_bb * 0.85,
            put_wall=weekly_positioning.put_wall * 0.98,
            call_wall=weekly_positioning.call_wall * 0.99,
            max_bull=weekly_positioning.max_bull * 0.98,
            gamma_flip=weekly_positioning.gamma_flip * 0.99,
        )
        aligned = False

    return (monthly, aligned)


# ============================================================================
# PHASE E: FLASHALPHA CONFIRMATION
# ============================================================================

def phase_e_flashalpha_confirmation(ticker: str, weekly_positioning: PositioningData) -> str:
    """
    Query FlashAlpha GEX (Weekly expiry) to confirm dealer regime independently.

    Returns "Confirmed" | "Neutral" | "Contradicts".
    """
    # Stub: Query FlashAlpha API for Weekly GEX

    # Synthetic confirmation (assume mostly confirmed for strong candidates)
    if ticker in ("QQQ", "AAPL"):
        return "Confirmed"
    elif ticker == "MSFT":
        return "Neutral"
    else:
        return "Confirmed"


# ============================================================================
# PHASE F: SMC VALIDATION
# ============================================================================

def phase_f_smc_validation(ticker: str, positioning: PositioningData) -> SMCValidation:
    """
    Check 1D buyer control, daily demand/supply, 1H CHOCH/BOS, liquidity.

    Returns SMCValidation object.
    """
    # Stub: Query TradingView for SMC structure

    # Synthetic SMC (assume strong for tier-1 names)
    if ticker in ("QQQ", "AAPL", "SPY"):
        return SMCValidation(
            buyer_control_1d="Strong",
            daily_demand_present=True,
            daily_supply_overhead=False,
            hour_1_setup="Bullish",
            liquidity_sweep_confirmation=True,
            entry_directly_into_supply=False,
        )
    else:
        return SMCValidation(
            buyer_control_1d="Mixed",
            daily_demand_present=True,
            daily_supply_overhead=True,
            hour_1_setup="Mixed",
            liquidity_sweep_confirmation=False,
            entry_directly_into_supply=False,
        )


# ============================================================================
# PHASE G: RANKING & CLASSIFICATION
# ============================================================================

def phase_g_ranking(
    ticker: str,
    spot: float,
    weekly_positioning: PositioningData,
    trajectory: TrajectoryMetrics,
    smc: SMCValidation,
    positioning_calcs: PositioningCalculations,
) -> tuple:
    """
    Apply 6-component weighting:
      30% Gamma buildup
      25% Vanna bull/bear strength & trajectory
      15% Put Wall behavior/proximity
      15% Positioning R/R
      10% IV contraction
       5% Price/volume confirmation

    Returns (ranking_score, runway_classification, candidate_classification).
    """

    # Gamma buildup score (0–100)
    gamma_score = min(100, (weekly_positioning.gamma / 20e6) * 100)

    # Vanna strength + trajectory
    vanna_score = min(100, (weekly_positioning.vanna_bb / 4.0) * 100)
    if trajectory.vanna_bb_trajectory == "Rising":
        vanna_score = min(100, vanna_score * 1.2)
    elif trajectory.vanna_bb_trajectory == "Deteriorating":
        vanna_score = max(0, vanna_score * 0.7)

    # Put Wall behavior (closer to spot = more support; use actual spot price)
    put_wall_pct = abs(weekly_positioning.put_wall - spot) / spot
    put_wall_score = max(0, 100 - (put_wall_pct * 1000))
    if trajectory.put_wall_trajectory == "Up":
        put_wall_score = min(100, put_wall_score * 1.15)

    # Positioning R/R
    rr_score = min(100, (positioning_calcs.positioning_rr / 2.0) * 100)

    # IV contraction (1D < 5D = contracting = good)
    iv_score = 100 if trajectory.iv_1d < trajectory.iv_5d else 50

    # Price/volume confirmation
    price_vol_score = 0
    if trajectory.price_trend_1d == "Bullish" and trajectory.volume_accumulation == "Rising":
        price_vol_score = 100
    elif trajectory.price_trend_1d == "Bullish" and trajectory.volume_accumulation == "Normal":
        price_vol_score = 75
    elif trajectory.price_trend_1d == "Neutral":
        price_vol_score = 50
    else:
        price_vol_score = 25

    # Weighted total
    ranking = RankingScore(
        gamma_buildup=gamma_score,
        vanna_strength=vanna_score,
        put_wall_behavior=put_wall_score,
        positioning_rr=rr_score,
        iv_contraction=iv_score,
        price_volume=price_vol_score,
        total=(
            gamma_score * 0.30 +
            vanna_score * 0.25 +
            put_wall_score * 0.15 +
            rr_score * 0.15 +
            iv_score * 0.10 +
            price_vol_score * 0.05
        ),
    )

    # Runway classification (use actual spot price)
    call_wall_distance_pct = (weekly_positioning.call_wall - spot) / spot
    supply_overhead = smc.daily_supply_overhead

    if call_wall_distance_pct > 0.05 and not supply_overhead:
        runway = "OPEN"
    elif call_wall_distance_pct > 0.02 and not supply_overhead:
        runway = "COMPRESSED"
    else:
        runway = "BLOCKED"

    # Candidate classification
    core_four_present = (
        weekly_positioning.gamma > 0 and
        weekly_positioning.vanna > 0 and
        trajectory.iv_1d < trajectory.iv_5d and
        trajectory.gamma_buildup_5d > 0
    )

    if not core_four_present:
        classification = "PASS"
    elif ranking.total >= 75 and smc.buyer_control_1d == "Strong" and trajectory.price_trend_1d == "Bullish":
        classification = "A+ PRIME"
    elif ranking.total >= 70 and smc.buyer_control_1d in ("Strong", "Mixed"):
        classification = "A"
    elif ranking.total >= 60:
        classification = "WATCH"
    else:
        classification = "PASS"

    return (ranking, runway, classification)


# ============================================================================
# PHASE H: ENTRY TIMING
# ============================================================================

def phase_h_entry_timing(
    ticker: str,
    positioning: PositioningData,
    trajectory: TrajectoryMetrics,
    classification: str,
) -> tuple:
    """
    Determine entry condition based on positioning and structure.

    Returns (entry_condition, first_target, secondary_target).
    """

    if classification == "PASS":
        return ("No trade", positioning.put_wall, positioning.call_wall)

    # Preferred pullback entry (Mode 1: DRIFT/SUPPORT)
    if positioning.gamma > 0:
        entry_condition = f"Wait for pullback to ${positioning.put_wall:.2f} (rising put wall support)"
        first_target = positioning.call_wall
        second_target = positioning.max_bull
    else:
        # Breakout entry (Mode 2)
        entry_condition = f"Monitor Call Wall ${positioning.call_wall:.2f} for weakening; breakout on acceptance"
        first_target = positioning.gamma_flip
        second_target = positioning.max_bull

    return (entry_condition, first_target, second_target)


# ============================================================================
# PHASE I: TRADE PLAN VALIDATION
# ============================================================================

def phase_i_trade_plan(
    ticker: str,
    spot: float,
    positioning: PositioningData,
    trajectory: TrajectoryMetrics,
) -> tuple:
    """
    Define stop and invalidation conditions.

    Returns (invalidation_level, event_risk_note).
    """

    # Invalidation = Put Wall decisively lost and not reclaimed
    invalidation = positioning.put_wall * 0.98  # 2% below put wall

    # Event risk
    event_risk = None
    if datetime.now().weekday() >= 4:
        event_risk = "Weekend event risk; monitor pre-market Monday"

    return (invalidation, event_risk)


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def run_top_quant() -> list:
    """Execute all 9 phases and return ranked candidate list."""

    print("\n" + "="*80)
    print("TOP QUANT v1.0 — DEALER POSITIONING SWING-TRADING FRAMEWORK")
    print("="*80)

    # Phase A: Market context
    print("\n[PHASE A] Market Context...")
    market_context = phase_a_market_context()
    print(f"  Event Risk: {market_context['event_risk']}")
    print(f"  Broad Regime: {market_context['broad_regime']}")
    print(f"  Market State: {market_context['market_state']}")

    # Phase B: QuantWheel screen
    print("\n[PHASE B] Weekly QuantWheel Screen (SPX 500 + NDX 100)...")
    candidates_raw = phase_b_quantwheel_screen()
    print(f"  Found {len(candidates_raw)} candidates passing core four filters.")

    # Process each candidate through phases C–I
    candidates_final = []

    for ticker, spot, weekly_positioning in candidates_raw:
        print(f"\n  → {ticker} @ ${spot:.2f}")

        # Phase C: Trajectory
        trajectory = phase_c_trajectory(ticker, weekly_positioning)
        print(f"      [C] Trajectory: Gamma buildup {trajectory.gamma_buildup_accel}, Vanna {trajectory.vanna_bb_trajectory}")

        # Phase D: Monthly
        monthly_positioning, aligned = phase_d_monthly_confirmation(ticker, weekly_positioning)
        flag = "🔥 WEEKLY + MONTHLY ALIGNED" if aligned else "⚠ Monthly divergence"
        print(f"      [D] {flag}")

        # Phase E: FlashAlpha
        flashalpha = phase_e_flashalpha_confirmation(ticker, weekly_positioning)
        print(f"      [E] FlashAlpha: {flashalpha}")

        # Phase F: SMC
        smc = phase_f_smc_validation(ticker, weekly_positioning)
        print(f"      [F] SMC: 1D buyers {smc.buyer_control_1d}, 1H {smc.hour_1_setup}")

        # Calculate positioning
        positioning_calcs = PositioningCalculations(
            upside_to_call_wall=weekly_positioning.call_wall - spot,
            upside_to_max_bull=weekly_positioning.max_bull - spot,
            downside_to_put_wall=spot - weekly_positioning.put_wall,
            positioning_rr=(weekly_positioning.max_bull - spot) / (spot - weekly_positioning.put_wall + 0.01),
        )

        # Phase G: Ranking
        ranking, runway, classification = phase_g_ranking(
            ticker, spot, weekly_positioning, trajectory, smc, positioning_calcs
        )
        print(f"      [G] Score: {ranking.total:.1f}/100 | Runway: {runway} | Class: {classification}")

        # Phase H: Entry
        entry_condition, first_target, second_target = phase_h_entry_timing(
            ticker, weekly_positioning, trajectory, classification
        )
        print(f"      [H] Entry: {entry_condition}")

        # Phase I: Trade plan
        invalidation, event_risk = phase_i_trade_plan(ticker, spot, weekly_positioning, trajectory)

        # Build final candidate
        candidate = Candidate(
            ticker=ticker,
            spot=spot,
            weekly_positioning=weekly_positioning,
            monthly_positioning=monthly_positioning,
            trajectory=trajectory,
            positioning_calcs=positioning_calcs,
            smc=smc,
            ranking=ranking,
            runway=runway,
            classification=classification,
            monthly_alignment=aligned,
            flashalpha_confirmation=flashalpha,
            entry_condition=entry_condition,
            invalidation_level=invalidation,
            first_target=first_target,
            secondary_target=second_target,
            event_risk=event_risk,
        )
        candidates_final.append(candidate)

    # Sort by ranking score descending
    candidates_final.sort(key=lambda c: c.ranking.total, reverse=True)

    return candidates_final


# ============================================================================
# FORMATTED OUTPUT
# ============================================================================

def print_report(candidates: list, market_context: dict):
    """Print formatted Top Quant report with classifications and ranked board."""

    print("\n" + "="*80)
    print("TOP QUANT REPORT — BULLISH SWING-TRADING CANDIDATES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Universe: SPX 500 + NDX 100")
    print(f"Market Context: {market_context['broad_regime']} | {market_context['market_state']}")
    print(f"Event Risk: {market_context['event_risk']}")

    # Separate by classification
    a_prime = [c for c in candidates if c.classification == "A+ PRIME"]
    a_list = [c for c in candidates if c.classification == "A"]
    watch = [c for c in candidates if c.classification == "WATCH"]
    breakout = [c for c in candidates if c.classification == "BREAKOUT"]
    pass_list = [c for c in candidates if c.classification == "PASS"]

    # A+ PRIME
    print("\n" + "─"*80)
    print("🔥 A+ PRIME CANDIDATES")
    print("─"*80)
    for c in a_prime:
        print(f"\n{c.ticker} @ ${c.spot:.2f}")
        print(f"  Weekly: Gamma {c.weekly_positioning.gamma:.1e} | Vanna B/B {c.weekly_positioning.vanna_bb:.1f}x")
        print(f"  Walls: Put ${c.weekly_positioning.put_wall:.2f} ↔ Call ${c.weekly_positioning.call_wall:.2f} | Max Bull ${c.weekly_positioning.max_bull:.2f}")
        print(f"  Ranking: {c.ranking.total:.1f}/100 | Runway: {c.runway}")
        print(f"  {c.entry_condition}")
        print(f"  Targets: {c.first_target:.2f} / {c.secondary_target:.2f} | Stop: {c.invalidation_level:.2f}")

    # A
    print("\n" + "─"*80)
    print("🟢 A CANDIDATES")
    print("─"*80)
    for c in a_list:
        print(f"\n{c.ticker} @ ${c.spot:.2f}")
        print(f"  Ranking: {c.ranking.total:.1f}/100 | Runway: {c.runway}")
        print(f"  {c.entry_condition}")

    # WATCH
    if watch:
        print("\n" + "─"*80)
        print("🟡 WATCH CANDIDATES (Developing)")
        print("─"*80)
        for c in watch:
            print(f"  {c.ticker}: {c.ranking.total:.1f}/100 | Waiting on {c.classification}")

    # PASS
    if pass_list:
        print("\n" + "─"*80)
        print("❌ PASS (Core four missing or blocked)")
        print("─"*80)
        for c in pass_list:
            print(f"  {c.ticker}: {c.ranking.total:.1f}/100")

    # Ranked board
    print("\n" + "="*80)
    print("FINAL RANKED BOARD")
    print("="*80)
    print(f"{'Rank':<5} {'Ticker':<8} {'Score':<8} {'Class':<12} {'Runway':<12} {'Entry Target':<15}")
    print("─"*80)
    for i, c in enumerate(candidates, 1):
        print(f"{i:<5} {c.ticker:<8} {c.ranking.total:<8.1f} {c.classification:<12} {c.runway:<12} ${c.first_target:<14.2f}")

    print("\n" + "="*80)


if __name__ == "__main__":
    market_context = phase_a_market_context()
    candidates = run_top_quant()
    print_report(candidates, market_context)
