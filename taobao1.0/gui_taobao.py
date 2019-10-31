# -*- coding: utf-8 -*-
# author:nxy

from tkinter import Canvas, PhotoImage, Label, StringVar, Entry, Button, Spinbox
from urllib.request import urlopen
from taobao_back import TaoBao
from taobao_back import logging
from PIL import Image
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror
import io
from threading import Thread


class App(object):
    def __init__(self, master):

        self.var_amount_page = ''
        self.var_amount_item = ''
        self.var_amount_img = ''

        # 总页数显示
        self.master = master
        self.chrome = TaoBao()
        self.chrome.open_taobao()
        self.amount_img = ''
        self.amount_page = ''
        self.amount_item = ''

        self.var_user_name = ''
        self.var_usr_pwd = ''
        # 用来显示验证码的

        self.image = ''
        # 商品图片url爬取延迟时间
        self.delay_time = ''
        # 登录的使用者名称
        self.login = self.chrome.login

        # 初始化登录页面
        self.init_widgets_login()
        self.update_login()

        # 右上角退出的时候 退出一些其他进程
        self.master.protocol("WM_DELETE_WINDOW", self.quit_exe)
        # 刷新二维码
        self.refresh_two_dimension()

    def clear_widgets(self):
        print(list(self.master.children.values()))
        for widgets in list(self.master.children.values()):
            widgets.destroy()
            widgets.pack_forget()

    def error_message(self):
        showerror('error_message', self.chrome.error_message)

    def init_widgets_login(self):
        self.master.title('天猫登录')
        self.master.geometry("350x350")
        self.master.resizable(False, False)

        self.canvas = Canvas(self.master, bg='green', height=140, width=140)
        self.canvas.place(x=105, y=0)

        account_label = Label(text='账号:', font=('Arial', 14))
        account_label.place(x=30, y=160)

        self.var_user_name = StringVar()
        self.var_user_name.set('')
        entry_usr_name = Entry(self.master, textvariable=self.var_user_name, font=('Arial', 14))
        entry_usr_name.place(x=80, y=160)

        label_two = Label(text='密码:', font=('Arial', 14))
        label_two.place(x=30, y=200)

        self.var_usr_pwd = StringVar()
        self.var_user_name.set('')
        entry_usr_pwd = Entry(self.master, textvariable=self.var_usr_pwd, font=('Arial', 14), show='*')
        entry_usr_pwd.place(x=80, y=200)

        btn_login = Button(self.master, text='账号登录', command=self.user_login)
        btn_login.place(x=155, y=260)

        sweep_login = Button(self.master, text='刷新验证码', command=self.refresh_two_dimension)
        sweep_login.place(x=260, y=50)

    def export_image(self):
        base_url = askdirectory()
        self.chrome.export_image(base_url)

    def init_widgets_show(self):
        # 登录后的页面显示
        self.clear_widgets()
        self.master.geometry("500x500")

        Label(text=self.chrome.login_name, font=('Arial', 14)).place(x=20, y=20)
        print('登录成功')

        order_message = Button(self.master, text='订单信息爬取', command=self.get_sell_shops)
        order_message.place(x=20, y=60)

        detail_image = Button(self.master, text='图片详情爬取', command=self.threed_detail_items)
        detail_image.place(x=20, y=100)

        self.delay_time = StringVar()
        sb = Spinbox(self.master, from_=3, to=10, increment=1, textvariable=self.delay_time,
                     command=self.delay_time.get(),
                     width=5)
        sb.place(x=120, y=105)

        quit_account = Button(self.master, text='导出所有图片', command=self.export_image)
        quit_account.place(x=20, y=140)

        quit_account = Button(self.master, text='退出账号', command=self.quit_account)
        quit_account.place(x=280, y=20)

        # quit_account = Button(self.master, text='暂停', command=self.chrome.time_out)
        # quit_account.place(x=120, y=140)
        #
        # quit_account = Button(self.master, text='开始', command=self.chrome.run_out)
        # quit_account.place(x=170, y=140)

        self.amount_page = Label(text='', font=('Arial', 14))
        self.amount_page.place(x=200, y=60)

        self.amount_item = Label(text='', font=('Arial', 14))
        self.amount_page.place(x=200, y=100)

        self.amount_img = Label(text='', font=('Arial', 14))
        self.amount_img.place(x=200, y=100)

        self.var_amount_page = StringVar()
        self.amount_page = Label(textvariable=self.var_amount_page, font=('Arial', 14))
        self.amount_page.place(x=200, y=60)

        self.var_amount_item = StringVar()
        self.amount_item = Label(textvariable=self.var_amount_item, font=('Arial', 14))
        self.amount_item.place(x=200, y=100)

        self.var_amount_img = StringVar()
        self.amount_img = Label(textvariable=self.var_amount_img, font=('Arial', 14))
        self.amount_img.place(x=200, y=140)

    def threed_detail_items(self):
        t = Thread(target=self.chrome.detail_image_selenium)
        t.setDaemon(True)
        t.start()

    def user_login(self):
        usr_name = self.var_user_name.get()
        usr_pwd = self.var_usr_pwd.get()
        self.chrome.account_login(usr_name, usr_pwd)

    def refresh_two_dimension(self):
        self.chrome.open_taobao()
        self.chrome.get_two_dimension_url()
        logging.info("验证码的url为：" + str(self.chrome.twe_dimension_url))
        if not self.chrome.twe_dimension_url:
            return
        image_bytes = urlopen(self.chrome.twe_dimension_url).read()
        data_stream = io.BytesIO(image_bytes)
        pil_image = Image.open(data_stream)
        pil_image.save('auth.gif')
        w, h = pil_image.size
        self.image = PhotoImage(file='auth.gif')
        self.canvas.create_image(h / 2 + 2, w / 2 + 2, anchor='center', image=self.image)

    def get_sell_shops(self):
        try:
            self.chrome.item_page()
        except Exception as e:
            logging.DEBUG(e)
            logging.DEBUG('出售商品页面不存在')

    def update_message(self):
        # 总页数显示
        logging.debug('页数' + str(self.chrome.current_page) + '/' + str(self.chrome.amount_page))
        show_page = '页数' + str(self.chrome.current_page) + '/' + str(self.chrome.amount_page)
        show_items = '商品数' + str(self.chrome.current_item) + '/' + str(self.chrome.amount_items)
        show_imgs = '商品数' + str(self.chrome.current_img) + '/' + str(self.chrome.amount_img)

        if self.chrome.error_message:
            self.error_message()
            self.chrome.error_message = ''
        self.var_amount_page.set(show_page)
        self.var_amount_item.set(show_items)
        self.var_amount_img.set(show_imgs)
        self.master.after(1000, self.update_message)

    def update_login(self):
        # 使用0 1 2 判断登录状态
        # 0 代表未登录
        # 1 代表登录
        # 2 首次登录
        if not self.chrome.login:
            # 为了防止页面卡顿 使用线程执行
            t = Thread(target=self.chrome.verify_login)
            t.setDaemon(True)
            t.start()

        if self.chrome.login == 2:
            # 等待显示完成后 再对显示的数据进行更新
            self.init_widgets_show()
            self.update_message()
            self.chrome.get_amount_page()
            self.chrome.login = 1
            print('login', self.chrome.login)
        self.master.after(3000, self.update_login)

    def quit_account(self):
        # self.chrome.logon 切换回 0
        self.chrome.login = 0
        # 删除chrom保存的信息
        self.chrome.driver.delete_all_cookies()
        print('cookies',self.chrome.driver.get_cookies())
        # 删除本地保存的chrome
        self.chrome.delete_cookies()
        # 打开登录页面
        self.chrome.driver.get(self.chrome.login_url)
        print('new_cookies',self.chrome.driver.get_cookies())
        # 清除当前所有控件
        self.clear_widgets()
        # 页面切回到登录状态
        self.init_widgets_login()

    def quit_exe(self):
        try:
            self.chrome.driver.quit()
        except Exception as e:
            logging.info(e)
        self.master.destroy()
