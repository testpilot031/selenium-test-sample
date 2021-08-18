-*- using:utf-8 -*-
'''
Sammary:

TODO:
'''


import time
import os
import json
import toml
import pprint
import sys

from multiprocessing import Process
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException


# test用
test_mode = 0
args = sys.argv
print(len(args))
if 2 == len(args):
    if type(args[1]) is str:
        if args[1] == "test_mode_normal":
            test_mode = 1
        if args[1] == "test_mode_error_unreach":
            test_mode = 2
        if args[1] == "test_mode_error_unmatchelement":
            test_mode = 3
    else:
        print('Argument is not string')
else:
    print('Arguments are too many')
print("test_mode is " + str(test_mode) + ". 0 is no test mode")


#def document_initialised(driver):
#    return driver.execute_script("return initialised")


def send_request(url,interval_sec,repeat_count):
    pid = os.getpid()
    JST = timezone(timedelta(hours=+9), 'JST')
    print('pid:'+ str(pid) + ' start, args:'+ url + ", " + str(interval_sec) + "," + str(repeat_count))


    start_time = None
    loginelement_text = None
    responsecode = None
    request_method_start_time = None
    request_method_end_time = None


    selector = "#xxxx > table > tbody > tr > td > a"
    # Trueならエラーを起こすための設定
    if test_mode == 3:
        selector = "abcdefg"


    csv_header = "request_method_start_time,request_method_end_time,responsetime(msec),url,responsecode"
    result = csv_header + "\n"


    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1200x600')
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {​​​​​​​"performance": "ALL"}​​​​​​​
    dest_address = url.replace('http://', '')
    dest_address = dest_address.replace('.', '_')
    dest_address = dest_address.replace('/', '')
    filename = '/xxx/xxx' + dest_address + "_"
    filename += datetime.now(JST).strftime('%Y%m%d%H%M%S') + '.log'


    for i in range(repeat_count):
        start_time = time.time()


        print('pid:'+ str(pid) + ' url : ' + url)
        driver = webdriver.Chrome(options=options, desired_capabilities=capabilities)
        # 10秒
        driver.set_page_load_timeout(10)
        request_method_start_time = datetime.now(JST)
        try:
            driver.get(url)
            request_method_end_time = datetime.now(JST)
            # response code 
            driver_current_url = driver.current_url
            responsecode = str(get_responsecode( driver.get_log("performance"), dest_address, driver_current_url))
            print('pid:'+ str(pid) + ', cur_url : ' + driver_current_url + ", responsecode: " + responsecode)
            if responsecode == "200":
                # html element
                # exception NoSuchElementException 
                loginelement = driver.find_element_by_css_selector(selector)
                print('pid:'+ str(pid) + ', loginelement_text : ' + loginelement.text)
                # login
                if loginelement.text == "login":
                    responsetime = (request_method_end_time - request_method_start_time).total_seconds()
                    result += str(request_method_start_time) + ", " + str(request_method_end_time) + ", " + str(responsetime) + ", " + url + "," + responsecode + "\n"
                    print('pid:'+ str(pid) + ', result : ' + url + "," + str(responsetime) + "," + str(request_method_start_time) + "," + str(request_method_end_time) + "," + responsecode)


        #
        # エラー処理
        #
        #
        except NoSuchElementException as no_such_element:
            request_method_end_time = datetime.now(JST)
            loginelement_text = ""
            errorstring = ""
            errorstring = str(no_such_element).replace('\n', '')
            print('pid:'+ str(pid) + ' NoSuchElementException')
            print('pid:'+ str(pid) + ' error:' + errorstring)
            #print('pid:'+ str(pid) + ' driver.page_source : ' + driver.page_source)
            result += str(request_method_start_time) + ",,," + url + ",,ERROR : " + errorstring + ' pid:'+ str(pid) + "\n"
            


        except Exception as e:
        # connection timeout 
            request_method_end_time = datetime.now(JST)
            loginelement_text = ""
            errorstring = ""
            errorstring = str(e).replace('\n', '')
            print('pid:'+ str(pid) + 'error:' + errorstring)
            result += str(request_method_start_time) + ",,," + url + ",,ERROR : " + errorstring + ' pid:'+ str(pid) + "\n"
            
        finally:
            csvfile = open(filename, 'a', encoding='UTF-8')
            csvfile.write(result)
            csvfile.close()
            result = ""
            responsecode = ""
            # driver object
            driver.quit()
            elapsed_time = time.time() - start_time
            if int(interval_sec) > elapsed_time :
                time.sleep(int(interval_sec) - elapsed_time)
            else:
                print('pid:'+ str(pid) +" interval_sec is short in this request")


    print('pid:'+ str(pid) + ' end, args:'+ url + ", " + str(interval_sec) + "," + str(repeat_count))


def get_responsecode( logs,dest_address,driver_current_url):
    responsecode = ""
    events = process_browser_logs_for_network_events(logs)
    for event in events:
        #pprint.pprint(event, stream=out)
        if "response" in event["params"]:
            if "url" in event["params"]["response"]:
                if event["params"]["response"]["url"] == driver_current_url:
                    if "status" in event["params"]["response"]:
                        responsecode = event["params"]["response"]["status"]
    return responsecode



def process_browser_logs_for_network_events(logs):
    """
    Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
    since we're interested in the network events specifically.
    """
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
                "Network.response" in log["method"]
                # or "Network.request" in log["method"]
                # or "Network.webSocket" in log["method"]
        ):
            yield log


def main():
    with open("/home/ssm-user/selenium-script/config.txt", "r") as fp:
        cfg = toml.load(fp)
    urls   = cfg["urls"]
    interval_sec = cfg["interval_sec"]
    repeat_count = cfg["repeat_count"]
    if test_mode > 0:
        interval_sec = 6
        repeat_count = 3
        if test_mode == 1:
            print("test_mode: " + str(test_mode) + " is normal")
        if test_mode == 2:
            print("test_mode: " + str(test_mode) + " is unreach")
            urls = ["http://xx.x.x.x","http://y.y.y.y"]
        if test_mode == 3:
            print("test_mode: " + str(test_mode) + " is no such element")
    pid = os.getpid()
    print('parent_pid:'+str(pid) + " start")
    for url in urls:
        proc = Process(target=send_request, args=(url,interval_sec,repeat_count))
        proc.start()


if __name__ == "__main__":
    main()
