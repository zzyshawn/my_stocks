

jin_ri = '20251009'

my_zhangting_date1 = ['20241014','20241015','20241016','20241017','20241018','20241021','20241022','20241023','20241024','20241025','20241028','20241029','20241030','20241031','20241101','20241104','20241105','20241106','20241107']



def set_jin_ri(my_today):
    global jin_ri
    jin_ri = my_today

def get_jin_ri():
    global jin_ri
    return jin_ri

def set_zt_list(zt_list):
    global my_zhangting_date1
    my_zhangting_date1 = zt_list

def get_zt_list():
    global my_zhangting_date1
    return my_zhangting_date1