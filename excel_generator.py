import xlwt

from tests.mocked_samples.aplaca_resp import APLACA_RESP
from tests.mocked_samples.autofarm_resp import AUTOFARM_RESP
from tests.mocked_samples.bake_resp import BAKE_RESP
from tests.mocked_samples.belt_resp import BELT_RESP
from tests.mocked_samples.coinwind_resp import COINWIND_RESP
from tests.mocked_samples.curve_resp import CURVE_RESP
from tests.mocked_samples.ellipsis_resp import ELLIPSIS_RESP
from tests.mocked_samples.filda_resp import FILDA_RESP
from tests.mocked_samples.hfi_resp import HFI_RESP
from tests.mocked_samples.lendhub_resp import LENDHUB_RESP
from tests.mocked_samples.mdex_resp import MDEX_RESP
from tests.mocked_samples.pancakebunny_resp import PANCAKEBUNNY_RESP
from tests.mocked_samples.sushi_resp import SUSHI_RESP
from tests.mocked_samples.venus_resp import VENUS_RESP
from tests.mocked_samples.vesper_resp import VESPER_RESP
from tests.mocked_samples.yfi_resp import YFI_RESP
from tests.mocked_samples.pancakeswap_resp import PANCAKESWAP_RESP


def write_ellipsis_data(data_excel, resp, name):
    data_sheet = data_excel.add_sheet(name)

    # style
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    if not resp:
        return

    left_section_data = resp.get('pool', {})

    i = 0

    for k, v in left_section_data.items():
        data_sheet.write(i, 0, k, style=style)
        data_sheet.write(i, 1, v)
        i = i + 1

    i = i + 1

    for k, v in resp.items():
        if k == 'pool':
            continue

        data_sheet.write(i, 0, k, style=style)
        data_sheet.write(i, 1, v)
        i = i + 1


def write_fyi_data(data_excel, resp, name):
    data_sheet = data_excel.add_sheet(name)

    if not resp.get('v1_assets') and not resp.get('v2_assets'):
        return

    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    # write the first row - title row
    if resp.get('v1_assets'):
        title_keys = resp.get('v1_assets')[0].keys()
    elif resp.get('v2_assets'):
        title_keys = resp.get('v2_assets')[0].keys()
    else:
        title_keys = ['asset', 'version', 'growth', 'total_assets']

    for _, title in enumerate(title_keys):
        data_sheet.write(0, _, title, style=style)

    i = 1

    # write the v1_assets
    for row in resp.get('v1_assets', {}):
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j + 1
        i = i + 1

    # write the v2_assets
    for row in resp.get('v2_assets', {}):
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j + 1
        i = i + 1


def write_lendhub_data(data_excel, resp, name):
    data_sheet = data_excel.add_sheet(name)

    if not resp:
        return

    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    i = 0
    lp_market_res = resp.get('lp_market_res', {})
    if lp_market_res:
        lp_market_title_keys = lp_market_res[0].keys()
        for _, title in enumerate(lp_market_title_keys):
            data_sheet.write(i, _, title, style=style)

    i = i + 1

    # write the lp_market_res
    for row in lp_market_res:
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j + 1
        i = i + 1

    i = i + 2

    single_market_res = resp.get('single_market_res', {})
    if single_market_res:
        single_market_title_keys = single_market_res[0].keys()
        for _, title in enumerate(single_market_title_keys):
            data_sheet.write(i, _, title, style=style)

    i = i + 1

    # write the lp_market_res
    for row in single_market_res:
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j + 1
        i = i + 1


def write_generic_data(data_excel, resp, name, sorted_field=None):
    data_sheet = data_excel.add_sheet(name)

    if not resp:
        return

    if sorted_field:
        resp.sort(key=lambda k:float(k.get(sorted_field).split('%')[0]), reverse=True)

    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    # write the first row - title row

    title_keys = resp[0].keys()
    for _, title in enumerate(title_keys):
        data_sheet.write(0, _, title, style=style)

    i = 1

    # write the content
    for row in resp:
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j+1
        i = i + 1


def write_hfi_data(data_excel, resp, name, sorted_field=None):

    data_sheet = data_excel.add_sheet(name)

    if not resp:
        return

    all_resp = []
    for rows in resp.values():
        all_resp.extend(rows)

    if sorted_field:
        all_resp.sort(key=lambda k:float(k.get(sorted_field).split('%')[0]), reverse=True)

    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    # write the first row - title row

    title_keys = all_resp[0].keys()
    for _, title in enumerate(title_keys):
        data_sheet.write(0, _, title, style=style)

    i = 1

    # write the content
    for row in all_resp:
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j + 1
        i = i + 1


if __name__ == '__main__':

    data_excel = xlwt.Workbook()

    write_generic_data(data_excel, PANCAKESWAP_RESP, 'PancakeSwap', "apr")
    write_generic_data(data_excel, VENUS_RESP, 'Venus')
    write_generic_data(data_excel, AUTOFARM_RESP, 'Autofarm', "APY")
    write_ellipsis_data(data_excel, ELLIPSIS_RESP, 'Ellipsis')
    write_generic_data(data_excel, PANCAKEBUNNY_RESP, 'Pancakebunny', "apy")
    write_generic_data(data_excel, BELT_RESP, 'Belt')
    write_generic_data(data_excel, APLACA_RESP, 'Aplaca', 'apy_u')
    write_generic_data(data_excel, BAKE_RESP, 'Bake', 'roi')
    write_generic_data(data_excel, CURVE_RESP, 'Curve', 'APY')
    write_fyi_data(data_excel, YFI_RESP, 'YFI')
    write_generic_data(data_excel, SUSHI_RESP, 'SUSHI', 'roi_year')
    write_generic_data(data_excel, VESPER_RESP, 'Vesper')
    write_generic_data(data_excel, MDEX_RESP, 'MDEX', 'APY')
    write_generic_data(data_excel, FILDA_RESP, 'FILDA')
    write_generic_data(data_excel, COINWIND_RESP, 'CoinWind', 'APY (Compound Interest)')
    write_lendhub_data(data_excel, LENDHUB_RESP, 'LendHub')
    write_hfi_data(data_excel, HFI_RESP, 'hecoFi', 'APY')

    data_excel.save('demo.xls')
