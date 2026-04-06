import sys
import yaml
from pathlib import Path
import pandas as pd

sys.path.insert(0, r"D:\code\qlib")

try:
    import qlib
    from qlib.constant import REG_CN
    from qlib.contrib.data.handler import Alpha158
except ImportError:
    qlib = None

class QlibFactorEngine:
    """基于原生 QLib 的因子引擎封装"""
    
    _initialized_uri = None
    
    @classmethod
    def get_config_path(cls) -> Path:
        """动态获取项目根目录下的 config.yaml"""
        # src/analysis/factors.py -> src/analysis -> src -> my_stocks
        root_dir = Path(__file__).resolve().parent.parent.parent
        return root_dir / "config" / "config.yaml"
    
    @classmethod
    def get_qlib_dir(cls) -> str:
        path = cls.get_config_path()
        default_dir = str(path.parent.parent / "src" / "data" / "qlib_data")
        if not path.exists():
            return default_dir
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get("data", {}).get("qlib_dir", default_dir)
        
    @classmethod
    def init_qlib(cls):
        if qlib is None:
            raise ImportError("qlib is not installed.")
            
        provider_uri = cls.get_qlib_dir()
        
        if cls._initialized_uri == provider_uri:
            return # Already initialized
            
        qlib.init(provider_uri=provider_uri, region=REG_CN)
        cls._initialized_uri = provider_uri
        print(f"QLib 全局初始化成功: {provider_uri}")

    @classmethod
    def compute_alpha158(cls, symbols: list, start_time: str = '2010-01-01', end_time: str = '2030-01-01') -> pd.DataFrame:
        """
        利用 QLib 原生 Alpha158 DataHandler 计算多只股票因子
        """
        cls.init_qlib()
        
        # 补齐 SH/SZ
        sz_sh_symbols = []
        for s in symbols:
            sz_sh_symbols.append(f"SH{s}" if str(s).startswith('6') else f"SZ{s}")
        
        handler = Alpha158(instruments=sz_sh_symbols, start_time=start_time, end_time=end_time)
        return handler.fetch()

    @classmethod
    def get_features(cls, symbols: list, fields: list, start_time: str = '2010-01-01', end_time: str = '2030-01-01') -> pd.DataFrame:
        """
        提取自定义特征
        """
        cls.init_qlib()
        sz_sh_symbols = []
        for s in symbols:
            sz_sh_symbols.append(f"SH{s}" if str(s).startswith('6') else f"SZ{s}")
            
        from qlib.data.dataset.handler import DataHandlerLP
        
        handler = DataHandlerLP(
            instruments=sz_sh_symbols,
            start_time=start_time,
            end_time=end_time,
            infer_processors=[],
            learn_processors=[],
            data_loader={
                "class": "QlibDataLoader",
                "kwargs": {
                    "config": fields
                }
            }
        )
        return handler.fetch()
