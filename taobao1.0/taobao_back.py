# -*- coding: utf-8 -*-
# author:nxy
from selenium.webdriver import ChromeOptions
from selenium import webdriver
from lxml import etree
import requests
import threading
from threading import Thread
import logging
import json
import os
import time
import csv
import re

logging.basicConfig(
    # filename='taobao.log', filemode="w",
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)


class TaoBao(object):

    def __init__(self):
        # 总页数
        self.amount_page = 0
        self.current_page = 0

        self.amount_items = 0
        self.current_item = 0

        self.amount_img = 0
        self.current_img = 0
        self.delay_time = 1

        option = ChromeOptions()

        # 用来控制图片爬取暂停的标志
        self.export_img_even = ''

        self.error_message = ''
        # 重定向
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # option.add_experimental_option("prefs", prefs)
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        option.add_argument("disable-web-security")
        # option.add_argument('--headless')
        # option.add_argument('--disable-gpu')
        path = r'chromedriver.exe'
        option.binary_location = 'Chrome/Application/chrome.exe'
        driver = webdriver.Chrome(executable_path=path, options=option)
        driver.implicitly_wait(5)
        self.driver = driver
        self.login_url = 'https://login.tmall.com'
        self.index_url = 'https://www.tmall.com'
        self.index_url2 = 'https://www.tmall.com/'
        self.shop_url = 'https://mai.taobao.com/seller_admin.htm'
        self.items_url = 'https://ipublish.tmall.com/tmall/manager/render.htm'
        self.detail_url = 'https://detail.tmall.com/item.htm'
        # 二维码地址
        self.twe_dimension_url = ''
        # 登录状态
        self.login = ''
        self.login_name = ''

        # 爬取详细页面的默认请求头
        self.headers = {
            "cache-control": "max-age=0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "sec-fetch-site": "none",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }


    def read_cookies(self):
        # 读取本地cookes
        if not os.path.exists('cookies.txt'):
            return
        with open("cookies.txt", "r") as fp:
            cookies = json.load(fp)
            for cookie in cookies:
                cookie.pop('domain')  # 如果报domain无效的错误
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
        logging.info('读取本地cookie完成')

    def save_cookies(self):
        # 简单的只保存最近一次的cookies 会覆盖，
        # 按照不同账号保存
        self.driver.get_cookies()
        with open("cookies.txt", "w") as fp:
            json.dump(self.driver.get_cookies(), fp)
            logging.info('保存cookies成功')

    def delete_cookies(self):
        try:
            os.remove("cookies.txt")
            print('删除cookies')
        except Exception as e:
            print(e)

    def get_two_dimension_url(self):
        try:
            ifrim = self.driver.find_element_by_xpath('//*[@id="J_loginIframe"]')
            self.driver.switch_to.frame(ifrim)
            time.sleep(0.5)
            img = self.driver.find_element_by_xpath('//*[@id="J_QRCodeImg"]/img')
            self.twe_dimension_url = img.get_attribute('src')
        except Exception as e:
            # 获取不到二维码  说明读取了cookies信息已经登录 直接去商品页面
            logging.info(e)
            self.driver.get(self.items_url)

    def open_taobao(self):
        print("open_taobao>>>>")
        # self.driver.get(self.login_url)
        try:
            # self.driver.delete_all_cookies()
            self.read_cookies()
            self.driver.get(self.login_url)
        except Exception as e:
            logging.info(e)
        time.sleep(0.5)
        print('open_taobao_<<<<<')

    def account_login(self, name, pwd):
        self.driver.get('https://login.tmall.com')
        # ifrim = self.driver.find_element_by_xpath('//*[@id="J_loginIframe"]')
        # self.driver.switch_to.frame(ifrim)
        time.sleep(15)
        # account_login = 'document.querySelector("#J_QRCodeLogin > div.login-links > a.forget-pwd.J_Quick2Static").click()'
        # self.driver.execute_script(account_login)
        time.sleep(3)
        query_name = 'document.querySelector("#TPL_username_1").value = "{0}"'.format(name)
        print(query_name)
        self.driver.execute_script(query_name)
        time.sleep(3)
        query_pwd = 'document.querySelector("#TPL_password_1").value = "{0}"'.format(pwd)
        self.driver.execute_script(query_pwd)
        time.sleep(3)
        login_button = 'document.querySelector("#J_SubmitStatic").click()'
        self.driver.execute_script(login_button)

    def window_switch(self, url):
        print('寻找的url为：', url)
        try:
            url_stop = self.driver.current_url.find('?')

            if url_stop:
                if self.driver.current_url[:url_stop] == url:
                    return
            if self.driver.current_url == url:
                return True
        except:
            # 有的当前页面关闭
            pass

        for window in self.driver.window_handles:
            print('=======')
            self.driver.switch_to.window(window)
            print('当前的url:', self.driver.current_url)
            url_stop = self.driver.current_url.find('?')
            if url_stop > 0:
                print('当前的url:', self.driver.current_url[:url_stop])
                if self.driver.current_url[:url_stop] == url:
                    return True
            if self.driver.current_url == url:
                return True
        print('未找到页面')
        return False

    def get_amount_page(self):
        self.driver.get(self.items_url)
        text = self.driver.page_source
        response = etree.HTML(text)
        # 所有列表的物品
        self.amount_page = response.xpath('//span[contains(@class,"next-pagination-display")]/text()')[1].strip()
        logging.info('获取订单页数为：' + str(self.amount_page))

    def item_page(self):
        # 在self.items_url 页面
        # 爬取订单详情
        def threed_page():
            for i in range(1, int(self.amount_page) + 1):
                self.current_page = i + 1
                self.driver.get(
                    'https://ipublish.tmall.com/tmall/manager/render.htm?pagination.current={0}&pagination.pageSize=20'.format(
                        i))
                text = self.driver.page_source
                response = etree.HTML(text)
                with open('sell_shops.csv', 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    all_shops = response.xpath('//tr[contains(@class,"next-table-row")]')
                    for one_shop in all_shops:
                        # shop_name ID price time
                        print(one_shop.xpath('.//span[@class="product-desc-span"]/a/@href'))
                        shop_list = one_shop.xpath(
                            '''.//span[@class="product-desc-span"]/text()|
                            .//span[@class="table-text-cell"]/text()|
                            .//span[@class="product-desc-span"]/a/@href|
                            .//span[@class="product-desc-span"]/a/text()''')
                        writer.writerow(shop_list)
                # time.sleep(1)

        item_page_thred = Thread(target=threed_page)
        item_page_thred.setDaemon(True)
        item_page_thred.start()

    def get_shops_url(self):
        # 返回有序列的订单id方便从断点开始
        all_shop_url = []
        with open('sell_shops.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i in reader:
                all_shop_url.append(i[0])
        return sorted(set(all_shop_url))

    def get_request_cookies(self):
        with open("cookies.txt", "r") as fp:
            cookies = json.load(fp)
        new_cookies = {}
        for i in cookies:
            new_cookies.update(
                {i['name']: i['value']}
            )
        return new_cookies

    def detail_image_selenium(self):
        all_shop_urls = self.get_shops_url()
        self.amount_items = len(all_shop_urls)
        print('self.amount_items', self.amount_items)
        for i in all_shop_urls:
            time.sleep(int(self.delay_time))
            self.current_item += 1
            self.driver.get(i)
            response = etree.HTML(self.driver.page_source)
            show_image = response.xpath('//ul[@id="J_UlThumb"]//img/@src')
            shop_name = response.xpath('//div[@class="tb-detail-hd"]/h1/text()')[0].strip()
            classify_image = response.xpath('//dd/ul/li/a/@style')
            print(classify_image)
            classify_image = list(map(lambda x: re.findall(r'.*?:url\((.*?)\).*?', x)[0], classify_image))

            with open('image_url.csv', 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([shop_name, 'show_image'] + show_image)
                writer.writerow([shop_name, 'classify_image'] + classify_image)

    def detail_image_requests(self):

        # 构建url得到总爬取的页数
        all_shop_urls = self.get_shops_url()
        self.amount_items = len(all_shop_urls)
        print('self.amount_items', self.amount_items)
        new_cookies = self.get_request_cookies()

        def thread_detail_image():
            # 中间如果失败记录失败位置
            try:
                for url in all_shop_urls:
                    time.sleep(int(self.delay_time))
                    self.current_item += 1
                    # 获取信息
                    response = requests.get(url, headers=self.headers, cookies=new_cookies)
                    response = etree.HTML(response.text)

                    def re_url(x):
                        return re.findall('.*?:url\((.*?)\).*?', x)[0]

                    show_image = response.xpath('//ul[@id="J_UlThumb"]//img/@src')
                    shop_name = response.xpath('//div[@class="tb-detail-hd"]/h1/text()')[0].strip()
                    classify_image = response.xpath('//dd/ul/li/a/@style')
                    print(classify_image)
                    classify_image = list(map(re_url, classify_image))

                    with open('image_url.csv', 'a', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        print(shop_name)
                        print(show_image)
                        print(classify_image)
                        writer.writerow([shop_name, 'show_image'] + show_image)
                        writer.writerow([shop_name, 'classify_image'] + classify_image)
            except Exception as e:
                logging.info(e)
                self.error_message = e
                self.current_item -= 1

        t = Thread(target=thread_detail_image)
        t.setDaemon(True)
        t.start()

    def export_image(self, base_path):

        def mkdir(path):
            path = path.strip()
            path = path.rstrip("\\")
            is_exists = os.path.exists(path)
            if not is_exists:
                os.makedirs(path)
                # print(path + ' 创建成功')
                return True
            else:
                # print(path + ' 目录已存在')
                return False

        with open('image_url.csv', 'r', encoding='utf-8') as f:
            render = list(csv.reader(f))
        self.amount_img = len(render)

        def threed_export_img(event):
            for one_data in render:
                event.wait()
                dir_shops = one_data[0]
                dir_image = one_data[1]
                path = os.path.join(base_path, 'image', dir_shops, dir_image)
                try:
                    mkdir(path)
                except:
                    continue
                start = 0
                for img_url in one_data:
                    if img_url[-3:] == 'jpg':
                        print('===')
                        zurl = re.sub('40x40|60x60', '430x430', img_url)

                        img_name = str(hash(zurl)) + '.jpg'
                        print('爬取的url为', zurl)
                        img = requests.get(url='https:' + zurl, verify=False)
                        with open(path + '\\' + img_name, 'wb') as f:
                            f.write(img.content)
                    start += 1
                self.current_img += 1

        self.export_img_even = threading.Event()  # 创建一个事件
        self.export_img_even.set()

        t = Thread(target=threed_export_img, args=(self.export_img_even,))
        t.setDaemon(True)
        t.start()

    def time_out(self):
        self.export_img_even.clear()

    def run_out(self):
        self.export_img_even.set()

    def verify_login(self):
        # 此是一个进程 每隔2秒钟判断一次登录状态
        # 根据页面的url来判断是否登录，可以寻找其他方法
        logging.info('验证当前url' + str(self.driver.current_url))
        if self.driver.current_url == self.index_url or self.driver.current_url == self.index_url2 \
                or self.driver.current_url == self.items_url:
            print('登录成功')

            if self.driver.current_url != self.items_url:
                self.driver.get(self.items_url)
            status = self.driver.find_element_by_xpath('//*[@id="login-info"]/span')
            self.login = 2
            self.login_name = '欢迎：' + str(status.get_attribute('textContent'))
            self.save_cookies()

        logging.info('未登录')
        time.sleep(2)

    def quit_taobao(self):
        self.driver.quit()
