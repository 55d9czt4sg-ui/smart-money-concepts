# TradingView SMC Integration — Phase 3 Implementation

This document shows exactly how to implement TradingView SMC (Smart Money Concepts) structure validation.

---

## Overview

Phase F validates entry quality by checking:
- **1D Structure:** Buyer control, demand/supply zones, order block positioning
- **1H Setup:** CHOCH (Change of Character), BOS (Break of Structure), liquidity sweeps
- **Entry Validation:** Price entry into supply vs demand zones

---

## TODO 1: `get_smc_1d_structure()` in `tradingview_smc_integration.py`

**Location:** `tradingview_smc_integration.py:33–57`

**What it does:** Fetches 1D demand/supply zones and buyer control strength.

**Current code (stub):**
```python
async def get_smc_1d_structure(ticker: str) -> Optional[dict]:
    try:
        print(f"[TODO] Fetch 1D SMC structure for {ticker}")
        return None
    except Exception as e:
        print(f"Error fetching 1D SMC for {ticker}: {e}")
        return None
```

**Replace with:**
```python
async def get_smc_1d_structure(ticker: str) -> Optional[dict]:
    try:
        # Call TradingView API via MCP
        # Two options: tvremix (preferred) or CLAUDE_DESKTOP
        
        # Option A: Using tvremix (if available)
        tv_1d = await mcp__tvremix__analyze_smc_tool(
            symbol=ticker,
            timeframe="1D"
        )
        
        # Option B: Using CLAUDE_DESKTOP MCP
        # tv_1d = await mcp__CLAUDE_DESKTOP__analyze_smc_tool(
        #     symbol=ticker,
        #     timeframe="1D"
        # )
        
        return {
            "buyer_control": tv_1d.buyer_control_strength,  # 0–1.0 float
            "demand_present": tv_1d.demand_zone_detected,  # bool
            "supply_overhead": tv_1d.supply_zone_detected,  # bool
            "recent_demand_zone": tv_1d.last_demand_level,  # float (price)
            "recent_supply_zone": tv_1d.last_supply_level,  # float (price)
            "ob_structure": tv_1d.order_block_structure  # dict or string
        }
    except Exception as e:
        print(f"Error fetching 1D SMC for {ticker}: {e}")
        return None
```

**Expected response fields:**
- `buyer_control_strength` (0–1.0): How strong is buyer control?
  - > 0.65 = "Strong" buyer control
  - < 0.40 = "Weak" buyer control
  - 0.40–0.65 = "Mixed"
- `demand_zone_detected` (bool): Is there a fresh demand zone?
- `supply_zone_detected` (bool): Is there supply overhead?
- `last_demand_level` (float): Most recent demand zone price
- `last_supply_level` (float): Most recent supply zone price

---

## TODO 2: `get_smc_1h_entry_quality()` in `tradingview_smc_integration.py`

**Location:** `tradingview_smc_integration.py:60–89`

**What it does:** Fetches 1H entry structure (CHOCH/BOS, liquidity sweeps).

**Current code (stub):**
```python
async def get_smc_1h_entry_quality(ticker: str) -> Optional[dict]:
    try:
        print(f"[TODO] Fetch 1H entry structure for {ticker}")
        return None
    except Exception as e:
        print(f"Error fetching 1H SMC for {ticker}: {e}")
        return None
```

**Replace with:**
```python
async def get_smc_1h_entry_quality(ticker: str) -> Optional[dict]:
    try:
        # Call TradingView API for 1H structure
        tv_1h = await mcp__tvremix__analyze_smc_tool(
            symbol=ticker,
            timeframe="1H"
        )
        
        # Optional: Get technicals for direction confirmation
        tech_1h = await mcp__tvremix__get_technicals(
            symbol=ticker,
            timeframe="1H"
        )
        
        return {
            "direction": tech_1h.summary.lower(),  # "bullish" | "bearish" | "neutral"
            "choch": tv_1h.change_of_character_confirmed,  # bool
            "bos": tv_1h.break_of_structure_confirmed,  # bool
            "liquidity_swept": tv_1h.recent_liquidity_sweep,  # bool
            "entry_quality": tv_1h.entry_zone_quality,  # 0–1.0 float
            "price_in_supply": tv_1h.price_in_supply_zone,  # bool
            "price_in_demand": tv_1h.price_in_demand_zone  # bool
        }
    except Exception as e:
        print(f"Error fetching 1H SMC for {ticker}: {e}")
        return None
```

**Expected response fields:**
- `direction` (str): "bullish" | "bearish" | "neutral"
- `choch` (bool): Change of Character = breaking previous structure
- `bos` (bool): Break of Structure = breaking liquidity levels
- `liquidity_swept` (bool): Recent sweep of institutional liquidity?
- `entry_quality` (0–1.0): Quality of entry zone (0.7+ is good)
- `price_in_supply` (bool): Currently trading in supply zone?
- `price_in_demand` (bool): Currently trading in demand zone?

