from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.orchestrator import StepDataPackager
from src.simulation.multi_stock_aggregator import MultiStockJsonAggregator


def test_pack_analysis_step_json_structure(tmp_path):
    packager = StepDataPackager(output_dirs={"real": tmp_path / "real", "simulation": tmp_path / "backtest"})

    analysis_result = {
        "d": {
            "indicator_df": [
                {"日期": "2024-09-01", "收盘": 10.0, "成交量": 100, "最低": 9.8, "最高": 10.3, "MA10": 10.1234, "MA20": 10.2234, "MA60": 10.3234, "MA120": 10.4234, "RSI_L6": 55.55, "RSI_H6": 44.44, "MACD_DIF": 0.1, "MACD_DEA": 0.05, "MACD_BAR": 0.1, "VOL": 100, "换手率": 1.234, "量比": 0.98, "VOL_MA5": 95, "VOL_MA20": 88, "VWAP": 0.00345},
                {"日期": "2024-09-02", "收盘": 10.555, "成交量": 120, "最低": 10.1, "最高": 10.8, "MA10": 10.9876, "MA20": 11.1234, "MA60": 11.2234, "MA120": 11.3234, "RSI_L6": 65.55, "RSI_H6": 54.44, "MACD_DIF": 0.2, "MACD_DEA": 0.1, "MACD_BAR": 0.2, "VOL": 120, "换手率": 2.345, "量比": 1.23, "VOL_MA5": 100, "VOL_MA20": 90, "VWAP": 0.00344},
            ],
            "chanlun_summary": {
                "last_zs_range": {"zd": 9.8, "zg": 10.8},
                "fx_times": [f"2024-09-{i:02d}" for i in range(1, 11)],
                "fx_types": ["top", "bottom"] * 5,
                "bi_times": [f"2024-09-{i:02d}" for i in range(5, 11)],
                "bi_types": ["top", "bottom", "top", "bottom", "top", "bottom"],
                "bi_values": [10.8, 9.8, 10.7, 9.9, 10.6, 10.0],
            },
        },
        "30": {
            "indicator_df": [
                {"日期": "2024-09-02 09:35:00", "收盘": 10.1, "成交量": 30, "最低": 10.0, "最高": 10.2, "RSI6": 51},
                {"日期": "2024-09-02 10:05:00", "收盘": 10.2, "成交量": 32, "最低": 10.1, "最高": 10.4, "RSI6": 53},
            ],
            "chanlun_summary": {
                "last_zs_range": {"zd": 10.0, "zg": 10.4},
                "fx_times": ["fallback"],
                "fx_types": ["fallback"],
                "bi_times": ["fallback"],
                "bi_types": ["fallback"],
                "bi_values": [99],
            },
            "chanlun_excel_rows": [
                {"日期": "2024-09-02 09:30:00", "分型类型": "无", "顶底": "无", "中枢顶ZG": None, "中枢底ZD": None, "最高价": 10.0, "最低价": 9.9},
                {"日期": "2024-09-02 10:00:00", "分型类型": "顶分型", "顶底": "上顶", "中枢顶ZG": 10.41, "中枢底ZD": 10.02, "最高价": 10.41, "最低价": 10.0},
                {"日期": "2024-09-02 10:30:00", "分型类型": "底分型", "顶底": "下底", "中枢顶ZG": 10.41, "中枢底ZD": 10.02, "最高价": 10.33, "最低价": 10.02},
            ],
        },
        "5": {
            "indicator_df": [
                {"日期": "2024-09-02 09:35:00", "收盘": 10.11, "成交量": 5, "最低": 10.05, "最高": 10.13, "VWAP": 0.00345},
                {"日期": "2024-09-02 09:40:00", "收盘": 10.12, "成交量": 6, "最低": 10.08, "最高": 10.20, "VWAP": 0.00344},
            ],
            "chanlun_summary": {"last_zs_range": {"zd": 10.05, "zg": 10.2}},
        },
    }

    payload = packager.build_step_payload(
        stock_code="603906",
        user_id="u1",
        conversation_id="c1",
        analysis_result=analysis_result,
    )

    assert "now" not in payload
    assert payload["stock_code"] == "603906"
    assert payload["day"]["close"] == [10.0, 10.55]
    assert payload["day"]["value"] == [100, 120]
    assert payload["day"]["indicators"]["MA10"] == [10, 11]
    assert payload["day"]["indicators"]["MA20"] == [10, 11]
    assert payload["day"]["indicators"]["MA60"] == [10, 11]
    assert payload["day"]["indicators"]["MA120"] == [10, 11]
    assert payload["day"]["indicators"]["RSI_L6"] == [56, 66]
    assert payload["day"]["indicators"]["RSI_H6"] == [44, 54]
    assert payload["day"]["indicators"]["MACD_DIF"] == [0.1, 0.2]
    assert payload["day"]["indicators"]["MACD_DEA"] == [0.05, 0.1]
    assert payload["day"]["indicators"]["MACD_BAR"] == [0.1, 0.2]
    assert payload["day"]["indicators"]["VOL"] == [100, 120]
    assert payload["day"]["indicators"]["换手率"] == [1.23, 2.35]
    assert payload["day"]["indicators"]["量比"] == [0.98, 1.23]
    assert payload["day"]["indicators"]["VOL_MA5"] == [95, 100]
    assert payload["day"]["indicators"]["VOL_MA20"] == [88, 90]
    assert payload["day"]["indicators"]["VWAP"] == [0.00345, 0.00344]
    assert payload["min30"]["chanlun"]["zs_range"] == [10.02, 10.41]
    assert payload["min30"]["chanlun"]["fx_times"] == ["2024-09-02 10:00:00", "2024-09-02 10:30:00"]
    assert payload["min30"]["chanlun"]["fx_types"] == ["顶分型", "底分型"]
    assert payload["min30"]["chanlun"]["bi_times"] == ["2024-09-02 10:00:00", "2024-09-02 10:30:00"]
    assert payload["min30"]["chanlun"]["bi_types"] == ["上顶", "下底"]
    assert payload["min30"]["chanlun"]["bi_values"] == [10.41, 10.02]
    assert payload["min30"]["indicators"]["RSI6"] == [51, 53]
    assert payload["min5"]["indicators"]["VWAP"] == [0.00345, 0.00344]
    assert payload["min5"]["time"] == ["2024-09-02 09:35:00", "2024-09-02 09:40:00"]


