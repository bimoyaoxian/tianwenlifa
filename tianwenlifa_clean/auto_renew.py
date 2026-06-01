#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PythonAnywhere 免费 Web 应用自动续期脚本
=========================================
自动登录 PythonAnywhere，找到 "Run until 1 month from today"
按钮并点击，防止网站过期停服。

用法:
    # 交互式输入密码
    python auto_renew.py

    # 从环境变量读取密码（推荐）
    set PA_PASSWORD=你的密码
    python auto_renew.py

    # 强制运行（忽略间隔检查）
    python auto_renew.py --force

    # 或直接写用户名密码到脚本底部（不推荐）
"""

import os
import re
import sys
import json
import time
import argparse
import getpass
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装 beautifulsoup4: pip install beautifulsoup4")
    sys.exit(1)

# ====== 配置 ======
USERNAME = "Arreao"
DOMAIN = "arreao.pythonanywhere.com"
MIN_INTERVAL_DAYS = 20       # 最小续期间隔（天），不到则跳过
STATE_FILE = "auto_renew.state"  # 记录上次续期时间的文件
# ==================


def check_interval(force=False):
    """检查距上次续期是否已过 MIN_INTERVAL_DAYS 天，force=True 则跳过检查"""
    if force:
        return True
    state_path = Path(STATE_FILE)
    if not state_path.exists():
        # 没有状态文件，首次运行，允许执行
        return True
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        last_time = data.get("last_renew_time", 0)
        elapsed_days = (time.time() - last_time) / 86400
        remaining = MIN_INTERVAL_DAYS - elapsed_days
        if elapsed_days < MIN_INTERVAL_DAYS:
            print(f"[v] 距上次续期仅 {elapsed_days:.1f} 天，"
                  f"需满 {MIN_INTERVAL_DAYS} 天后再续（还差 {remaining:.1f} 天），跳过本次")
            return False
        return True
    except Exception as e:
        print(f"[!] 读取状态文件失败: {e}，按需执行")
        return True


def save_state():
    """保存当前时间到状态文件"""
    state_path = Path(STATE_FILE)
    try:
        data = {"last_renew_time": time.time()}
        state_path.write_text(json.dumps(data), encoding="utf-8")
    except Exception as e:
        print(f"[!] 写入状态文件失败: {e}")


def renew():
    password = os.environ.get("PA_PASSWORD")
    if not password:
        password = getpass.getpass(f"请输入 {USERNAME} 的 PythonAnywhere 密码: ")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    })

    # 1. 登录
    print("[1/4] 正在登录 PythonAnywhere...")
    login_url = "https://www.pythonanywhere.com/accounts/login/"
    resp = session.get(login_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf:
        print("[x] 获取 CSRF Token 失败")
        return False
    csrf_token = csrf.get("value")

    payload = {
        "csrfmiddlewaretoken": csrf_token,
        "auth-username": USERNAME,
        "auth-password": password,
        "login_view-current_step": "auth",
    }
    resp = session.post(login_url, data=payload,
                        headers={"Referer": login_url})

    if "Invalid username or password" in resp.text:
        print("[x] 用户名或密码错误")
        return False
    print("[v] 登录成功")

    # 2. 访问 Web 管理页
    print("[2/4] 正在访问 Web 管理页面...")
    web_url = f"https://www.pythonanywhere.com/user/{USERNAME}/webapps/"
    resp = session.get(web_url)
    if DOMAIN not in resp.text:
        print(f"[x] 未找到 Web 应用 {DOMAIN}")
        return False
    print("[v] 找到 Web 应用")

    # 3. 检查续期按钮
    print("[3/4] 检查续期按钮...")
    soup = BeautifulSoup(resp.text, "html.parser")

    # 方式1: 找 "Run until 1 month from today" 按钮
    extend_btn = soup.find("a", string=re.compile(r"Run until 1 month", re.I))
    if not extend_btn:
        extend_btn = soup.find("button", string=re.compile(r"Run until 1 month", re.I))
    if not extend_btn:
        # 方式2: 找 data-action="extend" 的按钮
        extend_btn = soup.find("a", {"data-action": "extend"})
    if not extend_btn:
        # 方式3: 找包含 "Extend" 的链接
        extend_btn = soup.find("a", string=re.compile(r"Extend", re.I))

    if not extend_btn:
        print("[v] 无需续期（可能刚续过，按钮还没出现）")
        return True

    # 4. 点击续期
    print("[4/4] 正在点击续期按钮...")
    extend_url = extend_btn.get("href")
    if extend_url:
        if not extend_url.startswith("http"):
            extend_url = f"https://www.pythonanywhere.com{extend_url}"
        resp = session.get(extend_url, headers={"Referer": web_url})
        if resp.status_code == 200:
            print("[v] 续期成功！网站继续运行一个月")
            # 续期成功后保存时间戳
            save_state()
            return True
        else:
            print(f"[x] 续期请求失败 (HTTP {resp.status_code})")
            return False

    print("[x] 未找到续期按钮的链接")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PythonAnywhere 自动续期工具")
    parser.add_argument("--force", action="store_true",
                        help="强制续期，忽略间隔检查")
    args = parser.parse_args()

    print("=" * 50)
    print("  PythonAnywhere 自动续期工具")
    print(f"  用户: {USERNAME}  域名: {DOMAIN}")
    print("=" * 50)

    # 间隔检查
    if not check_interval(force=args.force):
        print("=" * 50)
        sys.exit(0)

    success = renew()
    print("=" * 50)
    if success:
        print("  状态: [v] 操作完成")
    else:
        print("  状态: [x] 失败，请手动续期")
        print("  https://www.pythonanywhere.com/user/Arreao/webapps/")
    print("=" * 50)
