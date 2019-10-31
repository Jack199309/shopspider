from gui_taobao import *
import time
from tkinter import Tk
import traceback
if __name__ == '__main__':
    try:
        root = Tk()
        app = App(root)
        root.mainloop()
    except Exception as e:
        traceback.print_exc()
        print(e)
        print('出错等待60秒')
        time.sleep(60)