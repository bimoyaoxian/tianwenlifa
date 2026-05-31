#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
司天学苑 - 本地离线版 CLI
"""
import sys
import json
from datetime import datetime

from .astronomy import (
    julian_day, julian_day_to_date, get_solar_term_jd,
    SOLAR_TERMS, local_time_to_true_solar,
)
from .lunar import solar_to_lunar, calculate_solar_terms, LunarDate
from .ganzhi import (
    year_gan_zhi, month_gan_zhi, day_gan_zhi, hour_gan_zhi,
    get_na_yin, TIAN_GAN, DI_ZHI, JIA_ZI, NA_YIN_TABLE,
)
from .bazi import calculate_bazi


def print_bazi_result(result: dict):
    """打印八字排盘结果"""
    print("=" * 50)
    print(f"  司天学苑 - 本地离线版八字排盘")
    print("=" * 50)

    info = result.get('input_info', {})
    if info:
        print(f"\n出生时间: {info.get('year')}年{info.get('month')}月{info.get('day')}日 "
              f"{info.get('hour')}:{info.get('minute') or '00'}")
        print(f"性    别: {info.get('gender', '')}")

    # 真太阳时
    if result.get('true_solar'):
        ts = result['true_solar']
        print(f"\n 真太阳时: {ts['true_solar_time']}")
        print(f"   时差方程: {ts.get('equation_of_time', 0):.2f}分钟")
        print(f"   经度修正: {ts.get('longitude_correction', 0):.2f}分钟")

    # 四柱
    print(f"\n  ┌──────┬──────┬──────┬──────┐")
    print(f"  │  年  │  月  │  日  │  时  │")
    print(f"  ├──────┼──────┼──────┼──────┤")
    print(f"  │  {result['year_pillar']}  │  {result['month_pillar']}  │  {result['day_pillar']}  │  {result['hour_pillar']}  │")
    print(f"  ├──────┼──────┼──────┼──────┤")
    print(f"  │{result['year_nayin']:^6}│{result['month_nayin']:^6}│{result['day_nayin']:^6}│{result['hour_nayin']:^6}│")
    print(f"  └──────┴──────┴──────┴──────┘")

    # 天干
    print(f"\n 天干: {result['year_gan']} {result['month_gan']} {result['day_gan']} {result['hour_gan']}")
    # 地支
    print(f" 地支: {result['year_zhi']} {result['month_zhi']} {result['day_zhi']} {result['hour_zhi']}")

    # 十神
    print(f"\n 十神:")
    print(f"  年干: {result.get('year_shi_shen', '')}")
    print(f"  月干: {result.get('month_shi_shen', '')}")
    print(f"  日干: {result.get('day_shi_shen', '')} ({result['day_gan']})")
    print(f"  时干: {result.get('hour_shi_shen', '')}")

    # 藏干
    print(f"\n 藏干:")
    if result.get('year_cang_gan'):
        cg = result['year_cang_gan']
        css = result.get('year_cang_gan_shi_shen', [])
        print(f"  年支{result['year_zhi']}: {', '.join(f'{g}({s})' for g, s in zip(cg, css))}")
    if result.get('month_cang_gan'):
        cg = result['month_cang_gan']
        css = result.get('month_cang_gan_shi_shen', [])
        print(f"  月支{result['month_zhi']}: {', '.join(f'{g}({s})' for g, s in zip(cg, css))}")
    if result.get('day_cang_gan'):
        cg = result['day_cang_gan']
        css = result.get('day_cang_gan_shi_shen', [])
        print(f"  日支{result['day_zhi']}: {', '.join(f'{g}({s})' for g, s in zip(cg, css))}")
    if result.get('hour_cang_gan'):
        cg = result['hour_cang_gan']
        css = result.get('hour_cang_gan_shi_shen', [])
        print(f"  时支{result['hour_zhi']}: {', '.join(f'{g}({s})' for g, s in zip(cg, css))}")

    # 日空
    if result.get('ri_kong'):
        print(f"\n 日空(旬空): {result['ri_kong']}")

    # 胎元
    if result.get('tai_yuan'):
        print(f"\n 胎元: {result['tai_yuan']} ({result.get('tai_yuan_nayin', '')})")

    # 命宫
    if result.get('ming_gong'):
        print(f"\n 命宫: {result['ming_gong']} ({result.get('ming_gong_nayin', '')})")

    # 身宫
    if result.get('shen_gong'):
        print(f"\n 身宫: {result['shen_gong']} ({result.get('shen_gong_nayin', '')})")

    # 生肖
    if result.get('sheng_xiao'):
        print(f"\n 生肖: {result['sheng_xiao']}")

    # 大运
    print(f"\n{'=' * 50}")
    print(f"  大运流年")
    print(f"{'=' * 50}")

    if result.get('qi_yun_info'):
        print(f"\n 起运: {result['qi_yun_info']}")
    if result.get('jiao_yun_date'):
        print(f" 交运: {result['jiao_yun_date']} (儒略日: {result.get('jiao_yun_jd', '')})")
    print(f" 顺逆: {'顺排' if result.get('forward_dayun') else '逆排'}")

    dayun_list = result.get('dayun_list', [])
    liunian_list = result.get('liunian_list', [])

    print(f"\n {'大运':^8} {'纳音':^8} {'十神':^8} {'年龄':^10} {'起始年份'}")
    print(f" {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 10} {'─' * 10}")
    for i, dy in enumerate(dayun_list):
        print(f" {dy['ganzhi']:^8} {dy['nayin']:^8} {dy['shi_shen']:^8} "
              f"{dy['age_start']}~{dy['age_end'] - 1}岁  {dy['year_start']}年")

    # 流年
    print(f"\n 流年:")
    for i, dy in enumerate(dayun_list):
        print(f"  【{dy['ganzhi']}大运 {dy['age_start']}~{dy['age_end'] - 1}岁】")
        if i < len(liunian_list):
            lns = liunian_list[i]
            ln_text = ' '.join([f"{ln['ganzhi']}({ln['shi_shen']})" for ln in lns])
            print(f"    {ln_text}")

    print(f"\n{'=' * 50}")


def run_cli():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='司天学苑 - 本地离线版八字排盘')
    parser.add_argument('--year', type=int, required=True, help='公历年份')
    parser.add_argument('--month', type=int, required=True, help='公历月份')
    parser.add_argument('--day', type=int, required=True, help='公历日期')
    parser.add_argument('--hour', type=int, required=True, help='出生小时 (0-23)')
    parser.add_argument('--minute', type=int, default=0, help='出生分钟')
    parser.add_argument('--gender', type=str, default='男', choices=['男', '女'], help='性别')
    parser.add_argument('--longitude', type=float, help='出生地经度 (东经), 用于真太阳时')
    parser.add_argument('--timezone', type=int, default=8, help='时区 (默认东八区)')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出')

    args = parser.parse_args()

    result = calculate_bazi(
        year=args.year,
        month=args.month,
        day=args.day,
        hour=args.hour,
        minute=args.minute,
        gender=args.gender,
        longitude=args.longitude,
        timezone_offset=args.timezone,
    )

    result['input_info'] = {
        'year': args.year,
        'month': args.month,
        'day': args.day,
        'hour': args.hour,
        'minute': args.minute,
        'gender': args.gender,
    }

    if args.json:
        # 清理不可JSON序列化的内容
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(i) for i in obj]
            return obj
        print(json.dumps(clean_for_json(result), ensure_ascii=False, indent=2))
    else:
        print_bazi_result(result)


def interactive():
    """交互式输入"""
    print("=" * 50)
    print("  司天学苑 - 本地离线版 v1.0")
    print("  输入出生信息进行八字排盘")
    print("=" * 50)

    try:
        year = int(input("\n公历年份: "))
        month = int(input("公历月份: "))
        day = int(input("公历日期: "))
        hour = int(input("出生小时 (0-23): "))
        minute_input = input("出生分钟 (回车=0): ")
        minute = int(minute_input) if minute_input.strip() else 0
        gender = input("性别 (男/女, 默认男): ") or '男'
        lon_input = input("出生地经度 (东经, 回车跳过): ")
        longitude = float(lon_input) if lon_input.strip() else None
    except KeyboardInterrupt:
        print("\n\n已取消")
        return
    except ValueError as e:
        print(f"\n输入格式错误: {e}")
        return

    result = calculate_bazi(
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        gender=gender, longitude=longitude,
    )
    result['input_info'] = {
        'year': year, 'month': month, 'day': day,
        'hour': hour, 'minute': minute, 'gender': gender,
    }
    print_bazi_result(result)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_cli()
    else:
        interactive()
