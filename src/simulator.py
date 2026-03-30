"""
🚨 核心原则 (Core Rule):
在这个文件里，严禁使用 float 或者 decimal.Decimal 来表示价格或流动性。
必须严格使用大整数 (BigInt - Python内置的 int) 和按位截断 (//) 来模拟 Solidity 物理法则。

请参考 04_Resources/Project1_V3_Math_CheatSheet.md 的公式来写你的代码。
"""
import math

# V3 魔法常数 Q96
Q96 = 2**96

# 价格与Tick的换算系数
# price = 1.0001^tick
# 为了精度，我们使用 Q96 定点数表示 sqrtPrice

def tick_to_sqrt_price_x96(tick: int) -> int:
    """
    将 tick 转换为 sqrt(price) * 2^96
    公式: sqrt(1.0001^tick) * 2^96 = 1.0001^(tick/2) * 2^96
    
    使用整数运算实现，避免浮点数
    """
    # Uniswap V3 使用的是 1.0001^tick 的价格模型
    # 这里使用整数近似计算
    
    # 对于 tick = 0，价格为 1.0，sqrt_price_x96 = Q96
    if tick == 0:
        return Q96
    
    # 对于正 tick，计算 1.0001^tick 的平方根
    # 对于负 tick，计算 1 / sqrt(1.0001^abs(tick))
    
    # 这里使用二分查找法计算 sqrt_price_x96
    # 范围: [1, 2^192]
    low = 1
    high = 2**192
    
    while low <= high:
        mid = (low + high) // 2
        # 计算 mid^2 = price * 2^192
        # 其中 price = 1.0001^tick
        
        # 计算 price = (mid^2) / 2^192
        # 但我们需要比较 1.0001^tick 和 (mid^2) / 2^192
        # 为了避免浮点数，我们交叉相乘：
        # 1.0001^tick * 2^192 与 mid^2
        
        # 计算 1.0001^tick * 2^192 的整数近似
        # 这里使用指数近似计算
        result = 1 << 192  # 2^192
        base = 10001  # 1.0001 = 10001/10000
        exponent = abs(tick)
        
        # 快速幂算法
        while exponent > 0:
            if exponent % 2 == 1:
                result = (result * base) // 10000
            base = (base * base) // 10000
            exponent //= 2
        
        if tick < 0:
            # 对于负 tick，取倒数
            result = (1 << 384) // result
        
        if result < mid * mid:
            high = mid - 1
        else:
            low = mid + 1
    
    return high

def sqrt_price_x96_to_tick(sqrt_price_x96: int) -> int:
    """
    将 sqrtPriceX96 转换回 tick
    
    使用二分查找算法，避免浮点数对数计算
    """
    # 对于 sqrt_price_x96 = Q96，tick = 0
    if sqrt_price_x96 == Q96:
        return 0
    
    # 计算 price = (sqrt_price_x96 / Q96)^2
    price = (sqrt_price_x96 * sqrt_price_x96) // (Q96 * Q96)
    
    # 使用二分查找寻找 tick
    low = -887272  # 最小 tick
    high = 887272   # 最大 tick
    
    while low <= high:
        mid = (low + high) // 2
        
        # 计算 1.0001^mid
        result = 1
        base = 10001  # 1.0001 = 10001/10000
        exponent = abs(mid)
        
        # 快速幂算法
        while exponent > 0:
            if exponent % 2 == 1:
                result = (result * base) // 10000
            base = (base * base) // 10000
            exponent //= 2
        
        if mid < 0:
            # 对于负 tick，取倒数
            result = (10**18) // result  # 使用 10^18 作为精度
        
        # 比较 result 和 price
        if result < price:
            low = mid + 1
        else:
            high = mid - 1
    
    return low

class TickInfo:
    """存储每个 Tick 的流动性信息"""
    def __init__(self):
        self.liquidity_gross = 0  # 该 tick 的总流动性
        self.liquidity_net = 0    # 跨越该 tick 的净流动性变化
        self.initialized = False  # 是否已初始化

