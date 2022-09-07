import requests


class SendRequest(object):
    """cookie+session鉴权的请求类封装"""

    def __init__(self):
        self.session = requests.session()

    # 发送请求
    def send(self, url, method, headers=None, params=None, data=None, json=None, files=None):
        # 将method转化为小写字母
        method = method.lower()
        # 发送get请求，接收响应结果
        if method == "get":
            response = self.session.get(url=url, params=params, headers=headers)
        # 发送post请求，接收响应结果
        elif method == "post":
            response = self.session.post(url=url, json=json, data=data, files=files, headers=headers)

        return response
