<div align="center">

# 天文历法

**中国传统天文历法推算引擎**

八字排盘 · 落甲历 · 五运六气 · 天文星象

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web-black)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📖 简介

天文历法是一套**离线可用的中国传统历法推算引擎**，提供：

- **八字排盘** — 四柱、十神、藏干、纳音、胎元、命宫、身宫、空亡
- **大运流年流月** — 标准历法 / 落甲历 双模式
- **落甲历** — 岁差修正的特殊干支历法
- **五运六气** — 岁运、司天、在泉、主运、主气、客气
- **天文星象** — 木星位置、二十八宿、斗建、星次、太阳系行星位置
- **AI 提示词** — 直接输出给 ChatGPT / DeepSeek 分析的排盘文本

---

## 🚀 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Web 服务
python web_app.py

# 3. 浏览器打开
#    http://127.0.0.1:5000   → 首页（日历 + 五运六气）
#    http://127.0.0.1:5000/bazi   → 八字排盘
#    http://127.0.0.1:5000/luojia → 落甲历日历
#    http://127.0.0.1:5000/tools  → 观天察时工具
```

### CLI 命令行

```bash
# 八字排盘 + AI 提示词
python prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男

# 完整排盘（含藏干、十神、胎元命宫身宫）
python prompt.py --year 1990 --month 6 --day 15 --hour 8 --mode detail

# 天文信息（五运六气、星象、行星位置）
python prompt.py --year 1990 --month 6 --day 15 --mode tianwen

# 全部信息合并输出
python prompt.py --year 1990 --month 6 --day 15 --hour 8 --mode full

# JSON 原始数据
python prompt.py --year 1990 --month 6 --day 15 --hour 8 --mode json

# 落甲历模式
python prompt.py --year 1990 --month 6 --day 15 --hour 8 --system luojia

# 未知时辰
python prompt.py --year 1990 --month 6 --day 15 --gender 女
```

---

## 🧩 输出模式

`prompt.py` 支持 6 种输出模式：

| 模式 | 说明 | 内容 |
|------|------|------|
| `prompt` | AI 提示词（默认） | 八字 + 胎元命宫身宫 + 大运流年表 + 流年流月 + 分析指引 |
| `bazi` | 八字简表 | 性别 + 日期 + 四柱 |
| `detail` | 完整排盘 | 八字 + 纳音 + 藏干十神 + 胎元命宫身宫 + 空亡 + 大运 + 流年流月 |
| `tianwen` | 天文信息 | 五运六气 + 斗建星次 + 木日相差 + 太阳系行星 |
| `full` | 全部信息 | detail + tianwen 合并 |
| `json` | 原始数据 | Python dict 全部字段 |

---

## 📁 项目结构

```
tianwenlifa/
├── calendar_engine/      # 核心引擎包
│   ├── astronomy.py      # 天文学基础（儒略日、节气、真太阳时、木星轨道）
│   ├── ganzhi.py         # 干支基础（六十甲子、纳音、五虎遁、五鼠遁、十神）
│   ├── bazi.py           # 标准八字排盘（胎元、命宫、身宫）
│   ├── luojia_calendar.py# 落甲历核心（年柱/月柱/日柱/时柱）
│   ├── dayun.py          # 大运流年（落甲历/标准 双模式）
│   ├── wuyun_liuqi.py    # 五运六气 + 天文星象
│   ├── lunar.py          # 公历转农历（tyme4py 天文算法，不限年份）
│   └── cli.py            # 命令行交互入口
├── templates/            # HTML 模板
│   ├── index.html        # 首页（日历 + 五运六气面板）
│   ├── bazi.html         # 八字排盘页
│   ├── luojia.html       # 落甲历日历页
│   └── tools.html        # 观天察时工具页
├── static/               # 静态资源（CSS/JS）
├── prompt.py             # ★ 单文件入口：八字排盘 + AI提示词 + 天象
├── web_app.py            # Flask Web 服务
├── main.py               # CLI 入口
├── luojia_full_engine.py # 落甲历独立引擎（精简版）
├── render.yaml           # Render.com 部署配置
└── requirements.txt      # Python 依赖
```

---

## ⚙️ 技术栈

| 模块 | 技术 |
|------|------|
| Web 框架 | Flask |
| 农历天文 | tyme4py（开普勒方程天文算法） |
| 节气计算 | 牛顿迭代求解开普勒方程，精度 1e-8° |
| 木星位置 | NASA JPL J2000 轨道根数 |
| 前端 | 原生 JS + Canvas（太阳系动画） |
| 生产部署 | gunicorn |

---

## 📜 免责声明

本项目仅用于**学习和研究目的**。算法实现参考了公开的天文学和传统命理学知识。不构成任何形式的命理咨询或决策建议。
核心来源于（周鹏说历法）：https://www.sitianxueyuan.com/

---

<div align="center">
Made with ❤️ for the study of Chinese traditional astronomy and calendar systems
</div>
