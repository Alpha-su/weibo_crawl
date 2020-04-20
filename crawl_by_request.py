import re
from pprint import pprint
import database
import requests
from scrapy import Selector
from urllib.parse import urlencode
import datetime
import random

COOKIE = 'SINAGLOBAL=2369024381646.083.1568719988213; login_sid_t=b0ab4f3e618d8624f6fb7f05ced95b16; cross_origin_proto=SSL; _s_tentry=cn.bing.com; Apache=713238676684.1003.1587192631917; ULV=1587192632930:9:1:1:713238676684.1003.1587192631917:1585548137802; appkey=; un=2017202087@ruc.edu.cn; SCF=AuDv4qH-BJEzpkv-OA89CMjwe8gYFC_Rydhw6hb7OKEGJ_q4iBhB7hG-ELIhfojEPbqV0dqBP1QyDeebhJ6AFv4.; SUHB=0TPVFFpzwiYjHc; SSOLoginState=1587308867; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Whug1J09jMDygr879obXUaN5JpX5oz75NHD95QNSheReKMcSoMNWs4DqcjeMs87qHv0UK2EeKeR; ALF=1589900937; SUB=_2A25zmBnZDeRhGeFK6FoQ9yjKzDuIHXVRYqeRrDV8PUJbkNANLU7skW1NQ3GAu1xBFRBWh_vauG6v1ScDprmv6nrX; wvr=6; UOR=,,cn.bing.com; webim_unReadCount=%7B%22time%22%3A1587365119845%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A10%2C%22msgbox%22%3A0%7D'


def get_one_page(url,cookie,timeout=2):
    headers = {
        'Accept': 'text / html, application / xhtml + xml, application / '
                  'xml;q = 0.9, image / webp, image / apng, * / *;q = 0.8, application / '
                  'signed - exchange;v = b3',
        'Accept - Encoding': 'gzip, deflate, br',
        'Accept - Language': 'zh - CN, zh;q = 0.9, en;q = 0.8',
        'Cache - Control': 'max - age = 0',
        'Connection': 'keep - alive',
        
        'Cookie': COOKIE,
        # 'Host': 'weibo.com',
        # 'Referer': 'https: // s.weibo.com / weibo / % 25E5 % 259E % 2583 % 25E5 % 259C % 25BE % 25E5 % 2588 % 2586 % 25E7 % 25B1'
        #            ' % 25BB?topnav = 1 & wvr = 6 & b = 1',
        # 'Upgrade - Insecure - Requests': '1',
        'User - Agent': 'Mozilla / 5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 75.0.3770.142Safari / 537.36'
    }
    # print(url)
    response = requests.get(url, headers=headers,timeout=timeout,allow_redirects=False)
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
    begin_time, end_time = '2020-02-08-00', '2020-02-08-01'
    db = database.Mysql('root','990211','weibo')
    while True:
        for page in range(1, 51):
            params = {
                'q': '政府',
                'typeall': 1,
                'suball': 1,
                'timescope': 'custom:' + begin_time + ':' + end_time,
                'Refer': 'g',
                'page': page
            }
            url = "https://s.weibo.com/weibo?" + urlencode(params)
            html = get_one_page(url)
            if html:
                parse_user(html,db)
        begin_time, end_time = get_next_time(end_time)
        print(end_time)
        if begin_time is None:
            break

def parse_friends(html):
    try:
        friends_name = re.findall(r'<a class="S_txt1".*?>(.*?)<\S\Sa>',html,re.S)
        # print(friends_name)
        return [item.strip() for item in friends_name]
    except Exception as e:
        print(e)
        return []
    

def get_all_friends(uid,cookie):  # 获取单个用户的关注列表
    name_list = []
    for page_num in range(1,200):
        params = {
                     'pids': 'Pl_Official_HisRelation__59',
                     'page': page_num,
                     'ajaxpagelet': '1',
                     'ajaxpagelet_v6': '1',
        # Pl_Official_HisRelation__59
        }
        url = 'https://weibo.com/p/100505{uid}/follow?'.format(uid=uid)
        url = url + urlencode(params)
        # print(url)
        response = get_one_page(url,cookie)
        if not response:continue
        try:
            response = eval(response[23:-11])['html']
        except Exception as e:
            print('获取响应阶段出现错误！' + str(e))
            continue
        # print(response)
        # return
        if not response:
            continue
        else:
            name_per_page = parse_friends(response)
            if not name_per_page:  # 翻页到尽头了
                break
            else:
                name_list = name_list + name_per_page
    return name_list

def get_user_detail():
    db = database.Mysql('root','990211','weibo')
    raw_user = db.select('user')
    sample_user = random.sample(raw_user,100000)
    for item in sample_user:
        href = item[1]
        uid = re.findall(r'.com/(.*?)\Srefer',href)[0]
        print('uid: {}'.format(uid))
        try:
            result = get_one_page(url='https://weibo.com/p/100505{uid}/info?mod=pedit_more'.format(uid=uid),timeout=1)
            pattern1 = r'<strong class=\S"W_f18\S">(.*?)<\S\Sstrong>'
            pattern2 = r'<span class=\S"pt_detail\S">(.*?)<\S\Sspan>'
            tmp1 = re.findall(pattern1,result,re.S)
            tmp2 = re.findall(pattern2,result.re.S)
            friends_count,followers_count,article_count = tmp1[0],tmp1[1],tmp1[2]
            if followers_count < 100000:
                friends = ' '.join(get_all_friends(uid))
            else:continue
            location = tmp2[1]
            gender = tmp2[2]
            tmp_dict = {'id':uid,'name':item[0],'location':location,'gender':gender,'followers_count':followers_count,
                        'friends_count':friends_count,'article_count':article_count,'friends':friends}
            print(tmp_dict)
            db.insert_one('user_detail',tmp_dict)
        except Exception as e:
            print(e)
            continue

if __name__ == '__main__':
    result = get_all_friends('5840965490',cookie)
    pprint(result)
    # print(len(result))
    
    # print(result)
    # pprint([item.strip() for item in re.findall(pattern2,result,re.S)])
    # print(get_user_detail())
    # get_user_detail()
    