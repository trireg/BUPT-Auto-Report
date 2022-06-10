from constant import *


import requests, re, json, copy, traceback


def ncov_report(username, password, name, is_useold):
    session = requests.Session()
    login_page = session.get(LOGIN_PAGE,headers={**COMMON_HEADERS, **COMMON_POST_HEADERS, 'Referer': HEADERS.REFERER_LOGIN_API
                 })
    submit = re.findall('(<input.*?name="submit".*value=")(.+)(")',login_page.text)[0][1]
    type = "username_password"
    execution = re.findall('(<input\s*name="execution".*?value=")(.+?)(")', login_page.text)[0][1]
    evenId = re.findall('(<input.*?name="_eventId".*value=")(.+)(")', login_page.text)[0][1]
    print('登录北邮 nCoV 上报网站')
    login_res = session.post(
        LOGIN_API,
        data={'username': username, 'password': password,
              'submit':submit,"type":type,
              "execution":execution,'_eventId':evenId},
        cookies=login_page.cookies,
        headers={**COMMON_HEADERS, **COMMON_POST_HEADERS, 'Referer': HEADERS.REFERER_LOGIN_API,
                 })
    # if login_res.status_code == 302:
    eai_sess = 'bem8ebuk320fgeiuulddvupgg7'
    UUkey = '7e2fe9c2bf6fb20788cc52f4eda41e76'
    cas_api = session.get(login_res.url,cookies={"eai-sess":eai_sess,"UUkey":UUkey})
    if cas_api.status_code != 200:
        raise RuntimeError('cas_api 状态码不是 200')
    # get_res = session.get(
    #     GET_API,
    #     headers={**COMMON_HEADERS, 'Accept': HEADERS.ACCEPT_HTML},
    # )
    # if get_res.status_code != 200:
    #     raise RuntimeError('get_res 状态码不是 200')
    try:
        old_data = json.loads('{' + re.findall(r'(?<=oldInfo: {).+(?=})', cas_api.text)[0] + '}')
    except:
        raise RuntimeError('未获取到昨日打卡数据，请今日手动打卡明日再执行脚本或使用固定打卡数据')
    post_data = json.loads(copy.deepcopy(INFO).replace("\n", "").replace(" ", ""))
    if is_useold:
        try:
            for k, v in old_data.items():
                if k in post_data:
                    post_data[k] = v
            geo = json.loads(old_data['geo_api_info'])

            province = geo['addressComponent']['province']
            city = geo['addressComponent']['city']
            if geo['addressComponent']['city'].strip() == "" and len(re.findall(r'北京市|上海市|重庆市|天津市', province)) != 0:
                city = geo['addressComponent']['province']
            area = province + " " + city + " " + geo['addressComponent']['district']
            address = geo['formattedAddress']
            post_data['province'] = province
            post_data['city'] = city
            post_data['area'] = area
            post_data['address'] = address

            # 强行覆盖一些字段
            post_data['ismoved'] = 0  # 是否移动了位置？否
            post_data['bztcyy'] = ''  # 不在同城原因？空
            post_data['sfsfbh'] = 0  # 是否省份不合？否
        except:
            print("加载昨日数据错误，采用固定数据")
            post_data = json.loads(copy.deepcopy(INFO).replace("\n", "").replace(" ", ""))
    report_res = session.post(
        REPORT_API,
        data=post_data,
        headers={**COMMON_HEADERS,**COMMON_POST_HEADERS,'Referer': HEADERS.REFERER_POST_API,},
    )
    if report_res.status_code != 200:
        raise RuntimeError('report_res 状态码不是 200')
    return post_data,report_res.text


def server_push(send_key: str,title: str,msg: str):
    server_push_url = "https://sctapi.ftqq.com/{}.send".format(send_key)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        'title':title,
        'desp':msg
    }
    return requests.post(url=server_push_url, headers=headers,data = body)

table = ['| name | msg |','|  :----:  | :----:  |']
title ='《每日填报》{success}/{total}填报成功!'
total = len(USERS)
success = 0
for user in  USERS:
    username,password,name,useold=user
    try:
        data,res = ncov_report(username=username,password=password,name=name,is_useold=(useold==0))

    except:
        data,res = '',traceback.format_exc()
    else:
        success += 1
    msg = '| '+ name + ' | ' + res + ' |'
    table.append(msg)
#     print(msg)
post_msg = '\n'.join(table)
server_push(SENDKEY,title.format(success = success,total = total),post_msg)
