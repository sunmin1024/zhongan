import pytest
from sem_inventory.common.basefunc import BaseFunc
from sem_inventory.common.handlepath import REPORTDIR
from sem_inventory.common.handle_email import send_email

if __name__ == '__main__':
    # 删除reports下的文件
    bf = BaseFunc()
    bf.del_file()
    # 启动pytest，执行测试运行程序
    pytest.main([
        # "./testcases/test_01ordercome.py",
        "--reruns", "2",
        "--report=reports.html",
        "--tester=孙敏",
        "--title=api自动化测试报告",
        "--desc=库存&订单自动化测试脚本",
        "--template=2"])
    # 生成测试报告后，获取测试报告的路径
    report_name = bf.find_file(REPORTDIR)[0]
    # 发送测试报告的邮件
    send_email(report_name, "vevor-Auto自动化测试报告")
