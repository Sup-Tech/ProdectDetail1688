import json
from configparser import ConfigParser
import jieba
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QTextBrowser, QPushButton, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
from functools import reduce
from common.iterableTool import IterableTool
from mythread import CrawlThread
import re


class ExpandingLEdit(QLineEdit):
    def __init__(self, horizontal_stretch):
        super(ExpandingLEdit, self).__init__()
        h_expand_size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed, QSizePolicy.LineEdit)
        h_expand_size_policy.setHorizontalStretch(horizontal_stretch)
        self.setSizePolicy(h_expand_size_policy)


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setup_ui()
        self.signal_slot()
        self.thread_build()
        # 读取配置文件
        self.cp = ConfigParser()
        self.cp.read('settings.cfg', encoding='utf-8')
        # 数据清洗预处理 - 读取产品中文名称禁用词 列表
        self.words_baned = json.loads(self.cp.get('settings', 'words_banded'))

    def thread_build(self):
        self.t = CrawlThread()
        self.t.result_signal[dict].connect(self.deal_result)
        self.t.result_signal[str].connect(self.deal_result)
        self.t.result_signal[str].connect(self.deal_log)
        self.t.log_signal[str].connect(self.deal_log)
        self.t.start()

    def setup_ui(self):
        self.setWindowTitle('1688商品详情爬取器')
        self.resize(450, 800)

        layout1 = QVBoxLayout()

        layout2 = QHBoxLayout()
        layout1.addLayout(layout2)
        self.url_1688 = ExpandingLEdit(3)
        self.url_1688.setPlaceholderText('1688链接')
        self.search_btn = QPushButton('Go')
        layout2.addWidget(self.url_1688)
        layout2.addWidget(self.search_btn)

        self.product_title = QLineEdit()
        self.product_title.setReadOnly(True)
        self.product_title.setPlaceholderText('商品标题')
        layout1.addWidget(self.product_title)

        layout3 = QHBoxLayout()
        layout1.addLayout(layout3)
        self.supplier_name = ExpandingLEdit(2)
        self.supplier_name.setReadOnly(True)
        self.supplier_name.setPlaceholderText('供应商名称')
        self.supplier_area = QLineEdit()
        self.supplier_area.setReadOnly(True)
        self.supplier_area.setPlaceholderText('供应商区域')
        layout3.addWidget(self.supplier_name)
        layout3.addWidget(self.supplier_area)

        layout4 = QHBoxLayout()
        layout1.addLayout(layout4)
        self.sku_attributes = QTextBrowser()
        self.sku_price = QTextBrowser()
        layout4.addWidget(self.sku_attributes)
        layout4.addWidget(self.sku_price)

        self.log_browser = QTextBrowser()
        layout1.addWidget(self.log_browser)

        self.setLayout(layout1)

    def signal_slot(self):
        self.search_btn.clicked.connect(self.crawl)

    def crawl(self):
        url = self.url_1688.text()
        print(url)
        self.supplier_area.clear()
        self.supplier_name.clear()
        self.product_title.clear()
        self.sku_price.clear()
        self.sku_attributes.clear()
        self.log_browser.clear()
        if url:
            self.t.put(url)
        else:
            self.log_browser.append('无效链接')

    def deal_result(self, e):
        if type(e) == dict:
            title = e['title']
            supplier_name = e['supllier_name']
            supplier_area = e['supllier_province']
            sku_attrs = e['sku_attrs']
            self.product_title.setText(self.title_handler(title))
            self.supplier_name.setText(supplier_name)
            self.supplier_area.setText(self.province_handle(supplier_area))
            i = 0
            for attr in sku_attrs:
                if i % 2 == 0:
                    self.sku_attributes.append(attr)
                else:
                    self.sku_price.append(attr)
                i += 1
        elif e == '网页404':
            self.sku_attributes.append('网页404')
            self.sku_price.append('网页404')
        elif e == '登录过期':
            self.sku_attributes.append('登录过期')
            self.sku_price.append('登录过期')

    def deal_log(self, e):
        self.log_browser.append(e)

    def quit(self):
        self.t.terminate()
        print('退出')

    def title_handler(self, title):
        """
        数据清洗-对爬取的商品标题
        去除无关词&去除重复词处理
        :param title: 标题字符串
        """
        # jieba 用户自定义字典
        jieba.load_userdict('words_to_ban.txt')
        tmp = jieba.lcut(title)
        # 去重
        index_list = IterableTool.sorted_remove_repeat(tmp)
        for i in index_list:
            tmp.pop(i)
        # 去禁词
        index = len(tmp) - 1
        while index > -1:
            if tmp[index] in self.words_baned:
                tmp.pop(index)
            index -= 1
        title = reduce(lambda x, y: x+y, tmp)
        return title

    @staticmethod
    def province_handle(data):
        """
        广东区 江浙沪 其它
        判断处于哪个区域
        :param data: str
        :return: str
        """
        pattern = re.compile(r'province=(.*);city=(.*)')
        result = '-'.join(pattern.search(data).groups())
        return result



