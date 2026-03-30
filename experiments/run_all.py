"""
🚀 Project 1: V3 状态机全流水线实验

功能：
1. 读取 spec.yaml 配置
2. 运行多个场景的模拟实验
3. 生成决策数据表和可视化报告
4. 输出关键指标和洞察
"""

import os
import sys
import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulator import V3PoolStateMachine, tick_to_sqrt_price_x96, Q96

# 实验配置
EXPERIMENT_CONFIG = {
    "scenarios": [
        {
            "name": "正常交易",
            "description": "常规大小的交易，测试基本功能",
            "trade_size_range": (1_000_000, 10_000_000),
            "num_trades": 50,
            "tick_range": (-100, 100),
            "initial_liquidity": 100_000_000
        },
        {
            "name": "大额交易",
            "description": "大额交易，测试滑点保护",
            "trade_size_range": (50_000_000, 100_000_000),
            "num_trades": 20,
            "tick_range": (-100, 100),
            "initial_liquidity": 100_000_000
        },
        {
            "name": "极端价格",
            "description": "在极端价格下测试系统稳定性",
            "trade_size_range": (1_000_000, 5_000_000),
            "num_trades": 30,
            "tick_range": (-50000, 50000),
            "initial_liquidity": 100_000_000,
            "extreme_tick": 50000
        },
        {
            "name": "流动性枯竭",
            "description": "测试流动性极低时的系统行为",
            "trade_size_range": (100_000, 1_000_000),
            "num_trades": 30,
            "tick_range": (-10, 10),
            "initial_liquidity": 1_000_000
        }
    ]
}


