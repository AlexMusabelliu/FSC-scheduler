import os, json, re, sys, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from itertools import chain

def load(file):
    r = {}
    if os.path.isfile(file):
        with open(file) as f:
            t = f.readlines()
            r.update({x[:x.find(":")]:x[x.find(":") + 1:x.rfind(",")] for x in t})
    else:
        print(f"{file} not found! It may have been deleted if this is not the first setup.")
    return r

def is_list(d):
    return d.count(",") > 0

def write_schedule(d, list=False):
    f = open("schedule.sched")
    if list:
        for i in d.split(","):
            ti = re.search(r"\d+:+\d+[AaPpMm]+", i)
            cl = re.search(r"[a-zA-Z ]+\s(?!\n)", i)
            li = re.search(r"https*://.*/.*\w", i)

            tiw = i[ti.start():ti.end()].strip()
            clw = i[cl.start():cl.end()].strip()
            liw = i[li.start():li.end()].strip()

            f.write(f"{tiw}\n{clw}\n{liw}\n\n")

    f.close()

def write_settings(args):
    f = open("settings.txt")
    f.write("user:{0},\n" % args.get("user"))
    f.write("alternate:{0},\n" % args.get("alternate"))
    f.close()


def setup():
    settings = {}
    print("Welcome to the schoology commandline organizer.")
    print("You will be guided for a first-time setup of your schoology schedule.")
    print("\nPress enter to continue...")
    input()

    print("Let's introduce eachother. Hi, I'm SCHEDULY, the CMD line scheduler. And you are?")
    settings.update({"user":input("Enter your username:    ")})
    print("Hi, {0}!" % settings.get("user"))
    while True:
        print("Do you go by an alternating schedule?")
        alt = input("Yes/[No]:    ")
        if alt[0].lower() == "y":
            alt = True
        else:
            alt = False
        print(("You have an alternating schedule." if alt else "You don't have an alternating schedule.") + " Is this correct?")
        cont = input("Yes/[No]:    ")
        if cont[0].lower() == "y":
            break
        print("Canceled the operation.")
    settings.update({"alternate":str(alt)})
    write_settings(settings)

    print("Let's start by getting the schedule together.")
    print("You can either enter your classes one-by-one, e.g.:")
    print("    Study Hall 9:26: https://g.co/meet/your-link-here")
    print("\nOr you can enter them all at once, e.g.:")
    print("    Study Hall 9:26: https://zoom.us/meeting/your-link-here, History 10:54: [link], Econ 1:07: [link], etc.")
    print("\nWhen you want to quit, just type 'quit' or 'q'")
    
    sched = input("\nPlease enter your schedule:\n")
    l = is_list(sched)

    write_schedule(sched, l)

    print("Thank you for setting up your user. You can now proceed with the program.")
    input("\nPress Enter to continue...")

def run_setting():
    pass

def load_sched():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    f = open("schedule.sched")
    t = f.read()
    b = t.split("\n\n")
    sched = {}
    for i in range(len(b)):
        d = b[i]
        ti = re.search(r"\d+:+\d+[AaPpMm]+", d)
        cl = re.search(r"[a-zA-Z ]+\s(?!\n)", d)
        li = re.search(r"https*://.*/.*\w", d)

        tiw = d[ti.start():ti.end()].strip()
        clw = d[cl.start():cl.end()].strip()
        liw = d[li.start():li.end()].strip()

        # f.write(f"{tiw}\n{clw}\n{liw}\n\n")
        
        sched.update({i:(clw, tiw, liw)})

    return sched

def init_sel():
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

    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("use-fake-ui-for-media-stream")
    driver = webdriver.Chrome(chrome_options=chrome_options)

    driver.get("https://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1&flowName=GlifWebSignIn&flowEntry=ServiceLogin")
    login(email, password)

def join_meet(link):
    # global driver
    # os.system(f"start chrome.exe {link} -incognito")
    XPATH = "//span[contains(text(), 'Join now')]/parent::span/parent::div"
    driver.get(link)
    element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATH))
            )
    join_button = driver.find_element_by_xpath(XPATH)
    join_button.click()

def run():
    init_sel()
    s = load_sched()
    sett = load("settings.txt")
    day = int(time.strftime("%w"))
    if day == 1:
        print("Sorry, no synchronous classes today! Enjoy your Monday!")
        return
    day = day > 1 and day < 4 

    if day:
        offset = 0
    else:
        offset = 4

    # offset = 4

    debounce = True
    old_time = None
    if sett.get("verbose") == "True":
        print(s)
        print([i for i in chain(range(0, 1), range(1 + offset, offset + 5))])

    while True:
        s = load_sched()
        t = time.time()

        days = t // 86400
        hours = int(time.strftime("%I"))
        minutes = int(time.strftime("%M"))
        seconds = t % 60
        am = time.strftime("%p").lower()
        # print(am)

        if not debounce and minutes != old_time:
            debounce = True

        for i in chain(range(0, 1), range(1 + offset, offset + 5)):
            # print(i)
            tim = s[i][1].lower()
            # print(tim)
            h = int(tim[:tim.rfind(":")])
            m = int(tim[tim.rfind(":") + 1:tim.rfind("m") - 1])
            cm = tim[tim.rfind("m") - 1:]

            if hours == h and minutes == m and am == cm and debounce:
                print("joining")
                join_meet(s[i][2])
                debounce = False
                old_time = m

        tim = s[len(s) - 1][1].lower()
        lh, lm = int(tim[:tim.rfind(":")]), int(tim[tim.rfind(":") + 1:tim.find("m") - 1])
        lam = tim[tim.rfind("m") - 1:]
        if hours > lh and minutes > lm and am == lam:
            break
            # pass

            # print(h, m, hours, minutes)
        # break
    print("The day is over! Enjoy the rest of it!")

def start():
    # print('started')
    while True:
        menu = {1:"Run", 2:"Settings", 3:"Quit"}
        func = {1:run, 2:run_setting, 3:sys.exit}

        print("\n".join([str(i) + ":" + str(menu.get(i)) for i in menu]))
        c = input("Enter a number:    ")

        func.get(int(c), (lambda: None))()
        # init_sel()
        # join_meet("https://g.co/meet/MyersAPecon1")

def main():
    global email, password
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    os.system("cls")
    
    settings = load("settings.txt")

    # print(settings)

    user = settings.get("user", "user")
    email, password = settings.get("email"), settings.get("password")

    print(f"Hello {user}!")

    if settings == {}:
        setup()
        
    start()

if __name__ == "__main__":
    main()