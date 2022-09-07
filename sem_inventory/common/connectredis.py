import redis
import json
import jsonpath
from sem_inventory.common.handleconfig import conf


class ConnRedis(object):
    def __init__(self):
        # 创建一个连接对象
        self.redis_conn = redis.Redis(
            host=conf.get("test_redis", "host"),
            port=conf.get("test_redis", "port"),
            password=conf.get("test_redis", "pwd"),
            encoding=conf.get("test_redis", "encoding"),
            db=6,
            decode_responses=True
        )

    # 查询单个值
    def select_one(self, key):
        result = self.redis_conn.get(key)
        try:
            d_result = json.loads(result)
        except TypeError as e:
            print("redis中未查询到对应的值")
            raise e
        else:
            return d_result

    # 查询单个hash值
    def select_hash(self, name, key):
        result = self.redis_conn.hget(name, key)
        try:
            d_result = json.loads(result)
        except TypeError as e:
            print("redis中未查询到对应的值")
            raise e
        else:
            return d_result

    # 查询指定的多个hash的key值
    def select_hashs(self, name, keys):
        result = self.redis_conn.hmget(name, keys)
        return result

    # 查询全部hash的key值
    def select_hkeys(self, name):
        result = self.redis_conn.hgetall(name)
        return result

    # 查询多个值
    def select_all(self, *args):
        result = self.redis_conn.mget(*args)
        return result

    # 关闭连接
    def close(self):
        self.redis_conn.close()


if __name__ == '__main__':
    name = "scp:inventory:goods:lock"
    key = "193802_1_US"
    keys = "23706_1_US,23706_1_US"
    red = ConnRedis()
    s = red.select_hashs("scp:inventory:goods:lock", ["42494_1_US", "23706_1_US"])
    # print(r)
    a = red.select_hash(name, key)
    print(a)
