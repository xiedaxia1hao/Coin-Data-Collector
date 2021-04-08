
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


if __name__ == '__main__':
    print(convert_valid_aplaca_data('1.29k%'))
    print(convert_valid_aplaca_data('1.29%'))