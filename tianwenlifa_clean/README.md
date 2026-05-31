

## 项目概述

基于 [www.sitianxueyuan.com](https://www.sitianxueyuan.com/)。

### 分析结论

| 模块 | 位置 | 状态 |
|------|------|------|
| 历法算法 | 后端 API (`ZiPingController`) | 已实现本地引擎 |
| 四柱排盘 | 后端 API + 前端展示 | 已实现本地引擎 |
| 节气计算 | 前端 `lunar.min.js` + 后端 | 已实现天文算法 |
| 真太阳时 | 前端计算 | 已实现 |
| 大运流年 | 后端 API | 已实现本地引擎 |
| 落甲历 | 前端 `luojia.js` | 部分理解(需继续逆向) |

### 架构说明

原网站使用 **前端JS + 后端API** 混合架构：
- `bazi.js` (混淆) → 收集表单数据 → POST → 后端 `ZiPingController` API
- `luojia.js` → 落甲历前端算法
- `js/lunar.min.js` → 农历计算工具库
- 月建使用**落甲历**(非标准农历)，考虑岁差修正

### 本地引擎架构

```
calendar_engine/
├── __init__.py
├── astronomy.py    # 天文学基础 (儒略日/真太阳时/节气)
├── ganzhi.py       # 干支/纳音/十神/藏干
├── lunar.py        # 农历转换 (1900-2100)
├── bazi.py         # 八字排盘
├── dayun.py        # 大运流年
├── cli.py          # 命令行入口
```

### 使用方法

```bash
# 交互模式
python main.py

# 命令行模式
python main.py --year 2026 --month 5 --day 27 --hour 16 --gender 男

# 真太阳时 (北京=116.4°E)
python main.py --year 2026 --month 5 --day 27 --hour 16 --gender 男 --longitude 116.4

# JSON输出
python main.py --year 2026 --month 5 --day 27 --hour 16 --gender 男 --json
```

### 依赖

- Python 3.8+
- Flask
- requests
- tyme4py（农历天文计算）

### 本机使用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务（访问 http://127.0.0.1:5000）
python web_app.py

# CLI 八字排盘
python prompt.py --year 2026 --month 5 --day 27 --hour 16 --gender 男

# 全部模式
python prompt.py --year 2026 --month 5 --day 27 --hour 16 --gender 男 --mode full
```

### 免责声明

本项目仅用于学习和研究目的，算法实现参考了公开的天文学和命理学知识。
