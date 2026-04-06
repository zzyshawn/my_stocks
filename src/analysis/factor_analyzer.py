import pandas as pd
import numpy as np
from typing import Dict, List
import scipy.stats as st

class FactorAnalyzer:
    """因子分析器，用于单票时间序列或横截面因子评估"""
    
    def __init__(self):
        pass
        
    def ic_analysis(self, factor_values: pd.Series, forward_returns: pd.Series, method="spearman") -> float:
        """
        计算单期 IC (Information Coefficient) 或 Rank IC
        目前主要用于单只股票的时间序列 IC (如果传入的是横截面数据则是截面 IC)
        """
        df = pd.DataFrame({'factor': factor_values, 'return': forward_returns}).dropna()
        if len(df) < 2:
            return np.nan
        return df['factor'].corr(df['return'], method=method)

    def summary_report(self, factor_df: pd.DataFrame, forward_returns: pd.Series) -> pd.DataFrame:
        """
        综合报告：计算每个因子的 Rank IC
        """
        results = []
        for col in factor_df.columns:
            ic = self.ic_analysis(factor_df[col], forward_returns, method="spearman")
            results.append({'Factor': col, 'Rank IC': ic})
        
        return pd.DataFrame(results).set_index('Factor')
