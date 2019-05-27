import pymysql


class EasyMysql:
    def __init__(self, host, user, password, db):
        self.cnn = pymysql.connect(host=host, user=user, password=password, db=db, charset='utf8')
        self.cur = self.cnn.cursor()
    
    def __del__(self):
        self.cur.close()
        self.cnn.close()

    def query_result(self, sql):
        return self.cur.execute(sql)

    def query_no_result(self, sql):
        try:
            self.cur.execute(sql)
            self.cnn.commit()
        except Exception as e:
            print('【提交失败】：{}'.format(e))
            self.cnn.rollback()
