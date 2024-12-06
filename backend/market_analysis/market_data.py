from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, List, Tuple
import yfinance as yf
import pandas as pd
import numpy as np


@dataclass
class IndexReturn:
    """
    数据类，用于存储单个指数的分析结果
    """

    symbol: str  # 指数代码
    name: str  # 指数名称
    annual_return: float  # 年化收益率
    total_return: float  # 总收益率
    annual_volatility: float  # 年化波动率
    latest_price: float  # 最新收盘价
    initial_price: float  # 起始价格
    daily_returns: pd.Series  # 日收益率序列
    price_series: pd.Series  # 价格序列
    analysis_period: int  # 分析期间（年）
    data_start_date: datetime  # 数据起始日期
    data_end_date: datetime  # 数据结束日期


@dataclass
class MarketAnalysis:
    """数据类，用于存储整体市场分析结果"""
    analysis_date: datetime  # 分析日期
    indices: Dict[str, IndexReturn]  # 各指数的分析结果
    summary_stats: Dict[str, float]  # 汇总统计


class MarketIndexAnalyzer:
    """
    市场指数分析器类
    根据内置的self.indices_dict中的指数代码和名称，对市场指数进行分析。
    需要修改指数的时候，只需要修改self.indices_dict即可。
    """

    def __init__(self):
        # 定义主要市场指数
        self.indices_dict = {
            'S&P 500': '^GSPC',
            '道琼斯工业平均指数': '^DJI',
            '纳斯达克综合指数': '^IXIC',
            '上证综指': '000001.SS',
            '深证成指': '399001.SZ',
            '恒生指数': '^HSI',
            '日经225': '^N225'
        }

    @staticmethod
    def _calculate_single_index_return(
            self,
            symbol: str,
            name: str,
            years: int = 10
    ) -> Optional[IndexReturn]:
        """
        根据需要计算的指数代码和名称以及回溯年数
        计算单个指数的回报指标


        参数:
        symbol (str): 指数代码
        name (str): 指数名称
        years (int): 回溯年数

        返回:
        Optional[IndexReturn]: 返回IndexReturn对象或None（如果获取数据失败）
        """
        try:
            # 计算日期范围，使用 relativedelta 进行更精确的年份计算
            end_date = datetime.now()
            start_date = end_date - relativedelta(years=years)

            # 获取数据
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                print(f"警告: {name} ({symbol}) 没有获取到数据")
                return None

            # 计算各项指标
            daily_returns = df['Close'].pct_change()  # 计算上下相邻的两项的百分比变化
            total_return = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1  # 计算最后一天相比于第一天的总收益率

            # 计算年化收益率
            trading_days = len(df)  # 获取交易日数
            years_passed = trading_days / 252  # 假设每年有252个交易日
            annual_return = (1 + total_return) ** (1 / years_passed) - 1  # 对总收益率进行开年次的根号，然后减1，计算年化收益率

            # 计算年化波动率
            annual_volatility = daily_returns.std() * np.sqrt(252)  # 由daily_returns.std计算出总年数的日波动率，然后乘以根号252，计算年化波动率

            return IndexReturn(
                symbol=symbol,
                name=name,
                annual_return=annual_return,
                total_return=total_return,
                annual_volatility=annual_volatility,
                latest_price=df['Close'].iloc[-1],
                initial_price=df['Close'].iloc[0],
                daily_returns=daily_returns,
                price_series=df['Close'],
                analysis_period=years,
                data_start_date=df.index[0],
                data_end_date=df.index[-1]
            )

        except Exception as e:
            print(f"错误: 处理 {name} ({symbol}) 时发生异常: {str(e)}")
            return None

    def analyze_market(self, years: int = 10) -> MarketAnalysis:
        """
        分析所有配置的市场指数
        从class的indices_dict中获取指数代码和名称
        然后使用_calculate_single_index_return方法计算每个指数的回报指标
        再利用_calculate_summary_stats方法计算汇总统计
        最后返回结果

        参数:
        years (int): 回溯年数

        返回:
        MarketAnalysis: 市场分析结果对象
        """
        indices_results = {}

        # 分析每个指数
        for name, symbol in self.indices_dict.items():
            print(f"分析 {name} ({symbol})...")
            result = self._calculate_single_index_return(symbol, name, years)  # result的类型是IndexReturn
            if result:
                indices_results[name] = result  # 将每个个股的分析结果保存在以个股名称命名的字典中

        # 计算汇总统计
        summary_stats = self._calculate_summary_stats(indices_results)

        # 创建并返回市场分析结果
        return MarketAnalysis(
            analysis_date=datetime.now(),
            indices=indices_results,
            summary_stats=summary_stats
        )

    @staticmethod
    def _calculate_summary_stats(
            self,
            indices_results: Dict[str, IndexReturn]
    ) -> Dict[str, float]:
        """计算汇总统计指标"""
        """返回所有分析的指数的一个总结"""
        returns = [index.annual_return for index in indices_results.values()]  # indices_results.values(
        # )返回的是IndexReturn对象，获取每个IndexReturn对象的annual_return属性，组成一个列表
        volatilities = [index.annual_volatility for index in indices_results.values()]
        # 获取每个IndexReturn对象的annual_volatility属性，组成一个列表

        return {
            'average_annual_return': np.mean(returns),
            'max_annual_return': np.max(returns),
            'min_annual_return': np.min(returns),
            'average_volatility': np.mean(volatilities),
            'max_volatility': np.max(volatilities),
            'min_volatility': np.min(volatilities)
        }

    @staticmethod
    def generate_report(self, analysis: MarketAnalysis) -> pd.DataFrame:
        """生成分析报告DataFrame"""
        """包括所需要分析的指数名称"""
        """将单个指数的分析结果进行汇总，转化为pd.DataFrame"""
        """可以根据单个的指数名称获取对应的分析结果"""
        report_data = []

        for name, index_return in analysis.indices.items():
            report_data.append({
                '指数名称': name,
                '年化收益率': f'{index_return.annual_return:.2%}',
                '总收益率': f'{index_return.total_return:.2%}',
                '年化波动率': f'{index_return.annual_volatility:.2%}',
                '最新价格': f'{index_return.latest_price:.2f}',
                '起始价格': f'{index_return.initial_price:.2f}',
                '分析起始日期': index_return.data_start_date.strftime('%Y-%m-%d'),
                '分析结束日期': index_return.data_end_date.strftime('%Y-%m-%d')
            })

        return pd.DataFrame(report_data)

    def save_results(
            self,
            analysis: MarketAnalysis,
            filename: str = 'market_analysis_results.csv'
    ):
        """保存分析结果到CSV文件"""
        """保存分析好的报告结果"""
        report_df = self.generate_report(analysis)
        report_df.to_csv(filename, encoding='utf-8-sig', index=False)
        print(f"\n分析结果已保存到 {filename}")


def main():
    # 使用示例
    analyzer = MarketIndexAnalyzer()

    # 进行分析
    analysis_result = analyzer.analyze_market(years=10)

    # 生成报告
    report_df = analyzer.generate_report(analysis_result)
    print("\n=== 分析报告 ===")
    print(report_df)

    # 打印汇总统计
    print("\n=== 汇总统计 ===")
    for stat_name, value in analysis_result.summary_stats.items():
        if 'return' in stat_name:
            print(f"{stat_name}: {value:.2%}")
        else:
            print(f"{stat_name}: {value:.4f}")


if __name__ == "__main__":
    main()
