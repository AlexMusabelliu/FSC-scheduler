import os, json, re, sys, time, threading, random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.command import Command
from itertools import chain
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from io import StringIO

class ClickLineEdit(QLineEdit):
    def __init__(self, *args):
        super(ClickLineEdit, self).__init__(*args)
        self.default_text = self.text()
    
    def focusInEvent(self, event):
        super(ClickLineEdit, self).focusInEvent(event)
        if not self.isModified():
            self.clear()
    
    def focusOutEvent(self, event):
        super(ClickLineEdit, self).focusOutEvent(event)
        if self.text() == "":
            self.setText(self.default_text)


class Form(QMainWindow):
    def __init__(self, parent=None):
        def send():
            parent.add_sched([course_name.text(), course_time.text(), course_link.text(), list([1 if x.isChecked() else 0 for x in days])])
            self.close()

        super(Form, self).__init__(parent)
        height, width = 720 // 3 , 1280 // 2

        self.setMinimumHeight(height) 
        self.setMaximumHeight(height)
        self.setMinimumWidth(width) 
        self.setMaximumWidth(width)

        days = [QCheckBox(x, self) for x in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
        course_name = ClickLineEdit("Name of class")
        course_time = ClickLineEdit("Time of class (HH:MM [AM/PM])")
        course_link = ClickLineEdit("Link for class ([http/https]://www...)")
        submit_button = QPushButton("Add to list")
        submit_button.setStyleSheet('''background-color: #FFFFFF;
                                        color: red;
                                        font-size: 18px;
                                        font-family: Tahoma, Verdana, Arial Black, Arial;
                                        max-width:300px;
                                        width:150px;
                                        height:50px;
                                        margin-left:490px;
                                        margin-right:490px;
                                        border:3px solid red;''')
        submit_button.clicked.connect(send)

        layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout2.addWidget(course_name)
        layout2.addWidget(course_time)
        layout2.addWidget(course_link)
        for x in days:
            layout1.addWidget(x)
            x.setStyleSheet("color:white;")

        layout.addLayout(layout2)
        layout.addLayout(layout1)
        layout.addWidget(submit_button)

        self.wdg = QWidget(self)
        self.wdg.setLayout(layout)
        self.setCentralWidget(self.wdg)

class Widget(QMainWindow):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        olddir = os.getcwd()
        os.chdir(os.path.abspath(os.path.dirname(__file__)))
        # print(os.getcwd())
        # os.chdir("..")

        self.debug_output = ""
        self.stopText = "Stop Running"
        self.ran = False
        self.form_active = False
        self.new_data = []
        self.seen_sched = False
        settings = load("settings.txt")
        self.name = settings.get("name", "")
        self.email = settings.get("email", "")
        self.password = settings.get("password", "")
        self.autoMute = settings.get("autoMute", "")
        print(settings)
        
        height, width = 720, 1280

        self.setMinimumHeight(height) 
        self.setMaximumHeight(height)
        self.setMinimumWidth(width) 
        self.setMaximumWidth(width)

        self.setWindowTitle("FSC Scheduler")

        self.popUp = QMenu(self)
        self.delete = QAction(QIcon("redx.png"), "Delete row")
        self.popUp.addAction(self.delete)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        os.chdir(olddir)

        self.test()

    def test(self):
        settings = load("settings.txt")
        if settings == {} or not settings.get("name") or not settings.get("email") or not settings.get("password"):
            self.set_setting()
        
        sched = load_sched()
        # print(settings, sched)
        if sched == {}:
            self.set_sched()

        self.main_menu()

    def reload(self, sett):
        self.name = sett.get("name", "")
        self.email = sett.get("email", "")
        self.password = sett.get("password", "")
        self.autoMute = sett.get("autoMute", "")

    def main_menu(self):
        self.settings = load("settings.txt")
        user = self.settings.get("name", "user")
        hellotext = f"Hello {user}"
        self.reload(self.settings)

        self.main = QPushButton("Run")
        self.opt = QPushButton("Options")
        self.quit = QPushButton("Quit")
        self.hello = QLabel(hellotext)
        self.hello.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.hello)
        layout.addWidget(self.main)
        layout.addWidget(self.opt)
        layout.addWidget(self.quit)

        self.main.clicked.connect(_run)
        self.opt.clicked.connect(self.run_setting)
        self.quit.clicked.connect(lambda: sys.exit())

        self.cmw(layout)

    def run_OFF(self):
        global cont_RUN, driver
        def _quit():
            while True:
                try:
                    driver.quit()
                    break
                except Exception as e:
                    # print(e)
                    if str(Exception) == "":
                        break
                
        cont_RUN = False
        self.stop.clicked.connect(lambda: None)
        if self.stopText != "All done! Click here to return...":
            self.stopText = "Quitting..."
        else:
            self.stopText = "Returning..."
            
        self.stop.setText(self.stopText)
        threading.Thread(target=lambda: _quit(), daemon=True).start()

    def clear_menu(self, is_sched):
        os.chdir(os.path.abspath(os.path.dirname(__file__)))
        if is_sched:
            f = "schedule.sched"
        else:
            f = "settings.txt"

        open(f, "w").close()

    def cmw(self, layout):
        self.wdg = QWidget(self)
        self.wdg.setLayout(layout)
        self.setCentralWidget(self.wdg)

    def confirm_delete(self, layout, is_sched=0):
        def finish(is_sched):
            self.clear_menu(is_sched)

            text = "Your " + ("schedule has" if is_sched else "settings have") + " been reset successfully."
            info = QLabel(text)

            layout = QHBoxLayout()
            layout.addWidget(info, alignment=Qt.AlignCenter)

            self.cmw(layout)

            QTimer.singleShot(1900, self.run_setting)

        if not is_sched:
            menu = "settings"
        else:
            menu = "schedule"
        text = f'''Are you sure you want to reset your {menu}?'''
        yes, no = QPushButton("Yes"), QPushButton("No")
        confirm = QLabel(text)
        confirm.setStyleSheet('''color:white;
                                height:300px;
                                max-height:300px;
                                width:600px;
                                font-size:30px;
                                font-family: Bookman, Verdana, Comic Sans MS, Arial;''')

        yes.setStyleSheet('''background-color: #FFFFFF;
                            color: red;
                            font-size: 18px;
                            font-family: Tahoma, Verdana, Arial Black, Arial;
                            max-width:300px;
                            width:120px;
                            height:80px;
                            min-width:120px;
                            margin-left:0px;
                            margin-right:0px;
                            border:3px solid red;''')

        no.setStyleSheet('''background-color: #FFFFFF;
                            color: red;
                            font-size: 18px;
                            font-family: Tahoma, Verdana, Arial Black, Arial;
                            max-width:300px;
                            width:120px;
                            height:80px;
                            min-width:120px;
                            margin-left:0px;
                            margin-right:0px;
                            border:3px solid red;''')


        nulayout = QVBoxLayout()
        nulayout.addWidget(confirm, alignment=Qt.AlignHCenter)
        nunulayout = QHBoxLayout()
        nunulayout.addWidget(no, alignment=Qt.AlignBottom | Qt.AlignLeft)
        nunulayout.addWidget(yes, alignment=Qt.AlignRight | Qt.AlignBottom)
        nulayout.addLayout(nunulayout)
        

        yes.clicked.connect(lambda: finish(is_sched))
        no.clicked.connect(self.run_setting)

        self.cmw(nulayout)

    def write_settings(self, args):
        f = open("settings.txt", "w")
        for k in args:
            f.write("%s:%s,\n" % (str(k), args.get(k)))

        f.close()

    def set_setting(self, is_again=0):
        def update_settings(func, **kwargs):
            if kwargs.get("name"):
                self.name = kwargs.get("name", "")
            if kwargs.get("email"):
                self.email = kwargs.get("email", "")
            if kwargs.get("password"):
                self.password = kwargs.get("password", "")
            if kwargs.get("autoMute"):
                self.autoMute = kwargs.get("autoMute", "")
                
            settings.update({k:kwargs.get(k) for k in kwargs if k != "arg"})
            arg = kwargs.get("arg")
            if arg:
                func(arg)
            else:
                func()

        def set_setting2():
            name_text = "Enter your name here" if self.name == "" else self.name
            # print("-" * 128, name_text)
            name = ClickLineEdit(name_text)
            name_label = QLabel("Name: ")

            self.nex = QPushButton("Next")
            self.nex.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                min-width:120px;
                                margin-left:0px;
                                margin-right:0px;
                                border:3px solid red;''')

            self.back = QPushButton("Back")
            self.back.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                margin-left:0px;
                                margin-right:490px;
                                border:3px solid red;''')

            nulayout = QHBoxLayout()
            nulayout.addWidget(name_label)
            nulayout.addWidget(name)

            for_back = QHBoxLayout()
            for_back.addWidget(self.back)
            for_back.addWidget(self.nex)

            layout = QVBoxLayout()
            layout.addLayout(nulayout)
            layout.addLayout(for_back)

            self.back.clicked.connect(lambda: self.set_setting(is_again))
            self.nex.clicked.connect(lambda: update_settings(set_setting3, name=name.text()))

            self.cmw(layout)

        def set_setting3():
            text = '''In order to sign in to Google meetings, an email address and password are needed.\nThese are kept confidential on your system.'''
            info = QLabel(text)

            email_text = "someone@example.com" if self.email == "" else self.email
            password_text = "Enter password" if self.password == "" else self.password
            email = ClickLineEdit(email_text)
            email_label = QLabel("Email: ")
            password = ClickLineEdit(password_text)
            password_label = QLabel("Password: ")

            self.nex = QPushButton("Next")
            self.nex.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                min-width:120px;
                                margin-left:0px;
                                margin-right:0px;
                                border:3px solid red;''')

            self.back = QPushButton("Back")
            self.back.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                margin-left:0px;
                                margin-right:490px;
                                border:3px solid red;''')

            e = QHBoxLayout()
            e.addWidget(email_label)
            e.addWidget(email)
            
            p = QHBoxLayout()
            p.addWidget(password_label)
            p.addWidget(password)

            b = QHBoxLayout()
            b.addWidget(self.back)
            b.addWidget(self.nex)

            layout = QVBoxLayout()
            layout.addLayout(e)
            layout.addLayout(p)
            layout.addLayout(b)

            self.back.clicked.connect(lambda: update_settings(set_setting2, email=email.text(), password=password.text()))
            self.nex.clicked.connect(lambda: update_settings(set_setting4, email=email.text(), password=password.text()))

            self.cmw(layout)

        def set_setting4():
            def final(): 
                self.write_settings(settings)
                text = "Your settings have been updated."
                info = QLabel(text)

                layout = QHBoxLayout()
                layout.addWidget(info, alignment=Qt.AlignCenter)

                self.cmw(layout)
            
                QTimer.singleShot(1900, self.run_setting if is_again else self.set_sched)

            self.nex = QPushButton("Finalize")
            self.nex.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                min-width:120px;
                                margin-left:0px;
                                margin-right:0px;
                                border:3px solid red;''')

            self.back = QPushButton("Back")
            self.back.setStyleSheet('''background-color: #FFFFFF;
                                color: red;
                                font-size: 18px;
                                font-family: Tahoma, Verdana, Arial Black, Arial;
                                max-width:300px;
                                width:120px;
                                height:80px;
                                margin-left:0px;
                                margin-right:490px;
                                border:3px solid red;''')

            text = '''Enable auto-mute'''
            # muteInfo = QLabel(text)
            muteButton = QCheckBox(text)
            # print("autoMute")
            muteButton.setChecked(self.autoMute == "True")
            muteButton.setToolTip("Whether or not to automatically mute the microphone when joining.")

            # mute = QHBoxLayout()
            # QHBoxLayout.addWidget(muteInfo)
            # QHBoxLayout.addWidget(muteButton)

            b = QHBoxLayout()
            b.addWidget(self.back)
            b.addWidget(self.nex)

            layout = QVBoxLayout()
            layout.addWidget(muteButton)
            layout.addLayout(b)
            
            self.back.clicked.connect(lambda: update_settings(set_setting3, email=email.text(), password=password.text()))
            self.nex.clicked.connect(lambda: update_settings(final, autoMute=muteButton.isChecked() == True, verbose=False))

            self.cmw(layout)

        # settings = load("settings.txt")

        self.nex = QPushButton("Next")
        self.nex.setStyleSheet('''background-color: #FFFFFF;
                            color: red;
                            font-size: 18px;
                            font-family: Tahoma, Verdana, Arial Black, Arial;
                            max-width:300px;
                            width:120px;
                            height:80px;
                            min-width:120px;
                            margin-left:0px;
                            margin-right:0px;
                            border:3px solid red;''')

        self.back = QPushButton("Back")
        self.back.setStyleSheet('''background-color: #FFFFFF;
                            color: red;
                            font-size: 18px;
                            font-family: Tahoma, Verdana, Arial Black, Arial;
                            max-width:300px;
                            width:120px;
                            height:80px;
                            margin-left:0px;
                            margin-right:490px;
                            border:3px solid red;''')

        settings = {}
        text = '''Welcome to the FSC Scheduler.\nYou will be guided through a first-time setup of your schedule.''' if not is_again else "Please set your settings."
        info = QLabel(text)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet('''color:white;
                                height:300px;
                                max-height:300px;
                                margin-bottom:30px;
                                font-size:18px;
                                font-family: Bookman, Verdana, Comic Sans MS, Arial;''')
        
        layout = QVBoxLayout()
        layout.addWidget(info)
        layout.addWidget(self.nex, alignment=Qt.AlignBottom | Qt.AlignRight)

        self.nex.clicked.connect(set_setting2)

        self.cmw(layout)
        #     print("Let's introduce eachother. Hi, I'm SCHEDULY, the CMD line scheduler. And you are?")
        #     settings.update({"user":input("Enter your username:    ")})
        #     print("Hi, {0}!".format(settings.get("user")))
        #     input("\nPress enter to continue...")
        #     os.system("cls")

        #     print("In order to properly sign in to your google meetings, you need to login to your school GMAIL account:")
        #     while True:
        #         em = input("\nPlease enter your email address:    ")
        #         pa = input("Please enter your password:    ")
        #         r = input(f"\nIs this correct?\nEmail:  {em}\nPassword:  {pa}\n\ny/N:    ")
        #         if r[0].lower() == "y":
        #             break
        #         print("Operation canceled...")
        #         time.sleep(0.5)

        #     settings.update({"email":em, "password":pa, "verbose":"False"})
        #     write_settings(settings)
        #     os.system("cls")
        #     set_sched()
        
    def run_setting(self):
        buttons = modify_set, modify_sched, theme, reset_set, reset_sched = QPushButton("Modify Settings"), \
                                                                            QPushButton("Modify Schedule"), QPushButton("Themes"), \
                                                                            QPushButton("Reset Settings"), QPushButton('Reset Schedule')

        self.back = QPushButton("Back")
        self.back.setStyleSheet('''background-color: #FFFFFF;
                            color: red;
                            font-size: 18px;
                            font-family: Tahoma, Verdana, Arial Black, Arial;
                            max-width:300px;
                            width:120px;
                            height:80px;
                            margin-left:0px;
                            margin-right:490px;
                            border:3px solid red;''')

        modify_sched.clicked.connect(self.set_sched)
        modify_set.clicked.connect(lambda: self.set_setting(1))
        self.back.clicked.connect(self.main_menu)

        layout = QVBoxLayout()
        for b in buttons:
            layout.addWidget(b)
        layout.addWidget(self.back, alignment=Qt.AlignBottom | Qt.AlignLeft)

        reset_sched.clicked.connect(lambda: self.confirm_delete(layout, 1))
        reset_set.clicked.connect(lambda: self.confirm_delete(layout))

        self.cmw(layout)
        # os.system("cls")
        # print("Settings\n1:Modify Settings\n2:Modify Schedule\n3:Reset Settings\n4:Reset Schedule\n5:Back")
        # c = input("Enter a number:    ")
        # if c == "1":
        #     os.system("notepad \"settings.txt\"")
        # elif c == "2":
        #     os.system("notepad \"schedule.sched\"")
        # elif c == "3":
        #     open("settings.txt", "w").close()
        #     os.system("cls")
        #     print("All cleared!")
        #     time.sleep(0.5)
        # elif c == "4":
        #     open("schedule.sched", "w").close()
        #     os.system("cls")
        #     print("All cleared!")
        #     time.sleep(0.5)
        # elif c == "5":
        #     return
        # else:
        #     print("Invalid input!")
        #     time.sleep(0.5)

        # run_setting()
        
    def run_menu(self):
        global read_IO
        self.ran = True
        self.stopText = "Stop Running"
        sys.stdout = read_IO = StringIO()
        self.debug = QLabel(self.debug_output)
        self.debug.setWordWrap(True)
        self.debug.setStyleSheet('''color:white;
                                    height:300px;
                                    max-height:300px;
                                    margin-bottom:30px;
                                    font-size:14px;
                                    font-family: Trebuchet-MS, Comic Sans MS, Arial;''')
        
        self.stop = QPushButton(self.stopText)
        # self.stop.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.debug)
        layout.addWidget(self.stop)

        self.stop.clicked.connect(self.run_OFF)

        self.cmw(layout)

    def update_run(self):
        def isalive(driver):
            try:
                driver.execute(Command.STATUS)
                return True
            except:
                return False

        global driver, glob_text
        try:
            if self.ran:
                alive = isalive(driver)
                # print(alive, random.random())
                if not alive:
                    self.ran = False
                    self.main_menu()
        except:
            # print(f"Glob_text: {glob_text}")
            pass
        
        if glob_text == "Set your schedule":
            self.stopText = "Set your schedule"
            self.stop.clicked.connect(self.set_sched)

        self.stop.setText(self.stopText)
    
    def update(self):
        to_show = read_IO.getvalue()
        self.debug_output = to_show
        try:
            self.update_run()
        except Exception as e:
            # print("couldn't run", e)
            pass
        try:
            self.debug.setText(self.debug_output)
        except Exception as e:
            # sys.stdout = old_IO
            # print(e)
            # sys.stdout = read_IO
            pass

    def add_sched(self, data):
        self.form_active = False
        # fach, ti, li, dys = *data
        new_row = self.cur_sched.rowCount() + 1
        self.cur_sched.setRowCount(new_row)
        dys = ["M", "T", "W", "TH", "F", "SA", "S"]
        str_days = " ".join([dys[i] for i in range(len(data[3])) if data[3][i] != 0])
        self.new_data.append(data[:-1] + [str_days])
        print(str_days)
        for i in range(4):
            elem = QTableWidgetItem(data[i]) if i != 3 else QTableWidgetItem(str_days)
            self.cur_sched.setItem(new_row - 1, i, elem)
        self.cur_sched.setItem(new_row - 1 , 5, QTableWidgetItem("X"))
        
        # elem = QTableWidgetItem(str(new_row))
        # elem = self.cur_sched
        # self.cur_sched.setVerticalHeaderItem(new_row - 1, elem)
        # elem.setContextMenuPolicy(Qt.CustomContextMenu)
        # elem.customContextMenuRequested.connect(lambda x: self.right_click(x, elem))

    def right_click(self, point):
        obj = self.cur_sched.itemAt(point)
        self.delete.triggered.connect(lambda: self.delete_row(obj))
        # print(obj, type(obj))
        if type(obj) == QTableWidgetItem:
            self.popUp.exec_(self.cur_sched.mapToGlobal(point))

    def delete_row(self, obj):
        r = obj.row()
        # for i in range(0, 4):
        self.cur_sched.removeRow(r)

    def show_form(self):
        if self.form_active == False:
            f = Form(self).show()
            self.form_active = True

    def set_sched(self):
        if not self.seen_sched:
            self.new_data = []
            self.seen_sched = True
            self.cur_sched = QTableWidget(self)
            self.cur_sched.setColumnCount(4)
            self.cur_sched.setHorizontalHeaderLabels(["Name", "Time", "Link", "Days"])
            header = self.cur_sched.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            self.cur_sched.setContextMenuPolicy(Qt.CustomContextMenu)
            self.cur_sched.customContextMenuRequested.connect(self.right_click)

        intro = '''Let's get your schedule together.\nUse the button below to open a form to make your schedule.\nDon't worry about capitalization - it'll be adjusted for.\n\n''' \
        '''Right-click to view additional actions.\nDouble-click to edit an entry.'''
        cont = QPushButton("Continue")
        cont.setStyleSheet("margin-right:0;color:red;border: 3px solid red;background-color: white;height:48px;width:120px;")
        cont.clicked.connect(self.set_sched_2)

        make_form = QPushButton("Add new item")
        make_form.clicked.connect(self.show_form)
        
        info = QLabel(intro)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet('''color:white;
                                height:300px;
                                max-height:300px;
                                margin-bottom:30px;
                                font-size:18px;
                                font-family: Bookman, Verdana, Comic Sans MS, Arial;''')

        layout = QVBoxLayout()
        layout.addWidget(info)
        layout.addWidget(self.cur_sched)
        layout.addWidget(make_form)
        layout.addWidget(cont, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.cmw(layout)

    def set_sched_2(self):
        def final():
            msg = '''Schedule has been updated. Returning to main menu.'''
            info = QLabel(msg)
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet('''color:white;
                                    height:300px;
                                    max-height:300px;
                                    margin-bottom:30px;
                                    font-size:18px;
                                    font-family: Bookman, Verdana, Comic Sans MS, Arial;''')
            
            layout = QVBoxLayout()
            layout.addWidget(info)

            write_schedule(self.new_data)
            
            self.cmw(layout)

            QTimer.singleShot(2500, self.main_menu)

        msg = '''This is your schedule:'''
        msg2 = '''Press confirm to update your schedule.'''

        info = QLabel(msg)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet('''color:white;
                                height:300px;
                                max-height:300px;
                                margin-bottom:30px;
                                font-size:18px;
                                font-family: Bookman, Verdana, Comic Sans MS, Arial;''')

        info2 = QLabel(msg2)
        info2.setAlignment(Qt.AlignCenter)
        info2.setStyleSheet('''color:white;
                                height:300px;
                                max-height:300px;
                                margin-bottom:30px;
                                font-size:18px;
                                font-family: Bookman, Verdana, Comic Sans MS, Arial;''')

        back = QPushButton("Back")
        back.setStyleSheet("margin-left:0;color:red;border: 3px solid red;background-color: white;height:48px;width:120px;")
        back.clicked.connect(self.set_sched)

        new_sched = self.cur_sched
        new_sched.setEditTriggers(QAbstractItemView.NoEditTriggers)
        new_sched.setSelectionMode(QAbstractItemView.SingleSelection)
        new_sched.setSelectionBehavior(QAbstractItemView.SelectRows)

        confirm = QPushButton("Confirm")
        confirm.clicked.connect(final)

        layout = QVBoxLayout()
        layout.addWidget(info)
        layout.addWidget(new_sched)
        layout.addWidget(info2)
        layout.addWidget(confirm)
        layout.addWidget(back, alignment=Qt.AlignLeft | Qt.AlignBottom)

        self.cmw(layout)

def load(file):
    r = {}
    if os.path.isfile(file):
        with open(file) as f:
            t = f.readlines()
            r.update({x[:x.find(":")]:x[x.find(":") + 1:x.rfind(",")] for x in t})
    else:
        print(f"{file} not found! It may have been deleted if this is not the first setup.")
    # print(r)
    return r

def is_list(d):
    return d.count(",") > 0

def write_schedule(d):
    f = open("schedule.sched", "w")
    for e in d:
        cl, ti, li, dy = e

        tiw = ti.strip()
        clw = cl.strip()
        liw = li.strip()
        dyw = dy.strip()

        f.write(f"{tiw}\n{clw}\n{liw}\n{dyw}\n\n")

    f.close()

def load_sched():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    try:
        f = open("schedule.sched")
    except Exception as e:
        # print(f"Failed to load schedule! Error: {e}")
        return {}
    t = f.read().rstrip()
    b = t.split("\n\n")
    sched = {}
    dy_dict = {"S":0, "M":1, "T":2, "W":3, "TH":4, "F":5, "SA":6}
    for i in range(len(b)):
        d = b[i]
        ti = re.search(r"\d+:+\d+[AaPpMm]+", d)
        cl = re.search(r"[a-zA-Z ]+\s(?!\n)(?=\d)", d)
        li = re.search(r"https*://.*/.*\w", d)
        dy = d.split("\n")[-1]
        
        try:
            tiw = d[ti.start():ti.end()].strip()
            clw = d[cl.start():cl.end()].strip()
            liw = d[li.start():li.end()].strip()
            dys = [dy_dict.get(x, 2) for x in dy.strip().split(" ")]

            # f.write(f"{tiw}\n{clw}\n{liw}\n\n")
            
            sched.update({i:(clw, tiw, liw, dys)})
        except:
            # print("Failed to load schedule...")
            return sched

    return sched

def init_sel(verbose="False"):
    global driver
    def login(em, pas):
        for i in range(2):
            XPATH = "//input[@type='email']" if i == 0 else "//input[@type='password']"
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATH))
            )
            while True:
                try:
                    e = driver.find_element_by_xpath(XPATH)
                    e.send_keys(em if i == 0 else pas)
                    break
                except:
                    pass
            e.send_keys(Keys.RETURN)
        time.sleep(1)

    settings = load("settings.txt")
    email, password = settings.get("email"), settings.get("password")

    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("use-fake-ui-for-media-stream")
    if verbose == "False":
        chrome_options.add_argument("--log-level=OFF")
    driver = webdriver.Chrome(chrome_options=chrome_options)

    driver.get("https://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1&flowName=GlifWebSignIn&flowEntry=ServiceLogin")
    login(email, password)

