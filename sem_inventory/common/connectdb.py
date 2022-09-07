import pymysql
from sem_inventory.common.handleconfig import conf


class DB(object):
    def __init__(self):
        # 创建一个连接对象
        self.conn = pymysql.connect(host=conf.get("test_db", "host"),
                                    port=conf.getint("test_db", "port"),
                                    user=conf.get("test_db", "user"),
                                    password=conf.get("test_db", "pwd"),
                                    charset=conf.get("test_db", "charset"),
                                    cursorclass=pymysql.cursors.DictCursor
                                    )
        # 创建一个游标
        self.cur = self.conn.cursor()

    def find_one(self, sql):
        """获取查询出来的第一条数据"""
        # 执行查询语句
        self.conn.commit()
        self.cur.execute(sql)
        data = self.cur.fetchone()
        return data

    def find_all(self, sql):
        """获取查询出来的所有数据"""
        self.conn.commit()
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    def find_count(self, sql):
        """返回查询数据的条数"""
        self.conn.commit()
        return self.cur.execute(sql)

    def insert_data(self, sql):
        """往数据库插入一条数据"""
        try:
            self.cur.execute(sql)
        except Exception as e:
            self.conn.rollback()
            raise e
        self.conn.commit()

    def update_data(self, sql):
        """更新数据库数据"""
        try:
            self.cur.execute(sql)
        except Exception as e:
            self.conn.rollback()
            raise e
        self.conn.commit()

    def del_data(self, sql):
        """删除数据"""
        try:
            self.cur.execute(sql)
        except Exception as e:
            self.conn.rollback()
            raise e
        self.conn.commit()

    def close(self):
        """关闭游标，断开连接"""
        self.cur.close()
        self.conn.close()
