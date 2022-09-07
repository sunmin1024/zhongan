import os
import jsonpath
import pytest
import json
import time
from decimal import Decimal
from sem_inventory.common.basefunc import BaseFunc
from sem_inventory.common.connectdb import DB
from sem_inventory.common.handlelog import log
from sem_inventory.common.handlepath import DATADIR
from sem_inventory.common.handlerequests import SendRequest
from sem_inventory.common.readexcel import ReadExcel
from sem_inventory.common.handleconfig import conf
from sem_inventory.common.handle_data import CaseDate, replace_data
from sem_inventory.common.connectredis import ConnRedis
from sem_inventory.common.testdata import TestData

case_file = os.path.join(DATADIR, "ordercome.xlsx")


class TestOderCome(object):
    """创建订单-->库存锁定流程"""
    excel_stock = ReadExcel(case_file, "stock")
    stock_cases = excel_stock.read_data()
    excel_more_stock = ReadExcel(case_file, "morestock")
    more_stock_cases = excel_more_stock.read_data()
    request = SendRequest()
    bf = BaseFunc()
    db = DB()
    red = ConnRedis()
    td = TestData()

    @pytest.mark.parametrize("case", stock_cases)
    def test_stock(self, case, send_request):
        """订单中一个商品时，库存锁定流程"""
        # 第一步，准备用例数据
        url = conf.get("test_env", "url") + case["url"]
        method = case["method"]
        data = case["data"]
        # 将json格式数据转化为python的字典数据
        d_data = json.loads(data)
        # 将platOrderSn字段替换为随机数
        d_data[0]["platOrderSn"] = self.bf.random_order_code()
        # 保存随机数产生的订单号
        CaseDate.order_num = d_data[0]["platOrderSn"] = self.bf.random_order_code()
        # 保存下单的商品数量
        CaseDate.goods_num = jsonpath.jsonpath(d_data, "$..goodsQuantity")[0]
        # 保存商品的sku,source,site
        CaseDate.sku = jsonpath.jsonpath(d_data, "$..goodsSku")[0]
        CaseDate.source = jsonpath.jsonpath(d_data, "$..source")[0]
        CaseDate.site = jsonpath.jsonpath(d_data, "$..site")[0]
        # 获取预期结果
        expected = eval(case["expected"])
        expected_code = expected["code"]
        expected_message = expected["message"]
        expected_status = expected["lock_status"]
        # 获取行号
        row = case["case_id"] + 1
        # 查询商品的market_id,goods_info_id
        goods_info_id_sql = self.excel_stock.read_sqls(case["sql"])[2]
        CaseDate.goods_info_id = str(self.db.find_one(replace_data(goods_info_id_sql))["goods_info_id"])
        market_id_sql = self.excel_stock.read_sqls(case["sql"])[3]
        CaseDate.market_id = str(self.db.find_one(replace_data(market_id_sql))["market_id"])
        # 将商品的goods_info_id,market_id,site_name进行拼接
        CaseDate.goods_hkey = "_".join([CaseDate.goods_info_id, CaseDate.market_id, CaseDate.site])

        # 第二步，发送请求，获取响应结果
        # 发送请求前，获取sku的冻结数量
        pre_db_sku_sql = self.excel_stock.read_sqls(case["sql"])[5]
        pre_sku_frozen_num = self.td.db_data(pre_db_sku_sql, "frozen_quantity")
        # 发送请求前，获取redis中lockStock的值
        name = eval(case["redis_key"])["name"]
        key = eval(replace_data(case["redis_key"]))["key"]
        pre_result = self.red.select_hash(name, key)
        pre_lock_stock = jsonpath.jsonpath(pre_result, "$..lockStock")[0]
        # 发送请求
        response = self.request.send(url=url, method=method, json=d_data)
        res = response.json()
        res_code = jsonpath.jsonpath(res, "$.code")[0]
        res_massage = jsonpath.jsonpath(res, "$.message")[0]
        # 查询数据库订单维度冻结的库存
        frozen_num_sql = self.excel_stock.read_sqls(case["sql"])[0]
        frozen_num = self.td.db_data(frozen_num_sql, "frozen_quantity")
        # 查询库存的锁单状态
        actual_status_sql = self.excel_stock.read_sqls(case["sql"])[1]
        lock_status = self.td.db_data(actual_status_sql, "status")
        # 发送请求后，获取redis中lockStock的值
        end_result = self.red.select_hash(name, key)
        end_lock_stock = jsonpath.jsonpath(end_result, "$..lockStock")[0]
        # 查询数据库sku的的市场、站点
        sku_info_sql = self.excel_stock.read_sqls(case["sql"])[5]
        db_sku_info = self.db.find_one(replace_data(sku_info_sql))
        sku_market_id = str(db_sku_info["market_id"])
        sku_site = db_sku_info["site"]
        # 查询冻结扣的商品数量
        end_sku_frozen_num = self.td.db_data(sku_info_sql, "frozen_quantity")

        # 第三步，断言
        try:
            # 断言实际结果和预期结果
            assert expected_code == res_code
            assert expected_message == res_massage
            assert expected_status == lock_status
            # 断言sku的站点和市场 查询表：inventory_sku_lock_record
            assert sku_market_id == CaseDate.market_id
            assert sku_site == CaseDate.site
            # 断言下单的商品和sku的商品冻结数量是否相等 查询表：inventory_sku_lock_record
            assert Decimal(CaseDate.goods_num) == Decimal(end_sku_frozen_num - pre_sku_frozen_num)
            # 断言下单的商品和冻结的商品是否相等 查询表：inventory_order_lock_record
            assert CaseDate.goods_num == frozen_num
            # 断言下单的商品和redis冻结的商品是否相等
            assert Decimal(CaseDate.goods_num) == Decimal(end_lock_stock - pre_lock_stock)
        except AssertionError as e:
            # 如果断言异常，则捕获异常并抛出，并将测试用例执行未通过的结果写入excel中
            self.excel_stock.write_data(row=row, column=11, value="未通过")
            log.error("用例：{}，执行未通过".format(case["title"]))
            log.exception(e)
            raise e
        else:
            # 测试用例执行通过，则将测试用例执行通过的结果写入excel中
            self.excel_stock.write_data(row=row, column=11, value="通过")
            log.info("用例：{}，执行通过".format(case["title"]))

    @pytest.mark.parametrize("case", more_stock_cases)
    def test_more_stock(self, case, send_request):
        """订单中多个商品时，库存锁定流程"""
        # 第一步，准备用例数据
        url = conf.get("test_env", "url") + case["url"]
        method = case["method"]
        data = case["data"]
        # 将json格式数据转化为python的字典数据
        d_data = json.loads(data)
        # 将platOrderSn字段替换为随机数
        d_data[0]["platOrderSn"] = self.bf.random_order_code()
        # 保存随机数产生的订单号
        CaseDate.order_num = d_data[0]["platOrderSn"] = self.bf.random_order_code()
        # 保存下单的商品数量
        CaseDate.goods_num1 = jsonpath.jsonpath(d_data, "$..goodsQuantity")[0]
        CaseDate.goods_num2 = jsonpath.jsonpath(d_data, "$..goodsQuantity")[1]
        # 保存商品的sku,source,site
        goods_skus = jsonpath.jsonpath(d_data, "$..goodsSku")
        CaseDate.sku = goods_skus[0]
        CaseDate.source = jsonpath.jsonpath(d_data, "$..source")[0]
        CaseDate.site = jsonpath.jsonpath(d_data, "$..site")[0]
        # 获取预期结果
        expected = eval(case["expected"])
        expected_code = expected["code"]
        expected_message = expected["message"]
        expected_status = expected["lock_status"]
        # 获取行号
        row = case["case_id"] + 1
        # 查询商品的market_id
        select_market_id = self.excel_more_stock.read_sqls(case["sql"])[3]
        market_id_dict = self.db.find_one(replace_data(select_market_id))
        CaseDate.market_id = str(market_id_dict["market_id"])
        # 查询商品的goods_info_id
        goods_sku_list = []
        for CaseDate.skus in goods_skus:
            select_goods_id = self.excel_more_stock.read_sqls(case["sql"])[2]
            exe_sql_dic = self.db.find_one(replace_data(select_goods_id))
            goods_info_id = exe_sql_dic["goods_info_id"]
            goods_sku_list.append(goods_info_id)
        CaseDate.goods_info_id1 = str(goods_sku_list[0])
        CaseDate.goods_info_id2 = str(goods_sku_list[1])
        # 将商品的goods_info_id,market_id,site_name进行拼接
        CaseDate.goods_hkey1 = "_".join([CaseDate.goods_info_id1, CaseDate.market_id, CaseDate.site])
        CaseDate.goods_hkey2 = "_".join([CaseDate.goods_info_id2, CaseDate.market_id, CaseDate.site])

        # 第二步，发送请求，获取响应结果
        # 发送请求前，获取第1个商品的sku维度的冻结库存
        pre_db_sku_sql1 = self.excel_stock.read_sqls(case["sql"])[5]
        pre_sku_frozen_num1 = self.td.db_data(pre_db_sku_sql1, "frozen_quantity")
        # pre_db_sku_info1 = self.db.find_one(replace_data(pre_db_sku_sql1))
        # pre_sku_frozen_num1 = pre_db_sku_info1["frozen_quantity"]
        # 发送请求前，获取第2个商品的sku维度的冻结库存
        pre_db_sku_sql2 = self.excel_stock.read_sqls(case["sql"])[6]
        pre_sku_frozen_num2 = self.td.db_data(pre_db_sku_sql2, "frozen_quantity")
        # pre_db_sku_info2 = self.db.find_one(replace_data(pre_db_sku_sql2))
        # pre_sku_frozen_num2 = pre_db_sku_info2["frozen_quantity"]
        # 发送请求前，获取redis中lockStock的值
        name = eval(case["redis_key"])["name"]
        key = eval(replace_data(case["redis_key"]))["key"]
        pre_result = self.red.select_hashs(name, key)
        pre_list = []
        # time.sleep(1)
        for pre_stock in pre_result:
            pre_stock_dic = json.loads(pre_stock)
            pre_lock_stock = jsonpath.jsonpath(pre_stock_dic, "$..lockStock")
            pre_list.append(pre_lock_stock)
        pre_lock_stock1 = pre_list[0][0]
        pre_lock_stock2 = pre_list[1][0]
        # 发送请求
        # time.sleep(1)
        response = self.request.send(url=url, method=method, json=d_data)
        res = response.json()
        res_code = jsonpath.jsonpath(res, "$.code")[0]
        res_massage = jsonpath.jsonpath(res, "$.message")[0]
        # time.sleep(1)
        # 查询库存的锁单状态
        # time.sleep(1)
        select_actual_status = self.excel_more_stock.read_sqls(case["sql"])[1]
        # lock_status = self.db.find_all(replace_data(select_actual_status))
        lock_status = self.td.db_datas(select_actual_status)
        lock_status1 = lock_status[0]["status"]
        lock_status2 = lock_status[1]["status"]
        # 查询数据库订单维度冻结的库存
        # time.sleep(1)
        select_frozen_num = self.excel_more_stock.read_sqls(case["sql"])[0]
        frozen_num_dic = self.td.db_datas(select_frozen_num)
        # frozen_num_dic = self.db.find_all(replace_data(select_frozen_num))
        frozen_num1 = frozen_num_dic[0]["frozen_quantity"]
        frozen_num2 = frozen_num_dic[1]["frozen_quantity"]
        # 发送请求后，获取redis中lockStock的值
        # time.sleep(1)
        end_result = self.red.select_hashs(name, key)
        end_list = []
        for end_stock in end_result:
            end_stock_dic = json.loads(end_stock)
            end_lock_stock = jsonpath.jsonpath(end_stock_dic, "$..lockStock")
            end_list.append(end_lock_stock)
        end_lock_stock1 = end_list[0][0]
        end_lock_stock2 = end_list[1][0]
        # 查询数据库sku的的市场、站点
        # 查询第1个商品的市场、站点
        sku_info_sql1 = self.excel_more_stock.read_sqls(case["sql"])[5]
        db_sku_info1 = self.db.find_one(replace_data(sku_info_sql1))
        sku_market_id1 = str(db_sku_info1["market_id"])
        sku_site1 = db_sku_info1["site"]
        # 查询第2个商品的市场、站点
        sku_info_sql2 = self.excel_more_stock.read_sqls(case["sql"])[6]
        db_sku_info2 = self.db.find_one(replace_data(sku_info_sql2))
        sku_market_id2 = str(db_sku_info2["market_id"])
        sku_site2 = db_sku_info2["site"]
        # 查询冻结的商品数量
        # 查询第1个商品sku维度冻结的数量
        end_sku_frozen_num1 = db_sku_info1["frozen_quantity"]
        # 查询第2个商品sku维度冻结的数量
        end_sku_frozen_num2 = db_sku_info2["frozen_quantity"]

        # 第三步，断言
        try:
            # 断言实际结果和预期结果
            assert expected_code == res_code
            assert expected_message == res_massage
            # 实际锁单状态和预期锁单状态对比
            assert expected_status == lock_status1
            assert expected_status == lock_status2
            # 断言sku的站点和市场 查询表：inventory_sku_lock_record
            assert sku_market_id1 == CaseDate.market_id
            assert sku_site1 == CaseDate.site
            assert sku_market_id2 == CaseDate.market_id
            assert sku_site2 == CaseDate.site
            # 断言下单的商品和sku的商品冻结数量是否相等 查询表：inventory_sku_lock_record
            assert Decimal(CaseDate.goods_num1) == Decimal(end_sku_frozen_num1 - pre_sku_frozen_num1)
            assert Decimal(CaseDate.goods_num2) == Decimal(end_sku_frozen_num2 - pre_sku_frozen_num2)
            # 断言下单的商品和冻结的2个商品是否相等 查询表：inventory_order_lock_record
            assert CaseDate.goods_num1 == frozen_num1
            assert CaseDate.goods_num2 == frozen_num2
            # 断言下单的商品和redis冻结的2个商品是否相等
            assert Decimal(CaseDate.goods_num1) == Decimal(end_lock_stock1 - pre_lock_stock1)
            assert Decimal(CaseDate.goods_num2) == Decimal(end_lock_stock2 - pre_lock_stock2)
        except AssertionError as e:
            # 如果断言异常，则捕获异常并抛出，并将测试用例执行未通过的结果写入excel中
            self.excel_more_stock.write_data(row=row, column=11, value="未通过")
            log.error("用例：{}，执行未通过".format(case["title"]))
            log.exception(e)
            raise e
        else:
            # 测试用例执行通过，则将测试用例执行通过的结果写入excel中
            self.excel_more_stock.write_data(row=row, column=11, value="通过")
            log.info("用例：{}，执行通过".format(case["title"]))
