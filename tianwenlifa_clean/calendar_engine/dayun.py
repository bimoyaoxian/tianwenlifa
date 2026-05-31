#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大运流年模块 - 落甲历系统

核心算法:
  - 年柱: 固定360天公式 (原版JS evaluateNewJiaziAndPhase)
    cycleOffset = floor((jd - 2437700.16667) / 360)
    年柱 = JIA_ZI[(50 + cycleOffset) % 60]

  - 天文历法月柱: 节气累积法 (匹配实际节气, 用于日历显示)
    月柱 = JIA_ZI[(49 + n_terms) % 60]

  - 大运: 每步3600天 = 10个落甲历年
  - 流年: 每段360天 = 1个落甲历年 (固定360天, 非立春)
  - 流月: 每段30天, 月柱用固定30天公式
    流月月柱 = JIA_ZI[(49 + floor((jd - 历元JD) / 30)) % 60]

  历元: 1962-02-05 04:00 UTC (JD 2437700.16667)
  日柱=甲戌 → "甲戌换年首"

  mode='luojia' (默认): 落甲历, 流年=360天块, 流月=30天块
  mode='standard': 标准历法, 流年=立春至立春, 流月=节气边界
"""
from .astronomy import julian_day, julian_day_to_date, get_solar_term_jd
from .ganzhi import (
    get_shi_shen, TIAN_GAN, DI_ZHI, JIA_ZI, NA_YIN_TABLE, year_gan_zhi,
    month_gan_zhi,
)

# 落甲历历元 (原版JS evaluateNewJiaziAndPhase)
_NEW_JIAZI_BASE_JD = 2437700.16667

# 主节气(立春/惊蛰/...) → 月柱计算用
_MAJOR_TERMS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]


def _luo_year_count(jd: float) -> int:
    """落甲历年计数: floor((jd - 历元JD) / 360)
    历元 1962-02-05 时计数=0 → 甲寅(50)
    原版JS: cycleOffset = Math.floor((jd - 2437700.16667) / 360)
    """
    return int((jd - _NEW_JIAZI_BASE_JD) // 360)


def _luo_year_at(jd: float) -> str:
    """落甲历年柱 at JD (固定360天公式)"""
    return JIA_ZI[(50 + _luo_year_count(jd)) % 60]


def _luo_month_at(jd: float) -> str:
    """
    落甲历月柱 at JD (节气累积法)
    委托 luojia_calendar._count_terms_since_epoch 实现（已验证 30/30 匹配API）
    """
    from .luojia_calendar import _count_terms_since_epoch
    count = _count_terms_since_epoch(jd)
    return JIA_ZI[(49 + count) % 60]


def calculate_dayun(year: int, month: int, day: int,
                    hour: int = None, minute: int = 0, second: int = 0,
                    gender: str = '男', bazi_year: int = None,
                    year_pillar: str = '', month_pillar: str = '',
                    day_pillar: str = '', hour_pillar: str = None,
                    longitude: float = None,
                    timezone_offset: int = 8,
                    mode: str = 'luojia') -> dict:
    """
    计算大运流年

    规则:
      阳男阴女 -> 顺排 (月柱往后推)
      阴男阳女 -> 逆排 (月柱往前推)
      阳: 甲丙戊庚壬(索引0,2,4,6,8), 阴: 乙丁己辛癸(1,3,5,7,9)

    大运: 每步3600天

    mode='luojia': 流年=360天块, 流月=30天块
    mode='standard': 流年=立春至立春, 流月=节气边界
    """
    # 1. 年干阴阳 → 用落甲历年干（匹配原版API）
    #    落甲历年柱由外部传入(year_pillar)
    #    阳=甲丙戊庚壬(偶索引), 阴=乙丁己辛癸(奇索引)
    year_gan = year_pillar[0]
    std_gan_idx = TIAN_GAN.index(year_gan)
    is_yang = (std_gan_idx % 2 == 0)

    # 2. 顺逆
    if (is_yang and gender == '男') or (not is_yang and gender == '女'):
        forward = True
    else:
        forward = False

    hour_unknown = (hour is None)

    # 月支对应的节气边界 (传统起运算法)
    month_zhi = month_pillar[1]
    month_zhi_idx = DI_ZHI.index(month_zhi) if month_zhi in DI_ZHI else 0

    month_start_term = {0: 22, 1: 0, 2: 2, 3: 4, 4: 6, 5: 8,
                        6: 10, 7: 12, 8: 14, 9: 16, 10: 18, 11: 20}
    month_end_term = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 10,
                      6: 12, 7: 14, 8: 16, 9: 18, 10: 20, 11: 22}

    start_term_idx = month_start_term.get(month_zhi_idx, 2)
    end_term_idx = month_end_term.get(month_zhi_idx, 4)

    # 节气JD → 用Kepler精确模型(匹配原版API), 取精确节气时间JD
    def _term_exact(yr, ti):
        return get_solar_term_jd(yr, ti)

    def _calc_qi_yun(h, m, s):
        """根据具体时辰计算起运值"""
        jd = julian_day(year, month, day) + (h - timezone_offset + m / 60.0 + s / 3600.0) / 24.0

        if forward:
            t_start = _term_exact(bazi_year, start_term_idx)
            t_end = _term_exact(bazi_year, end_term_idx)
            if t_end <= jd:
                if jd - t_end < 1.0:
                    t_end = jd
                else:
                    t_end = _term_exact(bazi_year + 1, end_term_idx)
        else:
            t_end = _term_exact(bazi_year, end_term_idx)
            t_start = _term_exact(bazi_year, start_term_idx)
            if t_start >= jd:
                if t_start - jd < 1.0:
                    t_start = jd
                else:
                    t_start = _term_exact(bazi_year - 1, start_term_idx)

        dtt = (t_end - jd) if forward else (jd - t_start)
        if dtt < 0:
            dtt = 0

        yy = int(dtt / 3)
        rd = dtt - yy * 3
        mm = int(rd * 4)
        dd = round((rd * 4 - mm) * 30)

        tz = timezone_offset / 24.0
        jdj = jd + dtt * 120
        jy, jm, jd_, _ = julian_day_to_date(jdj + tz)
        return yy, mm, dd, jd, dtt, jdj, jy, jm, jd_

    # 时辰未知处理：遍历12个时辰，取起运（按月取整）的众数
    if hour_unknown:
        shichen_hours = [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
        candidates = []
        for sh in shichen_hours:
            yy, mm, dd, _, _, _, _, _, _ = _calc_qi_yun(sh, 0, 0)
            total_m = yy * 12 + mm
            candidates.append((total_m, yy, mm, dd, sh))

        from collections import Counter
        mode_val = Counter(c[0] for c in candidates).most_common(1)[0][0]
        # 取第一个匹配众数的时辰
        match = next(c for c in candidates if c[0] == mode_val)
        _, qi_yun_years, qi_yun_months, qi_yun_days, mode_hour = match

        hour = mode_hour
        minute = 0
        second = 0

    # 正式计算（已知时辰或已选定众数时辰）
    qi_yun_years, qi_yun_months, qi_yun_days, jd_birth, days_to_term, jiao_yun_jd, jiao_yun_y, jiao_yun_m, jiao_yun_d = \
        _calc_qi_yun(hour, minute, second)

    # 时区调整量 (JD转本地日期用)
    tz_adj = timezone_offset / 24.0

    # 7. 排大运 (8步, 每步3600天 = 10个落甲历年)
    month_gz_idx = JIA_ZI.index(month_pillar)

    dayun_list = []
    for i in range(8):
        if forward:
            step_gz_idx = (month_gz_idx + (i + 1)) % 60
        else:
            step_gz_idx = (month_gz_idx - (i + 1)) % 60

        dayun_ganzhi = JIA_ZI[step_gz_idx]

        step_start_jd = jiao_yun_jd + i * 3600
        step_end_jd = jiao_yun_jd + (i + 1) * 3600 - 1

        sy, sm, sd, _ = julian_day_to_date(step_start_jd + tz_adj)
        ey, em, ed, _ = julian_day_to_date(step_end_jd + tz_adj)

        age_start = qi_yun_years + i * 10
        age_end = qi_yun_years + (i + 1) * 10

        dayun_list.append({
            'index': i,
            'ganzhi': dayun_ganzhi,
            'nayin': NA_YIN_TABLE.get(dayun_ganzhi, ''),
            'age_start': age_start,
            'age_end': age_end,
            'year_start': sy,
            'year_end': ey,
            'start_date': f"{sy}-{sm:02d}-{sd:02d}",
            'end_date': f"{ey}-{em:02d}-{ed:02d}",
            'start_jd': round(step_start_jd, 4),
            'end_jd': round(step_end_jd, 4),
            'shi_shen': get_shi_shen(JIA_ZI.index(day_pillar) % 10, step_gz_idx % 10),
        })

    # 8. 流年 + 流月
    #   落甲历: 按落甲历年首(360天块)对齐
    #   标准历法: 以立春(节气索引2)为界
    liunian_list = []
    ri_gan_idx = JIA_ZI.index(day_pillar) % 10

    for i in range(8):
        dy_start_jd = jiao_yun_jd + i * 3600
        dy_end_jd = dy_start_jd + 3599
        liunian = []

        if mode == 'standard':
            # === 标准历法: 流年以立春为界 ===
            sy, _, _, _ = julian_day_to_date(dy_start_jd + tz_adj)
            ey, _, _, _ = julian_day_to_date(dy_end_jd + tz_adj)
            lichun_jds = []
            for yr in range(int(sy) - 1, int(ey) + 2):
                lj = get_solar_term_jd(yr, 2)
                if dy_start_jd <= lj <= dy_end_jd:
                    lichun_jds.append((yr, lj))
            lichun_jds.sort(key=lambda x: x[1])
            boundaries = [(dy_start_jd, None)]
            for yr, lj in lichun_jds:
                boundaries.append((lj, yr))
            boundaries.append((dy_end_jd + 1, None))
            for ln_i in range(len(boundaries) - 1):
                ln_s = boundaries[ln_i][0]
                ln_e = boundaries[ln_i+1][0] - 1
                _, by = boundaries[ln_i]
                if by is None and lichun_jds:
                    by = lichun_jds[0][0] - 1
                elif by is None:
                    y, _, _, _ = julian_day_to_date(ln_s + tz_adj)
                    by = int(y)
                gz = year_gan_zhi(by)
                gi = JIA_ZI.index(gz) % 10
                # 流月: 按节气分割, 月柱用五虎遁 (标准历法)
                #   五虎遁: month_gan_zhi(年干, 月份), 寅=1,卯=2,...,丑=12
                #   项目内 SOLAR_TERMS 索引: 0小寒,2立春,4惊蛰,6清明,
                #     8立夏,10芒种,12小暑,14立秋,16白露,18寒露,20立冬,22大雪
                #   节气索引→月份: 小寒(0)=丑月(12), 立春(2)=寅月(1),
                #     惊蛰(4)=卯月(2), ..., 大雪(22)=子月(11)
                _TERM_TO_MONTH = {0:12, 2:1, 4:2, 6:3, 8:4, 10:5,
                                  12:6, 14:7, 16:8, 18:9, 20:10, 22:11}
                # 节气前一月: 小寒前=子月(11), 立春前=丑月(12), ...
                _PREV_MONTH = {0:11, 2:12, 4:1, 6:2, 8:3, 10:4,
                               12:5, 14:6, 16:7, 18:8, 20:9, 22:10}
                # 查找流年内所有主节气
                sy_m, _, _, _ = julian_day_to_date(ln_s + tz_adj)
                ey_m, _, _, _ = julian_day_to_date(ln_e + tz_adj)
                tlist = []
                for yr in range(int(sy_m) - 1, int(ey_m) + 2):
                    for ti in _MAJOR_TERMS:
                        tj = get_solar_term_jd(yr, ti)
                        if ln_s <= tj <= ln_e:
                            tlist.append((ti, tj))
                tlist.sort(key=lambda x: x[1])
                # 按节气边界构建月段 (term_index, start_jd, end_jd)
                segs = []
                if tlist:
                    if tlist[0][1] - ln_s > 1e-4:
                        pm = _PREV_MONTH[tlist[0][0]]
                        segs.append((pm, ln_s, tlist[0][1] - 1e-4))
                    for i in range(len(tlist)):
                        s_jd = tlist[i][1]
                        e_jd = tlist[i+1][1] - 1e-4 if i < len(tlist) - 1 else ln_e
                        segs.append((_TERM_TO_MONTH[tlist[i][0]], s_jd, e_jd))
                else:
                    segs.append((0, ln_s, ln_e))  # 无节气, 兜底
                # 用五虎遁计算各月月柱
                year_gan_idx = JIA_ZI.index(gz) % 10
                liuyue = []
                for mi, (mth, ms, me) in enumerate(segs):
                    if mth > 0:
                        m_gz = month_gan_zhi(year_gan_idx, mth)
                    else:
                        m_gz = ''
                    mgi = JIA_ZI.index(m_gz) % 10 if m_gz else 0
                    sb, sm, sd, _ = julian_day_to_date(ms + tz_adj)
                    eb, em, ed, _ = julian_day_to_date(me + tz_adj)
                    liuyue.append({
                        'index': mi, 'ganzhi': m_gz,
                        'shi_shen': get_shi_shen(ri_gan_idx, mgi),
                        'start_date': f"{int(sb)}-{int(sm):02d}-{int(sd):02d}",
                        'end_date': f"{int(eb)}-{int(em):02d}-{int(ed):02d}",
                    })
                bs, bm, bd, _ = julian_day_to_date(ln_s + tz_adj)
                es, em, ed, _ = julian_day_to_date(ln_e + tz_adj)
                liunian.append({
                    'index': ln_i, 'year': int(bs), 'ganzhi': gz,
                    'nayin': NA_YIN_TABLE.get(gz, ''),
                    'shi_shen': get_shi_shen(ri_gan_idx, gi),
                    'start_date': f"{int(bs)}-{int(bm):02d}-{int(bd):02d}",
                    'end_date': f"{int(es)}-{int(em):02d}-{int(ed):02d}",
                    'start_jd': round(ln_s, 4), 'end_jd': round(ln_e, 4),
                    'liuyue': liuyue,
                })
        else:
            # === 落甲历: 流年按落甲历年首(360天块), 流月=12个30天块 ===
            yi0 = _luo_year_count(dy_start_jd)
            ys0 = _NEW_JIAZI_BASE_JD + yi0 * 360
            offset = dy_start_jd - ys0
            is_aligned = (abs(offset) < 0.001)
            for ln_i in range(10):
                if is_aligned:
                    ln_s = dy_start_jd + ln_i * 360
                    ln_e = ln_s + 359
                else:
                    if ln_i == 0:
                        ln_s = dy_start_jd
                        ln_e = ys0 + 360 - 1
                    elif ln_i < 9:
                        ln_s = ys0 + ln_i * 360
                        ln_e = ys0 + (ln_i + 1) * 360 - 1
                    else:
                        ln_s = ys0 + 9 * 360
                        ln_e = dy_end_jd
                gz = _luo_year_at(ln_s)
                gi = JIA_ZI.index(gz) % 10
                # 流月: 每30天一块, 直到流年末尾
                #   月首 = 流年首 + mi * 30
                #   月柱 = _luo_month_at(月首) - 用节气累积法, 已验证匹配API
                #   注意: 最后一个月的月末 = 流年尾, 不一定是30天整
                liuyue = []
                mi = 0
                while True:
                    ms = ln_s + mi * 30          # 月首JD
                    if ms >= ln_e:
                        break                    # 超出流年范围
                    me_jd = ms + 29              # 月末JD(默认29天后)
                    if me_jd >= ln_e:
                        me_jd = ln_e             # 最后一个月贴流年尾
                    m_gz = _luo_month_at(ms)     # 取月首的月柱
                    mgi = JIA_ZI.index(m_gz) % 10
                    sb, sm, sd, _ = julian_day_to_date(ms + tz_adj)
                    eb, em, ed, _ = julian_day_to_date(me_jd + tz_adj)
                    liuyue.append({
                        'index': mi,
                        'start_date': f"{int(sb)}-{int(sm):02d}-{int(sd):02d}",
                        'end_date': f"{int(eb)}-{int(em):02d}-{int(ed):02d}",
                        'ganzhi': m_gz,
                        'shi_shen': get_shi_shen(ri_gan_idx, mgi),
                    })
                    mi += 1
                bs, bm, bd, _ = julian_day_to_date(ln_s + tz_adj)
                es, em, ed, _ = julian_day_to_date(ln_e + tz_adj)
                liunian.append({
                    'index': ln_i, 'year': int(bs), 'ganzhi': gz,
                    'nayin': NA_YIN_TABLE.get(gz, ''),
                    'shi_shen': get_shi_shen(ri_gan_idx, gi),
                    'start_date': f"{int(bs)}-{int(bm):02d}-{int(bd):02d}",
                    'end_date': f"{int(es)}-{int(em):02d}-{int(ed):02d}",
                    'start_jd': round(ln_s, 4), 'end_jd': round(ln_e, 4),
                    'liuyue': liuyue,
                })

        liunian_list.append(liunian)

    return {
        'forward_dayun': forward,
        'qi_yun_age': round(days_to_term / 3, 4),
        'qi_yun_years': qi_yun_years,
        'qi_yun_months': qi_yun_months,
        'qi_yun_days': qi_yun_days,
        'qi_yun_info': f"命主于出生后{qi_yun_years}年{qi_yun_months}个月{qi_yun_days}天开始起运",
        'jiao_yun_jd': round(jiao_yun_jd, 6),
        'jiao_yun_date': f"{jiao_yun_y}-{jiao_yun_m:02d}-{jiao_yun_d:02d}",
        'dayun_list': dayun_list,
        'liunian_list': liunian_list,
        'hour_unknown': hour_unknown,
    }
