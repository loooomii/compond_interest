from ..utils.imports import *

@dataclass
class IndexReturn:
    """数据类，用于存储单个指数的分析结果"""
    symbol: str
    name: str
    annual_return: float
    total_return: float
    annual_volatility: float
    latest_price: float
    initial_price: float
    daily_returns: pd.Series
    price_series: pd.Series
    analysis_period: int
    data_start_date: datetime
    data_end_date: datetime

@dataclass
class MarketAnalysis:
    """数据类，用于存储整体市场分析结果"""
    analysis_date: datetime
    indices: Dict[str, IndexReturn]
    summary_stats: Dict[str, float]
