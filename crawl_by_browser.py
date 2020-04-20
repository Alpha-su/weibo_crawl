from pprint import pprint

import database
import asyncio
import random
from aiomultiprocess import Pool
import re
from pyppeteer import launch
from scrapy import Selector
from crawl_by_request import get_all_friends


COOKIE = '_T_WM=29379506481; ALF=1589854865; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WhpFuILj2nn.Mfn.jlzipO95JpX5K-hUgL.FoM71Kn7SoeXSoB2dJLoIpzLxKBLBonL1h5LxK.L1h-LBK-t; SCF=AuDv4qH-BJEzpkv-OA89CMjwe8gYFC_Rydhw6hb7OKEGhYgL9NSubJj0RSnK7quKXAsRxqPXF7sGAXpas34JQPo.; SUB=_2A25zn5TRDeRhGeFO4loR9i3IzTiIHXVRYzyZrDV6PUJbktANLVDmkW1NQSquqFhTGmMmey-XeYRnxhsBxWB8LNAP; SUHB=02Mvi0kwjO-U6b; SSOLoginState=1587274881; WEIBOCN_FROM=1110006030; MLOGIN=1; XSRF-TOKEN=d0ffdf; M_WEIBOCN_PARAMS=oid%3D4479860497788363%26lfid%3D1076036141121127%26luicode%3D20000174%26uicode%3D20000174'
ACCOUNT = '2017202087@ruc.edu.cn'
PWD = 'sgl1303262109'


async def init_browser():
    browser = await launch({
        'headless': False,  # 关闭无头模式
        # 'devtools': True,  # 打开 chromium 的 devtools
        # 'executablePath': '你下载的Chromium.app/Contents/MacOS/Chromiu',
        'args': [
            '--log-level=3  ',
            '--disable-images',
            '--disable-extensions',
            '--hide-scrollbars',
            '--disable-bundled-ppapi-flash',
            '--mute-audio',
            # '--no-sandbox',
            # '--disable-dev-shm-usage',  # 禁止使用/dev/shm，防止内存不够用,only for linux
            # '--disable-setuid-sandbox',
            '--disable-gpu',
            '–single-process',  # 将Dom的解析和渲染放到一个进程，省去进程间切换的时间
            '--disable-infobars',  # 禁止信息提示栏
            '--no-default-browser-check',  # 不检查默认浏览器
            '--disable-hang-monitor',  # 禁止页面无响应提示
            '--disable-translate',  # 禁止翻译
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-zygote',
        ],
        'dumpio': True,
    })
    page = await browser.pages()
    await page[0].close()
    return browser


async def request_check(req):
    '''请求过滤'''
    if req.resourceType in ['image', 'media']:
        await req.abort()
    else:
        await req.continue_()


async def intercept_response(res):
    resourceType = res.request.resourceType
    if resourceType in ['xhr']:
        resp = await res.text()
        if not resp:
            print("翻页到头")


def parse_user(uid, cookie, content):
    selector = Selector(text=content)
    try:
        tmp = selector.xpath('//*[@class="mod-fil-fans"]//span/text()').extract()
        friends_count, followers_count = int(tmp[0]), int(tmp[1])
    except:
        return None
    if followers_count > 100000: # 筛选大V
        return None
    else:
        name = selector.xpath('//*[@class="mod-fil-n"]//text()').extract_first()
        gender_text = selector.xpath('//*[@class="mod-fil-name m-txt-cut"]//i/@class').extract_first()
        if gender_text == "m-icon m-icon-male":
            gender = 'm'
        else:
            gender = 'f'
        description = selector.xpath('//p[@class="mod-fil-desc m-text-cut"]/text()').extract_first()
        try:
            friends = ' '.join(get_all_friends(uid,cookie))
        except Exception as e:
            friends = None
            print('获取关注列表失败！ ' + str(e))
        return {'id':uid,'name':name,'gender':gender,'followers_count':followers_count,
                'friends_count':friends_count,'description':description,'friends':friends}
    
    
async def get_cookie(page):
    cookies_list = await page.cookies()
    cookies = ''
    for cookie in cookies_list:
        str_cookie = '{0}={1};'
        str_cookie = str_cookie.format(cookie.get("name"), cookie.get('value'))
        cookies += str_cookie
        # print(cookies)
        # 将cookie 放入 cookie 池 以便多次请求 封账号 利用cookie 对搜索内容进行爬取
    return cookies