def test_build_data_ready_request_uses_json_path(tmp_path):
    packager = StepDataPackager(output_dirs={"real": tmp_path / "real", "simulation": tmp_path / "backtest"})
    json_path = tmp_path / "backtest" / "603906_step_02.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text("{}", encoding="utf-8")

    request = packager.build_data_ready_request(
        data_path=json_path,
        user_id="test_user",
        conversation_id="test_conv",
    )

    assert request == {
        "type": "DATA_READY",
        "data_path": str(json_path),
        "user_id": "test_user",
        "conversation_id": "test_conv",
    }


def test_multi_stock_payload_adds_now_and_field_descriptions(tmp_path):
    aggregator = MultiStockJsonAggregator()
    stock_payloads = {
        "603906": {
            "stock_code": "603906",
            "day": {"time": ["2024-09-02"]},
            "min30": {"time": ["2024-09-02 10:05:00"]},
            "min5": {"time": ["2024-09-02 10:05:00"]},
        },
        "002659": {
            "stock_code": "002659",
            "day": {"time": ["2024-09-02"]},
            "min30": {"time": ["2024-09-02 10:00:00"]},
            "min5": {"time": ["2024-09-02 10:00:00"]},
        },
    }
    aggregator._base_output_dir = lambda mode: tmp_path
    path = aggregator.write_multi_stock_step("simulation", "2024-09-02", 1, stock_payloads)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["now"] == "2024-09-02 10:05:00"
    assert "field_descriptions" in payload
    assert payload["stocks"]["603906"]["stock_code"] == "603906"
