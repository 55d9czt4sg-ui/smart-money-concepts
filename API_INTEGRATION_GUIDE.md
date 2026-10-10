# Top Quant v1.0 — API Integration Guide

## Overview

The Top Quant framework (`top_quant_runner.py`) is structured with all 9 phases defined and functional with mock data. This guide documents how to wire real API integrations.

## Available MCP Tools

### QuantWheel (Primary Data Source)

**Tools:**
- `mcp__QUANTWHEEL__screen_gex_tickers` — Screen SPX 500 + NDX 100 by GEX criteria
- `mcp__QUANTWHEEL__get_gex_heatmap` — Fetch gamma/vanna heatmap for ticker
- `mcp__QUANTWHEEL__get_stock_quote` — Get current spot price and basic data

**Phase B Integration (Weekly Screening):**

```python
# Call screen_gex_tickers with hard filters for positive gamma regime
response = mcp__QUANTWHEEL__screen_gex_tickers(
    markets=["SPX 500", "NDX 100"],
    filters={
        "gamma": "positive",
        "vanna": "positive",
        "put_wall_distance_min": 0,
        "put_wall_distance_max": 3,  # percentage from spot
        "gamma_buildup_5d": "rising",
        "put_wall_move": "up",
        "vanna_bull_bear_min": 2.0,
        "rv_iv_min": 1.00,
        "rv_iv_max": 1.50,
        "daily_move_min": -1,
        "daily_move_max": 2,
        "iv_status": "declining"
    }
)

# For each ticker, fetch positioning data
for ticker in response.tickers:
    gex_data = mcp__QUANTWHEEL__get_gex_heatmap(
        symbol=ticker,
        expiration="weekly"  # Standard Top Quant uses Weekly anchor
    )
    quote = mcp__QUANTWHEEL__get_stock_quote(symbol=ticker)
    
    # Build PositioningData from gex_data
    positioning = PositioningData(
        gamma=gex_data.gamma,
        vanna=gex_data.vanna_bull_bear,
        vanna_bb=gex_data.vanna_bull_bear_ratio,
        put_wall=gex_data.put_wall_level,
        call_wall=gex_data.call_wall_level,
        max_bull=gex_data.max_bull_level,
        gamma_flip=gex_data.gamma_flip_level,
        put_wall_move_today=gex_data.put_wall_direction,
        call_wall_move_today=gex_data.call_wall_direction
    )
```

### FlashAlpha (Gamma/Vanna Confirmation)

**Tools:**
- `mcp__FLASHALPHA__get_gex` — Fetch independent GEX snapshot
- `mcp__FLASHALPHA__get_vex` — Fetch vanna/vex data
- `mcp__FLASHALPHA__get_volatility` — IV data

**Phase E Integration (Independent Confirmation):**

```python
# For each candidate, confirm GEX regime via FlashAlpha
for ticker in candidates:
    fa_gex = mcp__FLASHALPHA__get_gex(
        symbol=ticker,
        expiration="weekly"
    )
    
    # Compare to QuantWheel data
    flashalpha_confirms = fa_gex.gamma_type == "positive"  # Same direction?
    
    # Return "Confirmed", "Neutral", or "Contradicts"
    if fa_gex.gamma > weekly_positioning.gamma * 0.8:
        return "Confirmed"
    elif fa_gex.gamma > weekly_positioning.gamma * 0.5:
        return "Neutral"
    else:
        return "Contradicts"
```

### TradingView (SMC Structure Validation)

**Tools (via CLAUDE_DESKTOP MCP):**
- `mcp__CLAUDE_DESKTOP__get_technicals` — 1D/4H technicals
- `mcp__CLAUDE_DESKTOP__analyze_smc_tool` — Smart Money Concepts analysis
- `mcp__CLAUDE_DESKTOP__analyze_swing_tool` — Swing structure analysis

**Phase F Integration (SMC Validation):**

```python
# Fetch 1D technicals and SMC structure
tv_1d = mcp__CLAUDE_DESKTOP__analyze_smc_tool(
    symbol=ticker,
    timeframe="1D"
)

tv_1h = mcp__CLAUDE_DESKTOP__analyze_smc_tool(
    symbol=ticker,
    timeframe="1H"
)

# Extract SMC signals
smc = SMCValidation(
    buyer_control_1d="Strong" if tv_1d.buyer_control > 0.7 else "Weak",
    daily_demand_present=tv_1d.demand_level_detected,
    daily_supply_overhead=tv_1d.supply_level_detected,
    hour_1_setup="Bullish" if tv_1h.direction == "up" else "Bearish",
    liquidity_sweep_confirmation=tv_1h.liquidity_swept,
    entry_directly_into_supply=tv_1h.price_in_supply
)
```

### Pineify (Flow Confirmation Layer — Optional)

**Tools:**
- `mcp__PINEIFY__find-options-flow-alerts` — Options flow data
- `mcp__PINEIFY__get-stock-research-snapshot` — Flow snapshot

**Phase E Extension (Flow Confirmation):**

```python
# Get options flow data for the candidate
flow_data = mcp__PINEIFY__find-options-flow-alerts(
    symbol=ticker,
    filter="bullish",
    timeframe="1d"
)

# Assess if flow confirms gamma/vanna positioning
flow_score = len(flow_data.bullish_flows) / (len(flow_data.bullish_flows) + len(flow_data.bearish_flows))

if flow_score > 0.65:
    return "Flow Confirms"
elif flow_score > 0.40:
    return "Flow Neutral"
else:
    return "Flow Contradicts"
```