def parse_context(db,uid,context):
    selector = Selector(text=context)
    card_list = selector.xpath('//div[@class="card-main"]')
    for card in card_list:
        time = card.xpath('.//span[@class="time"]//text()').extract_first()
        try:
            if time[:4] == '2019':
                continue
            elif (not time) or time[2] != '-':
                continue
        except:continue
        else:
            text_og = ''.join([item.strip() for item in card.xpath('.//div[@class="weibo-og"]//div[@class="weibo-text"]/text()').extract()])
            text_rp = ''.join([item.strip() for item in card.xpath('.//div[@class="weibo-rp"]//div[@class="weibo-text"]/span[2]/text()').extract()])
            attitude = [item.strip() for item in card.xpath('.//*[@class="m-ctrl-box m-box-center-a"]//h4/text()').extract()]
            repost,comment,star = 0,0,0
            try:
                if attitude[0] != "转发":
                    repost = int(attitude[0])
                if attitude[1] != "评论":
                    comment = int(attitude[1])
                if attitude[2] != "赞":
                    star = int(attitude[2])
            except:pass
            data_dict = {'id':uid,'created_at':time,'origin_text':text_og,'retweet_text':text_rp,'reposts_count':repost,
                         'comments_count':comment,'star_count':star}
            db.insert_one('content',data_dict)
            # print(data_dict)
        
            
def test_over(content):
    selector = Selector(text=content)
    times = selector.xpath('//span[@class="time"]/text()').extract()
    for time in times:
        try:
            if time[:4] == "2019":
                return True
        except:
            return True
    return False


async def solve_one(uid):
    db = database.Mysql('root','990211','weibo')
    # browser = init_browser()
    browser = await launch({
        # 'headless': False,  # 关闭无头模式
        # 'devtools': True,  # 打开 chromium 的 devtools
        # 'executablePath': '你下载的Chromium.app/Contents/MacOS/Chromiu',
        'args': [
            '--log-level=3  ',
            '--disable-images',
            '--disable-extensions',
            '--hide-scrollbars',
            '--disable-bundled-ppapi-flash',
            '--mute-audio',
            '--disable-accelerated-2d-canvas', # canvas渲染
            '--no-sandbox',
            '--disable-dev-shm-usage',  # 禁止使用/dev/shm，防止内存不够用,only for linux
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '–single-process',  # 将Dom的解析和渲染放到一个进程，省去进程间切换的时间
            '--disable-infobars',  # 禁止信息提示栏
            '--no-default-browser-check',  # 不检查默认浏览器
            '--disable-hang-monitor',  # 禁止页面无响应提示
            '--disable-translate',  # 禁止翻译
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-zygote',
        ],
        'dumpio': True,
    })
    profile_url = 'https://m.weibo.cn/u/{uid}'.format(uid=uid)
    page = await browser.newPage()
    await page.evaluate("""
        () =>{
            Object.defineProperties(navigator,{
                webdriver:{
                get: () => false
                }
            })
        }
    """)
    await asyncio.wait([page.waitForNavigation(),page.goto('https://passport.weibo.cn/signin/login?')])
    await asyncio.sleep(2)
    await page.type('#loginName',ACCOUNT)
    await page.type('#loginPassword',PWD)
    await page.keyboard.press('Enter')
    await page.setRequestInterception(True)
    page.on('request', request_check)
    await asyncio.wait([page.waitForNavigation(),page.goto(profile_url)])
    await asyncio.sleep(2)
    cookie = await get_cookie(page)
    # print(cookie)
    user_dict = parse_user(uid,cookie,await page.content())
    if not user_dict:return
    else: db.insert_one('user_detail',user_dict)
    # pprint(user_dict)
    # 爬取用户发文
    for i in range(200):
        print(i)
        # 滚动到页面底部
        try:
            page.on('request', request_check)
            await page.evaluate('window.scrollBy({top:document.documentElement.scrollHeight})')
            # page.on('response', intercept_response)
        except Exception as e:
            print(e)
            await asyncio.sleep(1)
        await asyncio.sleep(0.5)
        if test_over(await page.content()):
            break
    parse_context(db,uid,await page.content())
    await browser.close()


async def main():
    db = database.Mysql('root', '990211', 'weibo')
    raw_user = db.select('user')
    sample_user = random.sample(raw_user, 100000)
    uid_list = [re.findall(r'.com/(.*?)\Srefer',item[1])[0] for item in sample_user]
    # uid_list = ['1686695593','6994312954','3646683305','3781835550']
    # uid_list = ['3646683305']
    # config_list = split_task(config_dli)
    for i in range(2000):
        begin = i * 50
        end = (i+1) * 50
        async with Pool() as pool:
            await pool.map(solve_one, uid_list[begin:end])
        # await pool.map(solve_one, uid_list[2:])
        
if __name__ == '__main__':
    asyncio.run(main())
    # str1 = '{"ok":1,"data":"\u6bcf\u65e5\u4e00\u5584"}'
    # print(json.loads(str1)['data'])