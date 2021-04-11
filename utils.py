from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from multiprocessing.pool import ThreadPool
from logging import getLogger
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import multiprocessing as mp
import random
import time
import os
import traceback
from constants import SEED_PHRASE, METAMASK_PASSWORD, HECO_NETWORK_CONFIG, SMART_CHAIN_NETWORK_CONFIG, \
    NETWORK_AND_SLUG_MAPPING

logger = getLogger(__name__)

MAX_THREAD_COUNT = mp.cpu_count()
THREAD_POOL = ThreadPool(MAX_THREAD_COUNT)
METAMASK_EXTENSION_NAME = 'nkbihfbeogaeaoehlefnkodbefgpgknn'
METAMASK_EXTENSION_FILE_NAME = METAMASK_EXTENSION_NAME + '.crx'
METAMASK_HOMEPAGE_URL = 'chrome-extension://{}'.format(METAMASK_EXTENSION_NAME)


def create_browser(webdriver_path='./chromedriver', show_browser=True, network_needed=None, b_id=-1):
    print("--remote-debugging-port={}".format(str(b_id)))
    # create a selenium object that mimics the browser
    browser_options = Options()
    user_data_dir = "./user_data/data_{}".format(b_id)
    browser_options.add_argument('--no-sandbox')
    browser_options.add_argument("--user-data-dir={}".format(user_data_dir))
    browser_options.add_argument("--disable-dev-shm-usage")
    # browser_options.add_argument("--remote-debugging-port={}".format(str(b_id)))
    browser_options.add_argument("--verbose")  # detail log

    # headless tag created an invisible browser
    if not show_browser:
        browser_options.add_argument("--headless")

    print('EXTENSION ADDING... b-id: {}'.format(b_id))
    browser_options.add_extension(os.path.abspath(METAMASK_EXTENSION_FILE_NAME))
    print('EXTENSION ADD... b-id: {}'.format(b_id))
    # chromedriver version: 89.0.4389.114
    browser = webdriver.Chrome(webdriver_path, chrome_options=browser_options)
    # print(browser.capabilities['browserVersion'])  # 89.0.4389.114
    # print(browser.capabilities['chrome']['chromedriverVersion']) # 2.41.578706 (5f725d1b4f0a4acbf5259df887244095596231db)

    print(49)

    print('before sleep url: {}'.format(browser.current_url))

    # todo
    random_sleep_time = random.uniform(2, 4)
    time.sleep(random_sleep_time)

    # maybe chrome://new-tab-page/？
    print('after sleep url: {}'.format(browser.current_url))
    # edge case
    # if browser.current_url == 'chrome://new-tab-page/':
    #     browser.quit()
    #     return create_browser(webdriver_path, show_browser, network_needed)

    # logger.error('CURRENT TRACEBACK: \n{}'.format(traceback.format_exc()))
    # traceback.print_stack()

    time.sleep(random.uniform(1, 2))
    # make sure the metamask is getting focused
    for handle in browser.window_handles:
        browser.switch_to.window(handle)

        # Switch to connect with metamask popup
        if 'MetaMask' in browser.title:
            break
    print('After changing the focus, the current url is: {}'.format(browser.current_url))
    time.sleep(random.uniform(1, 2))

    try:
        if browser.current_url == '{}/home.html#unlock'.format(METAMASK_HOMEPAGE_URL):
            # browser.quit()
            # return create_browser(webdriver_path, show_browser, network_needed)
            print('Entering the normal unlock page... b-id: {}'.format(b_id))
            WebDriverWait(browser, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"password\"]")))
            print('Trying find the password input... b-id: {}'.format(b_id))
            password_element = browser.find_element_by_xpath("//*[@id=\"password\"]")
            print('Finding the password input SUCCESS!...  b-id: {}'.format(b_id))
            password_element.send_keys(METAMASK_PASSWORD)
            WebDriverWait(browser, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"app-content\"]/div/div[4]/div/div/button"))).click()
            print('get into line 67')

            time.sleep(random.uniform(5, 8))

            try:
                metamask_asked_for_swapping_popup = browser.find_element(By.CLASS_NAME, "popover-header")
                if metamask_asked_for_swapping_popup:
                    close_button = metamask_asked_for_swapping_popup.find_element(By.TAG_NAME, 'button')
                    close_button.click()
            except Exception as e:
                pass

            # check the current network
            time.sleep(random.uniform(1, 2))
            WebDriverWait(browser, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"app-content\"]/div/div[1]/div/div[2]/div[1]/div")))
            current_selected_network = browser.find_element(By.XPATH, "//*[@id=\"app-content\"]/div/div[1]/div/div[2]/div[1]/div").text
            print('b_id: {}... CHECK NETWORK: {} vs. {}'.format(b_id, network_needed, current_selected_network))
            if network_needed and NETWORK_AND_SLUG_MAPPING.get(network_needed, '') != current_selected_network:
                try:
                    WebDriverWait(browser, 5).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[@id=\"app-content\"]/div/div[1]/div/div[2]/div[1]/div/div[2]"))).click()
                    WebDriverWait(browser, 5).until(EC.presence_of_element_located(
                        (By.CLASS_NAME, "dropdown-menu-item")))
                    drop_list = browser.find_elements(By.CLASS_NAME, "dropdown-menu-item")
                    for available_network in drop_list:
                        if available_network.text == NETWORK_AND_SLUG_MAPPING.get(network_needed, ''):
                            available_network.click()
                            time.sleep(1)
                            return browser
                    WebDriverWait(browser, 5).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[@id=\"app-content\"]/div/div[1]/div/div[2]/div[1]/div/div[2]"))).click()
                    # Config Smart Chain Network
                    if network_needed == 'sc':
                        config_network(browser, SMART_CHAIN_NETWORK_CONFIG)

                    # Config Heco Network
                    if network_needed == 'heco':
                        config_network(browser, HECO_NETWORK_CONFIG)
                except Exception as e:
                    pass
            return browser
    except Exception as e:
        print("CREATED BROWSER FAIL P1: {}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("CREATED BROWSER FAIL P1: {}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        browser.quit()
        return create_browser(webdriver_path, show_browser, network_needed, b_id)

    # Wait until the metamask extension UI pops out
    print('try to config')
    try:
        print('Current URL: {}'.format(browser.current_url))
        print('***************************************')
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/div/button")))
        config_metamask(browser, network_needed)
    except Exception as e:
        # the extention load failed.. reloading...
        print("CREATED BROWSER FAIL P2: {}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("CREATED BROWSER FAIL P2: {}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        browser.quit()
        return create_browser(webdriver_path, show_browser, network_needed, b_id)

    return browser


def config_metamask(browser, network_needed):
    # # we don't need to config metamask if the network needed is eth or not in ['heco', 'sc']
    # if network_needed == 'eth' or network_needed not in ['heco', 'sc']:
    #     return

    # Click "Get Started" Button
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/div/button"))).click()

    # Click "Import Wallet" Button
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/div[2]/div/div[2]/div[1]/button"))).click()

    # Click "No Thanks" Button
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/div/div[5]/div[1]/footer/button[1]"))).click()

    # Input "Seed Phrase" Element
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/form/div[4]/div[1]/div/input")))
    seed_phrase_element = browser.find_element_by_xpath("//*[@id=\"app-content\"]/div/div[3]/div/div/form/div[4]/div[1]/div/input")
    seed_phrase_element.send_keys(SEED_PHRASE)

    # Input "New password" & "Confirm Password" Element
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"password\"]")))
    new_password_element = browser.find_element_by_xpath("//*[@id=\"password\"]")
    confirm_password_element = browser.find_element_by_xpath("//*[@id=\"confirm-password\"]")
    new_password_element.send_keys(METAMASK_PASSWORD)
    confirm_password_element.send_keys(METAMASK_PASSWORD)

    # Click "Term of Use" Checkbox
    checkbox_element = browser.find_element_by_xpath("//*[@id=\"app-content\"]/div/div[3]/div/div/form/div[7]/div")
    checkbox_element.click()

    # Click "Import" Button
    import_button_element = browser.find_element_by_xpath("//*[@id=\"app-content\"]/div/div[3]/div/div/form/button")
    import_button_element.click()

    # Click "All Done" Button
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/button"))).click()

    # Config Smart Chain Network
    if network_needed == 'sc':
        config_network(browser, SMART_CHAIN_NETWORK_CONFIG)

    # Config Heco Network
    if network_needed == 'heco':
        config_network(browser, HECO_NETWORK_CONFIG)


