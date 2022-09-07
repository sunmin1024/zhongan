import json
import time

from sem_inventory.common.handleconfig import conf
from sem_inventory.common.handlelog import log
from sem_inventory.common.connectdb import DB
from sem_inventory.common.handle_data import replace_data
from sem_inventory.common.basefunc import BaseFunc
from sem_inventory.common.handlerequests import SendRequest


class TestData(object):
    """测试脚本中的测试数据的方法集合"""
    db = DB()
    bf = BaseFunc()
    request = SendRequest()

    def db_data(self, sql, key):
        """数据库查询不到数据时进行重试和异常捕获，并返回字典中的value(单条数据)"""
        if not self.db.find_one(replace_data(sql)):
            count = 0
            while True:
                try:
                    time.sleep(1)
                    self.db.find_one(sql)
                    count += 1
                    if count > 2 or self.db.find_one(replace_data(sql)):
                        result = self.db.find_one(replace_data(sql))[key]
                        break
                except TypeError as e:
                    print("*******数据库未查询到数据********")
                    log.error()
                    raise e
        else:
            time.sleep(1)
            result = self.db.find_one(replace_data(sql))[key]
        return result

    def db_datas(self, sql):
        """数据库查询不到数据时进行重试和异常捕获（多条数据）"""
        if not self.db.find_all(replace_data(sql)):
            count = 0
            while True:
                try:
                    time.sleep(1)
                    self.db.find_all(sql)
                    count += 1
                    if count > 2 or self.db.find_all(replace_data(sql)):
                        result = self.db.find_all(replace_data(sql))
                        break
                except TypeError as e:
                    print("*******数据库未查询到数据********")
                    log.error()
                    raise e
        else:
            time.sleep(1)
            result = self.db.find_all(replace_data(sql))
        return result

    def response_data(self, row_data):
        """准备用例数据，发送请求，获取响应结果"""
        url = conf.get("test_env", "url") + row_data["url"]
        method = row_data["method"]
        data = json.loads(row_data["data"])
        response = self.request.send(url=url, method=method, json=data)
        return response.json()
