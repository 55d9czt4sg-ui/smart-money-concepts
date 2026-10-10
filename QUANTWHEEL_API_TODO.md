# QuantWheel API Implementation TODOs

This document shows exactly where and how to implement the three QuantWheel API calls to wire Phase 1 live screening.

---

## TODO 1: `get_gex_heatmap_for_ticker()` in `quantwheel_integration.py`

**Location:** `quantwheel_integration.py:52–78`

**What it does:** Fetches GEX positioning data for a single ticker.

**Current code (stub):**
```python
async def get_gex_heatmap_for_ticker(ticker: str, expiration: str = "Weekly") -> Optional[PositioningSnapshot]:
    try:
        # TODO: Call QuantWheel API
        print(f"[TODO] Fetch GEX for {ticker} ({expiration})")
        return None
    except Exception as e:
        print(f"Error fetching GEX for {ticker}: {e}")
        return None
```

**Replace with:**
```python
async def get_gex_heatmap_for_ticker(ticker: str, expiration: str = "Weekly") -> Optional[PositioningSnapshot]:
    try:
        # Call QuantWheel APIs via MCP
        # NOTE: These are MCP tool references — adjust based on actual tool names
        
        # 1. Fetch GEX heatmap
        response = await mcp__QUANTWHEEL__get_gex_heatmap(
            symbol=ticker,
            expiration=expiration
        )
        
        # 2. Fetch current quote
        quote = await mcp__QUANTWHEEL__get_stock_quote(symbol=ticker)
        
        # 3. Build and return PositioningSnapshot
        return PositioningSnapshot(
            ticker=ticker,
            spot=quote.last_price,
            gamma=response.gamma,  # Net GEX value
            vanna=response.vanna,  # Vanna value
            vanna_bb=response.vanna_bull_bear_ratio,  # Bull/bear ratio
            put_wall=response.put_wall_level,
            call_wall=response.call_wall_level,
            max_bull=response.max_bull_level,  # Max pain / bull level
            gamma_flip=response.gamma_flip_level,  # Level where gamma regime reverses
            put_wall_move_today=response.put_wall_direction,  # "Up" | "Down" | "Flat"
            call_wall_move_today=response.call_wall_direction,
            expiration=expiration
        )
    except Exception as e:
        print(f"Error fetching GEX for {ticker}: {e}")
        return None
```

**Expected response fields from QuantWheel:**
- `gamma` — Net gamma exposure (float, millions)
- `vanna` — Vanna value (float)
- `vanna_bull_bear_ratio` — Bull/bear weighting (float)
- `put_wall_level`, `call_wall_level`, `max_bull_level`, `gamma_flip_level` — Price levels (float)
- `put_wall_direction`, `call_wall_direction` — Direction strings ("Up", "Down", "Flat")

---

## TODO 2: `screen_gex_tickers()` in `quantwheel_integration.py`

**Location:** `quantwheel_integration.py:97–160`

**What it does:** Screens SPX 500 + NDX 100 for candidates passing core four filters.

**Current code (stub):**
```python
async def screen_gex_tickers(
    markets: List[str] = ["SPX 500", "NDX 100"],
    expiration: str = "Weekly"
) -> List[str]:
    try:
        # TODO: Call QuantWheel screener API
        print(f"[TODO] Screen {', '.join(markets)} for core four filters")
        return []
    except Exception as e:
        print(f"Error screening QuantWheel: {e}")
        return []
```

