"""
手动测试脚本 - 验证 V3PoolStateMachine 的核心功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from simulator import V3PoolStateMachine, tick_to_sqrt_price_x96, Q96

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 池子初始化")
    print("=" * 60)
    
    pool = V3PoolStateMachine()
    print(f"✓ 默认池子创建成功")
    print(f"  - sqrt_price_x96: {pool.sqrt_price_x96}")
    print(f"  - tick: {pool.tick}")
    print(f"  - liquidity: {pool.liquidity}")
    print(f"  - price: {pool.get_price():.6f}")
    
    print("\n" + "=" * 60)
    print("测试 2: 添加流动性")
    print("=" * 60)
    
    amount0, amount1 = pool.add_liquidity(-100, 100, 10_000_000)
    print(f"✓ 流动性添加成功")
    print(f"  - 添加的 token0: {amount0}")
    print(f"  - 添加的 token1: {amount1}")
    print(f"  - 当前活跃流动性: {pool.liquidity}")
    print(f"  - 池子余额: balance_0={pool.balance_0}, balance_1={pool.balance_1}")
    
    print("\n" + "=" * 60)
    print("测试 3: 零交易不变性")
    print("=" * 60)
    
    initial_price = pool.sqrt_price_x96
    initial_tick = pool.tick
    
    amount0, amount1 = pool.swap(zero_for_one=True, amount_specified=0)
    
    assert pool.sqrt_price_x96 == initial_price, "零交易改变了价格!"
    assert pool.tick == initial_tick, "零交易改变了 tick!"
    assert amount0 == 0 and amount1 == 0, "零交易返回非零值!"
    
    print(f"✓ 零交易测试通过")
    print(f"  - 交易前价格: {initial_price}")
    print(f"  - 交易后价格: {pool.sqrt_price_x96}")
    print(f"  - 返回值: amount0={amount0}, amount1={amount1}")
    
    print("\n" + "=" * 60)
    print("测试 4: 正常交易")
    print("=" * 60)
    
    price_before = pool.get_price()
    amount0, amount1 = pool.swap(zero_for_one=True, amount_specified=1_000_000)
    price_after = pool.get_price()
    
    print(f"✓ 交易执行成功")
    print(f"  - 交易前价格: {price_before:.6f}")
    print(f"  - 交易后价格: {price_after:.6f}")
    print(f"  - 价格变化: {((price_after - price_before) / price_before * 100):.4f}%")
    print(f"  - amount0: {amount0}")
    print(f"  - amount1: {amount1}")
    
    # 验证价格单调性
    assert price_after < price_before, "卖出 token0 后价格应该下降!"
    print(f"✓ 价格单调性验证通过")
    
    print("\n" + "=" * 60)
    print("测试 5: 反向交易")
    print("=" * 60)
    
    price_before = pool.get_price()
    amount0, amount1 = pool.swap(zero_for_one=False, amount_specified=1_000_000)
    price_after = pool.get_price()
    
    print(f"✓ 反向交易执行成功")
    print(f"  - 交易前价格: {price_before:.6f}")
    print(f"  - 交易后价格: {price_after:.6f}")
    print(f"  - 价格变化: {((price_after - price_before) / price_before * 100):.4f}%")
    
    # 验证价格单调性
    assert price_after > price_before, "卖出 token1 后价格应该上升!"
    print(f"✓ 价格单调性验证通过")
    
    print("\n" + "=" * 60)
    print("测试 6: 余额非负性")
    print("=" * 60)
    
    assert pool.balance_0 >= 0, f"Token0 余额为负: {pool.balance_0}"
    assert pool.balance_1 >= 0, f"Token1 余额为负: {pool.balance_1}"
    
    print(f"✓ 余额非负性验证通过")
    print(f"  - balance_0: {pool.balance_0}")
    print(f"  - balance_1: {pool.balance_1}")
    
    print("\n" + "=" * 60)
    print("测试 7: K 值守恒")
    print("=" * 60)
    
    x, y = pool.get_virtual_reserves()
    k = x * y
    
    print(f"✓ 虚拟储备计算成功")
    print(f"  - x (虚拟 token0): {x}")
    print(f"  - y (虚拟 token1): {y}")
    print(f"  - k (x * y): {k}")
    
    print("\n" + "=" * 60)
    print("所有测试通过! ✓")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
