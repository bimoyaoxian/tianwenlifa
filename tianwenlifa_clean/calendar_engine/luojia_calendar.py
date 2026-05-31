#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
落甲历模块 - 司天学苑核心历法系统
历元: 1962-02-05 04:00 UTC (JD 2437700.16667)

年柱: 原版JS算法 (evaluateNewJiaziAndPhase)
   cycleOffset = Math.floor((jd - 2437700.16667) / 360)

月柱: 累积节气法 (纯天文, 零查表)
   月支 = 节气区间直接映射 (立春→寅, 惊蛰→卯, ...)
   月柱 = JIA_ZI[(49 + 累积跨过的节气数) % 60]
"""
import math
from datetime import datetime
from .astronomy import J2000, julian_day, get_solar_term_jd, SOLAR_TERMS
from .ganzhi import TIAN_GAN, DI_ZHI, JIA_ZI, NA_YIN_TABLE, day_gan_zhi

EPOCH = datetime(1962, 2, 5)

# 年柱历元（原版网站）
NEW_JIAZI_BASE_JD = 2437700.16667

# 主节气(立春/惊蛰/...) → 月支映射
_MAJOR_TERMS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
_TERM_TO_BRANCH = {0:1, 2:2, 4:3, 6:4, 8:5, 10:6, 12:7, 14:8, 16:9, 18:10, 20:11, 22:0}
EPOCH_MONTH_PILLAR = 49  # JIA_ZI[49] = 癸丑 (Kepler修正模型计数比VSOP87多1)


def _count_terms_since_epoch(jd: float) -> int:
    """统计从历元JD到目标JD之间跨过的节气数"""
    epoch_jd = NEW_JIAZI_BASE_JD
    from .astronomy import julian_day_to_date
    yy, _, _, _ = julian_day_to_date(jd)
    ref_year = int(yy)
    epoch_year = 1962
    start_year = min(ref_year, epoch_year) - 100
    end_year = max(ref_year, epoch_year) + 100
    
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
    """天文计算落甲历月支"""
    jd = julian_day(year, month, day)
    for ti in _MAJOR_TERMS:
        tj = get_solar_term_jd(year, ti)
        nti = (ti + 2) % 24
        ny = year + 1 if nti < ti else year
        ntj = get_solar_term_jd(ny, nti)
        if tj <= jd < ntj:
            return _TERM_TO_BRANCH[ti]
    for ti in [22]:
        tj = get_solar_term_jd(year - 1, ti)
        nti = (ti + 2) % 24
        ntj = get_solar_term_jd(year + 1, nti) if nti < ti else get_solar_term_jd(year, nti)
        if tj <= jd < ntj:
            return _TERM_TO_BRANCH[ti]
    raise ValueError(f"找不到节气区间: {year}-{month}-{day}")


def _luo_jd(jd_standard: float) -> int:
    return int(jd_standard - J2000 + 0.5)


def get_luojia_year(year: int, month: int = 3, day: int = 1, scheme: int = 1) -> str:
    """落甲历年柱（原版JS算法）
    
    原版 evaluateNewJiaziAndPhase:
      const diffDays = jd - 2437700.16667;
      const cycleOffset = Math.floor(diffDays / 360);
      cycleOffset=0 → 甲寅 (JIA_ZI[50])
    """
    jd = julian_day(year, month, day)
    cycle_offset = int(math.floor((jd - NEW_JIAZI_BASE_JD) / 360))
    return JIA_ZI[(cycle_offset + 50) % 60]


def get_luojia_day(year: int, month: int, day: int) -> str:
    return day_gan_zhi(julian_day(year, month, day))


def get_luojia_month_date(year: int, month: int, day: int) -> str:
    """落甲历月柱 (累积节气法, 零查表)"""
    jd = julian_day(year, month, day)
    n_terms = _count_terms_since_epoch(jd)
    return JIA_ZI[(EPOCH_MONTH_PILLAR + n_terms) % 60]


def get_luojia_hour(day_gan: int, luo_jd: float, actual_hour: int = None) -> str:
    if actual_hour is not None:
        zhi = (actual_hour + 1) // 2 % 12
    else:
        hour = ((luo_jd - int(luo_jd)) * 24 + 8) % 24
        zhi = (int(hour) + 1) // 2 % 12
    gan_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
    gan = (gan_map[day_gan % 10] + zhi) % 10
    return TIAN_GAN[gan] + DI_ZHI[zhi]


def get_wuyun_liuqi(year: int, day_jd: int) -> dict:
    gan_idx = (year - 4) % 10
    is_yang = gan_idx % 2 == 0
    return {'base_color': 'maleGreen' if is_yang else 'femaleBlue',
            'year_gan': TIAN_GAN[gan_idx], 'is_yang': is_yang}


def get_luojia_calendar(year: int, scheme: int = 1) -> list:
    months_data = []
    wuyun = get_wuyun_liuqi(year, 0)
    for month in range(1, 13):
        days = []
        max_day = 31 if month in [1,3,5,7,8,10,12] else (29 if month==2 and (year%4==0 and (year%100!=0 or year%400==0)) else (28 if month==2 else 30))
        for day in range(1, max_day + 1):
            jd = julian_day(year, month, day)
            luo_jd = _luo_jd(jd)
            day_ganzhi = get_luojia_day(year, month, day)
            solar_term = None
            for ti, tn in enumerate(SOLAR_TERMS):
                tj = get_solar_term_jd(year, ti)
                if abs(tj - jd) < 1.0: solar_term = tn; break
            color = 'white' if solar_term == '冬至' else wuyun['base_color']
            data_val = 366 if solar_term == '冬至' else (1 if solar_term else None)
            days.append({
                'year': year, 'month': month, 'day': day, 'jd': luo_jd,
                'color': color, 'data': data_val,
                'dayOfWeek': datetime(year, month, day).isoweekday() % 7,
                'ganzhi': day_ganzhi, 'solar_term': solar_term,
                'wuyun_season': wuyun['base_color'],
            })
        months_data.append({'year': year, 'month': month, 'month_name': f'{month}月', 'days': days})
    return months_data


def get_luojia_bazi(year: int, month: int, day: int,
                    hour: int = None, minute: int = 0,
                    gender: str = '男', scheme: int = 1,
                    longitude: float = None,
                    timezone_offset: int = 8) -> dict:
    jd = julian_day(year, month, day)
    luo_jd = _luo_jd(jd)
    true_solar_info = None
    actual_hour = hour
    hour_unknown = (hour is None)
    if hour_unknown:
        actual_hour = 12  # 仅用于真太阳时判断，时柱保持None
    if longitude is not None and not hour_unknown:
        from .astronomy import local_time_to_true_solar
        true_solar_info = local_time_to_true_solar(year, month, day, hour, minute, 0, longitude, timezone_offset)
        actual_hour = int(true_solar_info['true_solar_time'].split(':')[0])

    luo_year_pillar = get_luojia_year(year, month, day)
    luo_month_pillar = get_luojia_month_date(year, month, day)
    luo_day_pillar = get_luojia_day(year, month, day)
    
    if hour_unknown:
        luo_hour_pillar = None
        hour_gan_str = '*'
        hour_zhi_str = '*'
    else:
        # 晚子时(23:00-00:00)用次日日干
        if actual_hour == 23:
            from datetime import timedelta
            next_dt = datetime(year, month, day) + timedelta(days=1)
            next_day = get_luojia_day(next_dt.year, next_dt.month, next_dt.day)
            day_gan_idx = JIA_ZI.index(next_day) % 10
        else:
            day_gan_idx = JIA_ZI.index(luo_day_pillar) % 10
        
        zhi = (actual_hour + 1) // 2 % 12
        hour_gan = ({0:0,1:2,2:4,3:6,4:8,5:0,6:2,7:4,8:6,9:8}[day_gan_idx % 10] + zhi) % 10
        luo_hour_pillar = TIAN_GAN[hour_gan] + DI_ZHI[zhi]
        hour_gan_str = luo_hour_pillar[0]
        hour_zhi_str = luo_hour_pillar[1]

    terms = []
    for ti in [2,4,6,8,10,12,14,16,18,20,22,0]:
        tj = get_solar_term_jd(year, ti)
        y, m, d, hh = _jd_to_date(tj)
        terms.append({'name': SOLAR_TERMS[ti], 'date': f"{m}月{d}日", 'jd': round(tj, 6)})

    from .ganzhi import get_shi_shen, get_sheng_xiao, get_ri_kong, get_cang_gan, month_gan_zhi, year_gan_zhi
    
    ri_gan_idx = JIA_ZI.index(luo_day_pillar) % 10
    
    # 胎元: 月干顺推一位 + 月支顺推三位
    # 天干: (月干索引 + 1) % 10, 地支: (月支索引 + 3) % 12
    ty_gan_idx = JIA_ZI.index(luo_month_pillar) % 10
    ty_zhi_idx = JIA_ZI.index(luo_month_pillar) % 12
    tai_yuan_month_pillar = TIAN_GAN[(ty_gan_idx + 1) % 10] + DI_ZHI[(ty_zhi_idx + 3) % 12]
    
    # 命宫: 14 - (月令 + 时辰) or 26 - (月令 + 时辰)
    _MING_GONG_NUM = {'寅':1,'卯':2,'辰':3,'巳':4,'午':5,'未':6,
                      '申':7,'酉':8,'戌':9,'亥':10,'子':11,'丑':12}
    
    # 过中气检查 (命宫月令修正)
    jd_with_time = jd + (actual_hour - timezone_offset + minute / 60.0) / 24.0
    li_chun_jd = get_solar_term_jd(year, 2)
    zq_bazi_year = year if jd_with_time >= li_chun_jd else year - 1
    # 确定标准节气月
    _MONTH_TERMS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]
    zq_bazi_month = 1
    for i in range(12):
        ti, ni = _MONTH_TERMS[i], _MONTH_TERMS[(i + 1) % 12]
        ny = zq_bazi_year + 1 if ni < ti else zq_bazi_year
        if get_solar_term_jd(zq_bazi_year, ti) <= jd_with_time < get_solar_term_jd(ny, ni):
            zq_bazi_month = i + 1
            break
    else:
        zq_bazi_month = 12 if jd_with_time < get_solar_term_jd(zq_bazi_year, 2) else 1
    
    # 中气: 雨水,春分,谷雨,小满,夏至,大暑,处暑,秋分,霜降,小雪,冬至,大寒
    _ZHONG_QI = [3,5,7,9,11,13,15,17,19,21,23,1]
    zq_year = zq_bazi_year if zq_bazi_month <= 11 else zq_bazi_year + 1
    zq_jd = get_solar_term_jd(zq_year, _ZHONG_QI[zq_bazi_month - 1])
    
    month_zhi_mg = luo_month_pillar[1]
    if jd_with_time > zq_jd:
        mzhi_idx = (DI_ZHI.index(month_zhi_mg) + 1) % 12
        month_zhi_mg = DI_ZHI[mzhi_idx]
    
    uluo_year_gan_idx = TIAN_GAN.index(luo_year_pillar[0])
    ulyo_month_num = _MING_GONG_NUM[month_zhi_mg]
    ulyo_hour_num = _MING_GONG_NUM[luo_hour_pillar[1]] if not hour_unknown else _MING_GONG_NUM['子']
    total_mg = ulyo_month_num + ulyo_hour_num
    ming_gong_num = 14 - total_mg if total_mg < 14 else 26 - total_mg
    ming_gong = month_gan_zhi(uluo_year_gan_idx, ming_gong_num)
    
    # 身宫: 命宫 + 6
    shen_gong_num = (ming_gong_num + 6 - 1) % 12 + 1
    shen_gong = month_gan_zhi(uluo_year_gan_idx, shen_gong_num)
    
    return {
        'system': '落甲历', 'scheme': scheme,
        'scheme_name': {1: '五元六纪', 2: '古制二至', 3: '古制年尾'}.get(scheme, ''),
        'true_solar': true_solar_info, 'luo_jd': luo_jd,
        'year_pillar': luo_year_pillar, 'month_pillar': luo_month_pillar,
        'day_pillar': luo_day_pillar, 'hour_pillar': luo_hour_pillar,
        'year_nayin': NA_YIN_TABLE.get(luo_year_pillar, ''),
        'month_nayin': NA_YIN_TABLE.get(luo_month_pillar, ''),
        'day_nayin': NA_YIN_TABLE.get(luo_day_pillar, ''),
        'hour_nayin': NA_YIN_TABLE.get(luo_hour_pillar, '') if not hour_unknown else '',
        'year_gan': luo_year_pillar[0], 'year_zhi': luo_year_pillar[1],
        'month_gan': luo_month_pillar[0], 'month_zhi': luo_month_pillar[1],
        'day_gan': luo_day_pillar[0], 'day_zhi': luo_day_pillar[1],
        'hour_gan': hour_gan_str, 'hour_zhi': hour_zhi_str,
        'year_shi_shen': get_shi_shen(ri_gan_idx, JIA_ZI.index(luo_year_pillar) % 10),
        'month_shi_shen': get_shi_shen(ri_gan_idx, JIA_ZI.index(luo_month_pillar) % 10),
        'day_shi_shen': '元女' if gender == '女' else '元男',
        'hour_shi_shen': get_shi_shen(ri_gan_idx, JIA_ZI.index(luo_hour_pillar) % 10) if not hour_unknown else '',
        'sheng_xiao': get_sheng_xiao(luo_year_pillar),
        'ri_kong': get_ri_kong(luo_day_pillar),
        'year_cang_gan': get_cang_gan(luo_year_pillar[1]),
        'month_cang_gan': get_cang_gan(luo_month_pillar[1]),
        'day_cang_gan': get_cang_gan(luo_day_pillar[1]),
        'hour_cang_gan': get_cang_gan(luo_hour_pillar[1]) if not hour_unknown else [],
        'year_cang_gan_shi_shen': [get_shi_shen(ri_gan_idx, TIAN_GAN.index(cg)) for cg in get_cang_gan(luo_year_pillar[1])],
        'month_cang_gan_shi_shen': [get_shi_shen(ri_gan_idx, TIAN_GAN.index(cg)) for cg in get_cang_gan(luo_month_pillar[1])],
        'day_cang_gan_shi_shen': [get_shi_shen(ri_gan_idx, TIAN_GAN.index(cg)) for cg in get_cang_gan(luo_day_pillar[1])],
        'hour_cang_gan_shi_shen': [get_shi_shen(ri_gan_idx, TIAN_GAN.index(cg)) for cg in get_cang_gan(luo_hour_pillar[1])] if not hour_unknown else [],
        'tai_yuan': tai_yuan_month_pillar,
        'tai_yuan_nayin': NA_YIN_TABLE.get(tai_yuan_month_pillar, ''),
        'ming_gong': ming_gong,
        'ming_gong_nayin': NA_YIN_TABLE.get(ming_gong, ''),
        'shen_gong': shen_gong,
        'shen_gong_nayin': NA_YIN_TABLE.get(shen_gong, ''),
        'wuyun': get_wuyun_liuqi(year, luo_jd),
        'solar_terms': terms,
    }


def _jd_to_date(jd: float):
    from .astronomy import julian_day_to_date
    return julian_day_to_date(jd)
