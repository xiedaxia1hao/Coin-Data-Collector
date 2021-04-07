import time
from copy import copy
from constants import MDEX_URL, VENUS_API_URL, COINWIND_URL, FILDA_URL, LENDHUB_URL, HFI_URL, CURVE_API_URL, \
    YFI_API_URL, VESPER_API_URL, SUSHI_URL, PANCAKESWAP_URL, AUTOFARM_API_URL, ELLIPSIS_URL, PANCAKEBUNNY_URL, BELT_URL, \
    ALPACAFINANCE_URL, BAKE_URL
from utils import create_browser, run_in_threads, human_format
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import json
import traceback
import logging
logger = logging.getLogger(__name__)


def is_valid_mdex_row(items):
    return len(items) >= 6


# Browser Needed
def get_heco_mdex_data():
    try:
        driver = create_browser(b_id=1)
        driver.get(MDEX_URL)
        wait = WebDriverWait(driver, 10)
        table = \
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"app\"]/section/div[2]/div[2]/div/div[3]/table")))
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
                print("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return res
    except Exception as e:
        print("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_mdex_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_venus_data():
    try:
        resp = json.loads(requests.get(VENUS_API_URL).content)
        res = []
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
            except Exception as e:
                print("get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return res
    except Exception as e:
        print("get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_venus_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []


def get_heco_coinwind_data():
    try:
        driver = create_browser(network_needed='heco', b_id=3)
        driver.get(COINWIND_URL)

        main_window_handle = driver.current_window_handle

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"WEB3_CONNECT_MODAL_ID\"]/div/div/div[2]/div[1]/div"))).click()
            connect_metamask_v2(driver)
        except Exception as e:
            print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        # Switch back to main tab
        driver.switch_to.window(main_window_handle)
        time.sleep(5)
        rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiGrid-root MuiGrid-container MuiGrid-item MuiGrid-grid-xs-12')]")
        rows = copy(rows)
        res = []
        for i, row in enumerate(rows):
            try:
                # Sample row.text:
                # 'MDX\nStore MDX MDX\n0.0000\nEarned (MDX)\n108.34%\nAPY(Compound Interest)\n\n\n\n28,705,423.78\nVL (MDX)'
                items = str.splitlines(row.text)
                cols = row.find_elements(By.XPATH, "//div[contains(@class, 'MuiGrid-root MuiGrid-container MuiGrid-item MuiGrid-align-items-xs-center')]")
                earned_mdx = str.splitlines(cols[3*i].text)[0]
                apy = str.splitlines(cols[3*i+1].text)[0]
                vl_value = str.splitlines(cols[3*i+2].text)[0]
                vl_name = str.splitlines(cols[3*i+2].text)[1]
                res.append(
                    {
                        'Assets U': items[0],
                        'Assets D': items[1],
                        'Earned (MDX)': earned_mdx,
                        'APY (Compound Interest)': apy,
                        vl_name: vl_value
                    }
                )
            except Exception as e:
                print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return res
    except Exception as e:
        print("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_coinwind_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_heco_filda_data():
    try:
        driver = create_browser(network_needed='heco', b_id=2)
        driver.get(FILDA_URL)

        main_window_handle = driver.current_window_handle

        try:
            # connect the wallet
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div[1]/div[2]/div[2]/button"))).click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[3]/div/div/div[2]/div/div/div/button"))).click()

            connect_metamask_v2(driver)
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
        return res
    except Exception as e:
        print("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_filda_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def connect_metamask_v2(driver):

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
    try:
        driver = create_browser(network_needed='heco', b_id=4)
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

        time.sleep(2.5)

        lp_market_res = []
        single_market_res = []

        while not (lp_market_res and single_market_res):
            lp_market_res = []
            single_market_res = []

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
        return {
            "lp_market_res": lp_market_res,
            "single_market_res": single_market_res
        }
    except Exception as e:
        print("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                            traceback.format_exc()))
        logger.error("get_heco_lendhub_data error:{}.{}.{}".format(e.__class__.__name__, e,
                                                                   traceback.format_exc()))
        return {}
    finally:
        driver.close()


def get_heco_hfi_data():
    try:
        driver = create_browser(network_needed='heco', b_id=5)
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

        return res
    except Exception as e:
        print("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_heco_hfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {}
    finally:
        driver.close()


def get_eth_curve_data():
    try:
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
        return res
    except Exception as e:
        print("get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_curve_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []


def get_eth_yfi_data():
    try:
        resp = json.loads(requests.get(YFI_API_URL).content)
        v1_res = []
        v2_res = []
        for asset_info in resp:
            try:
                display_name = asset_info.get('displayName')
                version = asset_info.get('type')
                growth = asset_info.get('apy', {}).get('recommended', 'N/A')
                total_assets = asset_info.get('tvl', {}).get('value', 'N/A')
                if version == 'v1':
                    v1_res.append(
                        {
                            'asset': display_name,
                            'version': version,
                            'growth': "{:.2%}".format(growth),
                            'total_assets': "${:,}".format(float(total_assets)) if total_assets != 'N/A' else total_assets
                        }
                    )
                if version == 'v2':
                    v2_res.append(
                        {
                            'asset': display_name,
                            'version': version,
                            'growth': "{:.2%}".format(growth),
                            'total_assets': "${:,}".format(float(total_assets)) if total_assets != 'N/A' else total_assets
                        }
                    )
            except Exception as e:
                print("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return {
            'v1_assets': v1_res,
            'v2_assets': v2_res
        }
    except Exception as e:
        print("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_eth_yfi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {}


def get_eth_vesper_data():
    try:
        resp = json.loads(requests.get(VESPER_API_URL).content)
        res = []

        for pool in resp:
            try:
                # There is a bug in the response of the API for "vWBTC", below is a temporary walk around
                pool_deposits_D = float(pool.get('totalValue', 0)) / (10**int(pool.get('asset', {}).get('decimals', 1)))
                symbol = pool.get('asset', {}).get('symbol')
                price = pool.get('asset', {}).get('price', 1)
                pool_deposits_U = pool_deposits_D * price
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
        return res
    except Exception as e:
        print("get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_vesper_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []


def get_eth_sushi_data():
    try:
        driver = create_browser(b_id=6)
        driver.get(SUSHI_URL)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.TAG_NAME, "tbody")))

        time.sleep(2.5)
        table = driver.find_element(By.TAG_NAME, "tbody")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # in case that the table is not loaded yet
        while len(rows) < 12 or not rows:
            time.sleep(1)
            table = driver.find_element(By.TAG_NAME, "tbody")
            rows = table.find_elements(By.TAG_NAME, "tr")

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
        return res
    except Exception as e:
        print("get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_eth_sushi_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {}
    finally:
        driver.close()


# TODO: wait till Ziyue figure out how to handle APY
def get_eth_uniswap_data():
    pass


def get_sc_pancakeswap_data():
    try:
        driver = create_browser(b_id=7)
        driver.get(PANCAKESWAP_URL)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.TAG_NAME, "tbody")))

        time.sleep(3)
        table = driver.find_element(By.TAG_NAME, "tbody")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # in case that the table is not loaded yet
        while len(rows) < 50 or not rows:
            time.sleep(1)
            table = driver.find_element(By.TAG_NAME, "tbody")
            rows = table.find_elements(By.TAG_NAME, "tr")

        res = []
        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                res.append(
                    {
                        'pair': cols[0].text,
                        'apr': str.splitlines(cols[2].text)[1],
                        'liquidity': str.splitlines(cols[3].text)[1],
                        'multiplier': str.splitlines(cols[4].text)[1]
                    }
                )
            except Exception as e:
                print("get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return res
    except Exception as e:
        print("get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_pancakeswap_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_autofarm_data():
    try:
        resp = json.loads(requests.get(AUTOFARM_API_URL).content)
        pools = resp.get('pools', {})
        res = []
        for row in resp.get('table_data', {}):
            try:
                token_id = row[0]
                token_pool = pools.get(str(token_id), {})
                daily_apr = round(token_pool.get('APR', 0) / 365.0 * 100, 2)
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
        return res
    except Exception as e:
        print("get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_autofarm_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []


def is_valid_sc_ellipsis_data(res):
    return (res.get('pool', {}).get('rewards_apy') == '' and res.get('pool', {}).get('base_apy' == '%') and res.get('pool', {}).get('volume') == '') \
                    or (res.get('EPS/BNB_staking_apy') == '0' and res.get('3pool_lp_token_apy') == '0') \
                    or (res.get('EPS_unlocked_apy') == '0% in BUSD\nLocked APY' and res.get('EPS_locked_apy') == '0% in EPS + 0% in BUSD')


def get_sc_ellipsis_data():
    try:
        driver = create_browser(network_needed='sc', b_id=8)
        driver.get(ELLIPSIS_URL)
        main_window_handle = driver.current_window_handle
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"WEB3_CONNECT_MODAL_ID\"]/div/div/div[2]/div[1]/div"))).click()
            connect_metamask_v2(driver)
        except Exception as e:
            print("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)
        time.sleep(8)
        tables = driver.find_elements(By.TAG_NAME, 'fieldset')

        # max retry times: 10
        for i in range(10):
            res = {}
            for table in tables:
                legend_names = table.find_elements(By.TAG_NAME, 'legend')
                for legend_name in legend_names:
                    if str.strip(legend_name.text) == 'Ellipsis pools':
                        try:
                            info_table = table.find_element(By.TAG_NAME, 'table')
                            table_cols = info_table.find_elements(By.TAG_NAME, 'td')
                            res['pool'] = {
                                'asset': str.splitlines(table_cols[5].text)[1],
                                'base_apy': table_cols[6].text,
                                'rewards_apy': table_cols[7].text,
                                'volume': table_cols[8].text
                            }
                        except Exception as e:
                            res['pool'] = {
                                'asset': 'N/A',
                                'base_apy': 'N/A',
                                'rewards_apy': 'N/A',
                                'volume': 'N/A',
                            }

                    if str.strip(legend_name.text) == 'Stake LP Tokens':
                        try:
                            info = table.find_elements(By.TAG_NAME, 'div')
                            res['EPS/BNB_staking_apy'] = str.strip(info[0].text.split(':')[1])
                            res['3pool_lp_token_apy'] = str.strip(info[2].text.split(':')[1])
                        except Exception as e:
                            res['EPS/BNB_staking_apy'] = 'N/A'
                            res['3pool_lp_token_apy'] = 'N/A'

                    if str.strip(legend_name.text) == 'Stake EPS':
                        try:
                            info = table.find_elements(By.TAG_NAME, 'div')
                            res['EPS_unlocked_apy'] = str.strip(info[1].text.split(':')[1])
                            res['EPS_locked_apy'] = str.strip(info[2].text.split(':')[1])
                        except Exception as e:
                            res['EPS_unlocked_apy'] = 'N/A'
                            res['EPS_locked_apy'] = 'N/A'

            # if invalid output, we try to get the data again
            if is_valid_sc_ellipsis_data(res):
                time.sleep(3)
            else:
                break
        return res
    except Exception as e:
        print("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_ellipsis_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return {}
    finally:
        driver.close()


def get_sc_pancakebunny_data():
    try:
        driver = create_browser(network_needed='sc', b_id=9)
        driver.get(PANCAKEBUNNY_URL)
        time.sleep(2)

        try:
            main_window_handle = driver.current_window_handle

            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.CLASS_NAME, "placeholders-card"))).click()

            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div[6]/div[2]/div/div/div[3]/div[1]"))).click()

            connect_metamask_v2(driver)
        except Exception as e:
            print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)
        driver.refresh()

        time.sleep(6.66)

        res = []

        # max retry time: 20
        for i in range(20):
            if not res:
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
        return res
    except Exception as e:
        print("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_pancakebunny_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_belt_data():
    try:
        driver = create_browser(b_id=10)
        driver.get(BELT_URL)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id=\"router-wrapper\"]/div[2]/div[4]")))

        time.sleep(5)

        table = driver.find_element(By.CSS_SELECTOR, '.belt-pools')
        rows = table.find_elements(By.TAG_NAME, 'li')

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
        return res
    except Exception as e:
        print("get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_belt_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_aplaca_data():
    try:
        driver = create_browser(network_needed='sc', b_id=11)
        driver.get(ALPACAFINANCE_URL)

        # click 'connect to a wallet' button
        try:
            main_window_handle = driver.current_window_handle

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div/section/section/header/div[1]/div[3]/span[1]/button"))).click()

            time.sleep(1)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[3]/div/div[2]/div/div[2]/div[2]/div/button"))).click()

            connect_metamask_v2(driver)
        except Exception as e:
            print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))

        driver.switch_to.window(main_window_handle)
        time.sleep(8)


        table = driver.find_element(By.TAG_NAME, 'tbody')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        rows = copy(rows)

        res = []
        for row in rows:
            if not row.text:
                continue
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                name = str.splitlines(cols[1].text)[1]
                apy_u = str.splitlines(cols[2].text)[0]
                apy_d = str.splitlines(cols[2].text)[1]
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
            except Exception as e:
                print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                logger.error(
                    "get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
                continue
        return res
    except Exception as e:
        print("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error("get_sc_aplaca_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_bake_data():
    try:
        driver = create_browser(network_needed='sc', b_id=12)
        driver.get(BAKE_URL)

        try:
            main_window_handle = driver.current_window_handle

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"root\"]/div/div[2]/div[4]/button"))).click()

            time.sleep(1)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id=\"connect-METAMASK\"]"))).click()

            connect_metamask_v2(driver)
        except Exception as e:
            print("get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
            logger.error(
                "get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        driver.switch_to.window(main_window_handle)

        time.sleep(2)

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
        return res
    except Exception as e:
        print("get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        logger.error(
            "get_sc_bake_data error:{}.{}.{}".format(e.__class__.__name__, e, traceback.format_exc()))
        return []
    finally:
        driver.close()


def get_sc_smoothy_data(driver):
    pass


def get_data_concurrently():
    start_time = time.time()
    result = {}
    task_list = [
        (get_heco_mdex_data, ()),
        (get_heco_filda_data, ()),
        (get_heco_coinwind_data, ()),
        (get_heco_lendhub_data, ()),
        # (get_heco_hfi_data, ()), # FIX VPN
        (get_eth_curve_data, ()),
        (get_eth_yfi_data, ()),
        (get_eth_vesper_data, ()),
        (get_eth_sushi_data, ()),
        # (get_eth_uniswap_data, ()), # TODO
        (get_sc_pancakeswap_data, ()),
        (get_sc_venus_data, ()),
        (get_sc_autofarm_data, ()),
        # (get_sc_ellipsis_data, ()), # AA VPN CANNOT WORKING?
        (get_sc_pancakebunny_data, ()), # TODO: ????? WTF
        (get_sc_belt_data, ()),
        (get_sc_aplaca_data, ()),
        (get_sc_bake_data, ()) # TODO: ????? WTF
    ]
    return_values = run_in_threads(task_list)
    print("--- %s seconds ---" % (time.time() - start_time))
    __import__('pudb').set_trace()
    result['mdex_data'] = return_values[0]

    return return_values[0]


if __name__ == '__main__':
    # driver = create_browser(webdriver_path='./chromedriver', show_browser=True, network_needed='sc')
    start_time = time.time()
    res = {}
    # res[1] = get_heco_mdex_data() # Done; Browser NEEDED
    # res[2] = get_heco_filda_data()  # Done; METAMASK NEEDED
    # res[3] = get_heco_coinwind_data() # Done; METAMASK NEEDED
    # res[4] = get_heco_lendhub_data() # Done; METAMASK NEEDED
    #
    # # res[5] = get_heco_hfi_data() # Done; METAMASK NEEDED; AA VPN CANNOT WORKING?
    # res[6] = get_eth_curve_data() # Done; Fast API access
    # res[7] = get_eth_yfi_data() # Done; Fast API access
    # res[8] = get_eth_vesper_data() # Done; Fast API access
    # res[9] = get_eth_sushi_data() # Done; Browser NEEDED; No METAMASK NEEDED;
    # # res[10] = get_eth_uniswap_data() # TODO: wait till ziyue
    # res[11] = get_sc_pancakeswap_data() # Done; Browser NEEDED; No METAMASK NEEDED;
    # res[12] = get_sc_venus_data() # Done; Fast API access
    # res[13] = get_sc_autofarm_data() # Done; Fast API access
    # # res[14] = get_sc_ellipsis_data() # Done; METAMASK NEEDED; AA VPN CANNOT WORKING?
    # res[15] = get_sc_pancakebunny_data() # Done; METAMASK NEEDED; VPN NEEDED
    # res[16] = get_sc_belt_data() # Done; Browser NEEDED;
    # res[17] = get_sc_aplaca_data() # Done; METAMASK NEEDED
    # res[18] = get_sc_bake_data() # Done; METAMASK NEEDED
    # # res[19] = get_sc_smoothy_data(driver) # TODO: not yet

    # 5.5mins
    print("--- %s seconds ---" % (time.time() - start_time))

    get_data_concurrently()
    __import__('pudb').set_trace()


