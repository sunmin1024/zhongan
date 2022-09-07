import openpyxl
from sem_inventory.common.connectdb import DB


class ReadExcel(object):
    db = DB()

    def __init__(self, filename, sheet_name):
        self.filename = filename
        self.sheet_name = sheet_name

    def open(self):
        # 获取工作簿对象
        self.wb = openpyxl.load_workbook(self.filename)
        # 选择表单
        self.sh = self.wb[self.sheet_name]

    def read_data(self):
        """读取数据"""
        self.open()
        # 按行获取表单所有格子中的数据，每一行的数据放在一个元组中
        datas = list(self.sh.rows)
        # 获取第一行的数据，作为字典的键
        title = [i.value for i in datas[0]]
        # 创建一个空列表，用例存放用例数据
        cases = []
        # 遍历除第一行之外的数据
        for i in datas[1:]:
            # 获取该行数据的值
            values = [c.value for c in i]
            # 将该行数据和title（第一行数据）打包转换为字典
            case = dict(zip(title, values))
            # 将转换的字典添加到前面创建的空列表cases中
            cases.append(case)
        return cases

    def get_row(self, row):
        """获取exl中行信息,row--行数（int）"""
        if row <= 1:
            row_data = None
        else:
            test_dates = self.read_data()
            row_data = test_dates[row-2]
        return row_data

    def get_column(self, name):
        """获取excel中列信息"""
        column_data = []
        test_datas = self.read_data()
        for data in test_datas:
            column_data.append(data[name])
        return column_data

    def get_cell(self, row, name):
        """获取excel中某一单元格信息"""
        if row <= 1:
            cell_data = None
        else:
            test_dates = self.read_data()
            cell_data = test_dates[row - 2][name]
        return cell_data

    def read_sqls(self, sqls):
        """一个单元读取多条select的方法"""
        result_list = sqls.split("&")
        return result_list

    def result_datas(self, sqls):
        """一个单元格执行多个select的方法"""
        result_list = sqls.split("&")
        res_lists = []
        for sql in result_list:
            result = self.db.find_one(sql)
            res_lists.append(result)
        return res_lists

    def result_counts(self, sqls):
        """一个单元格执行多个select count(1) 的方法"""
        result_list = sqls.split("&")
        res_lists = []
        for sql in result_list:
            sql_data = self.db.find_count(sql)
            res_lists.append(sql_data)
        return res_lists

    def del_datas(self, sqls):
        """一个单元格执行多个delete语句"""
        result_list = sqls.split("&")
        res_lists = []
        for sql in result_list:
            sql_data = self.db.del_data(sql)
            res_lists.append(sql_data)
        return res_lists

    def write_data(self, row, column, value):
        """写入数据"""
        self.open()
        # 写入数据
        self.sh.cell(row=row, column=column, value=value)
        # 保存文件
        self.wb.save(self.filename)
