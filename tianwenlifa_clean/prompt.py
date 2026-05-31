#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘 + AI提示词 单文件入口
================================
一键算出八字、胎元、命宫、身宫、大运流年、五运六气、天象，
按 mode 切换不同输出内容。

用法:
    # 默认输出 AI 提示词
    python bazi_prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男

    # 不同输出模式
    python bazi_prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男 --mode bazi
    python bazi_prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男 --mode detail
    python bazi_prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男 --mode tianwen
    python bazi_prompt.py --year 1990 --month 6 --day 15 --hour 8 --gender 男 --mode full

    作为模块导入:
        from bazi_prompt import bazi
        print(bazi(1990, 6, 15, 8, output='prompt'))
        print(bazi(1990, 6, 15, 8, output='bazi'))
        print(bazi(1990, 6, 15, 8, output='detail'))
        print(bazi(1990, 6, 15, 8, output='tianwen'))
        print(bazi(1990, 6, 15, 8, output='full'))
        data = bazi(1990, 6, 15, 8, output='json')
"""

import sys
import json
from datetime import datetime

from calendar_engine.bazi import calculate_bazi
from calendar_engine.luojia_calendar import get_luojia_bazi
from calendar_engine.lunar import solar_to_lunar
from calendar_engine.ganzhi import DI_ZHI


def _calc(year, month, day, hour, minute, gender, longitude, system, timezone_offset):
    """统一计算，返回完整结果 dict"""
    hour_unknown = (hour is None)
    if system == 'luojia':
        r = get_luojia_bazi(year, month, day, hour, minute, gender, 1, longitude, timezone_offset)
        from calendar_engine.dayun import calculate_dayun
        dy = calculate_dayun(year, month, day, hour, minute, 0, gender,
                            year, r['year_pillar'], r['month_pillar'],
                            r['day_pillar'], r['hour_pillar'], longitude)
        r.update(dy)
        r['system_name'] = '落甲历'
    else:
        actual_hour = 12 if hour_unknown else hour
        r = calculate_bazi(year, month, day, actual_hour, minute, 0, gender, longitude, timezone_offset)
        if hour_unknown:
            for k in ['hour_pillar', 'hour_nayin', 'hour_shi_shen']:
                r[k] = '' if k == 'hour_pillar' else ''
            r['hour_gan'] = '*'; r['hour_zhi'] = '*'
            r['hour_cang_gan'] = []; r['hour_cang_gan_shi_shen'] = []
        from calendar_engine.dayun import calculate_dayun
        dy = calculate_dayun(year, month, day, hour, minute, 0, gender,
                            r.get('bazi_year', year), r['year_pillar'], r['month_pillar'],
                            r['day_pillar'], r['hour_pillar'], longitude, mode='standard')
        r.update(dy)
        r['system_name'] = '标准历法'
    lunar = solar_to_lunar(year, month, day)
    r['lunar_month'] = lunar.month_name
    r['lunar_day'] = lunar.day_name
    r['input_info'] = {'year': year, 'month': month, 'day': day,
                       'hour': hour, 'minute': minute, 'gender': gender}
    return r


def _now_info(r, age, cy, cm, cd):
    """返回 (cur_ln_txt, cur_ly_txt, cur_di, next_ly_list)"""
    cur_di = -1
    for i, d in enumerate(r.get('dayun_list', [])):
        if d['age_start'] <= age <= d['age_end'] - 1:
            cur_di = i
            break
    cur_ln = None
    if r.get('liunian_list') and cur_di >= 0:
        cur_ln = next((l for l in r['liunian_list'][cur_di] if l['year'] == cy), None)
    cur_ln_txt = ''
    cur_ly_txt = ''
    next_ly_list = []
    if cur_ln:
        cur_ln_txt = f"{cur_ln['ganzhi']}（{cy}年）{cur_ln['start_date']} ~ {cur_ln['end_date']}"
        today = f"{cy}-{cm:02d}-{cd:02d}"
        cur_ly = next((m for m in cur_ln.get('liuyue', []) if today >= m['start_date'] and today <= m['end_date']), None)
        if cur_ly:
            cur_ly_txt = f"{cur_ly['ganzhi']}月　{cur_ly['start_date']} ~ {cur_ly['end_date']}"
        else:
            cur_ly_txt = f"{cm}月（不在流月范围内）"
        # 后续流月（当前流月之后、同流年内的剩余月份）
        found = False
        for m in cur_ln.get('liuyue', []):
            if m['ganzhi'] == (cur_ly['ganzhi'] if cur_ly else None) and not found:
                found = True
                continue
            if found:
                next_ly_list.append(m)
    else:
        cur_ln_txt = f"{cy}年{cm}月{cd}日"
    return cur_ln_txt, cur_ly_txt, cur_di, next_ly_list


def _format_bazi(r, hour_unknown):
    """八字简表"""
    if hour_unknown:
        return f"{r['year_pillar']} {r['month_pillar']} {r['day_pillar']} 时辰未知"
    return f"{r['year_pillar']} {r['month_pillar']} {r['day_pillar']} {r['hour_pillar']}"


def _format_detail(r, hour_unknown):
    """完整排盘：八字+纳音+藏干十神+胎元+命宫+身宫+空亡+大运+流年流月"""
    now = datetime.now()
    cy, cm, cd = now.year, now.month, now.day
    info = r.get('input_info', {})
    age = cy - info.get('year', cy)
    cur_ln_txt, cur_ly_txt, cur_di, next_lys = _now_info(r, age, cy, cm, cd)

    lines = [f"八字：{_format_bazi(r, hour_unknown)}"]
    nayin = ' '.join(filter(None, [r.get('year_nayin',''), r.get('month_nayin',''),
                                    r.get('day_nayin',''), '' if hour_unknown else r.get('hour_nayin','')]))
    lines.append(f"纳音：{nayin}")
    for p in ['year', 'month', 'day', 'hour']:
        zhi = r.get(f'{p}_zhi', '')
        cg = r.get(f'{p}_cang_gan', [])
        ss = r.get(f'{p}_cang_gan_shi_shen', [])
        if cg:
            parts = [f"{g}({s})" for g, s in zip(cg, ss)] if ss else list(cg)
            lines.append(f"{zhi}藏：{' '.join(parts)}")
    for label, key, nkey in [('胎元','tai_yuan','tai_yuan_nayin'),('命宫','ming_gong','ming_gong_nayin'),('身宫','shen_gong','shen_gong_nayin')]:
        if r.get(key):
            n = f"（{r.get(nkey,'')}）" if r.get(nkey) else ''
            lines.append(f"{label}：{r[key]}{n}")
    if r.get('ri_kong'):
        lines.append(f"空亡：{r['ri_kong']}")
    if r.get('sheng_xiao'):
        lines.append(f"生肖：{r['sheng_xiao']}")
    if r.get('true_solar'):
        ts = r['true_solar']
        lines.append(f"真太阳时：{ts.get('true_solar_time','')}  时差：{ts.get('equation_of_time',0):.1f}分")
    # 大运
    if r.get('dayun_list'):
        dy_parts = []
        for i, d in enumerate(r['dayun_list']):
            mark = '←当前' if i == cur_di else ''
            dy_parts.append(f"{d['ganzhi']}（{d['age_start']}~{d['age_end']-1}岁）{mark}")
        lines.append(f"大运：{' '.join(dy_parts)}")
    # 当前流年流月 + 后续流月
    if cur_ln_txt:
        lines.append(f"当前流年：{cur_ln_txt}")
    if cur_ly_txt:
        lines.append(f"当前流月：{cur_ly_txt}")
    for m in next_lys:
        lines.append(f"　　　{m['ganzhi']}月　{m['start_date']} ~ {m['end_date']}")
    return '\n'.join(lines)


def _format_tianwen(year, month, day, r=None, system='luojia'):
    """天文信息：五运六气 + 木星天象 + 日月位置"""
    from calendar_engine.wuyun_liuqi import get_wuyun_liuqi_info
    from calendar_engine.astronomy import julian_day, get_solar_system_positions

    luo_year = r['year_pillar'] if r and r.get('year_pillar') else None
    wlq = get_wuyun_liuqi_info(year, month, day, luo_year_pillar=luo_year)

    lines = []
    # 五运六气
    lines.append(f"岁运：{wlq.get('sui_yun','')}")
    lines.append(f"司天：{wlq.get('si_tian','')}　在泉：{wlq.get('zai_quan','')}")
    lines.append(f"主气：{wlq.get('zhu_qi','')}（{wlq.get('zhu_qi_period','')}）")
    lines.append(f"主运：{wlq.get('zhu_yun','')}")
    lines.append(f"年支经络：{wlq.get('foot_jingluo','')}　月支经络：{wlq.get('hand_jingluo','')}")

    # 天象
    if wlq.get('dou_jian_text'):
        lines.append(f"斗建/星次：{wlq.get('dou_jian_text','')}　{wlq.get('xingci_text','')}")
    if wlq.get('tianxiang'):
        lines.append(f"天象：{wlq.get('tianxiang','')}")

    # 太阳系行星位置
    jd = julian_day(year, month, day)
    try:
        planets = get_solar_system_positions(jd)
        lines.append("")
        lines.append("【太阳系】")
        for p in planets:
            lines.append(f"  {p.get('name_cn','')}：黄经{p.get('helio_lon',0):.1f}° 距{p.get('distance',0):.2f}AU")
    except Exception:
        pass
    return '\n'.join(lines)


def _format_prompt(r, year, month, day, hour, minute, gender, system):
    """完整 AI 分析提示词"""
    hour_unknown = (hour is None)
    by, bm, bd = year, month, day
    bh = hour
    now = datetime.now()
    cy, cm, cd = now.year, now.month, now.day
    age = cy - by
    cur_ln_txt, cur_ly_txt, cur_di, next_lys = _now_info(r, age, cy, cm, cd)

    # 大运表
    dy_lines = ''
    for i, d in enumerate(r.get('dayun_list', [])):
        aS, aE = d['age_start'], d['age_end'] - 1
        is_cur = (i == cur_di)
        dy_lines += f"{i+1}. {d['ganzhi']}（{aS}~{aE}岁）　{d['start_date']} ~ {d['end_date']}{' ←当前大运' if is_cur else ''}\n"
        lns = r.get('liunian_list', [])[i] if i < len(r.get('liunian_list', [])) else None
        if lns:
            cur_year_lns = []
            for l in lns:
                mark = ' ←当前流年' if (is_cur and l['year'] == cy) else ''
                cur_year_lns.append(f"{l['ganzhi']}({l['year']}){l['start_date']}~{l['end_date']}{mark}")
            dy_lines += f"  　流年：{'、'.join(cur_year_lns)}\n"

    birth_time_str = '时辰未知' if hour_unknown else f"{bh:02d}:00"
    pillar_str = _format_bazi(r, hour_unknown)
    nayin_str = ' '.join(filter(None, [r.get('year_nayin',''), r.get('month_nayin',''),
                                        r.get('day_nayin',''), '(时辰未知)' if hour_unknown else r.get('hour_nayin','')]))

    txt = '你是一名资深命理师，请根据以下内容，合理分析八字。\n\n'
    if system == 'luojia':
        txt += '注意：以下八字排盘使用的是落甲历（岁星天文历法），以岁星(木星)运行为依据，\n'
        txt += '每个流年为一个落甲历年（约360天周期），并非公历自然年或节气年。\n'
        txt += '请按此天文历法体系分析，勿按常规节气年理解流年大运的交替规则。\n\n'
    else:
        txt += '\n'
    txt += '【基本信息】\n'
    txt += f'{gender}命\n'
    txt += f'出生：{by}年{bm}月{bd}日 {birth_time_str}\n'
    txt += f'八字：{pillar_str}\n'
    txt += f'纳音：{nayin_str}\n'
    if hour_unknown:
        txt += '注意：此八字时辰未知，时柱以"时辰未知"代替。\n'
        txt += '大运起运时间通过遍历12个时辰取众数（按月取整）计算。\n'
        txt += '请先向用户询问过去具体发生的几件事情，反推可能的出生时辰，\n'
        txt += '确认后再根据反推结果重新校准大运流年。\n'
    if r.get('tai_yuan'):
        n = f"（{r.get('tai_yuan_nayin','')}）" if r.get('tai_yuan_nayin') else ''
        txt += f"胎元：{r['tai_yuan']}{n}\n"
    if r.get('ming_gong'):
        n = f"（{r.get('ming_gong_nayin','')}）" if r.get('ming_gong_nayin') else ''
        txt += f"命宫：{r['ming_gong']}{n}\n"
    if r.get('shen_gong'):
        n = f"（{r.get('shen_gong_nayin','')}）" if r.get('shen_gong_nayin') else ''
        txt += f"身宫：{r['shen_gong']}{n}\n"
    if r.get('ri_kong'):
        txt += f"空亡：{r['ri_kong']}\n"
    if r.get('jiao_yun_date'):
        txt += f"交运时间：{r['jiao_yun_date']}\n"
    if r.get('qi_yun_info'):
        txt += f"起运：{r['qi_yun_info']}" + ('（12时辰众数估算）' if hour_unknown else '') + '\n'
    txt += f'\n【大运时间表（含每一步内的全部流年）】\n{dy_lines}'
    txt += f'\n【当前流年】{cur_ln_txt}\n'
    if cur_ly_txt:
        txt += f'【当前月份】{cur_ly_txt}\n'
    for m in next_lys:
        txt += f'  后续：{m["ganzhi"]}月　{m["start_date"]} ~ {m["end_date"]}\n'
    txt += '\n请使用禄命法以及子平法，综合看此八字。\n'
    txt += '首先，请先询问我过去具体所发生的五件事情，校准模型。\n'
    txt += '然后，询问我需要问什么问题。\n'
    txt += '以上请用白话文直接询问。\n'
    return txt


def bazi(year, month, day, hour=None, minute=0, gender='男',
         longitude=None, system='luojia', timezone_offset=8,
         output='prompt'):
    """
    八字排盘 — 按 output 参数返回不同内容

    参数:
        year, month, day: 公历出生日期
        hour: 出生小时 0-23, None=未知时辰
        minute: 分钟, 默认0
        gender: '男' 或 '女'
        longitude: 东经度, 默认None(不算真太阳时)
        system: 'luojia'(默认) 或 'standard'
        timezone_offset: 时区偏移, 默认东八区

        output: 输出模式 —
            'prompt'  - AI提示词 (默认, 八字+大运流年+分析指引)
            'bazi'    - 八字简表 (仅四柱+纳音)
            'detail'  - 完整排盘 (四柱+纳音+藏干十神+胎元命宫身宫+大运+当前流年流月)
            'tianwen' - 天文信息 (五运六气+木星天象+太阳系行星位置)
            'full'    - 全部信息 (detail + tianwen + 流年流月)
            'json'    - Python dict (原始数据)

    返回: str 或 dict (output='json'时)
    """
    r = _calc(year, month, day, hour, minute, gender, longitude, system, timezone_offset)
    hour_unknown = (hour is None)

    if output == 'bazi':
        info = r.get('input_info', {})
        birth = f"{info.get('year')}-{info.get('month'):02d}-{info.get('day'):02d}"
        bt = '未知' if hour_unknown else f"{hour:02d}:00"
        return f"{info.get('gender','')}命 {birth} {bt}\n{_format_bazi(r, hour_unknown)}"
    elif output == 'detail':
        return _format_detail(r, hour_unknown)
    elif output == 'tianwen':
        return _format_tianwen(year, month, day, r, system)
    elif output == 'full':
        parts = [_format_detail(r, hour_unknown), '', _format_tianwen(year, month, day, r, system)]
        return '\n'.join(parts)
    elif output == 'json':
        return r
    else:  # prompt (default)
        return _format_prompt(r, year, month, day, hour, minute, gender, system)


# ── CLI ──

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='八字排盘 — 可按需输出八字/排盘/天象/AI提示词')
    parser.add_argument('--year', type=int, required=True, help='公历年份')
    parser.add_argument('--month', type=int, required=True, help='公历月份')
    parser.add_argument('--day', type=int, required=True, help='公历日期')
    parser.add_argument('--hour', type=int, default=None, help='出生小时 0-23, 留空=未知时辰')
    parser.add_argument('--minute', type=int, default=0, help='出生分钟')
    parser.add_argument('--gender', type=str, default='男', choices=['男', '女'], help='性别')
    parser.add_argument('--longitude', type=float, default=None, help='东经度 (不填不算真太阳时)')
    parser.add_argument('--system', type=str, default='luojia', choices=['luojia', 'standard'], help='历法系统')
    parser.add_argument('--mode', type=str, default='prompt',
                        choices=['prompt', 'bazi', 'detail', 'tianwen', 'full', 'json'],
                        help='prompt=AI提示词(默认), bazi=八字简表, detail=完整排盘, tianwen=天文信息, full=全部, json=原始数据')
    args = parser.parse_args()

    result = bazi(args.year, args.month, args.day, args.hour,
                  args.minute, args.gender, args.longitude,
                  args.system, output=args.mode)

    if args.mode == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(result)


if __name__ == '__main__':
    main()
