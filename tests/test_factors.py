import pandas as pd
import numpy as np
import pytest
from src.analysis import FactorEngine, Factor

class DummyFactor(Factor):
    name = "DUMMY"
    def compute(self, df):
        return pd.Series([1, 2, 3], index=df.index)

def test_factor_engine_register():
    engine = FactorEngine()
    engine.register(DummyFactor())
    assert "DUMMY" in engine._factors

def test_factor_engine_compute():
    # 模拟数据
    df = pd.DataFrame({
        '收盘': [10, 11, 12, 11, 10],
        '最高': [11, 12, 13, 12, 11],
        '最低': [9, 10, 11, 10, 9],
        '开盘': [9.5, 10.5, 11.5, 11.5, 10.5],
        '成交量': [100, 200, 150, 120, 110],
        '换手率': [0.01, 0.02, 0.015, 0.012, 0.011]
    })
    
    engine = FactorEngine()
    engine.load_builtin("alpha158")
    res = engine.compute_all(df)
    
    # 结果是一个 DataFrame
    assert isinstance(res, pd.DataFrame)
    # 包含了 MOM_20, ATR_14 等列
    assert "MOM_20" in res.columns
    assert "ATR_14" in res.columns
    assert len(res) == len(df)
