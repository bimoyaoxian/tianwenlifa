#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五运六气 + 天文星象辅助计算
用于日历页面右侧信息面板
"""
from .astronomy import get_solar_term_jd, julian_day_to_date, J2000
from .astronomy import _jupiter_longitude, _sun_longitude
from .ganzhi import TIAN_GAN, DI_ZHI, JIA_ZI

# ========== 五运 ==========

# 天干化运：甲己土, 乙庚金, 丙辛水, 丁壬木, 戊癸火
GAN_TO_YUN = {0: '土', 1: '金', 2: '水', 3: '木', 4: '火',
              5: '土', 6: '金', 7: '水', 8: '木', 9: '火'}
GAN_TO_YUN_NAME = {0: '土运', 1: '金运', 2: '水运', 3: '木运', 4: '火运',
                   5: '土运', 6: '金运', 7: '水运', 8: '木运', 9: '火运'}

# 太过/不及：阳干太过, 阴干不及
GAN_TAI_BU = {0: '太过', 1: '不及', 2: '太过', 3: '不及', 4: '太过',
              5: '不及', 6: '太过', 7: '不及', 8: '太过', 9: '不及'}

# 主运顺序：木→火→土→金→水 (角徵宫商羽)
ZHU_YUN = ['木运(角)', '火运(徵)', '土运(宫)', '金运(商)', '水运(羽)']

# 客运：根据岁运的五行, 按相生顺序轮转
# 土→金→水→木→火
KE_YUN_SHENG = {'土': '金', '金': '水', '水': '木', '木': '火', '火': '土'}
KE_YUN_NAMES = {'土': '土运(宫)', '金': '金运(商)', '水': '水运(羽)', '木': '木运(角)', '火': '火运(徵)'}

# ========== 六气 ==========

# 地支化六气：司天
ZHI_TO_SITIAN = {
    0: '少阴君火',   # 子
    1: '太阴湿土',   # 丑
    2: '少阳相火',   # 寅
    3: '阳明燥金',   # 卯
    4: '太阳寒水',   # 辰
    5: '厥阴风木',   # 巳
    6: '少阴君火',   # 午
    7: '太阴湿土',   # 未
    8: '少阳相火',   # 申
    9: '阳明燥金',   # 酉
    10: '太阳寒水',  # 戌
    11: '厥阴风木',  # 亥
}

# 司天→在泉 对应 (对位相克)
SITIAN_TO_ZAIQUAN = {
    '少阴君火': '阳明燥金',
    '太阴湿土': '太阳寒水',
    '少阳相火': '厥阴风木',
    '阳明燥金': '少阴君火',
    '太阳寒水': '太阴湿土',
    '厥阴风木': '少阳相火',
}

# 主气顺序 (固定, 每气60.875天)
ZHU_QI = [
    ('大寒到惊蛰', '厥阴风木'),
    ('春分到小满', '少阴君火'),
    ('小满到大暑', '少阳相火'),
    ('大暑到秋分', '太阴湿土'),
    ('秋分到小雪', '阳明燥金'),
    ('小雪到大寒', '太阳寒水'),
]

# ========== 经络 ==========

# 年支→经络 (足) — 按原网站五运六气映射
# 子午:少阴→心, 丑未:太阴→脾/胃, 寅申:少阳→三焦/胆
# 卯酉:阳明→大肠/胃, 辰戌:太阳→膀胱, 巳亥:厥阴→肝/心包
ZHI_TO_JINGLUO_FOOT = {
    '子': '足少阴心经', '丑': '足太阴脾经', '寅': '足少阳胆经',
    '卯': '足阳明胃经', '辰': '足太阳膀胱经', '巳': '足厥阴肝经',
    '午': '足少阴心经', '未': '足阳明胃经', '申': '足少阳胆经',
    '酉': '足阳明胃经', '戌': '足太阳膀胱经', '亥': '足厥阴肝经',
}

# 月支→经络 (手)
MONTH_ZHI_TO_JINGLUO_HAND = {
    '寅': '手太阴肺经', '卯': '手阳明大肠经', '辰': '手阳明胃经',
    '巳': '手太阴脾经', '午': '手少阴心经', '未': '手太阳小肠经',
    '申': '手太阳膀胱经', '酉': '手少阴肾经', '戌': '手厥阴心包经',
    '亥': '手少阳三焦经', '子': '手少阳胆经', '丑': '手厥阴肝经',
}

# ========== 斗建 ==========

DOU_JIAN = {
    '子': '子方', '丑': '丑方', '寅': '寅方', '卯': '卯方',
    '辰': '辰方', '巳': '巳方', '午': '午方', '未': '未方',
    '申': '申方', '酉': '酉方', '戌': '戌方', '亥': '亥方',
}

# ========== 二十八宿 / 星次 ==========

# 地支→星次 (十二次)
ZHI_TO_XINGCI = {
    '子': '玄枵', '丑': '星纪', '寅': '析木', '卯': '大火',
    '辰': '寿星', '巳': '鹑尾', '午': '鹑火', '未': '鹑首',
    '申': '实沈', '酉': '大梁', '戌': '降娄', '亥': '娵訾',
}

# 地支→宿 (粗略对应)
ZHI_TO_XIU = {
    '子': '女虚危', '丑': '斗牛', '寅': '尾箕', '卯': '氐房心',
    '辰': '角亢', '巳': '翼轸', '午': '柳星张', '未': '井鬼',
    '申': '觜参', '酉': '胃昴毕', '戌': '奎娄', '亥': '室壁',
}

# ========== 主运时间 ==========

def get_zhu_yun_phase(year: int) -> list:
    """计算当年主运各运的交运日期 (以节气为参照)
    初运木: 大寒交运
    二运火: 春分后十三日交运
    三运土: 芒种后十日交运
    四运金: 处暑后七日交运
    五运水: 立冬后四日交运
    """
    # 主运交运节气参照 (注意本项目SOLAR_TERMS索引: 0=小寒,1=大寒,2=立春,5=春分,
    # 10=芒种,15=处暑,20=立冬)
    term_refs = [
        (1, 0),     # 初运木: 大寒(term 1) + 0日
        (5, 13),    # 二运火: 春分(term 5) + 13日
        (10, 10),   # 三运土: 芒种(term 10) + 10日
        (15, 7),    # 四运金: 处暑(term 15) + 7日
        (20, 4),    # 五运水: 立冬(term 20) + 4日
    ]
    stages = []
    for i, (ti, offset) in enumerate(term_refs):
        tj = get_solar_term_jd(year, ti)
        jd = tj + offset
        y, m, d, h = julian_day_to_date(jd)
        stages.append({
            'name': ZHU_YUN[i] if i < len(ZHU_YUN) else '',
            'start_date': f'{int(m):02d}-{int(d):02d}',
            'jd': round(jd, 4),
        })
    return stages

def get_wuyun_liuqi_info(year: int, month: int, day: int,
                          luo_year_pillar: str = None) -> dict:
    """获取指定日期的五运六气等信息
    luo_year_pillar: 落甲历年柱 (如 '己未'), 若不传则用标准年干支
    """
    from .ganzhi import year_gan_zhi
    from .astronomy import julian_day
    
    jd = julian_day(year, month, day)
    
    # 年干支 — 优先用落甲历
    if luo_year_pillar:
        ygz = luo_year_pillar
    else:
        ygz = year_gan_zhi(year)
    year_gan = TIAN_GAN.index(ygz[0])
    year_zhi = DI_ZHI.index(ygz[1]) if ygz[1] in DI_ZHI else 0
    year_zhi_str = ygz[1]
    
    # 1. 岁运
    yun = GAN_TO_YUN[year_gan]
    tai_bu = GAN_TAI_BU[year_gan]
    sui_yun = f'{yun}运{tai_bu}'
    
    # 2. 客运 (岁运的五行, 按相生排列)
    ke_yun_list = [yun]
    for _ in range(4):
        ke_yun_list.append(KE_YUN_SHENG[ke_yun_list[-1]])
    ke_yun_str = '→'.join([KE_YUN_NAMES[k] for k in ke_yun_list])
    
    # 3. 司天/在泉
    si_tian = ZHI_TO_SITIAN.get(year_zhi, '')
    zai_quan = SITIAN_TO_ZAIQUAN.get(si_tian, '')
    
    # 4. 主气 - 根据日期确定当前在哪个气
    # 实际计算在下面 qi_boundaries 循环中进行
    
    # 根据日期粗略判定主气
    # 大寒(1/20) → 春分(3/20) → 小满(5/21) → 大暑(7/23) → 秋分(9/23) → 小雪(11/22) → 大寒
    qi_boundaries = [
        (1, '大寒'),    # term 1 = 大寒 (本项目索引:0小寒,1大寒)
        (5, '春分'),    # term 5 = 春分
        (9, '小满'),    # term 9 = 小满
        (13, '大暑'),   # term 13 = 大暑
        (17, '秋分'),   # term 17 = 秋分
        (21, '小雪'),   # term 21 = 小雪
    ]
    qi_names = ['厥阴风木', '少阴君火', '少阳相火', '太阴湿土', '阳明燥金', '太阳寒水']
    qi_periods = ['大寒到春分', '春分到小满', '小满到大暑', '大暑到秋分', '秋分到小雪', '小雪到大寒']
    
    current_qi = ''
    current_qi_period = ''
    # 大寒前(1月初~1月19日) → 归属上年终气小雪到大寒
    first_dahan = get_solar_term_jd(year, 1)
    if jd < first_dahan:
        current_qi = qi_names[5]
        current_qi_period = qi_periods[5]
    else:
        for i, (ti, tname) in enumerate(qi_boundaries):
            tj = get_solar_term_jd(year, ti)
            if i == 5:
                next_tj = get_solar_term_jd(year + 1, 1)  # 小雪→大寒, 大寒在下一年
            else:
                next_tj = get_solar_term_jd(year, qi_boundaries[(i + 1) % 6][0])
            if tj <= jd < next_tj:
                current_qi = qi_names[i]
                current_qi_period = qi_periods[i]
                break
    
    # 5. 年支经络
    foot_jingluo = ZHI_TO_JINGLUO_FOOT.get(ygz[1], '')
    
    # 6. 月支经络 - 需要先计算标准节气月
    li_chun_jd = get_solar_term_jd(year, 2)
    if jd < li_chun_jd:
        bazi_year_num = year - 1
    else:
        bazi_year_num = year
    
    from .ganzhi import year_gan_zhi as ygz_func
    bazi_ygz = ygz_func(bazi_year_num)
    bazi_year_gan = JIA_ZI.index(bazi_ygz) % 10
    
    # 确定节气月
    month_terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]
    month_names = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
    bazi_month = 0
    for i, ti in enumerate(month_terms):
        nti = month_terms[(i + 1) % 12]
        ny = bazi_year_num + 1 if nti < ti else bazi_year_num
        tj = get_solar_term_jd(bazi_year_num, ti)
        ntj = get_solar_term_jd(ny, nti)
        if tj <= jd < ntj:
            bazi_month = i + 1
            break
    month_zhi_str = month_names[bazi_month - 1] if bazi_month > 0 else ''
    hand_jingluo = MONTH_ZHI_TO_JINGLUO_HAND.get(month_zhi_str, '')
    
    # 7. 斗建
    dou_jian = DOU_JIAN.get(ygz[1], '')

    # 8. 星次/宿 (基于地支的传统岁星周期)
    xing_ci = ZHI_TO_XINGCI.get(ygz[1], '')
    xiu = ZHI_TO_XIU.get(ygz[1], '')

    # 9. 主运 — 各运交运描述 (按当前日期所属的运)
    ZHU_YUN_DESC = [
        '大寒交木运',
        '春分后十三日交火运',
        '芒种后十日交土运',
        '处暑后七日交金运',
        '立冬后四日交水运',
    ]
    zhu_yun_stages = get_zhu_yun_phase(year)
    if jd < zhu_yun_stages[0]['jd']:
        # 大寒之前 → 上一年终运(水运)
        current_zhu_yun = ZHU_YUN_DESC[-1]
    else:
        current_zhu_yun = ZHU_YUN_DESC[0]
        for si, st in enumerate(zhu_yun_stages):
            next_si = (si + 1) % len(zhu_yun_stages)
            if next_si == 0:
                next_jd = get_solar_term_jd(year + 1, 1)  # 下一年大寒(term 1)
            else:
                next_jd = zhu_yun_stages[next_si]['jd']
            if st['jd'] <= jd < next_jd:
                current_zhu_yun = ZHU_YUN_DESC[si]
                break
    
    # 10. 实时木日相差 (当前日期)
    from .astronomy import _jupiter_longitude as _jup_lon, _sun_longitude as _sun_lon
    jup_now = _jup_lon(jd)
    sun_now = _sun_lon(jd)
    diff_now = (jup_now - sun_now + 360) % 360
    if diff_now > 180:
        diff_now = -(360 - diff_now)
    # 岁差偏移 at 节气年首
    li_chun_jd_year = get_solar_term_jd(year, 2)
    precession = (li_chun_jd_year - J2000) / 365.25 * 0.014
    
    # 月建 (斗建按月变化: 正月建寅,二月卯,三月辰...)
    # 实时木星所在的二十八宿 (基于地心黄经 + 岁差修正)
    # 传统二十八宿各宿度: 角12,亢9,氐15,房5,心5,尾18,箕11,斗26,牛8,女12,
    # 虚10,危17,室16,壁9,奎16,娄12,胃14,昴11,毕16,觜2,参9,井33,鬼4,
    # 柳15,星7,张18,翼18,轸17
    XIU_NAMES = ['角','亢','氐','房','心','尾','箕',
                 '斗','牛','女','虚','危','室','壁',
                 '奎','娄','胃','昴','毕','觜','参',
                 '井','鬼','柳','星','张','翼','轸']
    XIU_DEG =   [12,9,15,5,5,18,11,
                 26,8,12,10,17,16,9,
                 16,12,14,11,16,2,9,
                 33,4,15,7,18,18,17]
    # 角宿起始黄经 ≈ 184° at J2000 + 岁差(约0.014°/年)
    precession_angle = (jd - J2000) / 365.25 * 0.014
    ang_base = 184 + precession_angle  # 角宿起始黄经
    # 累计宿度 → 各宿起始黄经
    xiu_starts = []
    cum = 0
    for deg in XIU_DEG:
        xiu_starts.append(cum)
        cum += deg
    # 木星黄经相对于角宿起点的偏移
    jup_offset = (jup_now - ang_base + 360) % 360
    jupiter_xiu = ''
    for i in range(len(XIU_NAMES) - 1, -1, -1):
        if jup_offset >= xiu_starts[i]:
            jupiter_xiu = XIU_NAMES[i]
            break
    
    # 实时木星所在的星次 (十二次, 30°一等, 星纪起于冬至≈270°)
    CI_NAMES = ['星纪','玄枵','娵訾','降娄','大梁','实沈',
                '鹑首','鹑火','鹑尾','寿星','大火','析木']
    ci_start = 270 + precession_angle  # 星纪起始黄经 (冬至点)
    jup_ci_offset = (jup_now - ci_start + 360) % 360
    jupiter_ci = CI_NAMES[int(jup_ci_offset / 30) % 12]
    
    # 月建
    MONTH_JIAN = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
    month_jian = MONTH_JIAN[bazi_month - 1] if bazi_month > 0 else ''
    dou_jian_month = f'{year_zhi_str}年斗建在{DOU_JIAN.get(year_zhi_str,"")}　　{month_jian}月附近木日重合'
    
    return {
        'sui_yun': sui_yun,
        'si_tian': si_tian,
        'zai_quan': zai_quan,
        'foot_jingluo': foot_jingluo,
        'zhu_yun': current_zhu_yun,
        'zhu_qi': current_qi,
        'zhu_qi_period': current_qi_period,
        'hand_jingluo': hand_jingluo,
        'tianxiang': f'{year}年{month}月{day}日　　木日相差近{abs(diff_now):.0f}°（{"东" if diff_now >= 0 else "西"}）',
        'dou_jian_text': dou_jian_month,
        'xingci_text': f'木星在{jupiter_xiu}宿（{jupiter_ci}）',
        'precession_offset': f'木躔星次相对历元大约偏移{precession_angle:.0f}°',
    }
