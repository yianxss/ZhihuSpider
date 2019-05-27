import pprint
from zhihu_oauth import ZhihuClient
from zhihu_oauth.exception import NeedCaptchaException
import os
import time
import random
from bs4 import BeautifulSoup
import requests
import re
import easy_mysql

class ZhiHuSpider:
    def __init__(self, kw, data_table_name, cookie):
        self.cnn = easy_mysql.EasyMysql('localhost', 'root', '12345678', 'zhihu')
        self.kw = kw
        self.data_table_name = data_table_name
        self.cookie = cookie
        self.create_data_table()

    # 根据关键词获取问题的id
    def get_q_ids(self):
        header = {'cookie': self.cookie,
                  'referer': 'https://www.zhihu.com/',
                  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        search_url = 'https://www.zhihu.com/search?type=content&q={}'.format(self.kw)
        r = requests.get(search_url, headers=header)
        q_ids = re.findall(r'"id":"(\d+?)","type":"question"', r.text, re.MULTILINE)
        return q_ids

    # 账号密码存放在-login_info.txt
    # 格式：账号：xxx
    # 密码：XXX
    @staticmethod
    def login_ZhiHu():
        Client = ZhihuClient()
        with open('login_info.txt', 'r') as f:
            login_info = [item.split(":")[1].strip() for item in f.readlines()]
        TOKEN_FILE = 'token.pkl'
        if os.path.isfile(TOKEN_FILE):
            Client.load_token(TOKEN_FILE)
        else:
            try:
                Client.login(*login_info)
            except NeedCaptchaException:
                # 保存验证码并提示输入，重新登录
                with open('a.gif', 'wb') as f:
                    f.write(Client.get_captcha())
                captcha = input('please input captcha:')
                Client.login(login_info[0], login_info[1],captcha)
                Client.save_token(TOKEN_FILE)
        return Client

    def create_data_table(self):
        try:
            sql = """CREATE TABLE If Not Exists `{}` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `QID` varchar(20) NOT NULL,
                      `floor` int(11) DEFAULT NULL,
                      `author` varchar(20) DEFAULT NULL,
                      `coment_count` int(11) DEFAULT NULL,
                      `excerpt` text,
                      `content` text,
                      `thanks_count` int(11) DEFAULT NULL,
                      `voteup_count` int(11) DEFAULT NULL,
                      PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB  DEFAULT CHARSET=utf8
            """.format(self.data_table_name)
            print(sql)
            self.cnn.query_no_result(sql)
        except Exception as e:
            print(e)

    def main(self):
        client = self.login_ZhiHu()
        q_ids = self.get_q_ids()
        print(q_ids)
        if len(q_ids) != 0:
            for eve in self.get_q_ids():
                try:
                    self.cnn.query_result("SELECT count(*) FROM movie WHERE QID = '{}'".format(eve))
                    res_count = self.cnn.cur.fetchall()[0][0]
                    if res_count == 0:
                        question = client.question(int(eve))
                        answers = question.answers
                        for num, answer in enumerate(answers):
                            time.sleep(random.uniform(0.3, 1.5))
                            res = {
                                '楼层': "{:0>3d} ".format(num),
                                '作者': answer.author.name,
                                '评论数': answer.comment_count,  # 评论数
                                '摘要': answer.excerpt,
                                '感谢次数': answer.thanks_count,  # 感谢次数
                                '点赞数': answer.voteup_count,  # 点赞数
                                '全部内容': '\t'.join(BeautifulSoup(answer.content, 'lxml').stripped_strings),
                            }
                            sql = """INSERT INTO %s VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s')""" % (
                                self.data_table_name, 0, eve, res['楼层'], res['作者'], res['评论数'], res['摘要'], res['全部内容'],
                                res['感谢次数'], res['点赞数'])
                            self.cnn.query_no_result(sql)

                            pprint.pprint(res)
                            print('=' * 60)
                except Exception as e:
                    print("--------------------")
                    print(e)