def config_network(browser, network_config):
    browser.get('{}/home.html#settings/networks'.format(METAMASK_HOMEPAGE_URL))

    # Click "Add Network" Button
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[4]/div/div[2]/div[2]/div/div[1]/div/button"))).click()

    # Wait until all UI elements pop up
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"network-name\"]")))

    # Input "Network Name" Element
    network_name_element = browser.find_element_by_xpath("//*[@id=\"network-name\"]")
    network_name_element.send_keys(network_config.get('network_name'))

    # Input "New RPC URL" Element
    new_rpc_url_element = browser.find_element_by_xpath("//*[@id=\"rpc-url\"]")
    new_rpc_url_element.send_keys(network_config.get('new_rpc_url'))

    # Input "Chain ID" Element
    chain_id_element = browser.find_element_by_xpath("//*[@id=\"chainId\"]")
    chain_id_element.send_keys(network_config.get('chain_id'))

    # Input "Currency Symbol" Element
    currency_symbol_element = browser.find_element_by_xpath("//*[@id=\"network-ticker\"]")
    currency_symbol_element.send_keys(network_config.get('currency_symbol'))

    # Input "Block Explorer URL" Element
    block_explorer_url_element = browser.find_element_by_xpath("//*[@id=\"block-explorer-url\"]")
    block_explorer_url_element.send_keys(network_config.get('block_explorer_url'))

    # Click Save Button
    browser.find_element_by_xpath("//*[@id=\"app-content\"]/div/div[4]/div/div[2]/div[2]/div/div[2]/div[2]/div[7]/button[2]").click()
    time.sleep(10)


def run_in_threads(task_list, **kwargs):
    ttl = int(kwargs.get('timeout') or 120)
    print('MAX CORE NUMBER: {}'.format(mp.cpu_count()))
    task_map = {}
    for i, (func, params) in enumerate(task_list):
        task_map[i] = THREAD_POOL.apply_async(func, args=params)

    running_tasks = [task_map[i] for i in sorted(task_map.keys())]
    results = []
    for r in running_tasks:
        value = None
        try:
            value = r.get(ttl)
        except Exception as e:
            logger.error('Failed to get result from thread: {}.{}.{}'.format(e.__class__.__name__, e, traceback.format_exc()))
        results.append(value)
    return results


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
