#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
农历计算模块
基于 tyme4py 天文算法，不限年份
"""
from tyme4py.solar import SolarDay as _SolarDay
from .astronomy import SOLAR_TERMS, get_solar_term_jd, julian_day_to_date

# 农历月名
LUNAR_MONTH_NAMES = ['正', '二', '三', '四', '五', '六',
                     '七', '八', '九', '十', '冬', '腊']
LUNAR_DAY_NAMES = ['初一', '初二', '初三', '初四', '初五', '初六',
                   '初七', '初八', '初九', '初十',
                   '十一', '十二', '十三', '十四', '十五',
                   '十六', '十七', '十八', '十九', '二十',
                   '廿一', '廿二', '廿三', '廿四', '廿五',
                   '廿六', '廿七', '廿八', '廿九', '三十']


class LunarDate:
    """农历日期"""

    def __init__(self, year: int, month: int, day: int, is_leap: bool = False):
        self.year = year
        self.month = month
        self.day = day
        self.is_leap = is_leap

    @property
    def month_name(self) -> str:
        if self.month < 1 or self.month > 12:
            return f'?{self.month}?'
        name = LUNAR_MONTH_NAMES[self.month - 1]
        if self.is_leap:
            name = '闰' + name
        return name

    @property
    def day_name(self) -> str:
        if self.day < 1 or self.day > 30:
            return f'?{self.day}?'
        return LUNAR_DAY_NAMES[self.day - 1]

    def __str__(self):
        return f"{self.month_name}月{self.day_name}"

    def to_dict(self):
        return {
            'year': self.year,
            'month': self.month,
            'month_name': self.month_name,
            'day': self.day,
            'day_name': self.day_name,
            'is_leap': self.is_leap,
        }


def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    """
    公历转农历（天文算法，不限年份）
    返回 LunarDate 对象
    """
    solar = _SolarDay(year, month, day)
    lunar = solar.get_lunar_day()
    lm = lunar.get_lunar_month()
    # tyme4py 闰月返回负值（如 -2 表示闰二月），取绝对值得到月份
    raw_month = lunar.get_month()
    is_leap = lm.is_leap()
    lunar_month = abs(raw_month) if is_leap else raw_month
    return LunarDate(
        year=lunar.get_year(),
        month=lunar_month,
        day=lunar.get_day(),
        is_leap=is_leap,
    )


def calculate_solar_terms(year: int) -> list:
    """
    计算指定年份的所有节气日期
    返回 [(名称, 公历年, 月, 日, 时:分), ...]
    """
    terms = []
    for i, name in enumerate(SOLAR_TERMS):
        jd = get_solar_term_jd(year, i)
        y, m, d, hour = julian_day_to_date(jd)
        h = int(hour)
        minute = int((hour - h) * 60)
        terms.append({
            'name': name,
            'index': i,
            'year': y,
            'month': m,
            'day': d,
            'hour': h,
            'minute': minute,
            'jd': round(jd, 6),
        })
    return terms
