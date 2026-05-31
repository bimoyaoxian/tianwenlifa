#!/usr/bin/env python3
"""
原站API代理 - 使用Playwright调用原站后端API
返回的结果与原站完全一致
"""
import json, os, subprocess, tempfile

API_URL = 'https://website.ganzhilifa.com:8080/ZiPingController'
SCRIPT = '''
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Hook XHR to capture response
  let result = null;
  await page.exposeFunction('captureResult', (data) => { result = JSON.parse(data); });
  
  await page.addInitScript(() => {
    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(data) {
      this.addEventListener('load', function() {
        if (this.responseText && this.responseText.length > 50) {
          try { window.captureResult(this.responseText); } catch(e) {}
        }
      });
      return origSend.apply(this, arguments);
    };
  });
  
  await page.goto('https://www.sitianxueyuan.com/bazi.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  
  // Fill form and submit
  await page.locator('#pai_pan_name').fill(YOUR_NAME);
  await page.locator('#Cal_y').fill(YOUR_YEAR);
  await page.locator('#Cal_m').fill(YOUR_MONTH);
  await page.locator('#Cal_d').fill(YOUR_DAY);
  await page.locator('#Cal_s').selectOption(YOUR_HOUR);
  await page.locator('#gender_sex').selectOption(YOUR_GENDER);
  await page.getByRole('button', { name: '排盘' }).click();
  await page.waitForTimeout(2000);
  
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(e => {});
'''

def get_bazi_from_api(year, month, day, hour, minute=0, gender='男', tai_yuan=280):
    """通过Playwright代理调用原站API获取八字排盘结果"""
    g = '1' if gender == '男' else '0'
    
    script = SCRIPT.replace('YOUR_NAME', f'test_{year}{month}{day}')
    script = script.replace('YOUR_YEAR', str(year))
    script = script.replace('YOUR_MONTH', str(month))
    script = script.replace('YOUR_DAY', str(day))
    script = script.replace('YOUR_HOUR', str(hour))
    script = script.replace('YOUR_GENDER', g)
    
    # 写入临时JS文件
    tmpfile = os.path.join(tempfile.gettempdir(), f'bazi_proxy_{year}_{month}_{day}_{hour}.js')
    with open(tmpfile, 'w', encoding='utf-8') as f:
        f.write(script)
    
    try:
        result = subprocess.run(
            ['node', tmpfile],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.stdout and result.stdout.strip():
            return json.loads(result.stdout.strip())
        return None
    except Exception as e:
        print(f'API代理错误: {e}')
        return None
    finally:
        try: os.remove(tmpfile)
        except: pass


if __name__ == '__main__':
    # 测试
    result = get_bazi_from_api(2026, 5, 27, 16)
    if result:
        print(f'年: {result["year"]}')
        print(f'月: {result["month"]}')
        print(f'日: {result["day"]}')
        print(f'时: {result["hour"]}')
        print(f'大运: {" ".join(result["daYun"])}')
