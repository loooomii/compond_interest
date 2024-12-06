from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()


class Settings:
    # API设置
    API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '12.1'))

    # 缓存设置
    CACHE_DIR = 'data_cache'
    CACHE_VALIDITY_DAYS = 1

    # 重试设置
    MAX_RETRIES = 3

    # 市场指数配置
    INDICES = {
        'S&P 500': 'SPX',
        '道琼斯工业平均指数': 'DJI',
        '纳斯达克综合指数': 'IXIC',
        '上证综指': '000001.SH',
        '深证成指': '399001.SZ',
        '恒生指数': 'HSI',
        '日经225': 'N225'
    }
