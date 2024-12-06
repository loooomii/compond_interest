from ..utils.imports import *
from ..models.data_classes import IndexReturn, MarketAnalysis
from ..config.settings import Settings


class MarketIndexAnalyzer:
    """市场指数分析器类"""

    def __init__(self, api_key: str = None, cache_dir: str = None, request_delay: float = None):
        self.api_key = api_key or Settings.API_KEY
        self.cache_dir = cache_dir or Settings.CACHE_DIR
        self.request_delay = request_delay or Settings.REQUEST_DELAY
        self.indices_dict = Settings.INDICES

        if not self.api_key:
            raise ValueError("未设置 ALPHA_VANTAGE_API_KEY")

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.last_request_time = 0.0

    def _get_cache_path(self, symbol: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f'{symbol}_data.json')

    def _is_cache_valid(self, cache_path: str, max_age_days: int = 1) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False

        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - mtime
        return age.days < max_age_days

    def _wait_for_rate_limit(self):
        """确保API调用不超过频率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            wait_time = self.request_delay - time_since_last_request
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _log_api_usage(self):
        """记录API使用情况"""
        usage_file = os.path.join(self.cache_dir, 'api_usage.json')
        today = datetime.now().strftime('%Y-%m-%d')

        try:
            if os.path.exists(usage_file):
                with open(usage_file, 'r') as f:
                    usage = json.load(f)
            else:
                usage = {}

            usage[today] = usage.get(today, 0) + 1

            with open(usage_file, 'w') as f:
                json.dump(usage, f)
        except Exception as e:
            print(f"无法记录API使用情况: {str(e)}")

    def _calculate_single_index_return(self, symbol: str, name: str, years: int = 10) -> Optional[IndexReturn]:
        """计算单个指数的回报指标"""
        cache_path = self._get_cache_path(symbol)

        # 尝试使用缓存数据
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame.from_dict(data)
                df.index = pd.to_datetime(df.index)
                print(f"使用缓存数据: {name}")
            except Exception as e:
                print(f"缓存数据读取失败: {str(e)}")
                df = None
        else:
            df = None

        # 如果没有有效缓存，则从API获取数据
        if df is None:
            try:
                self._wait_for_rate_limit()
                ts = TimeSeries(key=self.api_key, output_format='pandas')
                df, _ = ts.get_daily_adjusted(symbol=symbol, outputsize='full')

                # 保存到缓存
                df_dict = df.to_dict()
                with open(cache_path, 'w') as f:
                    json.dump(df_dict, f)

                self._log_api_usage()
                print(f"从API获取新数据: {name}")
            except Exception as e:
                print(f"API数据获取失败: {str(e)}")
                return None

        try:
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - relativedelta(years=years)

            # 筛选数据时间范围
            df = df.loc[start_date:end_date]

            if df.empty:
                print(f"警告: {name} ({symbol}) 在指定时间范围内没有数据")
                return None

            # 计算日收益率
            daily_returns = df['5. adjusted close'].pct_change()

            # 计算总收益率
            total_return = (df['5. adjusted close'].iloc[-1] / df['5. adjusted close'].iloc[0]) - 1

            # 计算年化收益率
            trading_days = len(df)
            years_passed = trading_days / 252
            annual_return = (1 + total_return) ** (1 / years_passed) - 1

            # 计算年化波动率
            annual_volatility = daily_returns.std() * np.sqrt(252)

            return IndexReturn(
                symbol=symbol,
                name=name,
                annual_return=annual_return,
                total_return=total_return,
                annual_volatility=annual_volatility,
                latest_price=df['5. adjusted close'].iloc[-1],
                initial_price=df['5. adjusted close'].iloc[0],
                daily_returns=daily_returns,
                price_series=df['5. adjusted close'],
                analysis_period=years,
                data_start_date=df.index[0],
                data_end_date=df.index[-1]
            )

        except Exception as e:
            print(f"错误: 处理 {name} ({symbol}) 时发生异常: {str(e)}")
            return None

    def analyze_market(self, years: int = 10) -> MarketAnalysis:
        """分析所有配置的市场指数"""
        indices_results = {}
        failed_indices = []

        for name, symbol in self.indices_dict.items():
            for attempt in range(3):  # 最多重试3次
                print(f"分析 {name} ({symbol})... 尝试 {attempt + 1}/3")

                result = self._calculate_single_index_return(symbol, name, years)
                if result:
                    indices_results[name] = result
                    break

                if attempt < 2:  # 如果不是最后一次尝试，等待后重试
                    time.sleep(self.request_delay)

            if name not in indices_results:
                failed_indices.append(name)

        if failed_indices:
            print(f"\n警告: 以下指数获取失败: {', '.join(failed_indices)}")

        if not indices_results:
            raise Exception("所有数据获取均失败")

        summary_stats = self._calculate_summary_stats(indices_results)
        return MarketAnalysis(
            analysis_date=datetime.now(),
            indices=indices_results,
            summary_stats=summary_stats
        )

    @staticmethod
    def _calculate_summary_stats(indices_results: Dict[str, IndexReturn]) -> Dict[str, float]:
        """计算汇总统计指标"""
        returns = [index.annual_return for index in indices_results.values()]
        volatilities = [index.annual_volatility for index in indices_results.values()]

        return {
            'average_annual_return': np.mean(returns),
            'max_annual_return': np.max(returns),
            'min_annual_return': np.min(returns),
            'average_volatility': np.mean(volatilities),
            'max_volatility': np.max(volatilities),
            'min_volatility': np.min(volatilities)
        }

    def generate_report(self, analysis: MarketAnalysis) -> pd.DataFrame:
        """生成分析报告DataFrame"""
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

    def save_results(self, analysis: MarketAnalysis, filename: str = 'market_analysis_results.csv'):
        """保存分析结果到CSV文件"""
        report_df = self.generate_report(analysis)
        report_df.to_csv(filename, encoding='utf-8-sig', index=False)
        print(f"\n分析结果已保存到 {filename}")