class ExperimentRunner:
    """实验运行器"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        self.results = []
        self.metrics = []
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def run_experiment(self, scenario: Dict) -> Dict:
        """
        运行单个实验场景
        
        Returns:
            实验结果字典
        """
        print(f"\n{'='*80}")
        print(f"🧪 运行场景: {scenario['name']}")
        print(f"📋 描述: {scenario['description']}")
        print(f"{'='*80}")
        
        # 初始化池子
        initial_tick = scenario.get('extreme_tick', 0)
        sqrt_price_x96 = tick_to_sqrt_price_x96(initial_tick)
        
        pool = V3PoolStateMachine(
            sqrt_price_x96=sqrt_price_x96,
            tick=initial_tick,
            fee=3000  # 0.3%
        )
        
        # 添加初始流动性
        tick_lower, tick_upper = scenario['tick_range']
        initial_liquidity = scenario['initial_liquidity']
        pool.add_liquidity(tick_lower, tick_upper, initial_liquidity)
        
        print(f"  初始价格 tick: {initial_tick}")
        print(f"  初始流动性: {initial_liquidity}")
        print(f"  流动性区间: [{tick_lower}, {tick_upper}]")
        print(f"  交易次数: {scenario['num_trades']}")
        
        # 记录初始状态
        initial_price = pool.get_price()
        initial_balance_0 = pool.balance_0
        initial_balance_1 = pool.balance_1
        
        # 运行交易序列
        trades = []
        min_price = initial_price
        max_price = initial_price
        total_volume = 0
        
        import random
        random.seed(42)  # 固定随机种子，保证可重复性
        
        for i in range(scenario['num_trades']):
            # 随机选择交易方向
            zero_for_one = random.choice([True, False])
            
            # 随机选择交易大小
            min_size, max_size = scenario['trade_size_range']
            trade_size = random.randint(min_size, max_size)
            
            # 记录交易前状态
            price_before = pool.get_price()
            
            # 执行交易
            try:
                amount0, amount1 = pool.swap(
                    zero_for_one=zero_for_one,
                    amount_specified=trade_size
                )
                
                # 记录交易后状态
                price_after = pool.get_price()
                
                # 计算滑点
                slippage = abs(price_after - price_before) / price_before if price_before > 0 else 0
                
                # 更新统计
                min_price = min(min_price, price_after)
                max_price = max(max_price, price_after)
                total_volume += abs(amount0) + abs(amount1)
                
                trades.append({
                    'trade_id': i,
                    'direction': 'ETH->USDC' if zero_for_one else 'USDC->ETH',
                    'size': trade_size,
                    'amount0': amount0,
                    'amount1': amount1,
                    'price_before': price_before,
                    'price_after': price_after,
                    'slippage': slippage
                })
                
            except Exception as e:
                print(f"  ⚠️  交易 {i} 失败: {e}")
                trades.append({
                    'trade_id': i,
                    'direction': 'ETH->USDC' if zero_for_one else 'USDC->ETH',
                    'size': trade_size,
                    'error': str(e)
                })
        
        # 计算最终指标
        final_price = pool.get_price()
        price_change = (final_price - initial_price) / initial_price if initial_price > 0 else 0
        
        # 计算无常损失 (简化版)
        # IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        price_ratio = final_price / initial_price if initial_price > 0 else 1
        impermanent_loss = 2 * (price_ratio ** 0.5) / (1 + price_ratio) - 1 if price_ratio > 0 else 0
        
        # 计算手续费收入
        fee_revenue = (pool.balance_0 - initial_balance_0) * 0.003 + (pool.balance_1 - initial_balance_1) * 0.003
        
        result = {
            'scenario_name': scenario['name'],
            'description': scenario['description'],
            'initial_price': initial_price,
            'final_price': final_price,
            'price_change': price_change,
            'min_price': min_price,
            'max_price': max_price,
            'price_volatility': (max_price - min_price) / initial_price if initial_price > 0 else 0,
            'total_volume': total_volume,
            'num_trades': len(trades),
            'successful_trades': len([t for t in trades if 'error' not in t]),
            'failed_trades': len([t for t in trades if 'error' in t]),
            'avg_slippage': sum(t.get('slippage', 0) for t in trades) / len([t for t in trades if 'error' not in t]) if trades else 0,
            'max_slippage': max((t.get('slippage', 0) for t in trades), default=0),
            'impermanent_loss': impermanent_loss,
            'fee_revenue': fee_revenue,
            'final_balance_0': pool.balance_0,
            'final_balance_1': pool.balance_1,
            'final_liquidity': pool.liquidity,
            'trades': trades
        }
        
        # 打印关键指标
        print(f"\n  📊 关键指标:")
        print(f"    初始价格: {initial_price:.6f}")
        print(f"    最终价格: {final_price:.6f}")
        print(f"    价格变化: {price_change*100:.2f}%")
        print(f"    价格波动率: {result['price_volatility']*100:.2f}%")
        print(f"    总交易量: {total_volume:,.0f}")
        print(f"    成功交易: {result['successful_trades']}/{result['num_trades']}")
        print(f"    平均滑点: {result['avg_slippage']*100:.4f}%")
        print(f"    最大滑点: {result['max_slippage']*100:.4f}%")
        print(f"    无常损失: {impermanent_loss*100:.4f}%")
        print(f"    手续费收入: {fee_revenue:.6f}")
        
        return result
    
    def run_all_experiments(self) -> List[Dict]:
        """运行所有实验场景"""
        print("🚀 [System] 启动 Project 1：V3 状态机极限压测台...")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for scenario in EXPERIMENT_CONFIG['scenarios']:
            result = self.run_experiment(scenario)
            self.results.append(result)
        
        print(f"\n{'='*80}")
        print("✅ [Status] 所有实验场景运行完毕")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        return self.results
    
    def generate_metrics_csv(self):
        """生成指标 CSV 文件"""
        csv_path = os.path.join(self.output_dir, 'metrics.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '场景名称',
                '初始价格',
                '最终价格',
                '价格变化(%)',
                '价格波动率(%)',
                '总交易量',
                '成功交易数',
                '失败交易数',
                '平均滑点(%)',
                '最大滑点(%)',
                '无常损失(%)',
                '手续费收入',
                '最终余额0',
                '最终余额1',
                '最终流动性'
            ])
            
            # 写入数据
            for result in self.results:
                writer.writerow([
                    result['scenario_name'],
                    result['initial_price'],
                    result['final_price'],
                    result['price_change'] * 100,
                    result['price_volatility'] * 100,
                    result['total_volume'],
                    result['successful_trades'],
                    result['failed_trades'],
                    result['avg_slippage'] * 100,
                    result['max_slippage'] * 100,
                    result['impermanent_loss'] * 100,
                    result['fee_revenue'],
                    result['final_balance_0'],
                    result['final_balance_1'],
                    result['final_liquidity']
                ])
        
        print(f"\n📊 [DataCollector] 指标数据已保存到: {csv_path}")
    
    def generate_trades_csv(self):
        """生成交易明细 CSV 文件"""
        csv_path = os.path.join(self.output_dir, 'trades.csv')
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '场景名称',
                '交易ID',
                '方向',
                '交易大小',
                'Amount0',
                'Amount1',
                '交易前价格',
                '交易后价格',
                '滑点(%)',
                '错误信息'
            ])
            
            # 写入数据
            for result in self.results:
                for trade in result['trades']:
                    writer.writerow([
                        result['scenario_name'],
                        trade.get('trade_id', ''),
                        trade.get('direction', ''),
                        trade.get('size', ''),
                        trade.get('amount0', ''),
                        trade.get('amount1', ''),
                        trade.get('price_before', ''),
                        trade.get('price_after', ''),
                        trade.get('slippage', 0) * 100 if 'slippage' in trade else '',
                        trade.get('error', '')
                    ])
        
        print(f"📊 [DataCollector] 交易明细已保存到: {csv_path}")
    
    def generate_insights_report(self):
        """生成洞察报告"""
        report_path = os.path.join(self.output_dir, 'insights.md')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 🪐 Project 1: V3 状态机实验洞察报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 执行摘要\n\n")
            
            # 找出关键发现
            max_slippage_scenario = max(self.results, key=lambda x: x['max_slippage'])
            max_il_scenario = max(self.results, key=lambda x: abs(x['impermanent_loss']))
            max_volume_scenario = max(self.results, key=lambda x: x['total_volume'])
            
            f.write(f"- **最高滑点场景**: {max_slippage_scenario['scenario_name']} "
                   f"({max_slippage_scenario['max_slippage']*100:.4f}%)\n")
            f.write(f"- **最大无常损失场景**: {max_il_scenario['scenario_name']} "
                   f"({max_il_scenario['impermanent_loss']*100:.4f}%)\n")
            f.write(f"- **最高交易量场景**: {max_volume_scenario['scenario_name']} "
                   f"({max_volume_scenario['total_volume']:,.0f})\n")
            
            f.write("\n## 🎯 场景分析\n\n")
            
            for result in self.results:
                f.write(f"### {result['scenario_name']}\n\n")
                f.write(f"**描述**: {result['description']}\n\n")
                
                f.write("| 指标 | 数值 |\n")
                f.write("|------|------|\n")
                f.write(f"| 初始价格 | {result['initial_price']:.6f} |\n")
                f.write(f"| 最终价格 | {result['final_price']:.6f} |\n")
                f.write(f"| 价格变化 | {result['price_change']*100:.2f}% |\n")
                f.write(f"| 价格波动率 | {result['price_volatility']*100:.2f}% |\n")
                f.write(f"| 总交易量 | {result['total_volume']:,.0f} |\n")
                f.write(f"| 成功/失败交易 | {result['successful_trades']}/{result['failed_trades']} |\n")
                f.write(f"| 平均滑点 | {result['avg_slippage']*100:.4f}% |\n")
                f.write(f"| 最大滑点 | {result['max_slippage']*100:.4f}% |\n")
                f.write(f"| 无常损失 | {result['impermanent_loss']*100:.4f}% |\n")
                f.write(f"| 手续费收入 | {result['fee_revenue']:.6f} |\n")
                f.write("\n")
            
            f.write("## 🔍 关键发现\n\n")
            
            # 分析滑点阈值
            f.write("### 滑点分析\n\n")
            f.write("根据实验结果，我们发现:\n\n")
            
            for result in self.results:
                if result['max_slippage'] > 0.05:  # 5%
                    f.write(f"- ⚠️ **{result['scenario_name']}**: 最大滑点超过 5% 安全阈值 "
                           f"({result['max_slippage']*100:.2f}%)，存在资金风险\n")
                else:
                    f.write(f"- ✅ **{result['scenario_name']}**: 滑点控制在安全范围内 "
                           f"({result['max_slippage']*100:.4f}%)\n")
            
            f.write("\n### 无常损失分析\n\n")
            for result in self.results:
                if abs(result['impermanent_loss']) > 0.01:  # 1%
                    f.write(f"- ⚠️ **{result['scenario_name']}**: 无常损失显著 "
                           f"({result['impermanent_loss']*100:.4f}%)\n")
                else:
                    f.write(f"- ✅ **{result['scenario_name']}**: 无常损失较小 "
                           f"({result['impermanent_loss']*100:.4f}%)\n")
            
            f.write("\n## 💡 决策建议\n\n")
            f.write("基于以上实验结果，作为 CTO 的建议:\n\n")
            f.write("1. **滑点保护**: 建议设置 5% 的滑点上限，防止大额交易造成过大价格冲击\n")
            f.write("2. **流动性管理**: 在极端价格场景下，需要增加流动性深度\n")
            f.write("3. **无常损失对冲**: 考虑为 LP 提供无常损失保险机制\n")
            f.write("4. **监控告警**: 实时监控滑点和无常损失指标，超过阈值时触发告警\n")
            
            f.write("\n---\n")
            f.write("*报告由 V3 状态机实验流水线自动生成*\n")
        
        print(f"📄 [Report] 洞察报告已保存到: {report_path}")
    
    def generate_json_report(self):
        """生成 JSON 格式的完整报告"""
        json_path = os.path.join(self.output_dir, 'report.json')
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'num_scenarios': len(self.results)
            },
            'summary': {
                'total_trades': sum(r['num_trades'] for r in self.results),
                'total_volume': sum(r['total_volume'] for r in self.results),
                'avg_slippage': sum(r['avg_slippage'] for r in self.results) / len(self.results) if self.results else 0,
                'max_slippage': max(r['max_slippage'] for r in self.results) if self.results else 0
            },
            'results': self.results
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 [Report] JSON 报告已保存到: {json_path}")


def main():
    """主函数"""
    print("🚀 [System] 启动 Project 1：V3 状态机极限压测台...")
    print("📊 [DataCollector] 正在记录池内资产变动曲线...")
    
    # 创建实验运行器
    runner = ExperimentRunner(output_dir="results")
    
    # 运行所有实验
    results = runner.run_all_experiments()
    
    # 生成输出文件
    runner.generate_metrics_csv()
    runner.generate_trades_csv()
    runner.generate_insights_report()
    runner.generate_json_report()
    
    print(f"\n{'='*80}")
    print("✅ [Status] 流水线运行完毕")
    print(f"📁 所有结果已保存到 results/ 目录")
    print(f"{'='*80}")
    
    # 返回关键指标摘要
    print("\n📊 关键指标摘要:")
    for result in results:
        print(f"  {result['scenario_name']}: "
              f"价格变化 {result['price_change']*100:+.2f}%, "
              f"最大滑点 {result['max_slippage']*100:.4f}%, "
              f"无常损失 {result['impermanent_loss']*100:.4f}%")


if __name__ == "__main__":
    main()
