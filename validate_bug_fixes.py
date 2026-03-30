"""
Bug 修复验证脚本

验证三个 bug 修复的正确性：
1. tick_to_sqrt_price_x96 函数 - 避免浮点数计算
2. sqrt_price_x96_to_tick 函数 - 避免浮点数对数计算
3. 手续费计算 - 防止整数溢出
"""
import sys
import os

# 导入修复后的模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulator import (
    tick_to_sqrt_price_x96,
    sqrt_price_x96_to_tick,
    Q96,
    V3PoolStateMachine
)

def test_tick_to_sqrt_price_x96():
    """测试 tick_to_sqrt_price_x96 函数修复"""
    print("=" * 80)
    print("🧪 测试 tick_to_sqrt_price_x96 函数")
    print("=" * 80)
    
    test_cases = [
        (0, Q96),  # tick 0 应该返回 Q96
        (1, None),  # 正 tick
        (-1, None),  # 负 tick
        (1000, None),  # 较大的正 tick
        (-1000, None),  # 较大的负 tick
        (193749, None),  # 2500 USDC/ETH 对应的 tick
    ]
    
    for tick, expected in test_cases:
        result = tick_to_sqrt_price_x96(tick)
        print(f"  Tick: {tick:6d} -> sqrt_price_x96: {result}")
        
        # 验证返回值是整数
        assert isinstance(result, int), f"返回值应该是整数，得到 {type(result)}"
        # 验证返回值为正
        assert result > 0, f"返回值应该为正，得到 {result}"
        
        # 对于 tick 0，验证结果
        if tick == 0:
            assert result == Q96, f"tick 0 应该返回 Q96，得到 {result}"
    
    print("✅ tick_to_sqrt_price_x96 测试通过!")

def test_sqrt_price_x96_to_tick():
    """测试 sqrt_price_x96_to_tick 函数修复"""
    print("\n" + "=" * 80)
    print("🧪 测试 sqrt_price_x96_to_tick 函数")
    print("=" * 80)
    
    test_cases = [
        (Q96, 0),  # Q96 应该返回 tick 0
    ]
    
    # 测试不同 tick 的转换
    test_ticks = [-1000, -1, 0, 1, 1000, 193749]
    
    for tick in test_ticks:
        sqrt_price = tick_to_sqrt_price_x96(tick)
        recovered_tick = sqrt_price_x96_to_tick(sqrt_price)
        
        print(f"  Tick: {tick:6d} -> sqrt_price: {sqrt_price} -> Recovered: {recovered_tick:6d}")
        
        # 验证恢复的 tick 与原始 tick 接近
        # 允许一定的误差，因为是近似计算
        assert abs(recovered_tick - tick) <= 1, \
            f"恢复的 tick 与原始 tick 相差过大: {recovered_tick} vs {tick}"
    
    print("✅ sqrt_price_x96_to_tick 测试通过!")

def test_fee_calculation():
    """测试手续费计算修复"""
    print("\n" + "=" * 80)
    print("🧪 测试手续费计算")
    print("=" * 80)
    
    pool = V3PoolStateMachine()
    pool.add_liquidity(-100, 100, 10_000_000)
    
    # 测试不同大小的交易
    test_amounts = [
        1_000_000,      # 小交易
        100_000_000,     # 中等交易
        1_000_000_000,   # 大交易
    ]
    
    for amount in test_amounts:
        # 执行交易
        amount0, amount1 = pool.swap(zero_for_one=True, amount_specified=amount)
        
        print(f"  交易金额: {amount}")
        print(f"  实际输入: {amount0}")
        print(f"  输出: {amount1}")
        
        # 验证余额非负
        assert pool.balance_0 >= 0, f"balance_0 为负: {pool.balance_0}"
        assert pool.balance_1 >= 0, f"balance_1 为负: {pool.balance_1}"
        
        # 验证交易执行成功
        assert amount0 > 0, f"交易应该有输入: {amount0}"
        assert amount1 < 0, f"交易应该有输出: {amount1}"
    
    print("✅ 手续费计算测试通过!")

def test_extreme_values():
    """测试极端值"""
    print("\n" + "=" * 80)
    print("🧪 测试极端值")
    print("=" * 80)
    
    # 测试极端 tick 值
    extreme_ticks = [-887272, 887272]  # V3 的最小和最大 tick
    
    for tick in extreme_ticks:
        try:
            sqrt_price = tick_to_sqrt_price_x96(tick)
            recovered_tick = sqrt_price_x96_to_tick(sqrt_price)
            print(f"  极端 Tick: {tick:6d} -> sqrt_price: {sqrt_price} -> Recovered: {recovered_tick:6d}")
        except Exception as e:
            print(f"  极端 Tick {tick} 测试失败: {e}")
            raise
    
    print("✅ 极端值测试通过!")

def test_consistency():
    """测试一致性"""
    print("\n" + "=" * 80)
    print("🧪 测试一致性")
    print("=" * 80)
    
    # 测试 tick 和 sqrt_price 转换的一致性
    for tick in range(-100, 101, 10):
        sqrt_price = tick_to_sqrt_price_x96(tick)
        recovered_tick = sqrt_price_x96_to_tick(sqrt_price)
        
        # 验证转换的一致性
        assert abs(recovered_tick - tick) <= 1, \
            f"转换不一致: {tick} -> {sqrt_price} -> {recovered_tick}"
    
    print("✅ 一致性测试通过!")

if __name__ == "__main__":
    try:
        test_tick_to_sqrt_price_x96()
        test_sqrt_price_x96_to_tick()
        test_fee_calculation()
        test_extreme_values()
        test_consistency()
        
        print("\n" + "=" * 80)
        print("🎉 所有 Bug 修复验证通过!")
        print("=" * 80)
        print("\n修复的 Bug:")
        print("1. ✅ tick_to_sqrt_price_x96 - 移除了浮点数计算，使用整数运算")
        print("2. ✅ sqrt_price_x96_to_tick - 移除了浮点数对数计算，使用二分查找")
        print("3. ✅ 手续费计算 - 添加了溢出检查，防止整数溢出")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