---

## TODO 3: `validate_smc_structure()` synthesis logic

**Location:** `tradingview_smc_integration.py:92–150`

**Current synthesis (already working):**
```python
# If either fails, return degraded score
if not smc_1d or not smc_1h:
    return SMCValidation(...Mixed scores...)

# Synthesize into final scores
buyer_control = "Strong" if smc_1d.get("buyer_control", 0) > 0.65 else "Weak"
demand_present = smc_1d.get("demand_present", False)
supply_overhead = smc_1d.get("supply_overhead", False)

hour_setup = smc_1h.get("direction").capitalize()
if smc_1h.get("choch") or smc_1h.get("bos"):
    hour_setup = "Bullish"
```

**This is production-ready.** No changes needed—it already:
1. Handles API failures gracefully
2. Synthesizes 1D and 1H data
3. Produces SMCValidation output matching phase_f requirements

---

## Implementation in `top_quant_runner.py`

**Already integrated!** Phase F now:
1. Checks if TradingView module is available
2. Calls `validate_smc_structure_sync(ticker)` if yes
3. Falls back to synthetic data if no

No changes needed in `top_quant_runner.py`.

---

## Testing Workflow

### Step 1: Test with Mock Data (Current)
```bash
python3 top_quant_runner.py
```
Output shows synthetic SMC scores (all "Strong" for tier-1 names).

### Step 2: Implement TODOs 1 & 2
Replace the `[TODO]` print statements with actual MCP calls to TradingView.

### Step 3: Test with Real TradingView Data
```bash
python3 top_quant_runner.py
```
Output now shows real 1D demand/supply structure and 1H CHOCH/BOS confirmation.

### Step 4: Verify SMC Scores Match Reality
- Strong candidates should have: Strong buyer control + No supply overhead + Bullish 1H setup
- Weak candidates should show: Mixed or weak buyer control, supply overhead

---

## TradingView API Options

### Option A: tvremix MCP (Preferred)
- Faster, more direct access to TradingView data
- Available via plugin in Claude desktop
- Tools: `analyze_smc_tool`, `analyze_swing_tool`, `get_technicals`

**Verify availability:**
```bash
# Check if tvremix is available in your MCP config
grep -i tvremix ~/.claude/mcp.json  # or .claude.json
```

### Option B: CLAUDE_DESKTOP MCP
- Broader set of tools (fundamentals, earnings, etc.)
- Also has SMC analysis capability
- Might be slightly slower

---

## SMC Concept Reference

**CHOCH (Change of Character):**
- Price breaks a previous swing high/low
- Signals structural shift in bias
- Used to confirm momentum change

**BOS (Break of Structure):**
- Price breaks through a liquidity level
- Often accompanied by sweep of stop orders
- Signals institutional intervention

**Demand Zone:**
- Area where smart money previously bought
- Shows on chart as area where price bounced
- Entry pullbacks here are optimal

**Supply Zone:**
- Area where smart money previously sold
- Shows on chart as area where price sold off
- Overhead resistance on rallies

**Buyer Control:**
- Percentage of recent candles closing above mid-point
- > 65% = strong buyers present
- < 40% = sellers in control

---

## Field Name Variations

API response field names may vary slightly between:
- `tvremix` → `change_of_character_confirmed` vs. `choch_confirmed`
- `buyer_control_strength` vs. `buyer_control_percent`
- `price_in_supply_zone` vs. `supply_zone_active`

**Always validate actual field names** from your MCP tool responses. If field names don't match:
1. Print the full response: `print(json.dumps(tv_1d, indent=2))`
2. Update field access in the code
3. Commit the corrected names

---

## Implementation Checklist

When you have TradingView MCP access:

- [ ] Verify tvremix or CLAUDE_DESKTOP is available in your MCP config
- [ ] Test API call for one ticker manually (e.g., AAPL on 1D)
- [ ] Implement `get_smc_1d_structure()` with actual MCP call
- [ ] Implement `get_smc_1h_entry_quality()` with actual MCP call
- [ ] Run test: `python3 top_quant_runner.py`
- [ ] Verify SMC scores are reasonable (not all "Strong" or all "Weak")
- [ ] Check that Phase F outputs real demand/supply levels
- [ ] Commit: "Wire TradingView SMC validation (Phase 3)"

---

## Impact on Ranking

SMC validation feeds into Phase G (ranking):
- Strong buyer control + no supply overhead → Boosts classification to A+
- Weak buyer control + supply overhead → Downgrades to A or WATCH
- CHOCH + BOS in 1H → Confirms entry quality

Real SMC data will make candidate selections **much more precise**.

---

**Next Steps After Phase 3:**
1. Phase 3: QuantWheel live screening (Phase 1 — highest priority)
2. Phase 4: Pineify flow confirmation (optional)
3. Phase 5: Robinhood retail positioning (optional)

---

**Last Updated:** 2026-10-10  
**Status:** Ready for TradingView API implementation
