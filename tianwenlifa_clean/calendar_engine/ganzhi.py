#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
干支模块 - 天干地支、纳音、生肖
"""

# 十天干
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 十二地支
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十二生肖
SHENG_XIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']

# 六十甲子
JIA_ZI = []
for i in range(60):
    JIA_ZI.append(TIAN_GAN[i % 10] + DI_ZHI[i % 12])

# 纳音五行表 (六十甲子纳音)
NA_YIN_TABLE = {
    '甲子': '海中金', '乙丑': '海中金',
    '丙寅': '炉中火', '丁卯': '炉中火',
    '戊辰': '大林木', '己巳': '大林木',
    '庚午': '路旁土', '辛未': '路旁土',
    '壬申': '剑锋金', '癸酉': '剑锋金',
    '甲戌': '山头火', '乙亥': '山头火',
    '丙子': '涧下水', '丁丑': '涧下水',
    '戊寅': '城墙土', '己卯': '城墙土',
    '庚辰': '白腊金', '辛巳': '白腊金',
    '壬午': '杨柳木', '癸未': '杨柳木',
    '甲申': '泉中水', '乙酉': '泉中水',
    '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹雳火', '己丑': '霹雳火',
    '庚寅': '松柏木', '辛卯': '松柏木',
    '壬辰': '长流水', '癸巳': '长流水',
    '甲午': '沙中金', '乙未': '沙中金',
    '丙申': '山下火', '丁酉': '山下火',
    '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土',
    '壬寅': '金箔金', '癸卯': '金箔金',
    '甲辰': '覆灯火', '乙巳': '覆灯火',
    '丙午': '天河水', '丁未': '天河水',
    '戊申': '大驿土', '己酉': '大驿土',
    '庚戌': '钗钏金', '辛亥': '钗钏金',
    '壬子': '桑柘木', '癸丑': '桑柘木',
    '甲寅': '大溪水', '乙卯': '大溪水',
    '丙辰': '沙中土', '丁巳': '沙中土',
    '戊午': '天上火', '己未': '天上火',
    '庚申': '石榴木', '辛酉': '石榴木',
    '壬戌': '大海水', '癸亥': '大海水',
}


def get_tian_gan(index: int) -> str:
    """根据索引获取天干 (0-9)"""
    return TIAN_GAN[index % 10]


def get_di_zhi(index: int) -> str:
    """根据索引获取地支 (0-11)"""
    return DI_ZHI[index % 12]


def get_jia_zi(index: int) -> str:
    """根据索引获取六十甲子 (0-59)"""
    return JIA_ZI[index % 60]


def get_na_yin(gan_zhi: str) -> str:
    """获取纳音"""
    return NA_YIN_TABLE.get(gan_zhi, '')


def get_sheng_xiao(year_gan_zhi: str) -> str:
    """根据年干支获取生肖"""
    dz = year_gan_zhi[1]  # 地支字符
    if dz in DI_ZHI:
        idx = DI_ZHI.index(dz)
        return SHENG_XIAO[idx]
    return ''


def year_gan_zhi(year: int) -> str:
    """获取年干支"""
    # 甲子年 = 0, 公元4年为甲子年
    idx = (year - 4) % 60
    return JIA_ZI[idx]


def month_gan_zhi(year_gan: int, month: int, is_lunar_month: bool = False) -> str:
    """
    获取月干支 (使用五虎遁)
    year_gan: 年干索引 (0-9)
    month: 农历月份 (1-12)
    """
    # 五虎遁: 甲己之年丙作首, 乙庚之岁戊为头,
    #          丙辛必定寻庚起, 丁壬壬位顺行流,
    #          若问戊癸何方发, 甲寅之上好追求
    gan_map = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0,
               5: 2, 6: 4, 7: 6, 8: 8, 9: 0}
    start_gan = gan_map[year_gan % 10]
    # 正月(寅月)开始
    gan = (start_gan + (month - 1)) % 10
    zhi = (month - 1 + 2) % 12  # 寅=2
    return TIAN_GAN[gan] + DI_ZHI[zhi]


def day_gan_zhi(jd: float) -> str:
    """
    获取日干支
    jd: 儒略日
    julian_day返回中间夜JD (e.g. 2461187.5)
    int(jd+0.5)取到午时JD整数部分, 对应API的todayJd
    API验证: 2026-05-27 todayJd=2461188 -> 辛丑(37)
    """
    idx = (int(jd + 0.5) + 49) % 60
    return JIA_ZI[idx]


def hour_gan_zhi(day_gan: int, hour: int) -> str:
    """
    获取时干支 (使用五鼠遁)
    day_gan: 日干索引 (0-9)
    hour: 小时 (0-23)
    """
    # 五鼠遁: 甲己还加甲, 乙庚丙作初,
    #          丙辛从戊起, 丁壬庚子居,
    #          戊癸何方发, 壬子是真途
    gan_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
               5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
    # 地支时辰: 子=23-1, 丑=1-3, ...
    zhi = (hour + 1) // 2 % 12
    start_gan = gan_map[day_gan % 10]
    gan = (start_gan + zhi) % 10
    return TIAN_GAN[gan] + DI_ZHI[zhi]


def get_shi_shen(day_gan: int, other_gan: int) -> str:
    """
    十神计算
    day_gan: 日干
    other_gan: 其他干
    返回: 十神名称
    """
    # 天干五行: 甲乙木(2), 丙丁火(3), 戊己土(4), 庚辛金(0), 壬癸水(1)
    gan_wuxing = {0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 4, 6: 0, 7: 0, 8: 1, 9: 1}

    # 阴阳
    gan_yinyang = {0: 0, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 0, 9: 1}

    day_wx = gan_wuxing[day_gan % 10]
    day_yy = gan_yinyang[day_gan % 10]
    other_wx = gan_wuxing[other_gan % 10]
    other_yy = gan_yinyang[other_gan % 10]

    # 生克关系
    # 生我者: 印 (正印同阴阳, 偏印异)
    # 我生者: 食伤 (食神同阴阳, 伤官异)
    # 克我者: 官杀 (正官同阴阳, 七杀异)
    # 我克者: 财 (正财同阴阳, 偏财异)
    # 同我者: 比劫 (比肩同阴阳, 劫财异)

    # 五行生克 (0金, 1水, 2木, 3火, 4土)
    # 生: 金生水, 水生木, 木生火, 火生土, 土生金
    # 克: 金克木, 木克土, 土克水, 水克火, 火克金

    relation = (other_wx - day_wx) % 5  # 0=同我, 1=我生, 2=我克, 3=克我, 4=生我

    mapping = {
        0: ('比肩', '劫财'),
        1: ('食神', '伤官'),
        2: ('正财', '偏财'),
        3: ('正官', '七杀'),
        4: ('正印', '偏印'),
    }

    same_yy = (day_yy == other_yy)
    return mapping[relation][0 if same_yy else 1]


# 地支藏干
CANG_GAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

DI_ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}


def get_cang_gan(zhi: str) -> list:
    """获取地支藏干"""
    return CANG_GAN.get(zhi, [])


def get_ri_kong(day_gan_zhi_str: str) -> str:
    """
    计算日空 (旬空/空亡)
    """
    idx = JIA_ZI.index(day_gan_zhi_str) if day_gan_zhi_str in JIA_ZI else -1
    if idx < 0:
        return ''
    # 每旬10天, 对应地支为空亡
    xun = idx // 10
    kong_zhi_1 = (10 - xun * 2) % 12
    kong_zhi_2 = (11 - xun * 2) % 12
    return DI_ZHI[kong_zhi_1] + DI_ZHI[kong_zhi_2]
