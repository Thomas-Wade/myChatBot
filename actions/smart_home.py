from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
import re, pymysql

class FormUtility:

    def validate_num(self, value, dispatcher, tracker, domain):
        if re.match(r'\d+', value):
            return {"num": int(value)}
        elif value in ['max_value', 'min_value']:
            return {"num": value}
        else:
            try:
                int_num = self.__zh2num(value)
                return {"num": int_num}
            except ValueError:
                dispatcher.utter_message(text='抱歉，这不是一个合法的数字')
                return {"num": None}

    def validate_device(self, value, dispatcher, tracker, domain):
        select_str = "SELECT `position` FROM `device_status` WHERE `device_type`='%s'" % (value)
        result = self.__run_sql(select_str)
        if len(result) == 1:
            return {"device": value, 'position': result[0]['position']}
        else:
            return {"device": value}

    def __zh2num(self, num_str):
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
            else:
                raise ValueError('not a valid number char')
        return sum + cur

    def __run_sql(self, select_str):
        connection = pymysql.connect(host='rm-bp17or9z0d49569x7wo.mysql.rds.aliyuncs.com',
                                     user='thomas_mysql',
                                     password='Cptbtptp123!',
                                     db='chatbot_sql',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            # Read a single record
            cursor.execute(select_str)
            connection.commit()
            result = cursor.fetchall()
        # connection.close()
        return result

    def check_position_has_device(self, dispatcher, position, device):
        select_str = "SELECT COUNT(*) FROM `device_status` WHERE `device_type`='%s' AND `position`='%s'" % (
            device, position)
        count = self.__run_sql(select_str)[0]['COUNT(*)']
        if count == 0:
            dispatcher.utter_message(text='%s里没有%s' % (position, device))
            return False
        elif count > 1:
            dispatcher.utter_message(text='%s里不知有一个%s，请重新输入' % (position, device))
            return False
        else:
            return True

    def is_open(self, position, device):
        select_str = "SELECT open FROM `device_status` WHERE `device_type`='%s' AND `position`='%s'" % (
            device, position)
        return self.__run_sql(select_str)[0]['open'] == 1

    def get_temperature(self, position, device):
        select_str = "SELECT temperature FROM `device_status` WHERE `device_type`='%s' AND `position`='%s'" % (
            device, position)
        return self.__run_sql(select_str)[0]['temperature']

    def set_device_property_value(self, position, device,column_name, value):
        select_str = "UPDATE `chatbot_sql`.`device_status` SET `{column_name}` ='{value}' WHERE `device_type` = '{device}' AND `position`='{position}'" \
            .format(value=value, device=device, position=position, column_name = column_name)
        self.__run_sql(select_str)

    def get_min_max_temperature(self, position, device):
        select_str = "SELECT `device_property`.`min_temperature`, `device_property`.`max_temperature`  FROM `device_status`, `device_property` WHERE `device_status`.`device_id` = `device_property`.`device_id` AND `device_status`.`device_type`='%s' AND `device_status`.`position`='%s'" % (
            device, position)
        result = self.__run_sql(select_str)[0]
        return result['min_temperature'], result['max_temperature']

class OpenForm(FormAction, FormUtility):

    def name(self):
        return "open_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position"]

    def submit(self, dispatcher, tracker, domain):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if FormUtility.is_open(self, position, device):
            dispatcher.utter_message(text='%s的%s早就打开了' % (position, device))
            return [AllSlotsReset()]
        FormUtility.set_device_property_value(self, position, device,'open', 1)
        dispatcher.utter_message(text='%s的%s打开' % (position, device))
        return [AllSlotsReset()]

class CloseForm(FormAction, FormUtility):

    def name(self):
        return "close_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position"]

    def submit(self, dispatcher, tracker, domain):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if not FormUtility.is_open(self, position, device):
            dispatcher.utter_message(text='%s的%s早就关上了' % (position, device))
            return [AllSlotsReset()]
        FormUtility.set_device_property_value(self, position, device,'open', 0)
        dispatcher.utter_message(text='%s的%s关了' % (position, device))
        return [AllSlotsReset()]