**Replace with:**
```python
async def screen_gex_tickers(
    markets: List[str] = ["SPX 500", "NDX 100"],
    expiration: str = "Weekly"
) -> List[str]:
    try:
        # Call QuantWheel screener with core four filters
        response = await mcp__QUANTWHEEL__screen_gex_tickers(
            markets=markets,
            expiration=expiration,
            filters={
                "gamma_type": "positive",  # Positive gamma = dealer short gamma
                "vanna_type": "positive",  # Positive vanna = bull bias
                "put_wall_distance_min": 0,  # Put wall 0–3% from spot
                "put_wall_distance_max": 3,  # (percentage)
                "gamma_buildup_5d": "rising",  # Gamma building = mean reversion
                "put_wall_move": "up",  # Support rising
                "vanna_bull_bear_min": 2.0,  # Strong bull/bear ratio
                "rv_iv_min": 1.00,  # Realized vol >= implied vol
                "rv_iv_max": 1.50,  # Cap to avoid overheated
                "daily_move_min": -1,  # Daily move range -1% to +2%
                "daily_move_max": 2,
                "iv_status": "declining"  # IV contraction = positive setup
            }
        )
        
        # Extract and return list of passing tickers
        return response.tickers  # List[str] of passing symbols
    except Exception as e:
        print(f"Error screening QuantWheel: {e}")
        return []
```

**Expected response:**
- `response.tickers` — List of ticker symbols passing all filters
  - Example: ["AAPL", "MSFT", "QQQ", "SPY", ...]
  - Typically 20–50 results from SPX 500 + NDX 100

---

## TODO 3: Call in `phase_b_quantwheel_screen()` function flow

**Location:** `top_quant_runner.py:198–215`

**Current state:** Framework already integrated and working!

The flow is already in place in `top_quant_runner.py`:

```python
if QUANTWHEEL_AVAILABLE:
    print("  → Attempting QuantWheel API call...")
    candidates_raw = screen_spx_ndx_sync()  # <-- Calls our integration layer
    if candidates_raw:
        print(f"  ✓ QuantWheel API returned {len(candidates_raw)} candidates")
    else:
        print("  ⚠ QuantWheel API unavailable or returned no results")
        print("  → Using mock data for testing")
        candidates_raw = _get_mock_candidates()
else:
    print("  → QuantWheel integration not available")
    print("  → Using mock data for testing")
    candidates_raw = _get_mock_candidates()
```

**No changes needed here.** The framework already:
1. Tries `screen_spx_ndx_sync()` first
2. Falls back to mock data if unavailable
3. Continues all 9 phases regardless

Once TODO 1 and 2 are implemented with actual MCP calls, this will automatically start using live data.

---

## Implementation Checklist

When you have access to QuantWheel MCP tools:

- [ ] Update `get_gex_heatmap_for_ticker()` with actual `mcp__QUANTWHEEL__get_gex_heatmap` calls
- [ ] Update `screen_gex_tickers()` with actual `mcp__QUANTWHEEL__screen_gex_tickers` calls
- [ ] Test with 5–10 candidates first (verify field names match response structure)
- [ ] Run full framework: `python3 top_quant_runner.py`
- [ ] Verify all 9 phases execute with real data
- [ ] Commit and push to branch

---

## Testing Without API

The framework works perfectly with mock data right now. To test the 9-phase pipeline:

```bash
python3 top_quant_runner.py
```

Output shows:
- ✅ Phase A: Market context
- ✅ Phase B: 4 mock candidates selected
- ✅ Phases C–I: Full analysis pipeline with mock positioning data
- ✅ Final report with A+ PRIME tier rankings

---

## MCP Tool Naming

The stub code uses placeholder names like `mcp__QUANTWHEEL__get_gex_heatmap`.

**Verify actual tool names** from your QuantWheel MCP server:
- Available tools: `list_mcp_servers` or check `.claude/mcp.json`
- Tool naming convention: Usually `mcp__<SERVER>__<tool_name>` or similar
- Adjust the function calls to match your actual tool names

---

**Next Steps:**
1. Implement the two `quantwheel_integration.py` TODOs
2. Run the framework with real data
3. Monitor for any field name mismatches (adjust response field access as needed)
4. Commit successful live integration
5. Move to Phase 2 (FlashAlpha confirmation)

---

**Last Updated:** 2026-10-10  
**Status:** Ready for implementation when QuantWheel MCP tools available
