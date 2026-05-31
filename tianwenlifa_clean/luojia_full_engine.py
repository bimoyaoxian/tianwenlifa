#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
落甲历完整引擎
基于API数据验证的360天周期历法系统

历元: 1962-02-05 04:00 UTC (JD 2437700.16667)

年柱: 原版网站JS算法
   cycleOffset = Math.floor((jd - 2437700.16667) / 360)
   cycleOffset=0 → 甲寅岁

月柱: 累积节气法 (纯天文, 零查表)
   月支 = 节气区间直接映射 (立春→寅, 惊蛰→卯, ...)
   月柱 = JIA_ZI[(49 + 累积跨过的节气数) % 60]
   49 = 历元时刻的月柱(癸丑), 从API数据反推验证

日柱: (int(jd + 0.5) + 49) % 60
时柱: 五鼠遁
"""
import math
from calendar_engine.astronomy import julian_day, get_solar_term_jd
from calendar_engine.ganzhi import TIAN_GAN, DI_ZHI, JIA_ZI

# ============================================================
# 历元
# ============================================================
NEW_JIAZI_BASE_JD = 2437700.16667  # 年柱历元 (原版网站)
EPOCH_JD = julian_day(1962, 2, 5)  # 2437700.5, 月柱的整数天计数用

# ============================================================
# 主节气(立春/惊蛰/...) → 月支映射
# 立春(term 2)→寅(2), 惊蛰(4)→卯(3), 清明(6)→辰(4), ...
# ============================================================
_MAJOR_TERMS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
_TERM_TO_BRANCH = {0:1, 2:2, 4:3, 6:4, 8:5, 10:6, 12:7, 14:8, 16:9, 18:10, 20:11, 22:0}

# 历元时刻的月柱索引 (从30组API数据反推)
EPOCH_MONTH_PILLAR = 49  # JIA_ZI[49] = 癸丑


def _count_terms_since_epoch(jd: float) -> int:
    """统计从历元JD到目标JD之间跨过的节气数 (正=往后, 负=往前)"""
    epoch_jd = NEW_JIAZI_BASE_JD
    from calendar_engine.astronomy import julian_day_to_date
    yy, _, _, _ = julian_day_to_date(jd)
    ref_year = int(yy)
    epoch_year = 1962
    start_year = min(ref_year, epoch_year) - 5
    end_year = max(ref_year, epoch_year) + 5
    
    if jd >= epoch_jd:
        count = 0
        for yr in range(start_year, end_year + 1):
            for ti in _MAJOR_TERMS:
                tj = get_solar_term_jd(yr, ti)
                if epoch_jd <= tj < jd:
                    count += 1
                elif tj >= jd:
                    break
        return count
    else:
        # 反向: 找jd之前最近的主节气(T)和epoch前最后一个主节气(L)
        # 统计[T, L]区间内的节气数(闭区间)
        nearest_t_before = None
        last_before_epoch = None
        for yr in range(start_year, end_year + 1):
            for ti in _MAJOR_TERMS:
                tj = get_solar_term_jd(yr, ti)
                if tj <= jd:
                    nearest_t_before = tj
                if tj < epoch_jd:
                    last_before_epoch = tj
                if tj >= epoch_jd:
                    break
        if nearest_t_before is None:
            return 0
        
        count = 0
        for yr in range(start_year, end_year + 1):
            for ti in _MAJOR_TERMS:
                tj = get_solar_term_jd(yr, ti)
                if nearest_t_before < tj < last_before_epoch:
                    count += 1
                elif tj >= last_before_epoch:
                    break
        return -count


def _get_luojia_month_branch(year: int, month: int, day: int) -> int:
    """天文计算落甲历月支
    月支 = 节气区间直接映射 (无偏移)
    立春→寅(2), 惊蛰→卯(3), ..., 大寒→丑(1)
    """
    jd = julian_day(year, month, day)
    for ti in _MAJOR_TERMS:
        tj = get_solar_term_jd(year, ti)
        nti = (ti + 2) % 24
        ny = year + 1 if nti < ti else year
        ntj = get_solar_term_jd(ny, nti)
        if tj <= jd < ntj:
            return _TERM_TO_BRANCH[ti]
    # 年初: 在上一年末
    for ti in [22, 0]:
        tj = get_solar_term_jd(year - 1, ti)
        nti = (ti + 2) % 24
        ntj = get_solar_term_jd(year, nti) if nti > ti else get_solar_term_jd(year, nti)
        if tj <= jd < ntj:
            return _TERM_TO_BRANCH[ti]
    raise ValueError(f"找不到节气区间: {year}-{month}-{day}")


def _get_yi_mi(year: int, month: int, day: int):
    """计算积年yi和积月mi"""
    target_jd = julian_day(year, month, day)
    days = int(target_jd - EPOCH_JD + 0.5)
    yi = days // 360
    mi = (days % 360) // 30
    return yi, mi


def get_luojia_year(year: int, month: int, day: int) -> str:
    """落甲历年柱 (原版JS算法)"""
    jd = julian_day(year, month, day)
    cycle_offset = int(math.floor((jd - NEW_JIAZI_BASE_JD) / 360))
    return JIA_ZI[(cycle_offset + 50) % 60]


def get_luojia_month(year: int, month: int, day: int) -> str:
    """落甲历月柱 (累积节气法, 零查表)

    原理: 统计从历元(1962-02-05 04:00 UTC)到目标日期之间
         跨过了多少个主节气(立春/惊蛰/清明/立夏/芒种/小暑/
         立秋/白露/寒露/立冬/大雪/小寒),
         每个节气跨过=进入下一个月。
    公式: 月柱 = JIA_ZI[(49 + 累计节气数) % 60]
    """
    jd = julian_day(year, month, day)
    n_terms = _count_terms_since_epoch(jd)
    return JIA_ZI[(EPOCH_MONTH_PILLAR + n_terms) % 60]


def get_luojia_day(year: int, month: int, day: int) -> str:
    """落甲历日柱"""
    jd = julian_day(year, month, day)
    return JIA_ZI[(int(jd + 0.5) + 49) % 60]


def get_luojia_hour(day_gan_idx: int, hour: int) -> str:
    """落甲历时柱（五鼠遁）"""
    zhi = (hour + 1) // 2 % 12
    gan_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
               5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
    gan = (gan_map[day_gan_idx % 10] + zhi) % 10
    return TIAN_GAN[gan] + DI_ZHI[zhi]


def get_bazi(year: int, month: int, day: int, hour: int = 12) -> dict:
    """获取完整八字"""
    ygz = get_luojia_year(year, month, day)
    mgz = get_luojia_month(year, month, day)
    dgz = get_luojia_day(year, month, day)
    day_gan_idx = TIAN_GAN.index(dgz[0])
    hgz = get_luojia_hour(day_gan_idx, hour)
    return {
        'year_pillar': ygz,
        'month_pillar': mgz,
        'day_pillar': dgz,
        'hour_pillar': hgz,
    }
