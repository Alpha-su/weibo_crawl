from pprint import pprint
import database
import requests
from scrapy import Selector
from urllib.parse import urlencode
import datetime


def get_one_page(page_num, begin_time, end_time):
    headers = {
        'Accept': 'text / html, application / xhtml + xml, application / '
                  'xml;q = 0.9, image / webp, image / apng, * / *;q = 0.8, application / '
                  'signed - exchange;v = b3',
        'Accept - Encoding': 'gzip, deflate, br',
        'Accept - Language': 'zh - CN, zh;q = 0.9, en;q = 0.8',
        'Cache - Control': 'max - age = 0',
        'Connection': 'keep - alive',
        
        'Cookie': 'SINAGLOBAL=2369024381646.083.1568719988213; login_sid_t=b0ab4f3e618d8624f6fb7f05ced95b16; cross_origin_proto=SSL; _s_tentry=cn.bing.com; Apache=713238676684.1003.1587192631917; ULV=1587192632930:9:1:1:713238676684.1003.1587192631917:1585548137802; appkey=; UOR=,,login.sina.com.cn; WBStorage=42212210b087ca50|undefined; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Whug1J09jMDygr879obXUaN5JpX5K2hUgL.FoMXe0npS0qcS0M2dJLoI7p7qPWyPNSfeKzpe0nt; ALF=1618747848; SSOLoginState=1587211849; SCF=AuDv4qH-BJEzpkv-OA89CMjwe8gYFC_Rydhw6hb7OKEGHuQozQ--vReUozp-7sNdzuuBoxh5nju1AC9IEoDj72M.; SUB=_2A25znp4ZDeRhGeFK6FoQ9yjKzDuIHXVQ7YjRrDV8PUNbmtANLUXFkW9NQ3GAu2yc4YZMwi6LKZ55ALFyVdbZgFKA; SUHB=0KAh7rWIwKR5Bq; un=2017202087@ruc.edu.cn; wvr=6; webim_unReadCount=%7B%22time%22%3A1587212658877%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A1%2C%22msgbox%22%3A0%7D',
        'Host': 's.weibo.com',
        'Referer': 'https: // s.weibo.com / weibo / % 25E5 % 259E % 2583 % 25E5 % 259C % 25BE % 25E5 % 2588 % 2586 % 25E7 % 25B1'
                   ' % 25BB?topnav = 1 & wvr = 6 & b = 1',
        'Upgrade - Insecure - Requests': '1',
        'User - Agent': 'Mozilla / 5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 75.0.3770.142Safari / 537.36'
    }
    params = {
        'q': '政府',
        'typeall': 1,
        'suball': 1,
        'timescope': 'custom:' + begin_time + ':' + end_time,
        'Refer': 'g',
        'page': page_num
    }
    url = "https://s.weibo.com/weibo?" + urlencode(params)
    # print(url)
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8-sig'
    if response.status_code == 200:
        # print(response.text)
        return response.text
    else:
        print('can not get url: ' + url)
        return None


def get_next_time(end_time):
    begin_time = end_time
    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d-%H')
    delta = datetime.timedelta(hours=1)
    end_time = end_time + delta
    if end_time > datetime.datetime(year=2020, month=3, day=6, hour=23):  # 终止时间
        return None, None
    else:
        end_time = end_time.strftime('%Y-%m-%d-%H')
        return begin_time, end_time


def parse_user(html_content, db):
    selector = Selector(text=html_content)
    card_list = selector.xpath('//div[@class="card-wrap"]')  # 定位到每一条微博
    for card in card_list:
        nick_name = card.xpath('.//a[@class="name"]/text()').extract_first()
        name_url = card.xpath('.//a[@class="name"]/@href').extract_first()
        if nick_name and name_url:
            db.insert_one('user',{'nick_name':nick_name,'name_url':name_url})


def get_all_users():
    begin_time, end_time = '2020-01-06-00', '2020-01-06-01'
    db = database.Mysql('root','990211','weibo')
    while True:
        for page in range(1, 51):
            html = get_one_page(page, begin_time, end_time)
            if html:
                parse_user(html,db)

        begin_time, end_time = get_next_time(end_time)
        print(end_time)
        if begin_time == None:
            break


if __name__ == '__main__':
    print(get_all_users())