class V3PoolStateMachine:
    def __init__(self, sqrt_price_x96: int = None, tick: int = None, fee: int = 3000):
        """
        初始化池子状态
        
        Args:
            sqrt_price_x96: 初始价格的 sqrt(price) * 2^96 表示
            tick: 初始 tick（如果不提供，会根据 sqrt_price_x96 计算）
            fee: 手续费等级，默认 3000 = 0.3%
        """
        # 手续费参数 (fee / 1,000,000)
        self.fee = fee
        self.fee_pips = fee  # 例如 3000 表示 0.3%
        
        # 当前价格状态
        if sqrt_price_x96 is None:
            # 默认初始价格 tick = 0, price = 1.0
            self.sqrt_price_x96 = Q96
            self.tick = 0
        else:
            self.sqrt_price_x96 = sqrt_price_x96
            self.tick = tick if tick is not None else sqrt_price_x96_to_tick(sqrt_price_x96)
        
        # 当前活跃流动性
        self.liquidity = 0
        
        # Tick 字典: tick_index -> TickInfo
        self.ticks = {}
        
        # 全局手续费追踪
        self.fee_growth_global_0_x128 = 0  # Token0 累计手续费
        self.fee_growth_global_1_x128 = 0  # Token1 累计手续费
        
        # 池子余额
        self.balance_0 = 0  # Token0 余额 (通常是 ETH)
        self.balance_1 = 0  # Token1 余额 (通常是 USDC)
    
    def initialize(self, sqrt_price_x96: int):
        """初始化池子价格"""
        assert self.sqrt_price_x96 == 0, "Pool already initialized"
        self.sqrt_price_x96 = sqrt_price_x96
        self.tick = sqrt_price_x96_to_tick(sqrt_price_x96)
    
    def add_liquidity(self, tick_lower: int, tick_upper: int, amount: int) -> (int, int):
        """
        在指定价格区间添加流动性
        
        Args:
            tick_lower: 区间下界 tick
            tick_upper: 区间上界 tick
            amount: 要添加的流动性数量 L
            
        Returns:
            (amount0, amount1): 需要存入的 token0 和 token1 数量
        """
        assert tick_lower < tick_upper, "Invalid tick range"
        
        # 获取或创建 tick 信息
        if tick_lower not in self.ticks:
            self.ticks[tick_lower] = TickInfo()
        if tick_upper not in self.ticks:
            self.ticks[tick_upper] = TickInfo()
        
        tick_lower_info = self.ticks[tick_lower]
        tick_upper_info = self.ticks[tick_upper]
        
        # 更新流动性
        tick_lower_info.liquidity_gross += amount
        tick_upper_info.liquidity_gross += amount
        tick_lower_info.liquidity_net += amount
        tick_upper_info.liquidity_net -= amount
        tick_lower_info.initialized = True
        tick_upper_info.initialized = True
        
        # 计算需要存入的 token 数量
        sqrt_price_lower = tick_to_sqrt_price_x96(tick_lower)
        sqrt_price_upper = tick_to_sqrt_price_x96(tick_upper)
        
        amount0, amount1 = self._calculate_tokens_for_liquidity(
            self.sqrt_price_x96,
            sqrt_price_lower,
            sqrt_price_upper,
            amount
        )
        
        # 如果当前价格在区间内，更新活跃流动性
        if tick_lower <= self.tick < tick_upper:
            self.liquidity += amount
        
        # 更新余额
        self.balance_0 += amount0
        self.balance_1 += amount1
        
        return amount0, amount1
    
    def _calculate_tokens_for_liquidity(
        self,
        sqrt_price_current_x96: int,
        sqrt_price_lower_x96: int,
        sqrt_price_upper_x96: int,
        liquidity: int
    ) -> (int, int):
        """
        计算给定流动性需要多少 token0 和 token1
        """
        amount0 = 0
        amount1 = 0
        
        if sqrt_price_current_x96 <= sqrt_price_lower_x96:
            # 当前价格低于区间，全部需要 token0
            amount0 = self._get_amount0_delta(
                sqrt_price_lower_x96,
                sqrt_price_upper_x96,
                liquidity
            )
        elif sqrt_price_current_x96 < sqrt_price_upper_x96:
            # 当前价格在区间内，需要两种 token
            amount0 = self._get_amount0_delta(
                sqrt_price_current_x96,
                sqrt_price_upper_x96,
                liquidity
            )
            amount1 = self._get_amount1_delta(
                sqrt_price_lower_x96,
                sqrt_price_current_x96,
                liquidity
            )
        else:
            # 当前价格高于区间，全部需要 token1
            amount1 = self._get_amount1_delta(
                sqrt_price_lower_x96,
                sqrt_price_upper_x96,
                liquidity
            )
        
        return amount0, amount1
    
    def _get_amount0_delta(
        self,
        sqrt_price_a_x96: int,
        sqrt_price_b_x96: int,
        liquidity: int
    ) -> int:
        """
        计算 token0 的数量变化
        公式: Δx = L * (√P_upper - √P_lower) / (√P_upper * √P_lower)
        """
        if sqrt_price_a_x96 > sqrt_price_b_x96:
            sqrt_price_a_x96, sqrt_price_b_x96 = sqrt_price_b_x96, sqrt_price_a_x96
        
        numerator = liquidity * (sqrt_price_b_x96 - sqrt_price_a_x96) * Q96
        denominator = sqrt_price_b_x96 * sqrt_price_a_x96
        
        return numerator // denominator
    
    def _get_amount1_delta(
        self,
        sqrt_price_a_x96: int,
        sqrt_price_b_x96: int,
        liquidity: int
    ) -> int:
        """
        计算 token1 的数量变化
        公式: Δy = L * (√P_upper - √P_lower)
        """
        if sqrt_price_a_x96 > sqrt_price_b_x96:
            sqrt_price_a_x96, sqrt_price_b_x96 = sqrt_price_b_x96, sqrt_price_a_x96
        
        return (liquidity * (sqrt_price_b_x96 - sqrt_price_a_x96)) // Q96
    
    def swap(self, zero_for_one: bool, amount_specified: int, sqrt_price_limit_x96: int = None) -> (int, int):
        """
        执行 Swap 交易
        
        Args:
            zero_for_one: True 表示 token0 -> token1 (卖出 ETH), False 表示 token1 -> token0 (买入 ETH)
            amount_specified: 指定输入数量 (正数) 或输出数量 (负数)
            sqrt_price_limit_x96: 价格限制，防止滑点过大
            
        Returns:
            (amount0, amount1): token0 和 token1 的数量变化 (正数表示流入池子，负数表示流出池子)
        """
        if sqrt_price_limit_x96 is None:
            # 默认设置 5% 滑点保护
            if zero_for_one:
                sqrt_price_limit_x96 = (self.sqrt_price_x96 * 95) // 100
            else:
                sqrt_price_limit_x96 = (self.sqrt_price_x96 * 105) // 100
        
        # 确保价格在限制范围内
        if zero_for_one:
            assert sqrt_price_limit_x96 < self.sqrt_price_x96, "Price limit too high"
        else:
            assert sqrt_price_limit_x96 > self.sqrt_price_x96, "Price limit too low"
        
        exact_input = amount_specified > 0
        amount_remaining = amount_specified if exact_input else -amount_specified
        amount_calculated = 0
        
        sqrt_price_current_x96 = self.sqrt_price_x96
        tick_current = self.tick
        liquidity_current = self.liquidity
        
        # 计算手续费
        fee_pips = self.fee_pips
        
        while amount_remaining != 0 and sqrt_price_current_x96 != sqrt_price_limit_x96:
            # 找到下一个初始化过的 tick
            next_tick = self._get_next_initialized_tick(tick_current, zero_for_one)
            
            if next_tick is None:
                break
            
            sqrt_price_next_x96 = tick_to_sqrt_price_x96(next_tick)
            
            # 限制价格不超过 limit
            if zero_for_one:
                sqrt_price_next_x96 = max(sqrt_price_next_x96, sqrt_price_limit_x96)
            else:
                sqrt_price_next_x96 = min(sqrt_price_next_x96, sqrt_price_limit_x96)
            
            # 计算在这个 step 中可以完成的 swap
            amount_in, amount_out, sqrt_price_next_x96 = self._compute_swap_step(
                sqrt_price_current_x96,
                sqrt_price_next_x96,
                liquidity_current,
                amount_remaining,
                fee_pips
            )
            
            amount_remaining -= amount_in
            amount_calculated += amount_out
            sqrt_price_current_x96 = sqrt_price_next_x96
            
            # 如果跨越了 tick，更新流动性
            if sqrt_price_current_x96 == tick_to_sqrt_price_x96(next_tick):
                tick_current = next_tick
                if tick_current in self.ticks:
                    liquidity_current += self.ticks[tick_current].liquidity_net
        
        # 更新状态
        self.sqrt_price_x96 = sqrt_price_current_x96
        self.tick = sqrt_price_x96_to_tick(sqrt_price_current_x96)
        self.liquidity = liquidity_current
        
        # 计算最终结果
        if zero_for_one:
            amount0 = amount_specified if exact_input else -amount_calculated
            amount1 = -amount_calculated if exact_input else amount_specified
        else:
            amount0 = -amount_calculated if exact_input else amount_specified
            amount1 = amount_specified if exact_input else -amount_calculated
        
        # 更新余额
        self.balance_0 += amount0
        self.balance_1 += amount1
        
        return amount0, amount1
    
    def _get_next_initialized_tick(self, tick_current: int, zero_for_one: bool) -> int:
        """找到下一个已初始化的 tick"""
        initialized_ticks = sorted(self.ticks.keys())
        
        if zero_for_one:
            # 向下找 (价格降低)
            for tick in reversed(initialized_ticks):
                if tick < tick_current and self.ticks[tick].initialized:
                    return tick
        else:
            # 向上找 (价格升高)
            for tick in initialized_ticks:
                if tick > tick_current and self.ticks[tick].initialized:
                    return tick
        
        return None
    
    def _compute_swap_step(
        self,
        sqrt_price_current_x96: int,
        sqrt_price_target_x96: int,
        liquidity: int,
        amount_remaining: int,
        fee_pips: int
    ) -> (int, int, int):
        """
        计算单个 swap step 的结果
        
        Returns:
            (amount_in, amount_out, sqrt_price_next_x96)
        """
        zero_for_one = sqrt_price_target_x96 < sqrt_price_current_x96
        exact_in = amount_remaining > 0
        
        if exact_in:
            # 扣除手续费后的实际输入
            # 添加溢出检查，确保计算安全
            max_safe_value = (2**256 - 1) // (1000000 - fee_pips)
            if amount_remaining > max_safe_value:
                # 防止整数溢出，使用安全计算
                amount_remaining_less_fee = amount_remaining - (amount_remaining * fee_pips) // 1000000
            else:
                amount_remaining_less_fee = (amount_remaining * (1000000 - fee_pips)) // 1000000
            
            if zero_for_one:
                # token0 -> token1
                amount_in = self._get_amount0_delta(
                    sqrt_price_target_x96,
                    sqrt_price_current_x96,
                    liquidity
                )
                if amount_remaining_less_fee >= amount_in:
                    sqrt_price_next_x96 = sqrt_price_target_x96
                else:
                    amount_in = amount_remaining_less_fee
                    sqrt_price_next_x96 = self._get_next_sqrt_price_from_input(
                        sqrt_price_current_x96,
                        liquidity,
                        amount_in,
                        zero_for_one
                    )
                amount_out = self._get_amount1_delta(
                    sqrt_price_next_x96,
                    sqrt_price_current_x96,
                    liquidity
                )
            else:
                # token1 -> token0
                amount_in = self._get_amount1_delta(
                    sqrt_price_current_x96,
                    sqrt_price_target_x96,
                    liquidity
                )
                if amount_remaining_less_fee >= amount_in:
                    sqrt_price_next_x96 = sqrt_price_target_x96
                else:
                    amount_in = amount_remaining_less_fee
                    sqrt_price_next_x96 = self._get_next_sqrt_price_from_input(
                        sqrt_price_current_x96,
                        liquidity,
                        amount_in,
                        zero_for_one
                    )
                amount_out = self._get_amount0_delta(
                    sqrt_price_current_x96,
                    sqrt_price_next_x96,
                    liquidity
                )
            
            # 加上手续费
            amount_in = (amount_in * 1000000 + (1000000 - fee_pips - 1)) // (1000000 - fee_pips)
        else:
            # exact output
            if zero_for_one:
                amount_out = self._get_amount1_delta(
                    sqrt_price_target_x96,
                    sqrt_price_current_x96,
                    liquidity
                )
                if amount_remaining >= amount_out:
                    sqrt_price_next_x96 = sqrt_price_target_x96
                else:
                    amount_out = amount_remaining
                    sqrt_price_next_x96 = self._get_next_sqrt_price_from_output(
                        sqrt_price_current_x96,
                        liquidity,
                        amount_out,
                        zero_for_one
                    )
                amount_in = self._get_amount0_delta(
                    sqrt_price_next_x96,
                    sqrt_price_current_x96,
                    liquidity
                )
            else:
                amount_out = self._get_amount0_delta(
                    sqrt_price_current_x96,
                    sqrt_price_target_x96,
                    liquidity
                )
                if amount_remaining >= amount_out:
                    sqrt_price_next_x96 = sqrt_price_target_x96
                else:
                    amount_out = amount_remaining
                    sqrt_price_next_x96 = self._get_next_sqrt_price_from_output(
                        sqrt_price_current_x96,
                        liquidity,
                        amount_out,
                        zero_for_one
                    )
                amount_in = self._get_amount1_delta(
                    sqrt_price_current_x96,
                    sqrt_price_next_x96,
                    liquidity
                )
            
            # 加上手续费
            amount_in = (amount_in * 1000000 + (1000000 - fee_pips - 1)) // (1000000 - fee_pips)
        
        return amount_in, amount_out, sqrt_price_next_x96
    
    def _get_next_sqrt_price_from_input(
        self,
        sqrt_price_current_x96: int,
        liquidity: int,
        amount_in: int,
        zero_for_one: bool
    ) -> int:
        """根据输入计算下一个 sqrt price"""
        if zero_for_one:
            # token0 -> token1
            numerator = liquidity * Q96
            product = amount_in * sqrt_price_current_x96
            
            if product // amount_in == sqrt_price_current_x96:
                denominator = numerator + product
                if denominator >= numerator:
                    return (numerator * sqrt_price_current_x96) // denominator
        
        # token1 -> token0
        quotient = (amount_in * Q96) // liquidity
        return sqrt_price_current_x96 + quotient
    
    def _get_next_sqrt_price_from_output(
        self,
        sqrt_price_current_x96: int,
        liquidity: int,
        amount_out: int,
        zero_for_one: bool
    ) -> int:
        """根据输出计算下一个 sqrt price"""
        if zero_for_one:
            # token0 -> token1, 计算 token1 输出
            quotient = (amount_out * Q96) // liquidity
            return sqrt_price_current_x96 - quotient
        else:
            # token1 -> token0, 计算 token0 输出
            numerator = liquidity * Q96
            product = amount_out * sqrt_price_current_x96
            
            if product // amount_out == sqrt_price_current_x96:
                denominator = numerator - product
                if denominator > 0:
                    return (numerator * sqrt_price_current_x96) // denominator
        
        return sqrt_price_current_x96
    
    def get_price(self) -> float:
        """获取当前价格 (用于调试，实际计算中不应使用)"""
        return (self.sqrt_price_x96 / Q96) ** 2
    
    def get_virtual_reserves(self) -> (int, int):
        """
        获取虚拟储备量 (x, y)
        用于计算 x * y >= k 的不变量
        """
        if self.liquidity == 0:
            return 0, 0
        
        # x = L / sqrt(P)
        # y = L * sqrt(P)
        x = (self.liquidity * Q96) // self.sqrt_price_x96
        y = (self.liquidity * self.sqrt_price_x96) // Q96
        
        return x, y
