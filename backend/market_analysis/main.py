import argparse
from datetime import datetime

from backend.market_analysis.core.analyzer import MarketIndexAnalyzer
from backend.market_analysis.config.settings import Settings


def setup_argument_parser():
    """设置命令行参数解析"""
    parser = argparse.ArgumentParser(description='市场指数分析工具')
    parser.add_argument(
        '--years',
        type=int,
        default=10,
        help='分析年限 (默认: 10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=f'market_analysis_{datetime.now().strftime("%Y%m%d")}.csv',
        help='输出文件名 (默认: market_analysis_YYYYMMDD.csv)'
    )
    return parser


def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = setup_argument_parser()
        args = parser.parse_args()

        print(f"\n=== 开始市场分析 ===")
        print(f"分析年限: {args.years} 年")
        print(f"输出文件: {args.output}")

        # 初始化分析器
        analyzer = MarketIndexAnalyzer()

        # 进行分析
        print("\n正在获取和分析数据...")
        analysis_result = analyzer.analyze_market(years=args.years)

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

        # 保存结果
        analyzer.save_results(analysis_result, filename=args.output)
        print(f"\n分析完成！结果已保存到 {args.output}")

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n分析过程中发生错误: {str(e)}")
        raise e


if __name__ == "__main__":
    main()