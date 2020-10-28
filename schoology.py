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

def write_schedule(d, lis=False):
    if os.path.isfile("schedule.sched"):
        f = open("schedule.sched", "w")
        f.close()
    f = open("schedule.sched", "a")
    if lis:
        for i in d.split(","):
            ti = re.search(r"\d+:+\d+[AaPpMm]+", i)
            cl = re.search(r"[a-zA-Z ]+\s(?=\d)(?!\n)", i)
            li = re.search(r"https*://.*/.*\w", i)

            tiw = i[ti.start():ti.end()].strip()
            clw = i[cl.start():cl.end()].strip()
            liw = i[li.start():li.end()].strip()

            f.write(f"{tiw}\n{clw}\n{liw}\n\n")

    f.close()

def write_settings(args):
    f = open("settings.txt", "w")
    for k in args:
        f.write("%s:%s,\n" % (str(k), args.get(k)))

    f.close()

def set_sched():
    print("Let's get your schedule together.")
    print("You can either enter your classes one-by-one, e.g.:")
    print("    Study Hall\n    9:26AM\n    https://g.co/meet/your-link-here")
    print("\nOr you can enter them all at once as a comma-separated list, e.g.:")
    print("    Study Hall 9:26AM https://zoom.us/meeting/your-link-here, History 10:54 [link], Econ 1:07 [link], etc.")
    print("\nWhen you want to quit, just type '!quit' or '!q'")
    print("Don't worry about capitalization: I'll adjust it so everything will work smoothly for you! :)")
    
    c = 0
    while True:
        sched = input("\nPlease enter your " + ("next " if c == 1 else "") + "schedule or type !q to finish your schedule:\n")
        l = is_list(sched)
        if sched[:2].lower() == "!q":
            break

        if not l:
            cl = sched
            ti = input("\nPlease give the time at which this class starts (e.g. 10:00AM):\n")
            li = input("\nPlease give the link for the meeting of this class:\n")
            sched = cl + ti + li

        write_schedule(sched, l)
        c = 1
        if l:
            break
    
    os.system("cls")
    print("Thank you for setting up your user. You can now proceed with the program.")
    input("\nPress Enter to continue...")
    os.system("cls")

def setup():
    settings = {}
    print("Welcome to the schoology commandline organizer.")
    print("You will be guided for a first-time setup of your schoology schedule.")
    print("\nPress enter to continue...")
    input()

    os.system('cls')

    print("Let's introduce eachother. Hi, I'm SCHEDULY, the CMD line scheduler. And you are?")
    settings.update({"user":input("Enter your username:    ")})
    print("Hi, {0}!".format(settings.get("user")))
    input("\nPress enter to continue...")
    os.system("cls")

    print("In order to properly sign in to your google meetings, you need to login to your school GMAIL account:")
    while True:
        em = input("\nPlease enter your email address:    ")
        pa = input("Please enter your password:    ")
        r = input(f"\nIs this correct?\nEmail:  {em}\nPassword:  {pa}\n\ny/N:    ")
        if r[0].lower() == "y":
            break
        print("Operation canceled...")
        time.sleep(0.5)

    settings.update({"email":em, "password":pa, "verbose":"False"})
    write_settings(settings)
    os.system("cls")
    set_sched()

def run_setting():
    os.system("cls")
    print("Settings\n1:Modify Settings\n2:Modify Schedule\n3:Reset Settings\n4:Reset Schedule\n5:Back")
    c = input("Enter a number:    ")
    if c == "1":
        os.system("notepad \"settings.txt\"")
    elif c == "2":
        os.system("notepad \"schedule.sched\"")
    elif c == "3":
        open("settings.txt", "w").close()
        os.system("cls")
        print("All cleared!")
        time.sleep(0.5)
    elif c == "4":
        open("schedule.sched", "w").close()
        os.system("cls")
        print("All cleared!")
        time.sleep(0.5)
    elif c == "5":
        return
    else:
        print("Invalid input!")
        time.sleep(0.5)

    run_setting()

def load_sched():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    f = open("schedule.sched")
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
            print("Failed to load schedule...")
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

def run():
    os.system("cls")
    sett = load("settings.txt")
    
    if sett.get("verbose") != "True":
        os.system("cls")

    if sett == {}:
        print("WARNING: no settings have been created; they will be created on next startup.")

    init_sel(sett.get("verbose", "False"))

    s = load_sched()
    if s == {}:
        os.system("cls")
        print("Your schedule is blank!\n")
        print("Press Enter to create a schedule...")
        set_sched()

    day = int(time.strftime("%w"))

    # offset = 4

    debounce = True
    old_time = None
    # class_nums = list(chain(range(0, 1), range(1 + offset, min(offset + 5, len(s)))))
    class_nums = range(len(s))
    if sett.get("verbose") == "True":
        print(s)
        print([i for i in class_nums])

    s = load_sched()
    while True:
        t = time.time()

        hours = int(time.strftime("%I"))
        minutes = int(time.strftime("%M"))
        seconds = t % 60
        am = time.strftime("%p").lower()
        # print(am)

        if not debounce and minutes - old_time > 5:
            debounce = True

        for i in class_nums:
            # print(i)
            tim = s[i][1].lower()
            clss = s[i][0]
            dys = s[i][3]
            # print(tim)
            h = int(tim[:tim.rfind(":")])
            m = int(tim[tim.rfind(":") + 1:tim.rfind("m") - 1])
            cm = tim[tim.rfind("m") - 1:]

            if debounce and day in dys and hours == h and minutes - m >= 0 and minutes - m <= 3 and am == cm:
                print(f"joining {clss}")
                for n in range(11):
                    try:
                        join_meet(s[i][2])
                        debounce = False
                        break
                    except:
                        print(f"Failed to join {clss}! Retrying..." + (f" {n}" if n > 0 else "" + "\n"))
                old_time = minutes
        

        tim = s[class_nums[len(class_nums) - 1]][1].lower()
        lh, lm = int(tim[:tim.rfind(":")]), int(tim[tim.rfind(":") + 1:tim.find("m") - 1])
        lam = tim[tim.rfind("m") - 1:].lower()
        lhours = int(time.strftime("%H"))

        # print(lhours, lh, minutes, lm)

        if lhours > lh + (12 if lam == "pm" and lh != 12 else 0) and minutes > lm:
            break
            # pass

            # print(h, m, hours, minutes)
        # break
    print("The day is over! Enjoy the rest of it!")
    input("Press Enter to continue...")

def start():
    while True:
        os.system("cls")
        print(f"Hello {user}!")
        # print("Main Menu")
        menu = {1:"Run", 2:"Settings", 3:"Quit"}
        func = {1:run, 2:run_setting, 3:sys.exit}

        print("\n".join([str(i) + ":" + str(menu.get(i)) for i in menu]))
        c = input("Enter a number:    ")

        func.get(int(c), (lambda: None))()

        # init_sel()
        # join_meet("https://g.co/meet/MyersAPecon1")

def main():
    global email, password, user
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    os.system("cls")
    
    settings = load("settings.txt")

    # print(settings)
    user = settings.get("user", "user")
    email, password = settings.get("email"), settings.get("password")

    if settings == {}:
        setup()
    elif open("schedule.sched").read() == "":
        set_sched()
        
    start()

if __name__ == "__main__":
    main()