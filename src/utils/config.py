"""
My Stocks 配置管理模块

提供全局配置的加载、管理和访问功能。
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import yaml


class ConfigManager:
    """配置管理器"""

    _instance: Optional["ConfigManager"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: Optional[str] = None) -> "ConfigManager":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        if self._config:
            return

        self._project_root = self._find_project_root()
        self._config_path = self._resolve_config_path(config_path)
        self._load_config()

    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "config").exists() or (current / "docs").exists():
                return current
            current = current.parent
        return Path(__file__).parent.parent.parent

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """解析配置文件路径"""
        if config_path:
            path = Path(config_path)
            if path.is_absolute():
                return path
            return self._project_root / config_path
        return self._project_root / "config" / "config.yaml"

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self._config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()

    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return self._project_root

    @property
    def config_path(self) -> Path:
        """获取配置文件路径"""
        return self._config_path

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点分隔的嵌套键

        Args:
            key: 配置键，如 "data.base_dir" 或 "naming.folder.pattern"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值（仅在内存中，不持久化）

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    # ============================================================
    # 数据目录相关方法
    # ============================================================

    def get_watchlist_path(self) -> Path:
        """
        获取监控清单文件路径

        Returns:
            监控清单文件的完整路径
        """
        watchlist_dir = self.get("data_source.watchlist.dir", "H:/股票信息/监控清单")
        watchlist_file = self.get("data_source.watchlist.file", "check_list.xlsx")
        return Path(watchlist_dir) / watchlist_file

    def get_data_dir(self, subdir: Optional[str] = None) -> Path:
        """
        获取数据目录路径

        Args:
            subdir: 子目录名称，如 "cache", "history", "kline" 等

        Returns:
            数据目录的完整路径
        """
        base_dir = self.get("data.base_dir", "data")

        # 处理相对路径
        if not Path(base_dir).is_absolute():
            base_path = self._project_root / base_dir
        else:
            base_path = Path(base_dir)

        if subdir:
            subdir_name = self.get(f"data.directories.{subdir}", subdir)
            return base_path / subdir_name

        return base_path

    def ensure_data_dirs(self) -> None:
        """确保所有数据目录存在"""
        base_dir = self.get_data_dir()
        base_dir.mkdir(parents=True, exist_ok=True)

        subdirs = self.get("data.directories", {})
        for subdir_name in subdirs.values():
            (base_dir / subdir_name).mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 文件命名相关方法
    # ============================================================

    def format_folder_name(
        self,
        symbol: str,
        name: str = "",
        market: str = "",
        **kwargs: Any
    ) -> str:
        """
        根据配置生成股票文件夹名称

        Args:
            symbol: 股票代码
            name: 股票名称
            market: 市场代码 (sz, sh, bj)
            **kwargs: 其他参数

        Returns:
            格式化后的文件夹名称
        """
        pattern = self.get("naming.folder.pattern", "{symbol}_{name}")

        full_code = f"{market}{symbol}" if market else symbol

        return pattern.format(
            symbol=symbol,
            name=name,
            market=market,
            full_code=full_code,
            **kwargs
        )

    def format_file_name(
        self,
        file_type: str,
        symbol: str = "",
        name: str = "",
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        market: str = "",
        strategy: str = "",
        **kwargs: Any
    ) -> str:
        """
        根据配置生成文件名称

        Args:
            file_type: 文件类型 (kline, realtime, financial, report, backtest, knowledge, log)
            symbol: 股票代码
            name: 股票名称
            date: 日期
            start: 开始日期
            end: 结束日期
            market: 市场代码
            strategy: 策略名称
            **kwargs: 其他参数

        Returns:
            格式化后的文件名称（包含扩展名）
        """
        config_key = f"naming.files.{file_type}"
        file_config = self.get(config_key, {})

        pattern = file_config.get("pattern", "{symbol}_{date}")
        extension = file_config.get("extension", ".csv")
        date_format = file_config.get("date_format", "%Y%m%d")

        # 处理日期格式
        if date is None:
            date = datetime.now().strftime(date_format)
        elif isinstance(date, datetime):
            date = date.strftime(date_format)

        if start and isinstance(start, datetime):
            start = start.strftime(date_format)
        if end and isinstance(end, datetime):
            end = end.strftime(date_format)

        type_map = {
            "kline": "daily",
            "realtime": "realtime",
            "financial": "financial",
            "report": "report",
            "backtest": "backtest",
            "knowledge": "knowledge",
            "log": "log"
        }

        filename = pattern.format(
            symbol=symbol,
            name=name,
            date=date,
            start=start or "",
            end=end or "",
            type=type_map.get(file_type, file_type),
            market=market,
            strategy=strategy,
            **kwargs
        )

        return filename + extension

    def get_stock_folder_path(
        self,
        symbol: str,
        name: str = "",
        market: str = "",
        data_type: str = "history"
    ) -> Path:
        """
        获取股票数据文件夹路径

        Args:
            symbol: 股票代码
            name: 股票名称 (未使用，保持接口兼容)
            market: 市场代码 (未使用，保持接口兼容)
            data_type: 数据类型 (未使用，股票数据直接在 base_dir 下)

        Returns:
            股票数据文件夹的完整路径
        """
        # 股票数据直接存放在 base_dir/{股票代码}/ 下
        base_path = self.get_data_dir()
        folder_name = self.format_folder_name(symbol, name, market)
        return base_path / folder_name

    def get_kline_file_path(
        self,
        symbol: str,
        period: str = "daily"
    ) -> Path:
        """
        获取K线数据文件路径

        实际文件路径示例:
        - 日线: H:/股票信息/股票数据库/daban/股票数据/000001/000001_d.xlsx
        - 30分钟: H:/股票信息/股票数据库/daban/股票数据/000001/000001_30.xlsx
        - 5分钟: H:/股票信息/股票数据库/daban/股票数据/000001/000001_5.xlsx

        Args:
            symbol: 股票代码 (如: 000001)
            period: 周期类型
                - "daily" 或 "d": 日线
                - "min30" 或 "30": 30分钟线
                - "min5" 或 "5": 5分钟线
                - "weekly" 或 "w": 周线
                - "monthly" 或 "m": 月线

        Returns:
            K线数据文件的完整路径
        """
        # 获取周期标识
        period_map = self.get("naming.files.kline.period_map", {
            "daily": "d",
            "min30": "30",
            "min5": "5",
            "weekly": "w",
            "monthly": "m"
        })

        # 如果传入的是简写标识，直接使用
        if period in period_map.values():
            period_code = period
        else:
            period_code = period_map.get(period, period)

        # 构建文件名: {股票代码}_{周期}.xlsx
        pattern = self.get("naming.files.kline.pattern", "{symbol}_{period}")
        extension = self.get("naming.files.kline.extension", ".xlsx")

        filename = pattern.format(symbol=symbol, period=period_code) + extension

        # 股票文件夹路径
        folder_path = self.get_stock_folder_path(symbol)

        return folder_path / filename

    def get_realtime_dir(self, symbol: str) -> Path:
        """
        获取股票的实时数据目录

        实时数据存放在 {股票代码}/realtime/ 目录下

        Args:
            symbol: 股票代码

        Returns:
            实时数据目录的完整路径
        """
        stock_folder = self.get_stock_folder_path(symbol)
        realtime_subdir = self.get("data.stock_subdirs.realtime", "realtime")
        return stock_folder / realtime_subdir

    def list_available_periods(self, symbol: str) -> list:
        """
        列出股票可用的数据周期

        Args:
            symbol: 股票代码

        Returns:
            可用周期列表，如 ["daily", "min30", "min5"]
        """
        available = []
        period_map = self.get("naming.files.kline.period_map", {
            "daily": "d",
            "min30": "30",
            "min5": "5"
        })

        folder_path = self.get_stock_folder_path(symbol)

        for period_name, period_code in period_map.items():
            file_path = self.get_kline_file_path(symbol, period_code)
            if file_path.exists():
                available.append(period_name)

        return available

    def get_stock_file_path(
        self,
        symbol: str,
        file_type: str,
        name: str = "",
        market: str = "",
        **kwargs: Any
    ) -> Path:
        """
        获取股票数据文件路径

        Args:
            symbol: 股票代码
            file_type: 文件类型
            name: 股票名称
            market: 市场代码
            **kwargs: 其他参数传递给 format_file_name

        Returns:
            股票数据文件的完整路径
        """
        # 根据文件类型确定数据目录
        dir_mapping = {
            "kline": "kline",
            "realtime": "cache",
            "financial": "financial",
            "report": "history",
            "backtest": "backtest",
            "knowledge": "knowledge",
            "log": "logs"
        }

        data_type = dir_mapping.get(file_type, "history")
        folder_path = self.get_stock_folder_path(symbol, name, market, data_type)

        filename = self.format_file_name(
            file_type=file_type,
            symbol=symbol,
            name=name,
            market=market,
            **kwargs
        )

        return folder_path / filename

    # ============================================================
    # 配置验证方法
    # ============================================================

    def validate(self) -> bool:
        """
        验证配置是否有效

        Returns:
            配置是否有效
        """
        required_keys = [
            "app.name",
            "data.base_dir",
            "naming.folder.pattern",
            "naming.files.kline.pattern"
        ]

        for key in required_keys:
            if self.get(key) is None:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """返回配置的字典形式"""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"ConfigManager(config_path='{self._config_path}')"


# 全局配置实例
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigManager 实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance


def reload_config() -> None:
    """重新加载配置"""
    global _config_instance
    if _config_instance:
        _config_instance.reload()


# 便捷访问函数
def get(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config().get(key, default)


def set_value(key: str, value: Any) -> None:
    """设置配置值"""
    get_config().set(key, value)


def get_data_dir(subdir: Optional[str] = None) -> Path:
    """获取数据目录"""
    return get_config().get_data_dir(subdir)


def format_folder_name(symbol: str, name: str = "", market: str = "", **kwargs: Any) -> str:
    """格式化文件夹名称"""
    return get_config().format_folder_name(symbol, name, market, **kwargs)


def format_file_name(file_type: str, symbol: str = "", **kwargs: Any) -> str:
    """格式化文件名称"""
    return get_config().format_file_name(file_type, symbol, **kwargs)