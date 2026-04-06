import pandas as pd
from .engine import BacktestResult

class BacktestReport:
    """回测报告生成器"""
    def __init__(self, result: BacktestResult):
        self.result = result

    def to_markdown(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 回测结果报告\n\n")
            f.write("## 绩效指标\n\n")
            for k, v in self.result.metrics.items():
                if 'return' in k or 'drawdown' in k:
                    f.write(f"- **{k}**: {v:.2%}\n")
                else:
                    f.write(f"- **{k}**: {v:.2f}\n")
            
            f.write(f"\n- **总交易笔数**: {len(self.result.trades)}\n")
            
            f.write("\n## 交易记录摘要\n\n")
            if self.result.trades:
                f.write("| 日期 | 标的 | 方向 | 价格 | 数量 | 盈亏估算 |\n")
                f.write("| --- | --- | --- | --- | --- | --- |\n")
                for t in self.result.trades[:15]:
                    f.write(f"| {t.date} | {t.symbol} | {t.direction} | {t.price:.2f} | {t.shares} | {t.pnl:.2f} |\n")
                if len(self.result.trades) > 15:
                    f.write(f"| ... | ... | ... | ... | ... | ... |\n")
            else:
                f.write("无交易记录\n")