def join_meet(link):
    # global driver
    # os.system(f"start chrome.exe {link} -incognito")
    if "g.co" in link or "google" in link:
        XPATH = "//span[contains(text(), 'Join now')]/parent::span/parent::div"
        driver.get(link)
        element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, XPATH))
                )
        join_button = driver.find_element_by_xpath(XPATH)
        join_button.click()
    else:
        driver.get("https://zoom.us/join")
        e = driver.find_element_by_id("join-confno")
        e.send_keys(link)
        e = driver.switchTo().activeElement();
        e.send_keys(Keys.ENTER)

def _run():
    global form
    form.test()
    form.run_menu()
    threading.Thread(target=run, daemon=True).start()
    # print("Done")

def run():
    global read_IO, cont_RUN, old_IO, form, glob_text
    sys.stdout = read_IO
    sett = load("settings.txt")
    
    if sett.get("verbose") != "True":
        verb = False
    else:
        verb = True

    if sett == {}:
        print("WARNING: no settings have been created; they will be created on next startup.")

    s = load_sched()
    if s == {}:
        print("Your schedule is blank!\n")
        print("Click below to set your schedule....")
    sys.stdout = old_IO

    while s == {}:
        glob_text = "Set your schedule"
        s = load_sched()
    sys.stdout = read_IO

    init_sel(sett.get("verbose", "False"))

    day = int(time.strftime("%w"))

    # offset = 4

    debounce = True
    old_time = None
    # class_nums = list(chain(range(0, 1), range(1 + offset, min(offset + 5, len(s)))))
    class_nums = range(len(s))
    if verb:
        print(s)
        print([i for i in class_nums])

    dayst = time.daylight
    cont_RUN = True
    while cont_RUN:
        t = time.time()

        hours = int(time.strftime("%I"))
        minutes = int(time.strftime("%M"))
        seconds = t % 60
        am = time.strftime("%p").lower()
        # print("CUR TIME: ", hours, minutes)

        if not debounce and (hours + (12 if am == "pm" else 0)) * 60 + minutes - old_time > 6:
            debounce = True

        for i in class_nums:
            # print(i)
            tim = s[i][1].lower()
            clss = s[i][0]
            dys = s[i][3]
            # print("RECORDED TIME: ", tim)
            h = int(tim[:tim.rfind(":")])
            m = int(tim[tim.rfind(":") + 1:tim.rfind("m") - 1])
            cm = tim[tim.rfind("m") - 1:]

            if debounce and day in dys and hours == h and minutes - m >= 0 and minutes - m <= 5 and am == cm:
                print(f"joining {clss}")
                for n in range(11):
                    try:
                        join_meet(s[i][2])
                        debounce = False
                        break
                    except:
                        print(f"Failed to join {clss}! Retrying..." + (f" {n}" if n > 0 else "" + "\n"))
                old_time = m + 60 * (h + (12 if cm == "pm" and h != 12 else 0))
        
        last = max([x for x in class_nums if day in s[x][3]], key=lambda x: int(s[x][1][:s[x][1].find(":")]) + int(s[x][1][s[x][1].find(":") + 1:-2]) / 60 + (12 if s[x][1][-2:].lower() == "pm" and s[x][1][:s[x][1].find(":")] != "12" else 0))
        tim = s[last][1].lower()
        lh, lm = int(tim[:tim.rfind(":")]), int(tim[tim.rfind(":") + 1:tim.find("m") - 1])
        lam = tim[tim.rfind("m") - 1:].lower()
        lhours = int(time.strftime("%H"))

        # print(lhours, lh, minutes, lm)

        if lhours > lh + (12 if lam == "pm" and lh != 12 else 0) and minutes > lm:
            break
            # pass
            # print(h, m, hours, minutes)
        # break
    sys.stdout = old_IO
    form.stopText = "All done! Click here to return..."

def start():
    global form
    app = QApplication()

    form = Widget()
    form.show()

    with open("design.qss", "r") as f:
        app.setStyleSheet(f.read())

    olddir = os.getcwd()
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    app.setWindowIcon(QIcon("logo.png"))
    os.chdir(olddir)
    
    app.exec_()

def main():
    global read_IO, old_IO, glob_text
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    os.system("cls")
    
    old_IO = sys.stdout
    read_IO = StringIO()
    glob_text = ""

    # if settings == {}:
        # setup()
    # elif open("schedule.sched").read() == "":
    #     set_sched()
        
    start()

if __name__ == "__main__":
    main()