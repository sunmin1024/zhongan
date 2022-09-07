import os
import random
import shutil
import time

from sem_inventory.common.handlepath import REPORTDIR


class BaseFunc(object):

    def assert_dict_item(self, dic1, dic2):
        """
        断言dic1中的所有元素都是diac2中的成员，成立返回True,不成立引发断言错误
        :param dic1: 字典
        :param dic2: 字典
        :return:
        """
        for item in dic1.items():
            if item not in dic2.items():
                raise AssertionError("{} items not in {}".format(dic1, dic2))

    def assert_li_dict(self, li, dic):
        """
        断言dic1中的所有元素都是diac2中的成员，成立返回True,不成立引发断言错误
        :param li: 列表
        :param dic: 字典
        :return:
        """
        li2 = []
        for item in dic.values():
            li2.append(item)
        if li2 != li:
            raise AssertionError("{} not equal {}".format(li, li2))

    def random_name(self):
        """随机生成一个名称"""
        print("--name")
        while True:
            s1 = random.choice(["abcd", "efg", "hijk", "fmn", "opq"])
            number = random.randint(1, 999999)
            name = s1 + str(number)
            return name

    def random_order_code(self):
        """生成一个随机订单号(年月日时分秒+time.time()的后7位)"""
        while True:
            order_no = str(
                time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + str(time.time()).replace('.', '')[-7:])
            return order_no

    def del_file(self):
        """删除reports目录下的文件"""
        if not os.path.exists(REPORTDIR):
            os.mkdir(REPORTDIR)
        else:
            shutil.rmtree(REPORTDIR)
            os.mkdir(REPORTDIR)

    def find_file(self, dir_path):
        file_list = []
        for file in os.listdir(dir_path):
            if file.endswith("html"):
                file_list.append(os.path.join(REPORTDIR, file))
        return file_list

if __name__ == '__main__':
    bf = BaseFunc()
    path = bf.find_file(REPORTDIR)
    print(path)