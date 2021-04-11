
def is_valid_sc_ellipsis_data(res):
    return (res.get('pool', {}).get('rewards_apy') == '' and res.get('pool', {}).get('base_apy' == '%') and res.get('pool', {}).get('volume') == '') \
                    or (res.get('EPS/BNB_staking_apy') == '0' and res.get('3pool_lp_token_apy') == '0') \
                    or (res.get('EPS_unlocked_apy') == '0% in BUSD\nLocked APY' and res.get('EPS_locked_apy') == '0% in EPS + 0% in BUSD')


def convert_valid_aplaca_data(apy):
    try:
        split_list = apy.split('%')
        str_num = split_list[0]
        if str_num.endswith('k'):
            str_num = float(str_num[:-1]) * 1000
        return '{}%'.format(str(str_num))
    except Exception as e:
        return apy


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


if __name__ == '__main__':
    res = {'data': {'单币区': [{'name': 'AAVE Plus', 'APY': '--', 'total': '8,239.11'}, {'name': 'UNI Plus', 'APY': '--', 'total': '206,969.74'}, {'name': 'HPT Plus', 'APY': '--', 'total': '318,015,260.90'}, {'name': 'HFIL', 'APY': '--', 'total': '33,084.40'}, {'name': 'MDX', 'APY': '--', 'total': '2,808,575.07'}, {'name': 'HT', 'APY': '--', 'total': '2,844,657.18'}, {'name': 'HUSD', 'APY': '72.08%', 'total': '13,363,079.40'}, {'name': 'USDT', 'APY': '76.07%', 'total': '18,367,946.44'}, {'name': 'HBTC Plus', 'APY': '15.22%', 'total': '582.0203'}, {'name': 'ETH', 'APY': '30.32%', 'total': '8,916.37'}, {'name': 'BCH', 'APY': '29.01%', 'total': '7,373.02'}, {'name': 'LTC', 'APY': '21.15%', 'total': '58,177.53'}, {'name': 'DOT Plus', 'APY': '16.22%', 'total': '656,322.79'}, {'name': 'HPT', 'APY': '15.36%', 'total': '14,432,488.58'}, {'name': 'SNX', 'APY': '--', 'total': '--'}, {'name': 'LINK', 'APY': '--', 'total': '--'}, {'name': 'BSV', 'APY': '--', 'total': '--'}, {'name': 'NEO', 'APY': '--', 'total': '--'}], 'LP 区': [{'name': 'MDX-HT Mdex LP', 'APY': '308.25%', 'total': '165,361.41'}, {'name': 'ETH-USDT Mdex LP', 'APY': '128.97%', 'total': '15,345.45'}, {'name': 'BTC-USDT Mdex LP', 'APY': '93.26%', 'total': '4,787.70'}, {'name': 'MDX-USDT Mdex LP', 'APY': '329.54%', 'total': '461,473.12'}], '创新区': [{'name': 'HUSD-USDT DEP LP', 'APY': '74.84%', 'total': '10,709,919.55'}, {'name': 'DEP-HUSD MDEX LP', 'APY': '0.00%', 'total': '0.010711'}, {'name': 'DEP-HT MDEX LP', 'APY': '0.00%', 'total': '656.46'}, {'name': 'HBO', 'APY': '387.72%', 'total': '662,525.46'}, {'name': 'HBO-USDT-LP', 'APY': '15426.32%', 'total': '61,531.94'}, {'name': 'HBO-BTC-LP', 'APY': '22568.45%', 'total': '40.5896'}, {'name': 'HBO-HT-LP', 'APY': '31385.45%', 'total': '26,901.04'}, {'name': 'HBO-HUSD-LP', 'APY': '56738.20%', 'total': '3.0160'}]}, 'tvl': ' $286,088,823.15'}
    res = res.get('data')
    print(is_valid_hfi_data(res))