### Robinhood (Retail Positioning — Optional)

**Tools:**
- `mcp__ROBINHOOD__get_option_chains` — Options chain data
- `mcp__ROBINHOOD__get_equity_positions` — Equity positioning

**Phase G Extension (Positioning Context):**

```python
# Check if retail is bullish or bearish on this ticker
rh_chain = mcp__ROBINHOOD__get_option_chains(symbol=ticker)

# Calculate put/call ratio
put_interest = sum(c.bid_size + c.ask_size for c in rh_chain.puts)
call_interest = sum(c.bid_size + c.ask_size for c in rh_chain.calls)

retail_bias = "bullish" if call_interest > put_interest else "bearish"
```

---

## Implementation Roadmap

### Phase 1: QuantWheel Integration (Required)
- [ ] Replace phase_b_quantwheel_screen() with live QuantWheel API calls
- [ ] Fetch SPX 500 + NDX 100 screening results with core four filters
- [ ] Build PositioningData objects from QuantWheel GEX heatmaps
- [ ] Test with 5–10 candidates and validate mock phase output

### Phase 2: FlashAlpha Integration (Required)
- [ ] Wire phase_e_flashalpha_confirmation() to query FlashAlpha GEX
- [ ] Compare FlashAlpha gamma direction vs QuantWheel
- [ ] Return "Confirmed", "Neutral", or "Contradicts" based on magnitude

### Phase 3: TradingView SMC Integration (Required)
- [ ] Wire phase_f_smc_validation() to fetch 1D + 1H technicals
- [ ] Validate buyer control, demand/supply zones, liquidity sweeps
- [ ] Score entry quality based on 1H CHOCH/BOS structure

### Phase 4: Historical Trajectory (Recommended)
- [ ] Add historical positioning query to phase_c_trajectory()
- [ ] Pull Weekly + Daily gamma/vanna for past 5 days
- [ ] Calculate acceleration and direction of gamma buildup

### Phase 5: Pineify Flow (Optional)
- [ ] Extend phase_e confirmation with flow data
- [ ] Add flow strength as additional data point to ranking

### Phase 6: Robinhood Context (Optional)
- [ ] Add retail put/call ratio as positioning context
- [ ] Include in final report commentary

---

## Testing Workflow

### Step 1: Run with Mock Data (✓ Complete)
```bash
python3 top_quant_runner.py
```
Output: 4 candidates with mock positioning, all phases functional.

### Step 2: Phase B Only (Live QuantWheel)
```bash
python3 -c "
from top_quant_runner import phase_b_quantwheel_screen
candidates = phase_b_quantwheel_screen()
print(f'Found {len(candidates)} candidates')
for ticker, spot, pos in candidates:
    print(f'{ticker} @ {spot}: Gamma {pos.gamma:.1e}, Vanna B/B {pos.vanna_bb:.1f}x')
"
```
Expected: 20–50 real SPX 500 + NDX 100 tickers passing core four filters.

### Step 3: Full 9-Phase Pipeline (All APIs)
```bash
python3 top_quant_runner.py
```
Expected: A+ PRIME tier candidates with real GEX, SMC, and confirmation data.

### Step 4: Generate Report
Final output: Ranked board with classifications, entry conditions, and targets.

---

## Error Handling & Fallbacks

All API calls must include error handling:

```python
try:
    result = mcp__QUANTWHEEL__get_gex_heatmap(symbol=ticker)
except TimeoutError:
    # QuantWheel API timeout
    print(f"Warning: QuantWheel timeout for {ticker}, skipping")
    return None
except ValueError as e:
    # Invalid symbol or parameters
    print(f"Error: Invalid parameters for {ticker}: {e}")
    return None
except Exception as e:
    # Unexpected error
    print(f"Error fetching data for {ticker}: {e}")
    return None
```

If an API is unavailable, the framework gracefully degrades:
- QuantWheel unavailable → Use cached/static screening list
- FlashAlpha unavailable → Rely on QuantWheel confirmation alone
- TradingView unavailable → Skip SMC validation, downgrade classification
- Pineify unavailable → Skip flow layer, use positioning alone
- Robinhood unavailable → Skip retail context, classification unchanged

---

## Data Validation

Always validate API responses:

1. **PositioningData Sanity Checks:**
   - `gamma > 0` (positive regime only)
   - `vanna_bb >= 1.0` (bull/bear ratio)
   - `put_wall < spot < call_wall` or `put_wall < spot < max_bull`
   - Wall levels should move in consistent directions (both up, both down, etc.)

2. **TrajectoryMetrics Consistency:**
   - IV should be declining (iv_1d < iv_5d)
   - Gamma buildup should be rising (gamma_buildup_5d > 0)
   - Price trend and volume should align (bullish trend + rising volume)

3. **SMCValidation Structure:**
   - If buyer_control_1d == "Strong", demand should be present
   - If daily_supply_overhead == True, entry_directly_into_supply should align
   - 1H setup should correspond to price trend

---

## Notes

- All timestamps are UTC
- Gamma/Vanna values are in millions (e.g., 12.5e6 = $12.5M gamma)
- Put/Call wall levels are dollar amounts
- Vanna B/B is a ratio (e.g., 2.8x = 2.8:1)
- Report output includes 0-100 ranking score and tier classification

---

**Last Updated:** 2026-10-10  
**Framework Version:** 1.0  
**Status:** Ready for Phase 1 (QuantWheel) integration
