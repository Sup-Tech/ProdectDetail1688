from PyQt5.QtCore import QThread, QWaitCondition, QMutex, pyqtSignal
import requests
from lxml import etree


class WebExistError(Exception):
    """
    错误:网页不存在
    """
    def __init__(self):
        pass

    def __str__(self):
        return '网页404'


class LoginExpire(Exception):
    """
    错误:网页登录过期
    """
    def __init__(self):
        pass

    def __str__(self):
        return '登录过期'


class CrawlThread(QThread):
    """
    基于pyqt界面的多线程爬虫
    """
    # 信号
    log_signal = pyqtSignal([str])
    result_signal = pyqtSignal([dict], [str])
    finished_signal = pyqtSignal()

    def __init__(self):
        """
        初始化
        :param url: 列表 包含链接和其它
        :param ban_words: 列表 商品标题禁用词
        """
        super(CrawlThread, self).__init__()
        self.url = ''
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self._isQueueEmpty = True
        self.header = {
            "Cookie": "cna=83PAEX6KM1UCAVatRgb3nL3T; lid=%E5%9C%A8%E7%AD%89%E4%B8%80%E5%B9%B42; ali_ab=39.172.217.70.1554009903313.1; __wapcsf__=1; ali_apache_track=c_mid=b2b-3228253168cbae5|c_lid=%E5%9C%A8%E7%AD%89%E4%B8%80%E5%B9%B42|c_ms=1|c_mt=3; ali_apache_tracktmp=c_w_signed=Y; UM_distinctid=170b4b8c91a25e-00465631615844-396d7406-384000-170b4b8c91b367; taklid=9e986aefdae34acc9a9d9e69c881b95a; cookie2=1603a7bd4bfe56a58d0412db2718ad94; hng=CN%7Czh-CN%7CCNY%7C156; t=9598868eca35dc170aab8a3ef3d2d6cb; __last_loginid__=%E5%9C%A8%E7%AD%89%E4%B8%80%E5%B9%B42; _tb_token_=7e80bb68e4763; __cn_logon__=true; __cn_logon_id__=%E5%9C%A8%E7%AD%89%E4%B8%80%E5%B9%B42; ali_apache_id=11.186.201.43.1587133534705.375358.1; cookie1=AHhUi6rILeVzRQMgv19ww87pTyWmQ6zCYVNjgVYAz5U%3D; cookie17=UNJTJzt5zxl%2B2g%3D%3D; sg=280; csg=456b0223; unb=3228253168; uc4=nk4=0%40tX%2B5Xt2e1oXZoyAxo7DwCZjoeec%3D&id4=0%40UgXUEvcYFV1laIy3sVr1GWno9qGU; _nk_=%5Cu5728%5Cu7B49%5Cu4E00%5Cu5E742; last_mid=b2b-3228253168cbae5; _csrf_token=1587550802854; CNZZDATA1253659577=659429046-1584916245-%7C1587547366; _is_show_loginId_change_block_=b2b-3228253168cbae5_false; _show_force_unbind_div_=b2b-3228253168cbae5_false; _show_sys_unbind_div_=b2b-3228253168cbae5_false; _show_user_unbind_div_=b2b-3228253168cbae5_false; __rn_alert__=false; alicnweb=touch_tb_at%3D1587550818987%7Clastlogonid%3D%25E5%259C%25A8%25E7%25AD%2589%25E4%25B8%2580%25E5%25B9%25B42; JSESSIONID=9C927FBFD8F0F6C5DB4F1302A0A63BBE; l=eBOinhqgQwVUoueoBOfwFurza77tsIRfguPzaNbMiT5P_36W5eKGWZjA-GtXCnGNnsFDR3Sv4XNQBJY8cPaEVxv9-eaZtOqEndLh.; isg=BBIS0PHHmA1ns-Sm9tlYiXklY970Ixa9lWHgy9xrOEWw77PpxLfGzx-FX0NTn45V",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
            "Referer": 'https://1688.com',
            }

    def put(self, url):
        self.url = url
        self._isQueueEmpty = False
        self.cond.wakeAll()

    def get_page(self):
        """
        网页请求
        :return: 无返回 通过信号传递数据
        """
        try:
            re = requests.get(self.url, headers=self.header)
            re.raise_for_status()
            print(re.url)
            if re.url == 'https://page.1688.com/shtml/static/wrongpage.html':
                raise WebExistError
            if re.url.startswith('https://login.1688.com/member/signin.htm?'):
                raise LoginExpire
        except WebExistError as e:
            self.result_signal[str].emit(str(e))
        except LoginExpire as e:
            self.result_signal[str].emit(str(e))
            self.log_signal[str].emit(str(e))
        except Exception as e:
            self.log_signal.emit(str(e))
        else:
            self.parse(re)

    def parse(self, response):
        """
        对requests的响应对象 进行数据提取和处理
        :param response: requests的响应对象
        :return: 通过信号传递 dict
        """
        response = etree.HTML(response.text)
        # 标题
        title = response.xpath('//h1[@class="d-title"]/text()')[0]
        # # SKU属性&供货价
        sku_attr_price = response.xpath('//table[@class="table-sku"]//tr//td[@class="name"]/span/text() | //table[@class="table-sku"]//tr//td[@class="price"]/span/em[@class="value"]/text()')
        # 供应商名称
        supllier_name = response.xpath('//p[@class="info"]/span[1]/text()')[0].strip()
        # 供应商区域
        supllier_province = response.xpath('//meta[@name="location"]/@content')[0]
        # 相关产品列表
        # relating_product_list = response.xpath('//div[@class="obj-relative"]//a/text()')

        item = {'title': title,
                'supllier_name': supllier_name,
                'supllier_province': supllier_province,
                'sku_attrs': sku_attr_price
                }
        self.result_signal[dict].emit(item)

    def run(self):
        while True:
            self.mutex.lock()
            if self._isQueueEmpty:
                print('1')
                self.cond.wait(self.mutex)
                print('2')
            else:
                print('3')
                self.get_page()
                print('4')
                self._isQueueEmpty = True
                print('5')
            self.mutex.unlock()