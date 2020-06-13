import pymysql

connection = pymysql.connect(host='rm-bp17or9z0d49569x7wo.mysql.rds.aliyuncs.com',
                             user='thomas_mysql',
                             password='Cptbtptp123!',
                             db='chatbot_sql',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
with connection.cursor() as cursor:
    # Read a single record
    sql = "UPDATE `chatbot_sql`.`device_status` SET `open` ='{open_value}' WHERE `device_type` = '{device}' AND `position`='{position}'" \
            .format(open_value=1, device='窗帘', position='次卧')
    cursor.execute(sql)
    connection.commit()
    result = cursor.fetchone()
    print(result)

def zh2num(num_str):
    unit_dict_base = {"十": 10, "百": 100, "千": 1000}
    digit_dict = {"零": 0, "一": 1, "二": 2, "两": 2, "俩": 2, "三": 3,
                  "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    sum = 0
    cur = 0
    for i, n in enumerate(num_str):
        if n in digit_dict:
            cur = digit_dict[n]
        elif i == 0 and n == '十':
            sum = unit_dict_base[n]
        elif n in unit_dict_base:
            cur *= unit_dict_base[n]
            sum += cur
            cur = 0
    return sum + cur
print(zh2num('二十五'))
