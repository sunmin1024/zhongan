import json
import os
import pytest

from sem_inventory.common.handleconfig import conf
from sem_inventory.common.handlepath import DATADIR
from sem_inventory.common.readexcel import ReadExcel
from sem_inventory.common.connectdb import DB
from sem_inventory.common.handle_data import CaseDate, replace_data
from sem_inventory.common.basefunc import BaseFunc
from sem_inventory.common.handlerequests import SendRequest
from sem_inventory.common.testdata import TestData


@pytest.fixture()
def clear_category_data():
    """测试用例执行完后清理环境数据"""
    # 读取excel的用例数据
    case_file = os.path.join(DATADIR, "ordercome.xlsx")
    excel = ReadExcel(case_file, "category")
    del_sql = excel.get_cell(2, "del_sql")
    db = DB()
    yield db
    # 执行删除数据的sql，并关闭数据库连接
    db.del_data(del_sql)
    db.close()


@pytest.fixture()
def clear_order():
    """库存冻结测试脚本执行完后删除订单"""
    # 读取excel的用例数据
    case_file = os.path.join(DATADIR, "ordercome.xlsx")
    excel = ReadExcel(case_file, "stock")
    db = DB()
    yield
    # 执行删除数据的sql，并关闭数据库连接
    del_sql = excel.get_cell(2, "del_sql")
    check_sql = excel.get_cell(2, "sql")
    check_order = excel.result_datas(check_sql)[4]
    CaseDate.del_order = check_order["plat_order_sn"]
    db.del_data(replace_data(del_sql))
    db.close()


@pytest.fixture(scope="class")
def send_request():
    """库存校验的测试用例执行前，先发送请求"""
    # 发送请求前，数据准备
    bf = BaseFunc()
    request = SendRequest()
    case_file = os.path.join(DATADIR, "ordercome.xlsx")
    excel = ReadExcel(case_file, "morestock")
    case = excel.read_data()[0]
    url = conf.get("test_env", "url") + case["url"]
    method = case["method"]
    data = case["data"]
    # 将json格式数据转化为python的字典数据
    d_data = json.loads(data)
    # 将platOrderSn字段替换为随机数
    d_data[0]["platOrderSn"] = bf.random_order_code()
    request.send(url=url, method=method, json=d_data)
    yield


@pytest.fixture()
def cancel_outbound_order():
    """上传订单的测试用例执行完后，查询数据库，如果有未取消的出库单，再次进行取消操作"""
    # 读取excel的用例数据
    case_file = os.path.join(DATADIR, "orderuplode.xlsx")
    excel = ReadExcel(case_file, "scorder")
    env_sql = excel.get_cell(2, "env_sql")
    td = TestData()
    db = DB()
    yield db
    # 查询数据库状态为1的出库单
    result = db.find_all(env_sql)
    # 如果有未取消的出库单，分别请求各自仓库的取消接口
    for data in result:
        # 判断【品晟】仓库如果有未取消的出库单，则发送请求取消
        if data["status"] == 1 and data["warehouse"] == "品晟":
            ps_row_data = excel.get_row(3)
            res = td.response_data(ps_row_data)
            if res["ask"] == "Success":
                db.update_data(ps_row_data["sql"])
        # 判断【风雷】仓库如果有未取消的出库单，则发送请求取消
        elif data["status"] == 1 and data["warehouse"] == "风雷":
            fl_row_data = excel.get_row(5)
            res = td.response_data(fl_row_data)
            if res["message"] == "success":
                db.update_data(fl_row_data["sql"])
        # 判断【4px】仓库如果有未取消的出库单，则发送请求取消
        elif data["status"] == 1 and data["warehouse"] == "4px":
            fpx_row_data = excel.get_row(7)
            res = td.response_data(fpx_row_data)
            if res["msg"] == "系统处理成功":
                db.update_data(fpx_row_data["sql"])
        # 判断【橙联】仓库如果有未取消的出库单，则发送请求取消
        elif data["status"] == 1 and data["warehouse"] == "橙联":
            cl_row_data = excel.get_row(9)
            res = td.response_data(cl_row_data)
            if res["success"] == "true":
                db.update_data(cl_row_data["sql"])
    db.close()



