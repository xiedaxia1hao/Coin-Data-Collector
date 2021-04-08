from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from multiprocessing.pool import ThreadPool
from logging import getLogger
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import time
import os
import traceback
from constants import SEED_PHRASE, METAMASK_PASSWORD, HECO_NETWORK_CONFIG, SMART_CHAIN_NETWORK_CONFIG

logger = getLogger(__name__)

MAX_THREAD_COUNT = 100
THREAD_POOL = ThreadPool(MAX_THREAD_COUNT)


def create_browser(webdriver_path='./chromedriver', show_browser=True, network_needed=None, b_id=-1):
    # create a selenium object that mimics the browser
    browser_options = Options()
    user_data_dir = "./user_data/data_{}".format(b_id)
    browser_options.add_argument('--no-sandbox')
    browser_options.add_argument("--user-data-dir={}".format(user_data_dir))
    browser_options.add_argument("--disable-dev-shm-usage")
    # browser_options.add_argument("--remote-debugging-port=9222")

    # headless tag created an invisible browser
    if not show_browser:
        browser_options.add_argument("--headless")

    # add metamask extention
    # browser_options.add_extension('./nkbihfbeogaeaoehlefnkodbefgpgknn{}.crx'.format(b_id))
    # if b_id == 1:
    #     extension_path = 'nkbihfbeogaeaoehlefnkodbefgpgknn1.crx'
    # elif b_id == 2:
    #     extension_path = 'nkbihfbeogaeaoehlefnkodbefgpgknn2.crx'
    # elif b_id == 3:
    #     extension_path = 'nkbihfbeogaeaoehlefnkodbefgpgknn3.crx'
    # elif b_id == 4:
    #     extension_path = 'nkbihfbeogaeaoehlefnkodbefgpgknn4.crx'

    browser_options.add_extension(os.path.abspath('nkbihfbeogaeaoehlefnkodbefgpgknn.crx'))
    browser = webdriver.Chrome(webdriver_path, chrome_options=browser_options)

    time.sleep(3)
    print(browser.current_url)
    if browser.current_url == 'chrome-extension://gnhbonneopkmbnchfdcoegmaeimkmagp/home.html#unlock':
        password_element = browser.find_element_by_xpath("//*[@id=\"password\"]")
        password_element.send_keys(METAMASK_PASSWORD)
        WebDriverWait(browser, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id=\"app-content\"]/div/div[4]/div/div/button"))).click()
        return browser

    # Wait until the metamask extension UI pops out
    print('not yet find get started')
    try:
        WebDriverWait(browser, 3).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div/div/button")))
    except Exception as e:
        # the extention load failed.. reloading...
        browser.close()
        return create_browser(webdriver_path, show_browser, network_needed)

    print('find get started')

    if network_needed:
        try:
            config_metamask(browser, network_needed)
        except Exception as e:
            # if for some reason we encounter the timeout error, let's re-create the browser again
            browser.close()
            create_browser(webdriver_path, show_browser, network_needed)

    return browser


def config_metamask(browser, network_needed):
    # we don't need to config metamask if the network needed is eth or not in ['heco', 'sc']
    if network_needed == 'eth' or network_needed not in ['heco', 'sc']:
        return

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
    browser.get('chrome-extension://gnhbonneopkmbnchfdcoegmaeimkmagp/home.html#settings/networks')

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
