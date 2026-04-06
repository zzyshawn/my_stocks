# Session Handoff - 2026-03-28

## 1. Current Task Objective
Implement a stock simulation system that generates real-time K-lines (5m/30m/daily) for backtesting, with proper data preparation, validation, and Agent integration points.

Expected output:
- Working simulation system that generates 48 steps of 5-minute data per trading day
- Proper 30-minute and daily aggregation from 5-minute data
- Backtest concatenation with historical baseline data
- Validation and print functions for manual verification
- Agent integration interface for future trading logic

## 2. Current Progress
- **Module 1 Data Split**: ✓ Completed and verified
  - Split raw d/30/5 data into `_1/_2` files by test start date
  - Files: `src/simulation/splitter.py`, `tests/test_splitter_603906.py`

- **Module 2 Single-day Realtime K-line & Merge**: ✓ In progress
  - Basic generation of 5m/30m/d realtime data from 48 bars
  - Backtest concatenation with `_1` baseline
  - Step-by-step printing for manual verification
  - Agent callback interface added
  - Key fixes:
    - 30-minute date now uses interval end time (e.g., 10:00 instead of 09:35)
    - 30m/d data now includes stock code column
    - Printing uses `_2` source data as original baseline (not from 5m aggregation)

- **Module 3 Indicators/Chanlun**: ❌ Not started
- **Module 4 Agent & Daily Evaluation**: ⚠️ Interface only (placeholder)
- **Module 5 Multi-day Loop**: ❌ Not started

## 3. Key Context
- **Project root**: `\\192.168.0.100\work_place\zzy-code\my_stocks`
- **Data directory**: `H:/股票信息/股票数据库/daban/股票数据`
- **Test stock**: `603906`
- **Test date**: `2024-09-02`
- **Trading times**: 09:35-11:30 (24 bars) + 13:05-15:00 (24 bars) = 48 bars total
- **30-minute aggregation**: 6 bars = 1 interval, but generate every step (1-6 = 1 bar, 7-12 = 2 bars, etc.)
- **Key requirement**: Each step must:
  1. Generate realtime 5m/30m/d files
  2. Concatenate with `_1` to produce backtest files
  3. Save step files for manual verification
  4. Call Agent callback for future integration

## 4. Key Findings
- Original 30-minute data uses interval END time (e.g., 10:00, 10:30)
- Stock code column must be preserved in aggregated 30m/d data
- `realtime_generator.py` now includes `step_callback` for Agent integration
- Windows file locking issues: Use date-based step directories (`steps/2024-09-02/step_01/`)

## 5. Unfinished Items (Priority Order)
1. **Fix print verification** - User reported STEP 01 showing incorrect comparison
2. **Complete Module 2 validation** - Ensure step-by-step printing works correctly
3. **Implement Module 3** - Indicators/Chanlun integration
4. **Implement Module 4** - Agent logic and daily evaluation
5. **Implement Module 5** - Multi-day loop with validation gates

## 6. Recommended Handoff Path
- First check: `src/simulation/realtime_generator.py` - verify step_callback works
- Run: `python tests/test_single_day_realtime_print_603906.py` - check output
- Check: `src/decision/realtime_agent_interface.py` - placeholder implementation
- Key files:
  - `src/simulation/splitter.py` (Module 1)
  - `src/simulation/realtime_generator.py` (Module 2)
  - `tests/test_single_day_realtime_print_603906.py` (validation)
  - `readme/需求文档_实时模拟交易系统.md` (requirements)
  - `readme/开发计划_实时模拟交易系统.md` (plan)

## 7. Risks and Caveats
- The STEP 01 comparison may show differences because:
  - 30m/d "original" baseline should come from `_2` files, not from 5m aggregation
  - The `source_30` calculation in print function may be incorrect
- Windows encoding issues with Chinese characters in print output
- Step file cleanup can cause permission errors on Windows

## 8. First Step for the Next Agent
Run the validation script and check STEP 01 output to verify the original vs generated data comparison is correct:

```bash
python tests/test_single_day_realtime_print_603906.py
```

The script should:
1. Print file paths for each step
2. Show "原始" (original) from `_2` source data
3. Show "生成" (generated) from realtime aggregation
4. Verify they match for the current step's cumulative data

If STEP 01 shows differences in 30m/d data, check that `source_day_30` and `source_day_d` are loaded from the correct `_2` files.
