import time
from copy import copy

from selenium.common.exceptions import TimeoutException, ElementNotVisibleException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from joblib import Parallel, delayed

from constants import MDEX_URL, VENUS_API_URL, COINWIND_URL, FILDA_URL, LENDHUB_URL, HFI_URL, CURVE_API_URL, \
    YFI_API_URL, VESPER_API_URL, SUSHI_URL, PANCAKESWAP_URL, AUTOFARM_API_URL, ELLIPSIS_URL, PANCAKEBUNNY_URL, BELT_URL, \
    ALPACAFINANCE_URL, BAKE_URL, ALPACAFINANCE_TVL_URL, BAKE_TVL_URL, PANCAKESWAP_TVL_URL, SUSHI_TVL_URL, CURVE_TVL_URL
from excel_generator import write_excel, write_ellipsis_excel, write_aplaca_excel
from utils import create_browser, run_in_threads, human_format, kill_chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import json
import traceback
import logging
import timeout_decorator
logger = logging.getLogger(__name__)


def is_valid_mdex_row(items):
    return len(items) >= 6


# Browser Needed
def get_heco_mdex_data():
    driver = create_browser(b_id=1)
    try:
        print(type(driver))
        print(isinstance(driver, WebDriver))
        driver.get(MDEX_URL)
        main_window_handle = driver.current_window_handle

        try:
            connect_metamask_v2(driver)
        except Exception as e:
            print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        # Switch back to main tab
        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 6).until(EC.presence_of_element_located(
            (By.XPATH,  "//*[@id=\"app\"]/section/div[2]/div[2]/div/div[3]/table")))

        table = driver.find_element(By.XPATH, "//*[@id=\"app\"]/section/div[2]/div[2]/div/div[3]/table")

        rows = table.find_elements(By.TAG_NAME, "tr")
        res = []

        for row in rows:
            try:
                items = row.text.split('\n')
                if is_valid_mdex_row(items):
                    res.append(
                        {
                            'LP': items[0],
                            'Daily Output': items[1],
                            'Monthly Output': items[2],
                            'Value Locked': items[3],
                            'APY': items[4],
                            'Your Reward': items[5]
                        }
                    )
            except Exception as e:
                print("get_heco_mdex_data get_row_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_heco_mdex_data get_row_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        # get tvl
        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"app\"]/section/div[1]/div[2]/div[1]/div").find_element(By.TAG_NAME, 'span').text
        except Exception as e:
            print("get_heco_mdex_data get tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_mdex_data get tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            tvl = None
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_sc_venus_data():
    try:
        resp = json.loads(requests.get(VENUS_API_URL).content)
        res = []
        tvl = 0
        for row in resp.get('data', {}).get('markets', {}):
            try:
                res.append(
                    {
                        'asset': row.get('underlyingSymbol'),
                        'total_supply_u': "${}".format(human_format(float(row.get('totalSupplyUsd')))),
                        'total_borrow_u': "${}".format(human_format(float(row.get('totalBorrowsUsd')))),
                        'supply_apy_u': str(round(float(row.get('supplyApy', 0)) + float(row.get('supplyVenusApy', 0)), 2)) + "%",
                        'supply_apy_d': str(round(float(row.get('supplyVenusApy', 0)), 2))+"%",
                        'borrow_apy_u': str(round(float(row.get('borrowApy', 0)) + float(row.get('borrowVenusApy', 0)), 2)) + "%",
                        'borrow_apy_d': str(round(float(row.get('borrowVenusApy', 0)), 2)) + "%",
                        'liquidity': "${}".format(human_format(float(row.get('liquidity', 0)))),
                        'price': "${}".format(human_format(float(row.get('tokenPrice', 0))))
                    }
                )
                tvl += float(row.get('totalSupplyUsd'))
            except Exception as e:
                print("get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return {
            'data': res,
            'tvl': '${:,}'.format(round(tvl, 2))
        }
    except Exception as e:
        print("get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }


def is_valid_coinwind_data(res):
    check_all_apy_validity = [_v == '0.00%' for row in res for _k, _v in row.items() if _k == 'APY (Compound Interest)']
    count_invalid_apy_num = sum(check_all_apy_validity)
    invalid_apy_percentage = count_invalid_apy_num * 1.0 / len(check_all_apy_validity) if len(check_all_apy_validity) > 0 else 0
    if invalid_apy_percentage > 0.2:
        return False
    return True


def get_heco_coinwind_data():
    driver = create_browser(network_needed='heco', b_id=3)
    try:
        driver.get(COINWIND_URL)

        main_window_handle = driver.current_window_handle

        try:
            WebDriverWait(driver, 4).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"WEB3_CONNECT_MODAL_ID\"]/div/div/div[2]/div[1]/div"))).click()
            connect_metamask_v2(driver)
        except ElementNotVisibleException as e:
            pass
        except Exception as e:
            print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        # Switch back to main tab
        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'MuiGrid-root MuiGrid-container MuiGrid-item MuiGrid-grid-xs-12')]")))
        for _ in range(10):
            rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiGrid-root MuiGrid-container MuiGrid-item MuiGrid-grid-xs-12')]")
            rows = copy(rows)
            res = []
            el = driver.find_element_by_tag_name('body')
            el.screenshot('coinwind.png')
            elem = driver.find_element_by_xpath("//*")
            source_code = elem.get_attribute("outerHTML")
            with open('coinwind.html', 'w') as f:
                f.write(source_code)
            for i, row in enumerate(rows):
                try:
                    # Sample row.text:
                    # 'MDX\nStore MDX MDX\n0.0000\nEarned (MDX)\n108.34%\nAPY(Compound Interest)\n\n\n\n28,705,423.78\nVL (MDX)'
                    items = str.splitlines(row.text)
                    res.append(
                        {
                            'Assets U': items[0],
                            'Assets D': items[1],
                            'Earned (MDX)': items[6],
                            'APY (Compound Interest)': items[11],
                            items[12]: items[13]
                        }
                    )
                except Exception as e:
                    print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    continue
            if not is_valid_coinwind_data(res):
                time.sleep(1)
            else:
                break
        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div/div[2]/div[1]/div[3]/div[1]/div[2]").text
        except Exception as e:
            tvl = None
            print("get_heco_coinwind_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_heco_coinwind_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_heco_filda_data():
    driver = create_browser(network_needed='heco', b_id=2)
    try:
        driver.get(FILDA_URL)

        main_window_handle = driver.current_window_handle

        try:
            # connect the wallet
            WebDriverWait(driver, 4).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div[1]/div[2]/div[2]/button"))).click()

            WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[3]/div/div/div[2]/div/div/div/button"))).click()

            connect_metamask_v2(driver)
        except TimeoutException as e:
            pass
        except Exception as e:
            print("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        # Switch back to main tab
        driver.switch_to.window(main_window_handle)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Markets_marketsItemRow')]")))

        rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'Markets_marketsItemRow')]")
        res = []
        for row in rows:
            try:
                items = row.text.split('\n')
                # U represents the upper row, the D represents the lower row
                res.append(
                    {
                        'Assets': items[0],
                        'Savings Rate U': items[1],
                        'Savings Rate D': items[2],
                        'Borrow Cost U': items[3],
                        'Borrow Cost D.': items[4],
                        'Liquidity U': items[5],
                        'Liquidity D': items[6],
                        'Total Borrowed U': items[7],
                        'Total Borrowed D': items[8],
                        'Total Supply U': items[9],
                        'Total Supply D': items[10],
                        'Utilization': items[11]
                    }
                )
            except Exception as e:
                print("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        try:
            tvl_placeholder = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div[2]/div[2]/div[3]/div/div[2]").text
            tvl = tvl_placeholder[tvl_placeholder.index('$')-1:] or tvl_placeholder
        except Exception as e:
            tvl = None
            print("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def connect_metamask_v2(driver):

    metamask_window_handle = None
    for i in range(5):
        if not metamask_window_handle:
            for handle in driver.window_handles:
                driver.switch_to.window(handle)

                # Switch to connect with metamask popup
                if driver.title == 'MetaMask Notification':
                    metamask_window_handle = handle
                    break

    # if we don't find the metamask, we could simply return
    if not metamask_window_handle:
        return

    # else, we connect the chrome with metamask
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div[2]/div[4]/div[2]/button[2]"))).click()

    time.sleep(1)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div[2]/div[2]/div[2]/footer/button[2]"))).click()

    time.sleep(0.5)


def connect_metamask(driver):

    main_window_handle = driver.current_window_handle

    metamask_window_handle = None
    for i in range(10):
        if not metamask_window_handle:
            for handle in driver.window_handles:
                driver.switch_to.window(handle)

                # Switch to connect with metamask popup
                if driver.title == 'MetaMask Notification':
                    metamask_window_handle = handle
                    break
    # if we don't find the metamask, we could simply return
    if not metamask_window_handle:
        driver.switch_to.window(main_window_handle)
        return

    # else, we connect the chrome with metamask
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div[2]/div[4]/div[2]/button[2]"))).click()

    time.sleep(1)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//*[@id=\"app-content\"]/div/div[3]/div/div[2]/div[2]/div[2]/footer/button[2]"))).click()

    time.sleep(0.5)

    driver.switch_to.window(main_window_handle)


def get_heco_lendhub_data():
    driver = create_browser(network_needed='heco', b_id=4)
    try:
        driver.get(LENDHUB_URL)

        main_window_handle = driver.current_window_handle

        try:
            connect_metamask_v2(driver)
        except Exception as e:
            print("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//tbody[contains(@class, 'ant-table-tbody')]")))

        time.sleep(3)

        lp_market_res = []
        single_market_res = []
        total_width = driver.execute_script("return document.body.offsetWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(total_width+750, total_height)
        if not (lp_market_res and single_market_res):
            lp_market_res = []
            single_market_res = []
            print(1)
            tables = driver.find_elements(By.XPATH, "//tbody[contains(@class, 'ant-table-tbody')]")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    try:
                        items = str.splitlines(row.text)
                        # LP Market
                        if len(items) == 5:
                            lp_market_res.append(
                                {
                                    'Assets': items[0],
                                    'Supply APY': items[1],
                                    'Total': items[2],
                                    'Wallet Balance': items[3],
                                    'manage': items[4]
                                }
                            )

                        # Single Market
                        if len(items) == 9:
                            # There is a issue here to parse the row.text by str.splitlines() or built-in split.
                            # Below is the temperary walkaround:
                            cols = row.find_elements(By.TAG_NAME, "td")
                            supply_apy_u = cols[1].find_elements(By.TAG_NAME, "span")[0].text
                            supply_apy_d = cols[1].find_elements(By.TAG_NAME, "div")[0].text
                            borrow_cost_u = cols[1].find_elements(By.TAG_NAME, "span")[0].text
                            borrow_cost_d = cols[1].find_elements(By.TAG_NAME, "div")[0].text

                            single_market_res.append(
                                {
                                    'Assets': cols[0].text,
                                    'Supply APY U': supply_apy_u,
                                    'Supply APY D': supply_apy_d,
                                    'Borrow Cost U': borrow_cost_u,
                                    'Borrow Cost D': borrow_cost_d,
                                    'Total Volume': cols[3].text,
                                    'Liquidity': cols[4].text,
                                    'Wallet Balance': cols[5].text,
                                    'Manage': cols[6].text
                                }
                            )
                    except Exception as e:
                        print("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                            traceback.format_exc()))
                        logger.error("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                                   traceback.format_exc()))
                        continue

        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"__layout\"]/div/div[2]/div[1]/div/div[1]/div/ul/li[2]/p").text
        except Exception as e:
            print("get_heco_lendhub_data tvl error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                traceback.format_exc()))
            logger.error("get_heco_lendhub_data tvl error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                       traceback.format_exc()))
            tvl = None
        return {
            'data': {
                "lp_market_res": lp_market_res,
                "single_market_res": single_market_res
            },
            'tvl': tvl
        }
    except Exception as e:
        print("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                            traceback.format_exc()))
        logger.error("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                   traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def is_valid_hfi_data(res):
    # if >30% apy and total data is valid, we assume the data is valid,
    #   as sometimes not all data will be available.
    for k, v in res.items():
        # check_all_apy_value = [_v for row in v for _k, _v in row.items() if _k == 'APY']
        # check_all_total_value = [_v for row in v for _k, _v in row.items() if _k == 'APY']
        check_all_apy_validity = [_v == '--' for row in v for _k, _v in row.items() if _k == 'APY']
        check_all_total_validity = [_v == '--' for row in v for _k, _v in row.items() if _k == 'total']
        count_valid_apy_num = sum(check_all_apy_validity)
        count_valid_total_num = sum(check_all_total_validity)
        valid_apy_percentage = 1 - count_valid_apy_num * 1.0 / len(check_all_apy_validity) if len(check_all_apy_validity) > 0 else 0
        valid_total_num = 1 - count_valid_total_num * 1.0 / len(check_all_total_validity) if len(check_all_total_validity) > 0 else 0

        if valid_apy_percentage < 0.7 or valid_total_num < 0.7:
            return False
    return True


def get_heco_hfi_data():
    driver = create_browser(network_needed='heco', b_id=5)
    try:
        driver.get(HFI_URL)

        main_window_handle = driver.current_window_handle

        try:
            connect_metamask_v2(driver)
        except Exception as e:
            print("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'coin-category')]")))

        for rep in range(10):
            coin_categories = driver.find_elements(By.XPATH, "//div[contains(@class, 'coin-category')]")
            coin_lists = driver.find_elements(By.XPATH, "//div[contains(@class, 'coin-list')]")
            res = {}

            for i in range(min(len(coin_categories), len(coin_lists))):
                try:
                    coin_category = coin_categories[i]
                    coin_list = coin_lists[i]

                    title = str.splitlines(coin_category.text)[0]

                    coin_boxs = coin_list.find_elements(By.CLASS_NAME, "coin-box")
                    for coin_box in coin_boxs:
                        coin_info = coin_box.find_elements(By.CSS_SELECTOR, ".flex-all")
                        name = coin_info[0].text.replace('\n', ' ')
                        apy = str.splitlines(coin_info[1].text)[1]
                        total = str.splitlines(coin_info[2].text)[1]
                        res.setdefault(title, []).append(
                            {
                                'name': name,
                                'APY': apy,
                                'total': total
                            }
                        )
                except Exception as e:
                    print("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    logger.error("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            if is_valid_hfi_data(res):
                break
            else:
                time.sleep(1)
                continue
        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"__layout\"]/div/div/div[1]/div[2]/div/p[1]/span[2]").text
        except Exception as e:
            tvl = None
            print("get_heco_hfi_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_hfi_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': {},
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_eth_curve_data():
    driver = create_browser(b_id=13)
    try:
        try:
            driver.get(CURVE_TVL_URL)
            # click close choose wallet button
            WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/aside/section/div[2]"))).click()

            # find the tvl place
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"total-balances\"]/span")))
            tvl = driver.find_element(By.XPATH, "//*[@id=\"total-balances\"]/span").text

            for i in range(10):
                if not tvl:
                    time.sleep(1)
                    tvl = driver.find_element(By.XPATH, "//*[@id=\"total-balances\"]/span").text
                else:
                    break
        except Exception as e:
            print("get_eth_curve_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_eth_curve_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            tvl = None
        resp = json.loads(requests.get(CURVE_API_URL).content)
        all_listed_pools = resp.get('apy', {}).get('day', {}).keys()
        res = []
        for pool in all_listed_pools:
            # skip pool
            if pool == 'compound':
                continue

            try:
                apy = resp.get('apy', {}).get('day', {}).get(pool)
                volume = resp.get('volume', {}).get(pool, 0)
                res.append(
                    {
                        'pool': pool,
                        'APY': "{:.2%}".format(apy),
                        'raw_volume': volume,
                        'formatted_volume': "${}".format(human_format(volume))
                    }
                )
            except Exception as e:
                print("get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)
        
def get_eth_yfi_data():
    try:
        resp = json.loads(requests.get(YFI_API_URL).content)
        v1_res = []
        v2_res = []
        tvl = 0
        for asset_info in resp:
            try:
                display_name = asset_info.get('displayName')
                version = asset_info.get('type')
                growth = asset_info.get('apy', {}).get('recommended', 'N/A')
                total_assets = asset_info.get('tvl', {}).get('value', 'N/A')
                tvl += float(total_assets) if total_assets != 'N/A' else 0
                if version == 'v1':
                    v1_res.append(
                        {
                            'asset': display_name,
                            'version': version,
                            'growth': "{:.2%}".format(growth),
                            'total_assets': "${:,.2f}".format(float(total_assets)) if total_assets != 'N/A' else total_assets
                        }
                    )
                if version == 'v2':
                    v2_res.append(
                        {
                            'asset': display_name,
                            'version': version,
                            'growth': "{:.2%}".format(growth),
                            'total_assets': "${:,.2f}".format(float(total_assets)) if total_assets != 'N/A' else total_assets
                        }
                    )
            except Exception as e:
                print("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return {
            'data': {
                'v1_assets': v1_res,
                'v2_assets': v2_res
            },
            'tvl': "${:,.2f}".format(tvl)
        }
    except Exception as e:
        print("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': {},
            'tvl': None
        }


def get_eth_vesper_data():
    try:
        resp = json.loads(requests.get(VESPER_API_URL).content)
        res = []
        tvl = 0

        for pool in resp:
            try:
                # There is a bug in the response of the API for "vWBTC", below is a temporary walk around
                pool_deposits_D = float(pool.get('totalValue', 0)) / (10**int(pool.get('asset', {}).get('decimals', 1)))
                symbol = pool.get('asset', {}).get('symbol')
                price = pool.get('asset', {}).get('price', 1)
                pool_deposits_U = pool_deposits_D * price
                tvl += pool_deposits_U
                pool_info = {
                    'name': pool.get('name'),
                    'spot': "{}%".format(pool.get('earningRates', {}).get('1')),
                    'avg': "{}%".format(pool.get('earningRates', {}).get('30')),
                    'vsp_delta_spot': "{}%".format(pool.get('vspDeltaRates', {}).get('1')),
                    'vsp_delta_avg': "{}%".format(pool.get('vspDeltaRates', {}).get('30')),
                    'pool_deposits_U': "${:,}".format(int(pool_deposits_U)),
                    'pool_deposits_D': "{:,} {}".format(round(pool_deposits_D, 4), symbol)
                }
                if pool_info.get('vsp_delta_spot') == 0:
                    pool_info['printed_spot'] = pool_info.get('spot')
                else:
                    pool_info['printed_spot'] = "{}%"\
                        .format(round(pool.get('earningRates', {}).get('1') + pool.get('vspDeltaRates', {}).get('1'), 2))

                if pool_info.get('vsp_delta_avg') == 0:
                    pool_info['printed_avg'] = pool_info.get('avg')
                else:
                    pool_info['printed_avg'] = "{}%" \
                        .format(round(pool.get('earningRates', {}).get('30') + pool.get('vspDeltaRates', {}).get('30'), 2))
            except Exception as e:
                print("get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            res.append(pool_info)
        return {
            'data': res,
            'tvl': "${:,}".format(int(tvl))
        }
    except Exception as e:
        print("get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }


def get_eth_sushi_data():
    driver = create_browser(b_id=6)
    try:
        driver.get(SUSHI_URL)
        main_window_handle = driver.current_window_handle

        # while open the sushi url (loads slowly), we go to sushi tvl site to get tvl
        try:
            driver.execute_script("window.open('https://app.sushi.com/home', 'new_window')")

            # be sure to change the focus
            for handle in driver.window_handles:
                if driver.current_url != 'https://app.sushi.com/home':
                    driver.switch_to.window(handle)
                else:
                    break

            WebDriverWait(driver, 40).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"tooltip-idBAR\"]/div")))
            _tvl = driver.find_element(By.XPATH, "//*[@id=\"tooltip-idBAR\"]/div").text
            _useless_percentage = driver.find_element(By.XPATH, "//*[@id=\"tooltip-idBAR\"]/div/span").text
            try:
                tvl = _tvl[:_tvl.index(_useless_percentage)]
            except Exception as e:
                tvl = _tvl
        except Exception as e:
            tvl = None
            print("get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.TAG_NAME, "tbody")))

        table = driver.find_element(By.TAG_NAME, "tbody")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # in case that the table is not loaded yet
        for i in range(10):
            print(i)
            if len(rows) < 12 or not rows:
                time.sleep(1)
                table = driver.find_element(By.TAG_NAME, "tbody")
                rows = table.find_elements(By.TAG_NAME, "tr")
            else:
                break

        res = []
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                pair = str.splitlines(cols[0].text)[1]
                roi = str.splitlines(cols[2].text)
                liquidity = str.splitlines(cols[3].text)
                res.append(
                    {
                        'pair': pair,
                        'roi_year': "{} (1y)".format(roi[0]),
                        'roi_month': "{} (1m)".format(roi[2]),
                        'roi_day': "{} (1d)".format(roi[4]),
                        'liquidity_u': liquidity[0],
                        'liquidity_m': liquidity[1],
                        'liquidity_d': liquidity[2]
                    }
                )
            except Exception as e:
                print("get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': {},
            'tvl': None
        }
    finally:
        kill_chrome(driver)

# TODO: wait till Ziyue figure out how to handle APY
def get_eth_uniswap_data():
    pass


def get_sc_pancakeswap_data():
    driver = create_browser(b_id=7)
    try:
        driver.get(PANCAKESWAP_URL)

        main_window_handle = driver.current_window_handle

        # while waiting for the resp of main url, we try to fetch the tvl first
        try:
            driver.execute_script("window.open('https://pancakeswap.finance/', 'new_window')")

            # be sure to change the focus
            for handle in driver.window_handles:
                if driver.current_url != 'https://pancakeswap.finance/':
                    driver.switch_to.window(handle)
                else:
                    break

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div[1]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/h2[2]")))
            tvl = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div[1]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/h2[2]").text
        except Exception as e:
            tvl = None
            print("get_sc_pancakeswap_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_pancakeswap_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.TAG_NAME, "tbody")))

        # in case that the table is not loaded yet
        for i in range(10):
            print(i)
            need_repeat_loop = True
            table = driver.find_element(By.TAG_NAME, "tbody")
            rows = table.find_elements(By.TAG_NAME, "tr")

            if len(rows) < 50 or not rows:
                continue
            res = []
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    apr = str.splitlines(cols[2].text)[1]
                    if apr == 'Loading...':
                        apr = '0.00%'
                    res.append(
                        {
                            'pair': cols[0].text,
                            'apr': apr,
                            'liquidity': str.splitlines(cols[3].text)[1],
                            'multiplier': str.splitlines(cols[4].text)[1]
                        }
                    )
                    need_repeat_loop = False
                except Exception as e:
                    print("get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    logger.error(
                        "get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    continue
            if not need_repeat_loop:
                break
            else:
                time.sleep(1)

        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_sc_autofarm_data():
    try:
        resp = json.loads(requests.get(AUTOFARM_API_URL).content)
        pools = resp.get('pools', {})
        res = []
        tvl = 0
        for row in resp.get('table_data', {}):
            try:
                token_id = row[0]
                token_pool = pools.get(str(token_id), {})
                daily_apr = round(token_pool.get('APR', 0) / 365.0 * 100, 2)
                tvl += row[4]
                res.append(
                    {
                        'token': row[2],
                        'TVL': "${}".format(human_format(row[4])),
                        'APY': row[5] + "%",
                        'daily_apr': str(daily_apr) + "%"
                    }
                )
            except Exception as e:
                print("get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': '${:,}'.format(int(tvl))
        }
    except Exception as e:
        print("get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }


def is_valid_sc_ellipsis_data(res):
    return (res.get('pool', [{}])[0].get('rewards_apy') != '' and res.get('pool', [{}])[0].get('base_apy') != '%' and res.get('pool', [{}])[0].get('volume') != '') \
                    and (res.get('EPS/BNB_staking_apy') != '0' and res.get('3pool_lp_token_apy') != '0' and res.get('fUSDT_lp_token_apy') != '0') \
                    and (res.get('EPS_unlocked_apy') != '0% in BUSD\nLocked APY' and res.get('EPS_locked_apy') != '0% in EPS + 0% in BUSD')


def get_sc_ellipsis_data():
    try:
        driver = create_browser(network_needed='sc', b_id=8)
        driver.get(ELLIPSIS_URL)
        main_window_handle = driver.current_window_handle

        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"WEB3_CONNECT_MODAL_ID\"]/div/div/div[2]/div[1]/div"))).click()
            connect_metamask_v2(driver)
        except TimeoutError as e:
            try:
                driver.get(ELLIPSIS_URL)
                main_window_handle = driver.current_window_handle
                WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                    (By.XPATH, "//*[@id=\"WEB3_CONNECT_MODAL_ID\"]/div/div/div[2]/div[1]/div"))).click()
                connect_metamask_v2(driver)
            except Exception as e:
                print("get_sc_ellipsis_data request web timeout:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_sc_ellipsis_data request web timeout:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        except Exception as e:
            print("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        # max retry times: 10
        for i in range(10):
            print(i)
            res = {}
            tables = driver.find_elements(By.TAG_NAME, 'fieldset')
            for table in tables:
                legend_names = table.find_elements(By.TAG_NAME, 'legend')
                for legend_name in legend_names:
                    if str.strip(legend_name.text) == 'Ellipsis pools':
                            info_tables = table.find_element(By.TAG_NAME, "table").find_elements(By.XPATH, "./a[*]")
                            for info_table in info_tables:
                                try:
                                    table_cols = info_table.find_elements(By.TAG_NAME, 'td')
                                    res.setdefault('pool', []).append(
                                        {
                                            'asset': str.splitlines(table_cols[0].text)[1],
                                            'base_apy': table_cols[1].text,
                                            'rewards_apy': table_cols[2].text,
                                            'volume': table_cols[3].text
                                        }
                                    )
                                except Exception as e:
                                    res.setdefault('pool', []).append(
                                        {
                                            'asset': 'N/A',
                                            'base_apy': 'N/A',
                                            'rewards_apy': 'N/A',
                                            'volume': 'N/A',
                                        }
                                    )

                    if str.strip(legend_name.text) == 'Stake LP Tokens':
                        try:
                            info = table.find_elements(By.TAG_NAME, 'div')
                            res['EPS/BNB_staking_apy'] = str.strip(info[0].text.split(':')[1])
                            res['3pool_lp_token_apy'] = str.strip(info[2].text.split(':')[1])
                            res['fUSDT_lp_token_apy'] = str.strip(info[4].text.split(':')[1])
                        except Exception as e:
                            res['EPS/BNB_staking_apy'] = 'N/A'
                            res['3pool_lp_token_apy'] = 'N/A'
                            res['fUSDT_lp_token_apy'] = 'N/A'

                    if str.strip(legend_name.text) == 'Stake EPS':
                        try:
                            info = table.find_elements(By.TAG_NAME, 'div')
                            res['EPS_unlocked_apy'] = str.strip(info[1].text.split(':')[1])
                            res['EPS_locked_apy'] = str.strip(info[2].text.split(':')[1])
                        except Exception as e:
                            res['EPS_unlocked_apy'] = 'N/A'
                            res['EPS_locked_apy'] = 'N/A'

            # if invalid output, we try to get the data again

            if not is_valid_sc_ellipsis_data(res):
                time.sleep(1.5)
            else:
                break
        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"total-balances\"]/span").text
        except Exception as e:
            tvl = None
            print("get_sc_ellipsis_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_ellipsis_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl,
        }
    except Exception as e:
        print("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': {},
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_sc_pancakebunny_data():
    driver = create_browser(network_needed='sc', b_id=9)
    try:
        driver.get(PANCAKEBUNNY_URL)
        time.sleep(1)

        main_window_handle = driver.current_window_handle

        try:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                (By.CLASS_NAME, "placeholders-card"))).click()

            WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div[6]/div[2]/div/div/div[3]/div[1]"))).click()

            connect_metamask_v2(driver)
        except Exception as e:
            print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        res = []

        # max retry time: 20
        for i in range(20):
            print(i)
            if not res:
                res = []
                time.sleep(1)
                rows = copy(driver.find_elements(By.CLASS_NAME, "row"))
                for row in rows:
                    try:
                        label = row.find_element(By.CLASS_NAME, "label")
                        rates = str.splitlines(row.find_element(By.CLASS_NAME, "rates").text)
                        detail_return = row.find_element(By.CSS_SELECTOR, ".details.return")
                        detail_balance = row.find_element(By.CSS_SELECTOR, ".details.balance")
                        detail_total = row.find_element(By.CSS_SELECTOR, ".details.total")

                        _row = {
                            'asset': label.text.replace('\n', ' '),
                            'apy': rates[0],
                            'earn': str.splitlines(detail_return.text)[1],
                            'balance': str.splitlines(detail_balance.text)[1],
                            'total_deposit': str.splitlines(detail_total.text)[1]
                        }

                        if len(rates) > 2:
                            _row['apr'] = str.split(rates[1], ' ')[1]
                        res.append(_row)
                    except Exception as e:
                        print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                        logger.error(
                            "get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            else:
                break

        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div[3]/div[1]/div[1]/div/div/div/div[1]/div[1]/span[1]").text
        except Exception as e:
            print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            tvl = None
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_sc_belt_data():
    driver = create_browser(network_needed='sc', b_id=10)
    try:
        driver.get(BELT_URL)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id=\"router-wrapper\"]/div[2]/div[4]")))

        table = driver.find_element(By.CSS_SELECTOR, '.belt-pools')
        rows = table.find_elements(By.TAG_NAME, 'li')

        for _ in range(10):
            while not rows:
                time.sleep(2)
                table = driver.find_element(By.CSS_SELECTOR, '.belt-pools')
                rows = table.find_elements(By.TAG_NAME, 'li')

        res = []
        for row in rows:
            try:
                name = str.splitlines(row.find_element(By.CLASS_NAME, 'name').text)[2]
                tvl = str.splitlines(row.find_element(By.CLASS_NAME, 'tvl').text)[1]
                volume = str.splitlines(row.find_element(By.CLASS_NAME, 'volume').text)[1]
                apr = str.splitlines(row.find_element(By.CLASS_NAME, 'apr').text)[1]
                apy = str.splitlines(row.find_element(By.CLASS_NAME, 'apy').text)[1]
                if tvl != '-' and volume != '-' and apr != '-' and apy != '-':
                    res.append(
                        {
                            'name': name,
                            'tvl': tvl,
                            'volume': volume,
                            'apr': apr,
                            'apy': apy
                        }
                    )
            except Exception as e:
                print("get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue

        try:
            tvl = driver.find_element(By.XPATH, "//*[@id=\"router-wrapper\"]/div[2]/div[2]/div[2]/span[2]").text
        except Exception as e:
            tvl = None
            print("get_sc_belt_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_belt_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def convert_valid_aplaca_data(apy):
    try:
        split_list = apy.split('%')
        str_num = split_list[0]
        if str_num.endswith('k'):
            str_num = float(str_num[:-1]) * 1000
        return '{}%'.format(str(str_num))
    except Exception as e:
        return apy


def get_sc_aplaca_data():
    driver = create_browser(network_needed='sc', b_id=11)
    try:
        driver.get(ALPACAFINANCE_URL)
        # click 'connect to a wallet' button
        try:
            main_window_handle = driver.current_window_handle

            WebDriverWait(driver, 29).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div/section/section/header/div[1]/div[3]/span[1]/button"))).click()

            WebDriverWait(driver, 31).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[3]/div/div[2]/div/div[2]/div[2]/div/button"))).click()

            connect_metamask_v2(driver)
        except TimeoutException as e:
            pass
        except Exception as e:
            print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        for i in range(10):
            need_repeat_loop = True
            connection_status = driver.find_element(By.XPATH, '//*[@id=\"root\"]/div/section/section/header/div[1]/div[3]/span[1]/button').text
            table = driver.find_element(By.TAG_NAME, 'tbody')
            rows = table.find_elements(By.TAG_NAME, 'tr')
            rows = copy(rows)
            res = []
            for row in rows:
                if not row.text:
                    continue
                cols = row.find_elements(By.TAG_NAME, 'td')
                try:
                    name = str.splitlines(cols[1].text)[1]
                    apy_u = convert_valid_aplaca_data(str.splitlines(cols[2].text)[0])
                    apy_d = convert_valid_aplaca_data(str.splitlines(cols[2].text)[1])
                    yield_farming = str.splitlines(cols[3].text)[1]
                    trading_fees = str.splitlines(cols[3].text)[3]
                    alpaca_rewards = str.splitlines(cols[3].text)[5]
                    borrowing_interest = str.splitlines(cols[3].text)[7]
                    leverage = str.splitlines(cols[4].text)[0]
                    res.append(
                        {
                            'name': name,
                            'apy_u': apy_u,
                            'apy_d': apy_d,
                            'yield_farming': yield_farming,
                            'trading_fees': trading_fees,
                            'alpaca_rewards': alpaca_rewards,
                            'borrowing_interest': borrowing_interest,
                            'leverage': leverage
                        }
                    )
                    need_repeat_loop = False
                # if the data is not ready, we retry
                except IndexError as e:
                    time.sleep(2)
                    need_repeat_loop = True
                    break
                except Exception as e:
                    print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    logger.error(
                        "get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    continue
            if not need_repeat_loop:
                break

        try:
            driver.get(ALPACAFINANCE_TVL_URL)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div/section/section/section/main/div[1]/div[1]/div[2]/div/div[2]/div/div/div/div[2]/div/div/span"))).click()
            tvl = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div/section/section/section/main/div[1]/div[1]/div[2]/div/div[2]/div/div/div/div[2]/div/div/span").text
        except Exception as e:
            tvl = None
            print("get_sc_aplaca_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_aplaca_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)
        

def get_sc_bake_data():
    driver = create_browser(network_needed='sc', b_id=12)
    try:
        driver.get(BAKE_URL)

        try:
            main_window_handle = driver.current_window_handle

            WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div/div[2]/div[4]/button"))).click()

            WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"connect-METAMASK\"]"))).click()

            connect_metamask_v2(driver)
        except TimeoutException as e:
            pass
        except Exception as e:
            print("get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)

        for i in range(10):
            table = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div/div[2]/div[5]")
            rows = copy(table.find_elements(By.XPATH, "./div[*]"))
            res = []
            for row in rows:
                try:
                    cols = row.find_elements(By.XPATH, "./div[*]")
                    asset = cols[2].text
                    deposit = str.splitlines(cols[3].text)[1]
                    earn = str.splitlines(cols[4].text)[1]
                    roi = str.splitlines(cols[5].text)[1]
                    res.append(
                        {
                            'asset': asset,
                            'deposit': deposit,
                            'earn': earn,
                            'roi': roi
                        }
                    )
                except Exception as e:
                    print("get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    logger.error(
                        "get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                    continue

            if all([row.get('roi') != 'Loading ...' for row in res]):
                break
            else:
                time.sleep(1)
                continue

        driver.get(BAKE_TVL_URL)
        for i in range(10):
            try:
                tvl = driver.find_element(By.XPATH, "//*[@id=\"root\"]/div/div[2]/div[4]/div/div[1]/div[2]/div[3]/div[2]/div/span").text
                if tvl == '0.000':
                    time.sleep(1)
                    continue
                else:
                    break
            except Exception as e:
                tvl = None
                print("get_sc_bake_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_bake_data tvl error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': res,
            'tvl': tvl
        }
    except Exception as e:
        print("get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {
            'data': [],
            'tvl': None
        }
    finally:
        kill_chrome(driver)


def get_task_needed(return_values):
    task_needed = []
    for i, row in enumerate(return_values):
        if not row or not row.get('data') or not row.get('tvl'):
            task_needed.append(i)
    # __import__('pudb').set_trace()
    return task_needed


def get_data_concurrently(task_list):
    return_values = run_in_threads(task_list)

    # task_needed = get_task_needed(return_values)
    # while task_needed:
        # new_task_list = [task_list[task_index] for task_index in task_needed]
        # new_return_values = run_in_threads(new_task_list)
        # for task_index in task_needed:
            # return_values[task_index] = new_return_values[task_needed.index(task_index)]
        # task_needed = get_task_needed(return_values)

    return return_values


def get_data():
    TASK_LIST = [
        (get_sc_aplaca_data, ()),
        (get_sc_pancakeswap_data, ()),
        (get_eth_sushi_data, ()),
        (get_eth_curve_data, ()),
        (get_sc_bake_data, ()),
        (get_sc_pancakebunny_data, ()),
        (get_heco_filda_data, ()),
        (get_heco_coinwind_data, ()),
        (get_heco_hfi_data, ()),
        (get_heco_lendhub_data, ()),
        (get_sc_ellipsis_data, ()),
        (get_heco_mdex_data, ()),
        (get_sc_belt_data, ()),
        (get_eth_yfi_data, ()),
        (get_eth_vesper_data, ()),
        (get_sc_venus_data, ()),
        (get_sc_autofarm_data, ())
    ]

    start_time = time.time()

    res = get_data_concurrently(TASK_LIST)
    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    print('START WRITING EXCEL...')
    write_excel(res)
    print("--- %s seconds ---" % (time.time() - start_time))

def get_data_serially():
    res = {}

    res[1] = get_heco_mdex_data() # Done; Browser NEEDED; 15s
    res[2] = get_heco_filda_data()  # Done; METAMASK NEEDED; 16s
    res[3] = get_heco_coinwind_data() # Done; METAMASK NEEDED # 13s
    res[4] = get_heco_lendhub_data() # Done; METAMASK NEEDED # 18s
    res[5] = get_heco_hfi_data() # Done; METAMASK NEEDED; 15s
    res[6] = get_eth_curve_data() # Done; Browser Needed and Fast API access; # 15s
    res[7] = get_eth_yfi_data() # Done; Fast API access;
    res[8] = get_eth_vesper_data() # Done; Fast API access
    res[9] = get_eth_sushi_data() # Done; Browser NEEDED; No METAMASK NEEDED; # 30s
    res[11] = get_sc_pancakeswap_data() # Done; Browser NEEDED; No METAMASK NEEDED; # 23s
    res[12] = get_sc_venus_data() # Done; Fast API access
    res[13] = get_sc_autofarm_data() # Done; Fast API access
    res[14] = get_sc_ellipsis_data() # Done; METAMASK NEEDED; AA VPN CANNOT WORKING? # 34s -> 20s
    res[15] = get_sc_pancakebunny_data() # Done; METAMASK NEEDED # 29s -> 17s
    res[16] = get_sc_belt_data() # Done; Browser NEEDED; 18s -> 12s
    res[17] = get_sc_aplaca_data() # Done; METAMASK NEEDED; 34s -> 24s
    res[18] = get_sc_bake_data() # Done; METAMASK NEEDED; 37s -> 18s


def test_joblib():
    start_time = time.time()
    job_list = [
        get_sc_aplaca_data,
        get_sc_pancakeswap_data,
        get_eth_sushi_data,
        get_eth_curve_data,
        get_sc_bake_data,
        get_sc_pancakebunny_data,
        get_heco_filda_data,
        get_heco_coinwind_data,
        get_heco_hfi_data,
        get_heco_lendhub_data,
        get_sc_ellipsis_data,
        get_heco_mdex_data,
        get_sc_belt_data,
        get_eth_yfi_data,
        get_eth_vesper_data,
        get_sc_venus_data,
        get_sc_autofarm_data
    ]
    res = Parallel(n_jobs=-1, prefer="threads")(delayed(job)() for job in job_list)
    print("--- %s seconds ---" % (time.time() - start_time))
    start_time = time.time()
    print('START WRITING EXCEL...')
    write_excel(res)
    print("--- %s seconds ---" % (time.time() - start_time))


def generate_ellipsis_data():
    res = get_sc_ellipsis_data()
    write_ellipsis_excel(res)


def generate_aplaca_data():
    res = get_sc_aplaca_data()
    write_aplaca_excel(res)


if __name__ == '__main__':
    # get_heco_mdex_data()
    # test_joblib()
    # generate_ellipsis_data()
    # generate_aplaca_data()
    # get_data_serially()
    get_data()
    # get_data_concurrently()

    res = {}

    # res[1] = get_heco_mdex_data()  # Done; Browser NEEDED; 15s
    # res[2] = get_heco_filda_data()  # Done; METAMASK NEEDED; 16s
    # res[3] = get_heco_coinwind_data()  # Done; METAMASK NEEDED # 13s
    # res[4] = get_heco_lendhub_data()  # Done; METAMASK NEEDED # 18s
    # res[5] = get_heco_hfi_data()  # Done; METAMASK NEEDED; 15s
    # res[6] = get_eth_curve_data()  # Done; Browser Needed and Fast API access; # 15s
    # res[7] = get_eth_yfi_data()  # Done; Fast API access;
    # res[8] = get_eth_vesper_data()  # Done; Fast API access
    # res[9] = get_eth_sushi_data()  # Done; Browser NEEDED; No METAMASK NEEDED; # 30s
    # res[11] = get_sc_pancakeswap_data()  # Done; Browser NEEDED; No METAMASK NEEDED; # 23s
    # res[12] = get_sc_venus_data()  # Done; Fast API access
    # res[13] = get_sc_autofarm_data()  # Done; Fast API access
    # res[14] = get_sc_ellipsis_data()  # Done; METAMASK NEEDED; AA VPN CANNOT WORKING? # 34s -> 20s
    # res[15] = get_sc_pancakebunny_data()  # Done; METAMASK NEEDED # 29s -> 17s
    # res[16] = get_sc_belt_data()  # Done; Browser NEEDED; 18s -> 12s
    # res[17] = get_sc_aplaca_data()  # Done; METAMASK NEEDED; 34s -> 24s
    # res[18] = get_sc_bake_data()  # Done; METAMASK NEEDED; 37s -> 18s
    
    print(res)
