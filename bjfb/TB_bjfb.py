"""
cron: 59 9 * * *
new Env('滨江发布_兑换')
"""
import random
import string
import time

import execjs
import requests
from tls_client import Session

from common.task import QLTask
from common.util import log, get_chrome_session, get_error_msg

TASK_NAME = '滨江发布_兑换'
FILE_NAME = 'BJFB.txt'

with open(r"TB_BjfbEncrypt.js", "r+") as f:
    js_code = f.read()
js = execjs.compile(js_code)


def get_time(session: Session) -> str:
    name = '获取时间'
    url = 'https://service.jifenfu.net/gateway-service/time/currentTime'
    res = session.get(url)
    if res.text.count('success') and res.json().get('success'):
        return res.json().get('data').get('timestamp')
    return get_error_msg(name, res)


def dh_hf(session: Session, timestamp: str) -> str:
    name = '兑换10元话费'
    url = 'https://service.jifenfu.net/sspmarketingactivity-service/client/marketing/order/activity/create'
    data = '{"ifDeductPoints":1,"marketingActivityGoodsId":"1696823088732135425","marketingActivityId":"1696823088530808833","num":1,"priceDetailDTOS":[{"points":2000,"priceType":2,"priceValue":1000},{"points":0,"priceType":1,"priceValue":0}],"goodsGroupDTOS":[{"freight":0,"goodsPrice":0,"serviceCode":"wnzc","skuDTOS":[{"num":1,"serviceCode":"wnzc","skuId":"CBA040010DA","skuMarketPrice":"1000","salePrice":1000,"skuListPicUrl":"//ossimage.jifenfu.net/goodsBusiness/APPGoodsIcon/DA040008_2.jpg","skuName":"三网话费10元","preSaleType":"","preSalePostDelayDays":"","preSalePostDate":"","goodsPriceType":1,"points":"2000","cashAmount":1000,"skuStatus":1,"specSnapshot":"[{\\"specId\\":\\"6003\\",\\"specName\\":\\"规格\\",\\"specValueId\\":\\"1116\\",\\"specValue\\":\\"10元\\"}]","spuId":"6003","inventory":99,"goodsPriceShowDTO":{"goodsPriceShowType":1,"cashAmount":null,"points":2000},"ifServerCard":null,"ifDeductBenefitCard":0,"ifErpPriceType":0,"isActivity":1,"marketingActivityGoodsId":"1696823088732135425","marketingActivityId":"1696823088530808833","activityPrice":"0","goodsExtJson":{"ext":"[]","priceOriginType":1,"ifCurrentUserRechargeAccount":1,"currentUserRechargeAccountType":2},"activityPriceThreshold":0,"ifActivityPriceThreshold":0,"ifLimitArea":0,"commonDisplayExtData":{"errCodeMsg":[]},"rechargeAccount":"","rechargeType":"RA000001","goodsDisplayExtJson":{},"priceShowTypeSnapshot":"{\\"goodsPriceShowType\\":1,\\"cashAmount\\":null,\\"points\\":2000}"}]}],"totalPrice":0,"rechargeAccount":"","rechargeType":"RA000001","skuOrderUserInfoDTO":[{"serviceCode":"wnzc","spuId":"6003","skuId":"CBA040010DA","skuName":"三网话费10元","submitUserinfo":{"rechargeType":"RA000001","ext":{"addressId":null}}}]}'
    update_headers(session, data, timestamp)
    res = session.post(url, data=data)
    if res.text.count('success') and res.json().get('success'):
        return f'{name}: 兑换成功'
    return get_error_msg(name, res)


def dh_ek(session: Session, timestamp: str) -> str:
    name = '兑换10京东E卡'
    url = 'https://service.jifenfu.net/sspmarketingactivity-service/client/marketing/order/activity/create'
    data = '{"ifDeductPoints":1,"marketingActivityGoodsId":"1696823088648249345","marketingActivityId":"1696823088530808833","num":1,"priceDetailDTOS":[{"points":2000,"priceType":2,"priceValue":1000},{"points":0,"priceType":1,"priceValue":0}],"goodsGroupDTOS":[{"freight":0,"goodsPrice":0,"serviceCode":"wnkq","skuDTOS":[{"num":1,"serviceCode":"wnkq","skuId":"AGA0100A0IA","skuMarketPrice":"1000","salePrice":1000,"skuListPicUrl":"//ossimage.jifenfu.net/erpadmin/default/20210525/f7ce2a83-23d9-4cb2-bbff-8a20bbe6b0d2.jpg","skuName":"京东E卡10元","preSaleType":"","preSalePostDelayDays":"","preSalePostDate":"","goodsPriceType":1,"points":"2000","cashAmount":1000,"skuStatus":1,"specSnapshot":"[{\\"specId\\":\\"7069\\",\\"specName\\":\\"规格\\",\\"specValueId\\":\\"1005\\",\\"specValue\\":\\"10元\\"}]","spuId":"7069","inventory":10,"goodsPriceShowDTO":{"goodsPriceShowType":1,"cashAmount":null,"points":2000},"ifServerCard":null,"ifDeductBenefitCard":0,"ifErpPriceType":0,"useDescription":"//ossimage.jifenfu.net/erpadmin/default/20210929/aa287693-d020-4f09-8161-9c871d87d6bb.html","isActivity":1,"marketingActivityGoodsId":"1696823088648249345","marketingActivityId":"1696823088530808833","activityPrice":"0","goodsExtJson":[],"activityPriceThreshold":0,"ifActivityPriceThreshold":0,"ifLimitArea":0,"commonDisplayExtData":{"errCodeMsg":[]},"goodsDisplayExtJson":{},"priceShowTypeSnapshot":"{\\"goodsPriceShowType\\":1,\\"cashAmount\\":null,\\"points\\":2000}"}]}],"totalPrice":0,"skuOrderUserInfoDTO":[]}'
    update_headers(session, data, timestamp)
    res = session.post(url, data=data)
    if res.text.count('success') and res.json().get('success'):
        return f'{name}: 兑换成功'
    return get_error_msg(name, res)


def update_headers(session: Session, data: str, timestamp: str):
    nonce = ''.join(random.sample(string.digits + string.digits + string.digits + string.digits + string.digits, 16))
    sign = js.call('TB_BjfbEncrypt', f'{data}{nonce}{timestamp}')
    headers = {'nonce': nonce, 'timestamp': timestamp, 'sign': sign}
    session.headers.update(headers)


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name, False)
        self.max_retries = 10
        # time.sleep(58)

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        dh = split[-2]
        cookies = split[-1]
        headers = {
            'Cookie': cookies,
            'Content-Type': 'application/json;charset=utf-8',
            'Referer': 'https://service.jifenfu.net/sspmall-front/index.html',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        }
        session = get_chrome_session()
        session.headers.update(headers)
        session.proxies = proxy

        timestamp = get_time(session)
        if dh == 'HF':
            result = dh_hf(session, timestamp)
            log.info(f'【{index}】{result}')
        if dh == 'EK':
            result = dh_ek(session, timestamp)
            log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
