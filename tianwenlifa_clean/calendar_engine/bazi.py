#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘模块
"""
from .astronomy import julian_day, get_solar_term_jd
from .astronomy import local_time_to_true_solar
from .astronomy import SOLAR_TERMS
from .ganzhi import (
    year_gan_zhi, month_gan_zhi, day_gan_zhi, hour_gan_zhi,
    get_na_yin, get_sheng_xiao, get_shi_shen, get_cang_gan,
    get_ri_kong, TIAN_GAN, DI_ZHI, JIA_ZI, NA_YIN_TABLE
)


def calculate_bazi(year: int, month: int, day: int, hour: int,
                   minute: int = 0, second: int = 0,
                   gender: str = '男',
                   longitude: float = None,
                   timezone_offset: int = 8) -> dict:
    """
    完整八字排盘 (标准节气历法)

    参数:
        year, month, day: 公历日期
        hour, minute, second: 出生时间
        gender: '男' 或 '女'
        longitude: 出生地经度 (东经, 度), 用于真太阳时
        timezone_offset: 时区偏移 (中国=8)

    返回:
        包含完整排盘结果的字典
    """
    result = {}

    # 1. 计算儒略日
    jd = julian_day(year, month, day)
    jd_with_time = jd + (hour - timezone_offset + minute / 60.0 + second / 3600.0) / 24.0

    # 2. 真太阳时计算
    true_solar_info = None
    actual_hour = hour
    if longitude is not None:
        true_solar_info = local_time_to_true_solar(
            year, month, day, hour, minute, second,
            longitude, timezone_offset
        )
        # 使用真太阳时的小时
        true_hour_str = true_solar_info['true_solar_time']
        actual_hour = int(true_hour_str.split(':')[0])

    result['true_solar'] = true_solar_info

    # 3. 计算四柱
    # 年柱: 以立春为界
    # 获取立春节气JD
    li_chun_jd = get_solar_term_jd(year, 2)  # 立春 index=2
    if jd_with_time < li_chun_jd:
        bazi_year = year - 1
    else:
        bazi_year = year

    year_pillar = year_gan_zhi(bazi_year)
    year_gan = TIAN_GAN.index(year_pillar[0])
    
    # 月柱: 以节气为界 (寅月=立春~惊蛰)
    # 确定月份节气
    month_terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]  # 立春开始的12个节气index
    month_names = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
    
    bazi_month = 1  # 寅月
    for i in range(12):
        term_idx = month_terms[i]
        next_idx = month_terms[(i + 1) % 12]
        
        term_year = bazi_year
        next_year = bazi_year + 1 if next_idx < term_idx else bazi_year
        
        term_jd = get_solar_term_jd(term_year, term_idx)
        next_term_jd = get_solar_term_jd(next_year, next_idx)
        
        if term_jd <= jd_with_time < next_term_jd:
            bazi_month = i + 1
            break
    else:
        if jd_with_time >= get_solar_term_jd(bazi_year, 2):
            bazi_month = 1
        else:
            bazi_month = 12
    
    month_pillar = month_gan_zhi(year_gan, bazi_month)
    result['month_start_term'] = SOLAR_TERMS[month_terms[bazi_month - 1]]
    result['month_start_term_jd'] = get_solar_term_jd(bazi_year, month_terms[bazi_month - 1])

    # 日柱
    day_pillar = day_gan_zhi(jd)
    day_gan_idx = JIA_ZI.index(day_pillar) % 10

    # 时柱
    hour_gan_pillar = hour_gan_zhi(day_gan_idx, actual_hour)
    hour_zhi_idx = DI_ZHI.index(hour_gan_pillar[1])

    result['bazi_year'] = bazi_year
    result['year_pillar'] = year_pillar
    result['month_pillar'] = month_pillar
    result['day_pillar'] = day_pillar
    result['hour_pillar'] = hour_gan_pillar

    result['year_gan'] = year_pillar[0]
    result['year_zhi'] = year_pillar[1]
    result['month_gan'] = month_pillar[0]
    result['month_zhi'] = month_pillar[1]
    result['day_gan'] = day_pillar[0]
    result['day_zhi'] = day_pillar[1]
    result['hour_gan'] = hour_gan_pillar[0]
    result['hour_zhi'] = hour_gan_pillar[1]

    # 4. 纳音
    result['year_nayin'] = get_na_yin(year_pillar)
    result['month_nayin'] = get_na_yin(month_pillar)
    result['day_nayin'] = get_na_yin(day_pillar)
    result['hour_nayin'] = get_na_yin(hour_gan_pillar)

    # 5. 生肖
    result['sheng_xiao'] = get_sheng_xiao(year_pillar)

    # 6. 十神
    result['year_shi_shen'] = get_shi_shen(day_gan_idx,
                                            JIA_ZI.index(year_pillar) % 10)
    result['month_shi_shen'] = get_shi_shen(day_gan_idx,
                                             JIA_ZI.index(month_pillar) % 10)
    result['hour_shi_shen'] = get_shi_shen(day_gan_idx,
                                            JIA_ZI.index(hour_gan_pillar) % 10)
    result['day_shi_shen'] = '元女' if gender == '女' else '元男'

    # 7. 藏干
    result['year_cang_gan'] = get_cang_gan(year_pillar[1])
    result['month_cang_gan'] = get_cang_gan(month_pillar[1])
    result['day_cang_gan'] = get_cang_gan(day_pillar[1])
    result['hour_cang_gan'] = get_cang_gan(hour_gan_pillar[1])

    # 藏干十神 (直接比较日干和藏干的天干索引)
    result['year_cang_gan_shi_shen'] = [get_shi_shen(day_gan_idx, TIAN_GAN.index(cg))
                                         for cg in result['year_cang_gan']]
    result['month_cang_gan_shi_shen'] = [get_shi_shen(day_gan_idx, TIAN_GAN.index(cg))
                                          for cg in result['month_cang_gan']]
    result['day_cang_gan_shi_shen'] = [get_shi_shen(day_gan_idx, TIAN_GAN.index(cg))
                                        for cg in result['day_cang_gan']]
    result['hour_cang_gan_shi_shen'] = [get_shi_shen(day_gan_idx, TIAN_GAN.index(cg))
                                         for cg in result['hour_cang_gan']]

    # 8. 日空
    result['ri_kong'] = get_ri_kong(day_pillar)

    # 9. 胎元
    # 胎元 = 月干顺推一位 + 月支顺推三位
    # 天干: (month_gan_idx + 1) % 10
    # 地支: (month_zhi_idx + 3) % 12
    month_gan_idx = JIA_ZI.index(month_pillar) % 10
    month_zhi_idx = JIA_ZI.index(month_pillar) % 12
    tai_yuan_gan_idx = (month_gan_idx + 1) % 10
    tai_yuan_zhi_idx = (month_zhi_idx + 3) % 12
    tai_yuan_str = TIAN_GAN[tai_yuan_gan_idx] + DI_ZHI[tai_yuan_zhi_idx]
    
    result['tai_yuan'] = tai_yuan_str
    result['tai_yuan_nayin'] = get_na_yin(tai_yuan_str) if tai_yuan_str else ''

    # 10. 命宫
    # 命宫 = 14 - (月令 + 时辰) or 26 - (月令 + 时辰)
    # 数字映射: 寅1, 卯2, ..., 丑12
    _MING_GONG_NUM = {'寅':1,'卯':2,'辰':3,'巳':4,'午':5,'未':6,
                      '申':7,'酉':8,'戌':9,'亥':10,'子':11,'丑':12}
    
    # 中气索引 (按bazi_month 1~12): 雨水,春分,谷雨,小满,夏至,大暑,处暑,秋分,霜降,小雪,冬至,大寒
    _ZHONG_QI_IDX = [3,5,7,9,11,13,15,17,19,21,23,1]
    
    month_zhi = month_pillar[1]
    # 过中气检查: 中气年份, 寅~子月同bazi_year, 丑月跨年到bazi_year+1
    zq_year = bazi_year if bazi_month <= 11 else bazi_year + 1
    zq_jd = get_solar_term_jd(zq_year, _ZHONG_QI_IDX[bazi_month - 1])
    
    if jd_with_time > zq_jd:
        # 过中气, 月令进一位
        mzhi_idx = (DI_ZHI.index(month_zhi) + 1) % 12
        month_zhi = DI_ZHI[mzhi_idx]
    
    month_num = _MING_GONG_NUM[month_zhi]
    hour_num = _MING_GONG_NUM[hour_gan_pillar[1]]
    total = month_num + hour_num
    ming_gong_num = 14 - total if total < 14 else 26 - total  # 1=寅, 2=卯, ..., 12=丑
    ming_gong = month_gan_zhi(year_gan, ming_gong_num)
    result['ming_gong'] = ming_gong
    result['ming_gong_nayin'] = get_na_yin(ming_gong)
    
    # 11. 身宫
    # 身宫 = 命宫 + 6 (子位起月法顺数至酉)
    shen_gong_num = (ming_gong_num + 6 - 1) % 12 + 1
    shen_gong = month_gan_zhi(year_gan, shen_gong_num)
    result['shen_gong'] = shen_gong
    result['shen_gong_nayin'] = get_na_yin(shen_gong)

    # 12. 大运
    from .dayun import calculate_dayun
    dayun_result = calculate_dayun(
        year, month, day, hour, minute, second,
        gender, bazi_year, year_pillar, month_pillar, day_pillar,
        hour_gan_pillar, longitude, timezone_offset,
        mode='standard'
    )
    result.update(dayun_result)

    result['gender'] = gender

    return result
