import os
import pytest
import jsonpath
import json

from sem_inventory.common.handlepath import DATADIR
from sem_inventory.common.handlerequests import SendRequest
from sem_inventory.common.readexcel import ReadExcel
from sem_inventory.common.handleconfig import conf
from sem_inventory.common.handle_data import CaseDate, replace_data
from sem_inventory.common.basefunc import BaseFunc
from sem_inventory.common.connectdb import DB
from sem_inventory.common.handlelog import log

case_file = os.path.join(DATADIR, "orderuplode.xlsx")


class TestOrderUpload(object):
    excel_stock = ReadExcel(case_file, "scorder")
    sc_cases = excel_stock.read_data()
    request = SendRequest()
    bf = BaseFunc()
    db = DB()

    @pytest.mark.parametrize("case", sc_cases)
    def test_sc_order(self, case, cancel_outbound_order):
        """订单上传海外仓流程"""
        # 第一步，准备用例数据
        url = conf.get("test_env", "url") + case["url"]
        method = case["method"]
        CaseDate.order_num = self.bf.random_order_code()
        data = json.loads(replace_data(case["data"]))
        expected = eval(case["expected"])
        row = case["case_id"] + 1
        # 发送请求，获取响应结果
        response = self.request.send(url=url, method=method, json=data)
        res = response.json()
        # 如果上传【品晟仓库】成功，则将出库单号和状态保存到数据库
        if case["title"] == "上传订单_品晟仓库" and res["ask"] == "Success":
            CaseDate.ps_upload = jsonpath.jsonpath(res, "$.orderCode")[0]
            self.db.insert_data(replace_data(case["sql"]))
        # 如果取消成功，则修改数据库状态为「已取消」
        if case["title"] == "取消出库单_品晟仓库" and res["ask"] == "Success":
            self.db.update_data(case["sql"])
        # 如果上传【风雷仓库】成功，则将出库单号和状态保存到数据库
        if case["title"] == "上传订单_风雷仓库" and res["message"] == "success":
            CaseDate.fl_upload = jsonpath.jsonpath(res, "$..jobNum")[0]
            self.db.insert_data(replace_data(case["sql"]))
        # 如果取消成功，则修改数据库状态为「已取消」
        if case["title"] == "取消出库单_风雷仓库" and res["message"] == "success":
            self.db.update_data(case["sql"])
        # 如果上传【4px仓库】成功，则将出库单号和状态保存到数据库
        if case["title"] == "上传订单_4px仓库" and res["msg"] == "系统处理成功":
            CaseDate.fpx_upload = jsonpath.jsonpath(res, "$..consignment_no")[0]
            self.db.insert_data(replace_data(case["sql"]))
        # 如果取消成功，则修改数据库状态为「已取消」
        if case["title"] == "取消出库单_4px仓库" and res["msg"] == "系统处理成功":
            self.db.update_data(case["sql"])
        # 如果上传【橙联仓库】成功，则将出库单号和状态保存到数据库
        if case["title"] == "上传订单_橙联仓库" and res["success"] == "true":
            CaseDate.cl_upload = jsonpath.jsonpath(res, "$..orderNumber")[0]
            self.db.insert_data(replace_data(case["sql"]))
        # 如果取消成功，则修改数据库状态为「已取消」
        if case["title"] == "取消出库单_橙联仓库" and res["success"] == "true":
            self.db.update_data(case["sql"])
        # 第三步 断言
        try:
            self.bf.assert_dict_item(expected, res)
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
