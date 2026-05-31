#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
司天学苑完整复刻 - Web 服务
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

from calendar_engine.bazi import calculate_bazi
from calendar_engine.luojia_calendar import get_luojia_bazi, get_luojia_calendar, get_luojia_year
from calendar_engine.luojia_calendar import get_luojia_month_date, _luo_jd
from calendar_engine.astronomy import (
    julian_day, julian_day_to_date, get_solar_term_jd, SOLAR_TERMS,
    local_time_to_true_solar, get_solar_system_positions,
)
from calendar_engine.lunar import solar_to_lunar
from calendar_engine.wuyun_liuqi import get_wuyun_liuqi_info
from calendar_engine.ganzhi import (
    year_gan_zhi, month_gan_zhi, day_gan_zhi, hour_gan_zhi,
    get_na_yin, TIAN_GAN, DI_ZHI, JIA_ZI, NA_YIN_TABLE,
)
from luojia_full_engine import get_bazi as new_luojia_bazi

app = Flask(__name__)

CITIES = {
    '': '-- 选择城市 --', 'beijing': '北京', 'shanghai': '上海',
    'guangzhou': '广州', 'shenzhen': '深圳', 'chengdu': '成都',
    'wuhan': '武汉', 'nanjing': '南京', 'tianjin': '天津',
    'chongqing': '重庆', 'hangzhou': '杭州', 'xian': '西安',
    'shenyang': '沈阳', 'qingdao': '青岛', 'changsha': '长沙',
    'zhengzhou': '郑州', 'kunming': '昆明', 'haerbin': '哈尔滨',
    'lanzhou': '兰州', 'nanning': '南宁',
    'taipei': '台北', 'hongkong': '香港',
}
CITY_LONS = {
    'beijing': 116.4, 'shanghai': 121.5, 'guangzhou': 113.3,
    'shenzhen': 114.1, 'chengdu': 104.1, 'wuhan': 114.3,
    'nanjing': 118.8, 'tianjin': 117.2, 'chongqing': 106.6,
    'hangzhou': 120.2, 'xian': 108.9, 'shenyang': 123.4,
    'qingdao': 120.3, 'changsha': 113.0, 'zhengzhou': 113.6,
    'kunming': 102.7, 'haerbin': 126.6, 'lanzhou': 103.8,
    'nanning': 108.4, 'taipei': 121.5, 'hongkong': 114.2,
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/bazi')
def bazi():
    return render_template('bazi.html', cities=CITIES, city_lons=json.dumps(CITY_LONS))


@app.route('/luojia')
def luojia():
    return render_template('luojia.html')


@app.route('/tools')
def tools():
    return render_template('tools.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# ===== API =====

@app.route('/api/calendar', methods=['POST'])
def api_calendar():
    """获取某年某月的日历数据 (含农历、干支、节气)"""
    data = request.json
    year = int(data['year'])
    month = int(data['month'])
    
    # 生成该月日历
    _, month_days = calendar_month(year, month)
    
    # 当月节气
    terms = []
    for ti in range(24):
        tj = get_solar_term_jd(year, ti)
        y, m, d, h = julian_day_to_date(tj)
        if m == month:
            hi, mi = int(h), int((h - int(h)) * 60)
            terms.append({
                'name': SOLAR_TERMS[ti], 'day': d, 'hour': hi, 'minute': mi
            })
    
    # 右侧信息面板
    info = get_calendar_info(year, month)
    
    return jsonify({
        'days': month_days,
        'terms': terms,
        'info': info,
    })


@app.route('/api/bazi', methods=['POST'])
def api_bazi():
    data = request.json
    year = int(data['year']); month = int(data['month']); day = int(data['day'])
    hour_raw = data.get('hour')
    hour = int(hour_raw) if hour_raw is not None and hour_raw != '' else None
    minute = int(data.get('minute', 0))
    gender = data.get('gender', '男')
    system = data.get('system', 'luojia')
    lon = data.get('longitude')
    if lon and lon != 'null' and lon != '':
        lon = float(lon)
    else:
        lon = None
    
    if system == 'luojia':
        result = get_luojia_bazi(year, month, day, hour, minute, gender, longitude=lon)
        result['system_name'] = '落甲历'
        # 大运
        from calendar_engine.dayun import calculate_dayun
        dy = calculate_dayun(year, month, day, hour, minute, 0, gender, year,
                            result['year_pillar'], result['month_pillar'],
                            result['day_pillar'], result['hour_pillar'], lon)
        result.update(dy)
    else:
        hour_unknown = (hour is None)
        result = calculate_bazi(year, month, day, hour if hour is not None else 12, minute, 0, gender, lon)
        result['system_name'] = '标准历法'
        # 未知时辰时覆盖时柱相关字段（calculate_bazi内部用了12导致假时柱）
        if hour_unknown:
            result['hour_pillar'] = None
            result['hour_nayin'] = ''
            result['hour_shi_shen'] = ''
            result['hour_gan'] = '*'
            result['hour_zhi'] = '*'
            result['hour_cang_gan'] = []
            result['hour_cang_gan_shi_shen'] = []
        from calendar_engine.dayun import calculate_dayun
        dy = calculate_dayun(year, month, day, hour, minute, 0, gender,
                            result.get('bazi_year', year),
                            result['year_pillar'], result['month_pillar'],
                            result['day_pillar'], result['hour_pillar'], lon,
                            mode='standard')
        result.update(dy)
    
    # 农历月日（用于紫薇/农历排盘复制）
    lunar = solar_to_lunar(year, month, day)
    result['lunar_month'] = lunar.month_name
    result['lunar_day'] = lunar.day_name

    result['input_info'] = {'year': year, 'month': month, 'day': day,
                            'hour': hour, 'minute': minute, 'gender': gender}
    return jsonify(result)


@app.route('/api/luojia_calendar', methods=['POST'])
def api_luojia_calendar():
    """落甲历全年数据"""
    data = request.json
    year = int(data['year'])
    scheme = int(data.get('scheme', 1))
    cal = get_luojia_calendar(year, scheme)
    # get_luojia_year 现在需要月日参数，这里用默认值6月1日
    return jsonify({'months': cal, 'year_pillar': get_luojia_year(year, 6, 1)})


@app.route('/api/solar_terms', methods=['POST'])
def api_solar_terms():
    data = request.json
    year = int(data['year'])
    terms = []
    for ti, name in enumerate(SOLAR_TERMS):
        tj = get_solar_term_jd(year, ti)
        y, m, d, h = julian_day_to_date(tj)
        hi, mi = int(h), int((h - int(h)) * 60)
        terms.append({'name': name, 'month': m, 'day': d, 'hour': hi, 'minute': mi, 'jd': round(tj, 4)})
    return jsonify(terms)


@app.route('/api/solar_system', methods=['POST'])
def api_solar_system():
    """返回太阳系各行星当前日心位置 (用于前端太阳系动画)"""
    data = request.json
    year = int(data['year'])
    month = int(data['month'])
    day = int(data['day'])
    jd = julian_day(year, month, day)
    positions = get_solar_system_positions(jd)
    return jsonify(positions)


def calendar_month(year, month):
    """生成单月日历数据"""
    import calendar as cal_mod
    _, max_day = cal_mod.monthrange(year, month)
    days = []
    for d in range(1, max_day + 1):
        jd = julian_day(year, month, d)
        lunar = solar_to_lunar(year, month, d)
        day_gz = day_gan_zhi(jd)
        
        # 落甲历年月柱
        luo_year = get_luojia_year(year, month, d)
        luo_month = get_luojia_month_date(year, month, d)
        
        # 节气
        term_name = None
        for ti in range(24):
            tj = get_solar_term_jd(year, ti)
            ty, tm, td, _ = julian_day_to_date(tj)
            if tm == month and td == d:
                term_name = SOLAR_TERMS[ti]
                break
        
        dt = datetime(year, month, d)
        weekday = dt.weekday()
        weekday = 0 if weekday == 6 else weekday + 1  # 周日=0
        
        # 标准节气历年月柱
        li_chun_jd = get_solar_term_jd(year, 2)  # 立春
        if jd < li_chun_jd:
            std_year_num = year - 1
        else:
            std_year_num = year
        std_year_gz = year_gan_zhi(std_year_num)
        # 标准节气月
        std_month_gz = ''
        month_terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]
        for mi, ti in enumerate(month_terms):
            nti = month_terms[(mi + 1) % 12]
            nt_year = std_year_num + 1 if nti < ti else std_year_num
            tj = get_solar_term_jd(std_year_num, ti)
            ntj = get_solar_term_jd(nt_year, nti)
            if tj <= jd < ntj:
                std_month_gz = month_gan_zhi(JIA_ZI.index(std_year_gz) % 10, mi + 1)
                break

        # 五运六气 (基于落甲历年干)
        wlq = get_wuyun_liuqi_info(year, month, d, luo_year_pillar=luo_year)

        days.append({
            'day': d, 'weekday': weekday,
            'lunar_month': lunar.month_name,
            'lunar_day': lunar.day_name,
            'ganzhi': day_gz,
            'luo_year': luo_year,
            'luo_month': luo_month,
            'std_year': std_year_gz,
            'std_month': std_month_gz,
            'term': term_name,
            'jd': round(jd, 4),
            'wuyun': {
                'sui_yun': wlq['sui_yun'],
                'si_tian': wlq['si_tian'],
                'zai_quan': wlq['zai_quan'],
                'foot_jingluo': wlq['foot_jingluo'],
                'zhu_yun': wlq['zhu_yun'],
                'zhu_qi': wlq['zhu_qi'],
                'zhu_qi_period': wlq['zhu_qi_period'],
                'hand_jingluo': wlq['hand_jingluo'],
                'tianxiang': wlq['tianxiang'],
                'dou_jian_text': wlq['dou_jian_text'],
                'xingci_text': wlq['xingci_text'],
                'precession_offset': wlq['precession_offset'],
            },
        })
    return max_day, days


def get_calendar_info(year, month):
    """获取右侧信息面板数据"""
    now = datetime(year, month, 1)
    jd_today = julian_day(year, month, min(now.day, 28))
    
    # 年柱
    year_gz = year_gan_zhi(year)
    # 月柱 (以节气为界)
    from calendar_engine.luojia_calendar import get_luojia_year, get_luojia_month_date
    luo_year = get_luojia_year(year, month, 15)
    luo_month = get_luojia_month_date(year, month, 15)
    
    # 节气
    terms = []
    for ti in range(24):
        tj = get_solar_term_jd(year, ti)
        y, m, d, h = julian_day_to_date(tj)
        if m == month:
            hi, mi = int(h), int((h - int(h)) * 60)
            terms.append(f"{SOLAR_TERMS[ti]}: {d}日 {hi}:{mi:02d}")
    
    # 农历
    lunar = solar_to_lunar(year, month, 1)
    
    return {
        'year_gz': year_gz,
        'luo_year': luo_year,
        'luo_month': luo_month,
        'lunar_year': lunar.year,
        'terms': terms,
    }


@app.route('/api/luojia_new', methods=['POST'])
def api_luojia_new():
    """新落甲历引擎八字"""
    data = request.json
    year = int(data['year']); month = int(data['month']); day = int(data['day'])
    hour = int(data.get('hour', 12))
    result = new_luojia_bazi(year, month, day, hour)
    return jsonify(result)


@app.route('/api/verify_luojia')
def api_verify_luojia():
    """验证新引擎 vs API数据"""
    try:
        with open('api_30data.json', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return jsonify({'error': f'对照数据文件不可用: {str(e)}'}), 503
    from calendar_engine.astronomy import julian_day
    api_map = {r['todayJd']: r for r in data}
    api_cases = [
        (2026,5,27,16),(1990,6,15,8),(2024,1,15,12),(2000,1,1,0),(1984,8,8,12),
        (2023,12,22,6),(2025,3,20,14),(2028,7,15,10),(1995,12,25,22),(2020,4,10,6),
        (2010,8,18,14),(2015,3,5,9),(2005,7,20,18),(1998,1,28,6),(2030,6,1,12),
        (1988,9,10,3),(2022,11,15,20),(1978,4,5,5),(2035,2,14,8),(1992,10,30,15),
        (2018,12,1,1),(2003,5,18,7),(1975,8,22,16),(2040,3,10,11),(1980,7,25,4),
        (2012,1,23,21),(1996,9,5,13),(2029,11,8,2),(2008,4,15,10),(1970,12,31,23),
    ]
    results = []
    ok = 0; fail = 0
    for y, m, d, h in api_cases:
        this_jd = int(julian_day(y, m, d) + 0.5)
        res = new_luojia_bazi(y, m, d, h)
        api = api_map.get(this_jd)
        if api:
            y_ok = 'OK' if res['year_pillar'] == api['year'] else 'FAIL'
            m_ok = 'OK' if res['month_pillar'] == api['month'] else 'FAIL'
            d_ok = 'OK' if res['day_pillar'] == api['day'] else 'FAIL'
            h_ok = 'OK' if res['hour_pillar'] == api['hour'] else 'FAIL'
            status = 'OK' if all(s == 'OK' for s in [y_ok, m_ok, d_ok, h_ok]) else 'FAIL'
            if status == 'OK': ok += 1
            else: fail += 1
            results.append({
                'date': f'{y}-{m:02d}-{d:02d}', 'y': res['year_pillar'], 'm': res['month_pillar'],
                'd': res['day_pillar'], 'h': res['hour_pillar'],
                'api_y': api['year'], 'api_m': api['month'], 'api_d': api['day'], 'api_h': api['hour'],
                'y_ok': y_ok, 'm_ok': m_ok, 'd_ok': d_ok, 'h_ok': h_ok, 'status': status
            })
    return jsonify({'ok': ok, 'fail': fail, 'total': ok+fail, 'details': results})


@app.route('/luojia_calc')
def luojia_calc():
    """落甲历八字计算器（纯前端，可输入任意日期）"""
    return '''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><title>落甲历验证 - 任意日期查询</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Times New Roman","宋体",serif;background:#e8e0d0;color:#000;padding:30px}
.box{border:1px solid #999;padding:20px;max-width:500px;margin:0 auto;background:#f8f4ec}
h3{text-align:center;margin-bottom:15px;letter-spacing:4px}
.row{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.row label{font-size:14px;display:flex;align-items:center;gap:4px}
.row input,.row select{border:1px solid #888;padding:4px 8px;background:#fff;font-size:14px;width:70px}
button{padding:6px 30px;border:1px solid #888;background:#f0e8d8;cursor:pointer;letter-spacing:4px}
button:hover{background:#e0d8c8}
.result{margin-top:15px;padding:12px;border:1px solid #bbb;background:#fff;display:none}
.pillar{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0}
.pillar-item{text-align:center;padding:10px;border:1px solid #bbb}
.pillar-item .label{font-size:11px;color:#666}
.pillar-item .value{font-size:24px;font-weight:bold;letter-spacing:4px}
.status{font-size:12px;color:#888;margin-top:8px;text-align:center}
.err{color:#c00;font-size:13px;text-align:center;margin-top:8px}
</style></head><body>
<div class="box">
<h3>落甲历 八字查询</h3>
<div class="row">
<label>年 <input type="number" id="y" value="2026" min="-4000" max="4000" style="width:80px"></label>
<label>月 <input type="number" id="m" value="5" min="1" max="12"></label>
<label>日 <input type="number" id="d" value="27" min="1" max="31"></label>
<label>时 <select id="h"><option value="23">23-1</option><option value="1">1-3</option><option value="3">3-5</option><option value="5">5-7</option><option value="7">7-9</option><option value="9">9-11</option><option value="11">11-13</option><option selected value="13">13-15</option><option value="15">15-17</option><option value="17">17-19</option><option value="19">19-21</option><option value="21">21-23</option></select></label>
<button onclick="calc()">查询</button>
</div>
<div class="result" id="result">
<div class="pillar" id="pillars"></div>
<div class="status" id="status"></div>
</div>
<div class="err" id="err"></div>
<p style="font-size:11px;color:#888;margin-top:15px;text-align:center">与原版网站对比验证，支持公元前4000年至公元4000年</p>
</div>
<script>
async function calc(){
const y=document.getElementById('y').value;
const m=document.getElementById('m').value;
const d=document.getElementById('d').value;
const h=document.getElementById('h').value;
document.getElementById('err').textContent='';
document.getElementById('result').style.display='none';
try{
const r=await fetch('/api/luojia_new',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({year:y,month:m,day:d,hour:h})});
const j=await r.json();
document.getElementById('result').style.display='block';
const labels=['年柱','月柱','日柱','时柱'];
const vals=[j.year_pillar,j.month_pillar,j.day_pillar,j.hour_pillar];
let html='';
for(let i=0;i<4;i++){html+='<div class="pillar-item"><div class="label">'+labels[i]+'</div><div class="value">'+vals[i]+'</div></div>';}
document.getElementById('pillars').innerHTML=html;
document.getElementById('status').textContent=y+'-'+m+'-'+d+' '+h+':00 计算完成';
}catch(e){document.getElementById('err').textContent='错误: '+e.message;}
}
</script>
</body></html>'''


@app.route('/api/verify_date', methods=['POST'])
def api_verify_date():
    """验证任意日期"""
    data = request.json
    if not data or 'year' not in data or 'month' not in data or 'day' not in data:
        return jsonify({'error': '缺少必填字段: year/month/day'}), 400
    from calendar_engine.astronomy import julian_day
    y = int(data['year']); m = int(data['month']); d = int(data['day']); h = int(data.get('hour', 12))
    res = new_luojia_bazi(y, m, d, h)
    # 计算yi, mi供参考
    days = int(julian_day(y, m, d) - 2437700.16667 + 0.5)
    yi = days // 360
    mi = (days % 360) // 30
    res['ji_nian'] = yi; res['ji_yue'] = mi
    return jsonify(res)


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    print("=" * 50)
    print("  司天学苑完整复刻版 Web 服务")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, host='127.0.0.1', port=5000)
