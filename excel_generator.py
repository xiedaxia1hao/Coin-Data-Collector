import xlwt

from constants import PANCAKESWAP_URL, VENUS_URL, AUTOFARM_URL, YFI_URL, ELLIPSIS_URL, LENDHUB_URL, HFI_URL, \
    PANCAKEBUNNY_URL, BELT_URL, ALPACAFINANCE_URL, BAKE_URL, CURVE_TVL_URL, SUSHI_URL, VESPER_URL, MDEX_URL, FILDA_URL, \
    COINWIND_URL
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

HEADER_OFFSET = 4


def write_ellipsis_data(data_excel, res, name, link):

    data_sheet = data_excel.add_sheet(name)

    resp = res.get('data', {})
    tvl = res.get('tvl')

    write_header(data_sheet=data_sheet, name=name, link=link, tvl=tvl, offset=5)

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


def write_fyi_data(data_excel, res, name, link):
    resp = res.get('data', {})
    tvl = res.get('tvl')

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

    write_header(data_sheet=data_sheet, name=name, link=link, tvl=tvl, offset=len(title_keys)+1)

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


def write_lendhub_data(data_excel, res, name, link):

    resp = res.get('data', {})
    tvl = res.get('tvl')

    data_sheet = data_excel.add_sheet(name)

    write_header(data_sheet=data_sheet, name=name, link=link, tvl=tvl, offset=10)

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


def write_generic_data(data_excel, res, name, link, sorted_field=None):
    data_sheet = data_excel.add_sheet(name)

    resp = res.get('data', {})
    tvl = res.get('tvl')

    if not resp:
        return

    if sorted_field:
        resp.sort(key=lambda k:float(k.get(sorted_field).split('%')[0]), reverse=True)


    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font


    title_keys = resp[0].keys()

    write_header(data_sheet=data_sheet, name=name, link=link, tvl=tvl, offset=len(title_keys)+1)

    i = 0

    # write the first row - title row
    for _, title in enumerate(title_keys):
        data_sheet.write(i, _, title, style=style)

    i = i + 1

    # write the content
    for row in resp:
        j = 0
        for k, v in row.items():
            data_sheet.write(i, j, v)
            j = j+1
        i = i + 1


def get_header_style():

    # font size: 20 -> height: 20 * 20
    # if we need size 16, let it be 16 * 20
    font = xlwt.Font()
    font.bold = True
    font.height = 20 * 20

    # middle alignment
    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_CENTER
    alignment.vert = xlwt.Alignment.VERT_CENTER

    # borders
    borders = xlwt.Borders()
    borders.top = xlwt.Borders.THICK
    borders.bottom = xlwt.Borders.THICK
    borders.left = xlwt.Borders.THICK
    borders.right = xlwt.Borders.THICK

    # attach
    style = xlwt.XFStyle()
    style.font = font
    style.alignment = alignment
    style.borders = borders

    return style


def write_header(data_sheet, name, link, tvl, offset):

    style = get_header_style()
    data_sheet.write_merge(1, 5, offset, offset+4, xlwt.Formula('HYPERLINK("{}";"{}")'.format(link, name or 'Name: N/A')), style=style)
    data_sheet.write_merge(6, 10, offset, offset+4, 'TVL: {}'.format(tvl or 'N/A'), style=style)


def write_hfi_data(data_excel, res, name, link, sorted_field=None):

    resp = res.get('data', {})
    tvl = res.get('tvl', {})

    data_sheet = data_excel.add_sheet(name)

    write_header(data_sheet=data_sheet, name=name, link=link, tvl=tvl, offset=4)


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

    write_generic_data(data_excel, PANCAKESWAP_RESP, 'PancakeSwap', PANCAKESWAP_URL, sorted_field="apr")
    write_generic_data(data_excel, VENUS_RESP, 'Venus', VENUS_URL)
    write_generic_data(data_excel, AUTOFARM_RESP, 'Autofarm', AUTOFARM_URL, sorted_field="APY")
    write_ellipsis_data(data_excel, ELLIPSIS_RESP, 'Ellipsis', ELLIPSIS_URL)
    write_generic_data(data_excel, PANCAKEBUNNY_RESP, 'Pancakebunny', PANCAKEBUNNY_URL, sorted_field="apy")
    write_generic_data(data_excel, BELT_RESP, 'Belt', BELT_URL)
    write_generic_data(data_excel, APLACA_RESP, 'Aplaca', ALPACAFINANCE_URL, sorted_field='apy_u')
    write_generic_data(data_excel, BAKE_RESP, 'Bake', BAKE_URL, sorted_field='roi')
    write_generic_data(data_excel, CURVE_RESP, 'Curve', CURVE_TVL_URL, sorted_field='APY')
    write_fyi_data(data_excel, YFI_RESP, 'YFI', YFI_URL)
    write_generic_data(data_excel, SUSHI_RESP, 'SUSHI', SUSHI_URL, sorted_field='roi_year')
    write_generic_data(data_excel, VESPER_RESP, 'Vesper', VESPER_URL)
    write_generic_data(data_excel, MDEX_RESP, 'MDEX', MDEX_URL, sorted_field='APY')
    write_generic_data(data_excel, FILDA_RESP, 'FILDA', FILDA_URL)
    write_generic_data(data_excel, COINWIND_RESP, 'CoinWind', COINWIND_URL, sorted_field='APY (Compound Interest)')
    write_lendhub_data(data_excel, LENDHUB_RESP, 'LendHub', LENDHUB_URL)
    write_hfi_data(data_excel, HFI_RESP, 'hecoFi', HFI_URL, sorted_field='APY')

    data_excel.save('test.xls')
