# 🪐 Project 1: Uniswap V3 State Machine (Starter Template)

> 🎈 **重要声明 (IMPORTANT)**: 
> 你当前所处的是**“纯净实战沙盒 (Starter Sandbox)”**。这里没有任何理论大纲和作业规格书。
> 本课程的所有红头文件、教学指导、工具链规范以及 Project 1 的打分标准（Rubric），均由 **教官的全球唯一主库 (SSOT)** 发布与维护。
> 👉 **[点击此处阅读课程原点：26Simu-Management-Modeling](https://github.com/booblu/26Simu-Management-Modeling)**
> 👉 **[点击此处查询 P1 任务规格书与计分板](https://github.com/booblu/26Simu-Management-Modeling/blob/main/03_Assignments/Project1_V3_State_Machine.md)**
> 👉 **[点击此处打开避坑保命的 Math Cheat Sheet](https://github.com/booblu/26Simu-Management-Modeling/blob/main/04_Resources/Project1_V3_Math_CheatSheet.md)**

## 
1. 把你在主库里学到的底层物理知识（Q64.96 定点数算法）移植进 `src/simulator.py` 里的那个空骨架中。
2. 疯狂地在 `tests/test_invariants.py` 中写能够把系统搞死（触发底板击穿）的独立红线测试断言。
3. 按照 `spec.yaml` 填写你做实验的初始环境与假设条件。

## 🚀 启动指北 (How to Run)

**1. 布置机房环境 (Install Environment)**
```bash
python -m pip install -r requirements.txt
```

**2. 呼叫日常断言法官 (Run CI Tests - 也是 GitHub 的判官流程)**
在推送到 Github 寻求跑分之前，请务必在你的电脑本地先拿满绿标：
```bash
pytest tests/ -v
```

**3. 启动全流水线与生成决策数据表 (Run Experiments)**
```bash
python experiments/run_all.py
```

## 📝 决策洞察 Memo (CEO 的信)

*(在此处删去占位符，写下你作为 CTO 和 CEO 的最终发现：在经历了自己设计的极限断言测试之后，V3 单池在极度失衡情况下的资金死亡滑点究竟在于哪个阈值？你的证明过程是什么？)*