class SetTemperatureForm(FormAction, FormUtility):
    def name(self):
        return "set_temperature_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position", "num"]

    def submit(self, dispatcher, tracker, domain, ):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if not FormUtility.is_open(self, position, device):
            FormUtility.set_device_property_value(self, position, device,'open', 1)
            dispatcher.utter_message(text='%s的%s打开' % (position, device))
        min_temperature, max_temperature = FormUtility.get_min_max_temperature(self, position, device)
        num = tracker.get_slot('num')

        if num == 'max_value':
            dispatcher.utter_message(
                text='%s的%s可设置为最高温度%s' % (position, device, str(max_temperature)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', max_temperature)
            return [AllSlotsReset()]
        elif num == 'min_value':
            dispatcher.utter_message(
                text='%s的%s可设置为最低温度%s' % (position, device, str(min_temperature)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', min_temperature)
            return [AllSlotsReset()]
        elif num > max_temperature:
            dispatcher.utter_message(
                text='%s的%s可设置的最高温度为%s， 无法设置到%s,将按最高温度设置' % (position, device, str(max_temperature), str(num)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', max_temperature)
            return [AllSlotsReset()]
        elif num < min_temperature:
            dispatcher.utter_message(
                text='%s的%s可设置的最低温度为%s， 无法设置到%s,将按最低温度设置' % (position, device, str(min_temperature), str(num)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', min_temperature)
            return [AllSlotsReset()]
        else:
            dispatcher.utter_message(
                text='%s的%s设置为%s' % (position, device, str(num)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', num)
            return [AllSlotsReset()]

    def validate_device(self, value, dispatcher, tracker, domain):
        if value not in ['空调', '热水器']:
            dispatcher.utter_message(text='%s不支持设置温度' % (value))
            return {"device": None}
        return FormUtility.validate_device(self, value, dispatcher, tracker, domain)

    def slot_mappings(self):
        return {
            "num": [
                self.from_entity(entity="max"),
                self.from_entity(entity="min"),
                self.from_entity(entity="num"),
            ],
        }

class SetModeForm(FormAction, FormUtility):

    def name(self):
        return "set_mode_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position", "mode"]

    def submit(self, dispatcher, tracker, domain, ):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if not FormUtility.is_open(self, position, device):
            FormUtility.set_device_property_value(self, position, device, 'open', 1)
            dispatcher.utter_message(text='%s的%s打开' % (position, device))
        mode = tracker.get_slot('mode')
        dispatcher.utter_message(
            text='%s的%s设置为%s' % (position, device, mode))
        FormUtility.set_device_property_value(self, position, device, 'mode', mode)
        return [AllSlotsReset()]

    def validate_device(self, value, dispatcher, tracker, domain):
        if value != '空调':
            dispatcher.utter_message(text='%s不支持设置模式' % (value))
            return {"device": None}
        return FormUtility.validate_device(self, value, dispatcher, tracker, domain)

    def validate_mode(self, value, dispatcher, tracker, domain):
        validate_mode_list = ["睡眠模式", "通风模式", "扫风模式", "左右扫风模式", "上下扫风模式", "送风模式", "自动模式", "制热模式", "制冷模式"]
        if value in validate_mode_list:
            return {"mode": value}
        else:
            dispatcher.utter_message(text = '抱歉，目前不支持"%s"'%value)
            return {"mode": None}

class TurnupTemperatureForm(FormAction, FormUtility):
    def name(self):
        return "turnup_temperature_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position", "num"]

    def submit(self, dispatcher, tracker, domain, ):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if not FormUtility.is_open(self, position, device):
            FormUtility.set_device_property_value(self, position, device, 'open', 1)
            dispatcher.utter_message(text='%s的%s打开' % (position, device))
        min_temperature, max_temperature = FormUtility.get_min_max_temperature(self, position, device)
        cur_temperature = FormUtility.get_temperature(self, position, device)
        num = cur_temperature + tracker.get_slot('num')
        if num > max_temperature:
            dispatcher.utter_message(
                text='{position}的{device}可设置的最高温度为{max_temperature}，当前温度为{cur_temperature} 无法升高{num},将按最高温度设置'.
                    format(position = position, device=device, max_temperature = max_temperature, num = tracker.get_slot('num'), cur_temperature = cur_temperature))
            FormUtility.set_device_property_value(self, position, device, 'temperature', max_temperature)
            return [AllSlotsReset()]
        else:
            dispatcher.utter_message(
                text='%s的%s设置为%s' % (position, device, str(num)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', num)
            return [AllSlotsReset()]

    def validate_device(self, value, dispatcher, tracker, domain):
        if value not in ['空调', '热水器']:
            dispatcher.utter_message(text='%s不支持设置温度' % (value))
            return {"device": None}
        return FormUtility.validate_device(self, value, dispatcher, tracker, domain)

class TurndownTemperatureForm(FormAction, FormUtility):
    def name(self):
        return "turndown_temperature_form"

    @staticmethod
    def required_slots(tracker: Tracker):
        return ["device", "position", "num"]

    def submit(self, dispatcher, tracker, domain, ):
        position = tracker.get_slot('position')
        device = tracker.get_slot('device')
        if not FormUtility.check_position_has_device(self, dispatcher, position, device):
            return [AllSlotsReset()]
        if not FormUtility.is_open(self, position, device):
            FormUtility.set_device_property_value(self, position, device, 'open', 1)
            dispatcher.utter_message(text='%s的%s打开' % (position, device))
        min_temperature, max_temperature = FormUtility.get_min_max_temperature(self, position, device)
        cur_temperature = FormUtility.get_temperature(self, position, device)
        num = cur_temperature - tracker.get_slot('num')
        if num < min_temperature:
            dispatcher.utter_message(
                text='{position}的{device}可设置的最低温度为{min_temperature}，当前温度为{cur_temperature} 无法降低{num},将按最低温度设置'.
                    format(position=position, device=device, min_temperature=min_temperature,
                           num=tracker.get_slot('num'), cur_temperature=cur_temperature))
            FormUtility.set_device_property_value(self, position, device, 'temperature', min_temperature)
            return [AllSlotsReset()]
        else:
            dispatcher.utter_message(
                text='%s的%s设置为%s' % (position, device, str(num)))
            FormUtility.set_device_property_value(self, position, device, 'temperature', num)
            return [AllSlotsReset()]
