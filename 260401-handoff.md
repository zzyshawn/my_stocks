# Session Handoff - 2026-04-01

## 1. Current Task Objective
Continue implementing the `my_stocks` simulation/realtime orchestration update. The target is a working multi-stock pipeline where simulation generates per-stock daily 48-step JSON history files, merges same-step payloads into one multi-stock JSON, sends `DATA_READY`, waits for agent reply, and then proceeds. Realtime mode still needs its true batch-fetch/analysis/merge loop. JSON structure must follow the user-defined schema and formatting rules.

## 2. Current Progress
- Added project entry at `main.py` with default-mode startup and simulation/realtime dispatch.
- Added/updated orchestration modules:
  - `src/simulation/orchestrator.py`
  - `src/simulation/multi_stock_runner.py`
  - `src/simulation/multi_stock_aggregator.py`
  - `src/simulation/realtime_generator.py` (previously existing, used by orchestrator)
  - `src/simulation/splitter.py`
  - `src/simulation/analysis_runner.py`
- Simulation flow changes completed so far:
  - single-stock stage generates history JSON only
  - IPC is only sent after multi-stock same-step merge
  - IPC client has retry + blocking wait in `ClientNotifier`
  - splitter no longer reuses existing `_1/_2`; it always overwrites
  - analysis input window reduced from 3000 to 1000 rows
  - added timing prints: `[SPLIT]`, `[ANALYSIS]`, `[STEP]`
- JSON structure changes completed so far:
  - single-stock JSON top-level `now` removed
  - merged multi-stock JSON top-level contains `now`, `field_descriptions`, `stocks`
  - formatting rules partially applied in `StepDataPackager._format_number`
  - chanlun fields now prefer `chanlun_excel_rows` over fallback summary
- Main indicators added into JSON flow via `analysis_runner._calculate_indicators()`:
  - `MA10/20/60/120`
  - `RSI_L6`, `RSI_H6`
  - `MACD_DIF`, `MACD_DEA`, `MACD_BAR`
  - `VOL`
  - `换手率`
  - `量比`
  - `VOL_MA5`, `VOL_MA20`
  - `VWAP`
- Chart analysis disabled by config:
  - `analysis.runner.enable_chanlun_analysis: false`
  - `analysis.runner.save_chanlun_html: false`
- Docs updated:
  - `readme/需求文档_实时模拟交易系统.md`
  - `readme/开发计划_实时模拟交易系统.md`
  - `readme/todo_list_缠论实时模拟.md`

## 3. Key Context
- User is very sensitive to incorrect interpretations. Re-read requirements before changing behavior.
- User explicitly required:
  - `main.py` is only a project entry; it should not require business CLI args.
  - Simulation is multi-stock, multi-thread, one trading day at a time, then same-step merge + send + wait.
  - Single-stock JSON should NOT have top-level `now`; merged multi-stock JSON SHOULD have `now`.
  - Chanlun data should come from generated `*_chanlun.xlsx` when possible.
  - Chart analysis itself should not run by default; not just HTML output disabled.
  - Split files `_1/_2` must always be overwritten because next day semantics change.
  - System speed matters more than reuse of stale outputs.
- Constraints:
  - User requested tests should still exist, but also dislikes unnecessary noisy test file generation.
  - Must keep responses short in CLI usage.
- Important config now in `config/config.yaml`:
  - `analysis.max_records: 1000`
  - `analysis.runner.enable_chanlun_analysis: false`
  - `analysis.runner.save_chanlun_html: false`
  - `simulation.multi_stock.debug_limit: 2`
  - `realtime.fetcher.debug_limit: 2`
  - `simulation.ipc.*` retry config

## 4. Key Findings
- The earlier “main.py seems frozen” issue was two separate problems:
  1. heavy import side effect from `src.data.qlib_dump` at module import time; fixed by lazy import inside `MultiStockSimulationRunner._load_target_codes()`
  2. actual long-running work after entering simulation, especially repeated per-step analysis
- Another major root cause found: IPC was incorrectly sent during each single-stock step. This was wrong per requirements and caused severe slowdown when service was down. Fixed so only merged multi-stock step sends IPC.
- The `splitter.py` cached `_1/_2` reuse logic was wrong for this workflow. It has been removed; split always overwrites now.
- Current JSON packager logic now supports `chanlun_excel_rows` by directly reading generated Excel rows attached in `analysis_runner._attach_result_summary()`.
- Current number formatting is global and may still not perfectly match every domain expectation. In particular, large indicators are rounded to integers. This matched current tests, but may need per-indicator formatting rules later if user objects.
- Realtime mode is still mostly a stub/orchestration shell. Simulation path is much further along.

## 5. Unfinished Items
1. **Highest priority:** Finish realtime true pipeline
   - batch fetch multiple stocks
   - prepare `_1` baseline by copy instead of split
   - generate per-stock JSON history
   - merge same-round multi-stock JSON
   - send `DATA_READY`
2. **High priority:** Verify real simulation pipeline behavior against actual data and agent service
   - especially step merge/send/wait ordering
   - ensure debug_limit/date range behavior matches user expectations
3. **High priority:** Review indicator formatting against user’s exact rules
   - user wanted nuanced significant-digit formatting; current implementation is approximate
4. **Medium priority:** Review whether `day/min30/min5` chanlun extraction fully matches user’s count requirements and exact field semantics on real exported Excel rows
5. **Medium priority:** Clean up docs one more time if behavior changes during realtime completion

## 6. Recommended Handoff Path
- Start with these files:
  - `main.py`
  - `src/simulation/multi_stock_runner.py`
  - `src/simulation/orchestrator.py`
  - `src/simulation/analysis_runner.py`
  - `src/simulation/multi_stock_aggregator.py`
  - `src/simulation/splitter.py`
  - `config/config.yaml`
- Verify first:
  1. simulation still sends IPC only at merged multi-stock step level
  2. single-stock JSON has no top-level `now`
  3. merged JSON has `now` and `field_descriptions`
  4. chart analysis remains disabled by config
- Useful commands:
  - `python -m pytest tests/test_orchestrator_message_schema.py tests/test_project_main.py`
  - `python -m py_compile main.py src/simulation/orchestrator.py src/simulation/multi_stock_aggregator.py src/simulation/multi_stock_runner.py src/simulation/analysis_runner.py src/simulation/splitter.py`
  - manual smoke run: `python -c "import main; main.main()"`
- If moving to realtime completion, inspect:
  - `src/data/realtime/my_real_time.py`
  - `config/config.yaml` realtime section
  - user requirement text in `readme/需求文档_实时模拟交易系统.md`

## 7. Risks and Caveats
- Do NOT reintroduce `_1/_2` reuse in splitter; user explicitly said it is wrong.
- Do NOT send IPC from single-stock stage again; only merged step should send.
- Do NOT assume current number formatting is final; user may challenge details.
- Be careful with `main.py` startup behavior. User previously reported “no prints” and “freeze”; avoid heavy imports at module import time.
- Realtime mode is incomplete; avoid claiming it works end-to-end without fresh verification.
- Repository has many modified/untracked files unrelated to this session. Do not assume everything in `git status` is from this task.

## First Step for the Next Agent
Open `src/simulation/multi_stock_runner.py` and `src/simulation/orchestrator.py`, then implement the missing realtime path so that it mirrors the now-correct simulation orchestration: per-stock outputs first, merged multi-stock JSON second, IPC send/wait last.
