# 本地运行测试指南

## 🐍 问题分析

看起来在当前的沙箱环境中无法识别 Python。这是因为：
- 沙箱环境是隔离的，可能没有安装 Python
- 或者 Python 安装了但没有添加到系统路径

## 🚀 解决方案：在本地环境中运行

### 步骤 1: 打开本地命令提示符

**Windows 用户**:
- 按下 `Win + R`
- 输入 `cmd` 或 `powershell`
- 点击 "确定"

**Mac 用户**:
- 打开 "终端" 应用

**Linux 用户**:
- 打开终端

### 步骤 2: 导航到项目目录

```bash
# Windows 示例
cd C:\Users\LENOVO\Documents\GitHub\26Simu-Project1-Starter

# Mac/Linux 示例
cd /Users/LENOVO/Documents/GitHub/26Simu-Project1-Starter
```

### 步骤 3: 验证 Python 安装

```bash
# 检查 Python 版本
python --version

# 如果上面的命令失败，尝试
py --version

# 或者
python3 --version
```

你应该看到类似这样的输出：
```
Python 3.8.10
```

### 步骤 4: 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 如果上面的命令失败，尝试
pip3 install -r requirements.txt

# 或者
python -m pip install -r requirements.txt
```

### 步骤 5: 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 如果上面的命令失败，尝试
python -m pytest tests/ -v

# 或者
pytest tests/test_invariants.py -v
```

### 步骤 6: 运行手动测试

如果 pytest 遇到问题，你可以运行我们创建的手动测试脚本：

```bash
python test_manual.py
```

## 📋 预期输出

成功运行测试后，你应该看到类似这样的输出：

```
========================================= test session starts =========================================
platform win32 -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
rootdir: C:\Users\LENOVO\Documents\GitHub\26Simu-Project1-Starter
tests collected 11 items

tests/test_invariants.py::test_zero_swap_no_state_change PASSED
ests/test_invariants.py::test_balances_never_negative PASSED
ests/test_invariants.py::test_xyk_invariant PASSED
ests/test_invariants.py::test_price_monotonicity PASSED
ests/test_invariants.py::test_slippage_protection PASSED
ests/test_invariants.py::test_liquidity_addition_increases_balances PASSED
ests/test_invariants.py::test_swap_without_liquidity PASSED
ests/test_invariants.py::test_tick_crossing_updates_liquidity PASSED
ests/test_invariants.py::test_fee_accumulation PASSED
ests/test_invariants.py::test_extreme_price_stability PASSED
ests/test_invariants.py::test_pool_initialization PASSED

========================================= 11 passed in 0.12s =========================================
```

## 🔧 常见问题解决方案

### 问题 1: Python 未找到

**解决方案**:
- 从 [Python 官网](https://www.python.org/downloads/) 下载并安装 Python
- 安装时勾选 "Add Python to PATH"

### 问题 2: pip 未找到

**解决方案**:
- 确保 Python 已正确安装并添加到 PATH
- 尝试使用 `python -m pip` 代替 `pip`

### 问题 3: 依赖安装失败

**解决方案**:
- 升级 pip: `pip install --upgrade pip`
- 检查网络连接
- 尝试使用国内镜像: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 问题 4: 测试运行失败

**解决方案**:
- 检查 Python 版本 (推荐 3.8+)
- 确保所有依赖都已正确安装
- 查看详细错误信息并修复

## 📞 求助

如果仍然遇到问题，请提供以下信息，我会进一步帮助你：

1. 你使用的操作系统 (Windows/Mac/Linux)
2. Python 版本
3. 具体的错误信息
4. 你尝试过的命令

---

**祝你测试成功！** 🎉
