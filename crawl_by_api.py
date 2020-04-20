from weibo import APIClient

import database
import re
import time

APP_KEY = '3131170114'  # 注意替换这里为自己申请的App信息
APP_SECRET = '6d598ad9eee096d07cc4d62bd41da086'
CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'  # 回调授权页面

def access():  # 获得weiboAPI登陆权限
    # 利用官方微博SDK
    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
    # 得到授权页面的url，利用webbrowser打开这个url
    url = client.get_authorize_url()
    print(url)
    
    # 获取code=后面的内容
    print('输入url中code后面的内容后按回车键：')
    code = input()
    r = client.request_access_token(code)
    access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
    expires_in = r.expires_in
    
    # 设置得到的access_token
    client.set_access_token(access_token, expires_in)
    return client


# 可以打印下看看里面都有什么东西
# statuses = client.get.users__show(uid='6141121127')  # 获取当前登录用户以及所关注用户（已授权）的微博
# print(statuses)
# length = len(statuses)
# print(length)
# 输出了部分信息
# for i in range(0, length):
#     print(u'昵称：' + statuses[i]['user']['screen_name'])
#     print(u'简介：' + statuses[i]['user']['description'])
#     print(u'位置：' + statuses[i]['user']['location'])
#
#     print(u'微博：' + statuses[i]['text'])

def get_user_detail():
    client = access()
    detail = client.users__show(uid="1317579221")
    print(detail)
    return
    # db = database.Mysql('root','990211','weibo')
    # result = db.select('user')[:1]
    # for item in result:
    #     name = item[0]
    #     print(name)
    #     detail = client.users__show(screen_name=name)
    #     print(detail)
        
    
if __name__ == '__main__':
    get_user_detail()