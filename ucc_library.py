import asyncio
import base64
import datetime
from hashlib import md5, sha1
import heapq
import json
import logging
import math
import mysql.connector
import os
import pymssql
import pyodbc
import random
import re
import requests
import socket
import sqlite3
import time
from zlib import crc32
from Settings import ENVIRONMENT


# TODO(suyako): 之后把var也换成类
# TODO(suyako): 集合的remove
class Components(object):
    logging.basicConfig(level=logging.INFO, filename='UCC logging.log', filemode='w')
    def __init__(self, ID, title, *value):
        self._ID = ID
        self._title = title
        self._value = value

    @property
    def default_property(self):
        raise NotImplementedError

    @default_property.setter
    def default_property(self, value):
        raise NotImplementedError


class Label(Components):
    def __init__(self, ID, title):
        super(Label, self).__init__(ID, title)
        self.Caption = title

    @property
    def default_property(self):
        return self.Caption

    @default_property.setter
    def default_property(self, value):
        self.Caption = value


class TextBox(Components):
    def __init__(self, ID, title, value):
        super(TextBox, self).__init__(ID, title, value)
        self.Text = value

    @property
    def default_property(self):
        return self.Text

    @default_property.setter
    def default_property(self, value):
        self.Text = value

    def append(self, *args):
        mode = args[0].lower()
        self.Text += args[1]

    def clear(self):
        self.Text = ''

    def remove(self, index, length):
        self.Text = self.Text[:index-1] + self.Text[index+length-1:]

    def bind(self, source, field_name=''):
        """对于TextBox, ListBox, Combo来讲，fie_name参数认为有且只有一个"""
        flag = 0
        if re.match('distinct', field_name.lower()) is not None:  # 如果存在DISTINCT关键字
            field_name = field_name[8:].strip()
            flag = 1
        if isinstance(source, varDB):  # 第一个参数为DB数据源的情况下
            if field_name not in source.value:
                raise ValueError('Field Name Error.')
            elif flag:
                self.Text = ''.join(set(source.value[field_name]))  # TODO: 暂时未知DISTINCT关键字保持有序还是无序
            else:
                self.Text = ''.join(source.value[field_name])
        elif isinstance(source, str):
            delimiter, expression = source, field_name  # 换了下名称以防误解
            if flag:
                self.Text = ''.join(set(expression.split(delimiter)))
            else:
                self.Text = ''.join(expression.split(delimiter))


class Image(Components):
    def __init__(self, ID, title, value):
        super(Image, self).__init__(ID, title)
        self.Picture = value
        logging.info("Image is not supported.")
        raise TypeError("Image is not supported.")

    @property
    def default_property(self):
        return self.Picture

    @default_property.setter
    def default_property(self, value):
        self.Picture = value


class Gif(Components):
    def __init__(self, ID, title, value):
        super(Gif, self).__init__(ID, title)
        self.Picture = value
        logging.info("Gif is not supported.")
        raise TypeError("Gif is not supported.")

    @property
    def default_property(self):
        return self.Picture

    @default_property.setter
    def default_property(self, value):
        self.Picture = value


class Apng(Components):
    def __init__(self, ID, title, value):
        super(Apng, self).__init__(ID, title)
        self.Picture = value
        logging.info("Apng is not supported.")
        raise TypeError("Apng is not supported.")

    @property
    def default_property(self):
        return self.Picture

    @default_property.setter
    def default_property(self, value):
        self.Picture = value


class CommandButton(Components):
    def __init__(self, ID, title, value):
        super(CommandButton, self).__init__(ID, title, value)
        self.Caption = title

    @property
    def default_property(self):
        return self.Caption

    @default_property.setter
    def default_property(self, value):
        self.Caption = value


class Menu(Components):
    def __init__(self, ID, title, value):
        super(Menu, self).__init__(ID, title, value)
        self.Title = title
        self.data = value.split(',')

    @property
    def default_property(self):
        return self.Title

    @default_property.setter
    def default_property(self, value):
        self.Title = value


class ComboBox(Components):
    def __init__(self, ID, title, value):
        super(ComboBox, self).__init__(ID, title, value)
        self.Text = ''
        self.data = value.split(',')

    @property
    def default_property(self):
        return self.Text

    @default_property.setter
    def default_property(self, value):
        self.Text = value

    def append(self, *args):
        mode = args[0].lower()
        self.data.extend(args[1:])

    def clear(self):
        self.data = []

    def remove(self, index):
        if isinstance(index, int):
            self.data = self.data[:index - 1].extend(self.data[index:])
        elif isinstance(index, str) and index.lower() == 'all':
            self.data = []
        else:
            raise TypeError()

    def bind(self, source, field_name=''):
        """对于TextBox, ListBox, Combo来讲，fie_name参数认为有且只有一个"""
        flag = 0
        if re.match('distinct', field_name.lower()) is not None:  # 如果存在DISTINCT关键字
            field_name = field_name[8:]
            flag = 1
        if isinstance(source, varDB):  # 第一个参数为DB数据源的情况下
            if field_name not in source.value:
                raise ValueError('Filed Name Error.')
            elif flag:
                self.data = list(set(source.value[field_name]))  # TODO: 暂时未知DISTINCT关键字保持有序还是无序
            else:
                self.data = source.value[field_name]
        elif isinstance(source, str):
            delimiter, expression = source, field_name  # 换了下名称以防误解
            if flag:
                self.data = set(expression.split(delimiter))
            else:
                self.data = expression.split(delimiter)


class ListBox(Components):
    def __init__(self, ID, title, value):
        super(ListBox, self).__init__(ID, title, value)
        self.Text = ''
        self.data = value.split(',')

    @property
    def default_property(self):
        return self.Text

    @default_property.setter
    def default_property(self, value):
        self.Text = value

    def append(self, *args):
        mode = args[0].lower()
        self.data.extend(args[1:])

    def clear(self):
        self.data = []

    def remove(self, index):
        if isinstance(index, int):
            self.data = self.data[:index - 1].extend(self.data[index:])
        elif isinstance(index, str) and index.lower() == 'all':
            self.data = []
        else:
            raise TypeError()

    def bind(self, source, field_name=''):
        """对于TextBox, ListBox, Combo来讲，fie_name参数认为有且只有一个"""
        flag = 0
        if re.match('distinct', field_name.lower()) is not None:  # 如果存在DISTINCT关键字
            field_name = field_name[8:]
            flag = 1
        if isinstance(source, varDB):  # 第一个参数为DB数据源的情况下
            if field_name not in source.value:
                raise ValueError('Filed Name Error.')
            elif flag:
                self.data = list(set(source.value[field_name]))  # TODO: 暂时未知DISTINCT关键字保持有序还是无序
            else:
                self.data = source.value[field_name]
        elif isinstance(source, str):
            delimiter, expression = source, field_name  # 换了下名称以防误解
            if flag:
                self.data = set(expression.split(delimiter))
            else:
                self.data = expression.split(delimiter)


class CheckBox(Components):
    def __init__(self, ID, title, value):
        super(CheckBox, self).__init__(ID, title, value)
        self.Value = 0

    @property
    def default_property(self):
        return self.Value

    @default_property.setter
    def default_property(self, value):
        self.Value = value


class OptionButton(Components):
    def __init__(self, ID, title, value):
        super(OptionButton, self).__init__(ID, title, value)
        self.Value = 0

    @property
    def default_property(self):
        return self.Value

    @default_property.setter
    def default_property(self, value):
        self.Value = value


class Timer(Components):
    def __init__(self, control):
        super(Timer, self).__init__(control)
        self.Interval = 1000

    @property
    def default_property(self):
        return self.Interval

    @default_property.setter
    def default_property(self, value):
        self.Interval = value


class Report(Components):
    def __init__(self, ID, title, value):
        super(Report, self).__init__(ID, title, value)
        self.SelectedIndex = 1
        self.data = list()

    @property
    def default_property(self):
        return self.SelectedIndex

    @default_property.setter
    def default_property(self, value):
        self.SelectedIndex = value

    def append(self, *args):
        mode = args[0].lower()
        self.data.append(list(args[1:]))

    def get(self, target, pos1=1, pos2=1):
        target = target.lower()
        if target == 'columntitle':
            return self.data[0][pos1 - 1]
        elif target == 'columnwidth':
            pass
        elif target == 'columnvisble':
            pass
        elif target == 'rowltwh':
            pass
        elif target == 'cellvalue':
            return self.data[pos1 - 1][pos2 - 1]
        elif target == 'cellforecolor':
            pass
        elif target == 'cellbackcolor':
            pass
        elif target == 'rowscount':
            return len(self.data)
        elif target == 'columnscount':
            return len(self.data[0])
        elif target == 'selectedrowindex':
            pass
        elif target == 'selectedrowcount':
            pass
        else:
            raise ValueError

    def set(self, target, *args):
        target = target.lower()
        if target == 'columnwidth':
            pass
        elif target == 'columnvisible':
            pass
        elif target == 'addindexcolumn':
            # 由于无法可视化，这里把index放在末尾
            for i, _ in enumerate(self.data):
                _ = _.append(i)
        elif target == 'cellvalue':
            pos1, pos2, value = args
            self.data[pos1 - 1][pos2 - 1] = value
        elif target == 'cellforecolor':
            pass
        elif target == 'cellbackcolor':
            pass
        elif target == 'removerow':
            index = args[0]
            self.data = self.data[:index].extend(self.data[index + 1:])
        elif target == 'selectrow':
            pass
        elif target == 'clearrows':
            self.data = self.data[1:]
        elif target == 'rowscolor':
            pass
        elif target == 'rowvalue':
            pos = args[0]
            length = len(args) - 1
            self.data[pos][:length] = args[1:]
        elif target == 'addrow':
            temp = ['' for n in range(len(self.data[0]))]
            temp[:len(args)] = args

    def bind(self, source, *field_names):
        if not isinstance(source, varDB):
            raise TypeError
        if field_names:
            field_names = [field_name for field_name in field_names if source.is_exist(field_name)]
        for i in source.count():
            self.data.append(source.get_irow(i, field_names))


class Tree(object):
    def __init__(self):
        self.data = dict()
        self.structure = dict()
    # def __init__(self, control):
    #     super(Tree, self).__init__(control)
    #     self.data = dict()
    #     self.structure = dict()  # 用来记录父节点ID与状态，对于root其父节点ID记为本身，状态为0表示未选中，为1表示选中

    @property
    def default_property(self):
        return self.data

    @default_property.setter
    def default_property(self, value):
        self.data = value

    def _track_path(self, ID):
        """追踪该ID在结构中的路径"""
        track_path = []
        while not self.structure[ID][0] == ID:
            track_path.append(ID)
            ID = self.structure[ID][0]
        track_path.append(ID)
        return track_path

    def _open(self, ID):
        """参考文件的open方法，该函数打开目标节点，若节点不存在则创建一个新的空节点并打开该节点"""
        track_path = self._track_path(ID)
        target = self.data
        while track_path:
            _ = track_path.pop()
            try:
                target = target[_]
            except KeyError:
                target[_] = dict()
                target = target[_]
        return target

    def append(self, *args):
        parent_ID = args[1]
        private_ID = args[2]
        private_title = args[3]
        if not parent_ID:
            if private_ID.lower() == 'root':
                self.structure[private_ID] = [private_ID, 0]
                self.data[private_ID] = dict(title=private_title)
            else:
                raise ValueError
        else:
            self.structure[private_ID] = [parent_ID, 0]
            target = self._open(private_ID)
            target['title'] = private_title

    def is_exist(self, node):
        """判断节点是否存在"""
        if node not in self.structure:
            raise KeyError
        else:
            return self._open(node)

    def get(self, *args):
        mode =args[0].lower()
        if mode == 'id':
            index = args[1]
            try:
                node = args[2]
            except IndexError:
                return list(self.structure.keys())
            target = self.is_exist(node)
            if index.lower() == 'all':
                return list(target.keys())[1:]
            else:
                return list(target.keys())[index]
        elif mode == 'title':
            target = self.is_exist(args[1])
            return target['title']
        elif mode == 'forecolor':
            pass
        elif mode == 'childrencount':
            target = self.is_exist(args[1])
            return len(target) - 1
        elif mode == 'selectedid':
            target = []
            for _ in self.structure:
                if _[1]:
                    target.append(_)
            return target
        elif mode == 'selectedcount':
            return len(self.structure)
        elif mode == 'node':
            return self.is_exist(args[1])
        elif mode == 'checked':
            return self.is_exist(args[1])[1]

    def set(self, *args):
        mode = args[0].lower()
        if mode == 'bold':
            pass
        elif mode == 'clear':
            self.data = {}
            self.structure = {}
        elif mode == 'expand':
            pass
        elif mode == 'expandall':
            pass
        elif mode == 'forecolor':
            pass
        elif mode == 'id':
            self.is_exist(args[1])
            self.is_exist(args[2])[args[1]] = dict(title='empty')
        elif mode == 'icon':
            pass
        elif mode == 'iconsize':
            pass
        elif mode == 'fullrowselect':
            pass  # TODO(suyako): 不清楚函数功能
        elif mode == 'multicheck':
            pass  # TODO(suyako): 应该无法实现
        elif mode == 'remove':
            node = args[1]
            del self.is_exist(self.structure[node])[node]  # 打开node的上级节点，然后删除node条目
        elif mode == 'select':
            self.structure[args[1]][1] = int(args[2])
        elif mode == 'showlines':
            pass
        elif mode == 'title':
            self.is_exist(args[1])['title'] = args[2]
        elif mode == 'visible':
            pass
        elif mode == 'parentid':
            pass  # TODO(suyako): 不清楚函数功能

    def bind(self, source, root, parent, ID, title, image):
        """
        :param root: 根节点id
        :param parent: 父节点id所在列
        :param ID: 自身id所在列
        :param title:  自身title所在列
        """
        if not isinstance(source, varDB):
            raise TypeError
        self.structure = {}
        for _ in zip(source.value[ID], source.value[parent]):
            self.structure[_[0]] = [_[1], 0] if _[1] else [root, 0]
        for i in range(source.count()):
            parent_ID = source.value[parent][i]
            private_ID = source.value[ID][i]
            private_title = source.value[title][i]
            if not parent_ID:
                if private_ID == root:
                    self.data[private_ID]['title']=private_title
                else:
                    raise ValueError
            else:
                target = self._open(private_ID)
                target['title'] = private_title

    def __str__(self):
        return str(self.data)

# class LED(pyb.LED):
#     '一个重构的LED类，继承自pyboard上的LED类，主要改变是增加了value属性'
#     def __init__(self, index):
#         pyb.LED(index)
#
#     @property
#     def value(self):
#         return int(self.intensity() > 0)
#
#     @value.setter
#     def value(self, flag):
#         if flag not in [0, 1]:
#             raise ValueError("LED only has two status: on, off. Please check your input.")
#         else:
#             self.intensity(flag * 255)


# class Pin(pyb.Pin):
#     '重构Pin类，继承自pyboard上的Pin类'
#     def __init__(self, index):
#         pyb.Pin(index)

# LED1 = LED(1)
# LED2 = LED(2)
# LED3 = LED(3)
# LED4 = LED(4)

# ======================================================================================================================
# System functions library
# ======================================================================================================================
# <editor-fold desc="System functions library.">
def _process_time(paratime):
    currtime = time.localtime()
    year = str(currtime.tm_year) + '-'
    month = str(currtime.tm_mon) + '-'
    day = str(currtime.tm_mday)
    space = ' '
    hour = str(currtime.tm_hour) + ':'
    minute = str(currtime.tm_min) + ':'
    sec = str(currtime.tm_sec)
    timetuple = [year, month, day, space, hour, minute, sec]
    m = re.match('(\d{4})?(-\d{2})?(-\d{2})?(\s)?(\d{2}:)?(\d{2}:)?(\d{2})?', paratime).groups()
    for i, _ in enumerate(m):
        if _ is not None:
            timetuple[i] = _
    return time.strptime(''.join(timetuple), '%Y-%m-%d %X')


def clipboard(mode, *args):
    mode = mode.lower()
    if mode == 'set':
        ENVIRONMENT['clipboard'] = args
        return args
    elif mode == 'get':
        return ENVIRONMENT['clipboard']
    elif mode == 'clear':
        ENVIRONMENT['clipboard'] = None


def getdateadd(mode, interval, currdate, workday='1111100', holiday=None):
    heap = []
    mode = mode.lower()
    currdate = _process_time(currdate)
    if holiday is not None:
        for i, _ in enumerate(re.split('[,\s]', holiday)):
            y, m, d, H, M, S = currdate[:6]
            heapq.heappush(heap, datetime.datetime(y, m, d, H, M, S))
    y, m, d, H, M, S, wday, yday = currdate[:8]
    currdate = datetime.datetime(y, m, d, H, M, S)
    if mode == 'year':
        res = datetime.datetime(y+interval, m, d, H, M, S)
    elif mode == 'month':
        carry_year = (m + interval) // 12
        m = (m - 1 + interval) % 12 + 1
        res = currdate + datetime.timedelta(y + carry_year, m, d, H, M, S)
    elif mode == 'day':
        res = currdate + datetime.timedelta(days=interval)
    elif mode == 'hour':
        res = currdate + datetime.timedelta(hours=interval)
    elif mode == 'minute':
        res = currdate + datetime.timedelta(minutes=interval)
    elif mode == 'second':
        res = currdate + datetime.timedelta(seconds=interval)
    elif mode == 'weekday':
        if not isinstance(workday, str):
            workday = str(workday)
        day_to_work_perweek = sum([1 for _ in workday if _ == '1'])
        temp = interval % day_to_work_perweek
        days = interval // day_to_work_perweek * 7
        while (workday*2)[7+wday] is not '1':
            wday -= 1
            days -= 1
        for _ in (workday*3)[wday+8:]:
            if not temp:
                break
            if _ is not '0':
                temp -= 1
            days += 1
        holiday_not_account = currdate + datetime.timedelta(days=days)
        wday = time.strptime(str(holiday_not_account), '%Y-%m-%d %X').tm_wday
        incre = 0
        if heap:
            try:
                while heapq.heappop(heap) <= holiday_not_account:
                    while workday[(wday + 1 + incre) % 7] is '0':
                        incre += 1
                    incre += 1
            except IndexError:
                pass
        res = holiday_not_account + datetime.timedelta(days=incre)
    return res


def getdatetime(*param):
    def process_mode(mode):
        py_mode = []
        for _ in re.split('([ -:])', mode):
            if _ == 'YYYY' or _.lower() == 'year':
                py_mode.append('%Y')
            elif _ == 'MM' or _.lower() == 'month':
                py_mode.append('%m')
            elif _ == 'DD' or _.lower() == 'day':
                py_mode.append('%d')
            elif _ == 'HH' or _.lower() == 'hour':
                py_mode.append('%H')
            elif _ == 'mm' or _.lower() == 'minute':
                py_mode.append('%M')
            elif _ == 'ss' or _.lower() == 'second':
                py_mode.append('%S')
            else:
                py_mode.append(_)
        return ''.join(py_mode)
    if not param:
        return time.strftime('%y-%m-%d %X', time.localtime())
    else:
        mode = process_mode(param[0])
        try:
            param[1]
        except IndexError:
            paratime = time.localtime()
        else:
            paratime = _process_time(param[1])
        return time.strftime(mode, paratime)


# TODO(suyako): mode还未完全写完
def getdatediff(mode, time1, time2):
    time1 = _process_time(time1)
    time2 = _process_time(time2)
    y,m,d,H,M,S = time1[:6]
    time1 = datetime.datetime(y, m, d, H, M, S)
    y, m, d, H, M, S = time2[:6]
    time2 = datetime.datetime(y, m, d, H, M, S)
    difftime = time2 - time1
    mode = mode.lower()
    if mode == 'h':
        return int(difftime.total_seconds() / 3600)
    elif mode == 'm':
        return int(difftime.total_seconds() / 60)
    elif mode == 's':
        return int(difftime.total_seconds())
    elif mode == 'd':
        return difftime.days


def getversion(mode):
    if mode.lower() == 'app':
        return ENVIRONMENT['app_version']
    elif mode.lower() == 'runtime':
        return ENVIRONMENT['ucc_version']


# TODO(suyako): run
# def run(*param):
#     if len(param) == 1:
#         os.system(param[0])
#     elif len(param) == 2:
#         if param[0].lower() == 'wait':
#             async def curr_
# </editor-fold>

# ======================================================================================================================
# Logic functions library
# ======================================================================================================================
# <editor-fold desc="Logic functions library.">
# </editor-fold>

# ======================================================================================================================
# Object functions library
# ======================================================================================================================
# <editor-fold desc="Object functions library.">
def clear(*args):
    for e in args:
        e.clear()


def clone(*args):
    *left, right = args
    for _ in left:
        left = right  # TODO(suyako): 类的创建要更为细致


# TODO(suyako): 要重新考虑组件类的设计
def new(type_name, ID, title, container, visible=1):
    type_name(ID, title, container)
# </editor-fold>


# ======================================================================================================================
# Data functions library
# ======================================================================================================================
# <editor-fold desc="Data functions library.">
def db(*args):
    mode = args[0].lower()
    if mode == 'access':
        database = pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;" % args[1])
    elif mode == 'db2':
        pass
    elif mode == 'excel':
        pass  # TODO(suyako): demo不成功
    elif mode == 'mysql':
        database = mysql.connector.connect(host=args[1], user=args[3], password=args[4], database=args[2])
    elif mode == 'sqlite':
        database = sqlite3.connect(args[1])
    elif mode == 'sqlserver':
        database = pymssql.connect(host=args[1], user=args[3], password=args[4], database=args[2])
    elif mode == 'string':
        data = re.split(args[2], args[1])
        for _ in data:
            _ = re.split(args[3], _)
        if args[-1] == 1:
            pass  # TODO(suyako): 参数未知
        else:
            pass
    try:
        cursor = database.cursor()
    except UnboundLocalError:
        return
    cursor.execute(args[-1][3:].strip())  # UCC中SQL语句会有SQL关键字，所以这里从第三个字符位开始然后去掉两边的空格
    data = varDB()
    try:
        target = cursor.fetchall()
    except pyodbc.ProgrammingError:
        return
    field_names = [e[0] for e in cursor.description]
    data.append(field_names, target)
    cursor.close()
    database.close()
    return data


def getrecordcount(source):
    if not isinstance(source, dict):
        raise TypeError
    else:
        return len(source)


def getfieldvalue(source, index, field_name):
    if not isinstance(source, varDB):
        raise TypeError
    return source.value[field_name][index-1]


def my_json(mode, target, source):
    """
    如果source为字典，则由于预处理中去掉引号的原因，需要先对source进行处理重新加上引号，另：这里的所有键值对都处理为字符串
    也可以自己造轮子
    """
    def process(s):
        s = re.sub('\s*:\s*', ':', s)  # 把多余的空格去掉
        s = re.sub('\s*,\s*', ',', s)  # 把多余的空格去掉
        # s = json.dumps(s, separators=(',', ':'))  json自带有去空格功能，不过这里实现有些问题所以没用
        words = re.split('([^{},:]+)', s)
        value = [word.strip() for word in words if word.strip()]
        return '"'.join(value)  # json的laod方法要求一定为双引号
    source = process(source) if '{' in source else source
    mode = mode.lower()
    data = json.loads(source)
    while '.' in target:
        [left, target] = re.split('\.', target, 1)
        data = data[left]
    data = data[target]
    if mode == 'value':
        return data
    elif mode == 'count':
        return len(data) if isinstance(data, list) or isinstance(data, dict) else 0
    elif mode == 'collection':
        return {target: data}


def my_input(prompt, *args):
    try:
        default = args[1]
    except IndexError:
        return input(prompt)
    else:
        answer = input(prompt)
        return answer if answer else default


def my_math(mode, value):
    mode = mode.lower()
    mapping = {'abs': math.fabs, 'atn': math.atan, 'cos': math.cos, 'exp': math.exp, 'log': math.log, 'sqr': math.sqrt,
               'sin': math.sin, 'tan': math.tan}
    if mode in mapping:
        return mapping[mode](value)
    elif mode == 'int':
        return int(value)
    elif mode == 'round':
        return int(value + 0.5)
    elif mode == 'sgn':
        return 1 if value > 0 else int(value == 0) - 1


def my_return(*args):
    return args


# TODO(suyako): 搞清return_type代表的含义
def webservice(mode, return_type, url, param=None):
    mode = mode.lower()
    if mode == 'get':
        return requests.get(url=url)


class varDB(object):
    def __init__(self):
        self.value = dict()
        self._record_count= 0
        self._field_count = 0

    def append(self, field_names, target):
        """
        value的数据结构为：{字段名1：相应值1，字段名2：相应值2，...}
        :param field_names: 所需要提取的字段名
        :param target: 目标值
        """
        self._record_count = len(target)  # 数据的记录数量
        self._field_count = len(field_names)  # 所需要提取的字段数量
        for _ in field_names:
            self.value.setdefault(_, list())
        for i, _ in enumerate(field_names):
            for e in target:
                self.value[_].append(e[i])

    def is_exist(self, field_name):
        """判断是否存在field_name的字段名"""
        try:
            self.value[field_name]
        except KeyError as e:
            raise False
        else:
            return True

    def count(self):
        return self._record_count

    def get_irow(self, i, *field_names):
        """返回第i行字段名为field_names的数据，i从0开始算起"""
        res = []
        # 如果field_names为空，则返回所有字段
        if not field_names:
            field_names = self.value.keys()
        for field_name in field_names:
            res.append(self.value[field_name][i])
        return res
# </editor-fold>


# ======================================================================================================================
# String functions library
# ======================================================================================================================
# <editor-fold desc="String functions library.">
# TODO(suyako): convert，格式太多了


def mydecode(type, mode, source):
    if type.lower() == 'string':
        return base64.b64decode(source).decode()
    elif type.lower() == 'file':
        with open(source, 'rb') as f:
            return base64.b64decode(f.read()).decode()


def myencode(type, mode, source):
    if type.lower() == 'string':
        return base64.b64encode(source.encode())
    elif type.lower() == 'file':
        with open(source, 'rb') as f:
            return base64.b64encode(f.read())


def fillstring(source, length, fill='*', loc=1):
    if loc:
        return fill * (length -len(source)) + source
    else:
        return source + fill * (length -len(source))


def findstring(source, target, index):
    _ = source[index:].find(target)
    return _ + index + 1 if _ > 0 else 0  # TODO(uncertain)


def getasc(character, delimiter='-'):
    return delimiter.join((str(ord(_)) for _ in list(character)))


def getchr(ascii, delimiter='-'):
    ascii = str(ascii)
    return delimiter.join(chr(int(_)) for _ in ascii.split(delimiter))


def getpartofstring(source, _, mode):
    def getpartofstring1(source, _, mode):
        m = re.split(_, source)
        if mode == 'left' or mode == 'first':
            return m[0]
        elif mode == 'right':
            return m[1:]
        elif mode == 'count':
            return len(m) - 1
        elif mode == 'last':
            return m[-1]
        else:
            try:
                int(mode)
            except ValueError:
                raise ValueError('Part should be an integer.')
            else:
                return m[int(mode)]

    def getpartofstring2(source, start, length):
        return source[start - 1:start + int(length) -1]

    def getpartofstring3(souce, _, mode):
        if mode == 'binding':
            print('3 binding on')  # TODO(suyako)
        elif mode == 'datasource':
            print('3 datasource on')  # TODO(suyako)
        else:
            raise ValueError('Check mode in UCC.')

    if mode.lower() in ['left', 'right', 'count', 'first', 'last']:
        return getpartofstring1(source, _, mode.lower())
    elif mode.lower() in ['binding', 'datasource']:
        return getpartofstring3(source, _, mode.lower())
    else:
        if isinstance(_, str):
            return getpartofstring1(source, _, mode.lower())
        elif isinstance(_, int):
            return getpartofstring2(source, _, mode.lower())
        else:
            raise ValueError('Parameters error in GetPartOfString.')


def hash(type, mode, source):
    def getMd5(type, source):
        m = md5()
        if type.lower() == 'file':
            with open(source, 'rb') as f:
                m.update(f.read())
        elif type.lower() == 'string':
            m.update(source.encode())
        else:
            raise ValueError('Only file or string is accepted.')
        return m.hexdigest().upper()

    def getSha1(type, source):
        m = sha1()
        if type.lower() == 'file':
            with open(source, 'rb') as f:
                m.update(f.read())
        elif type.lower() == 'string':
            m.update(source.encode())
        else:
            raise ValueError('Only file or string is accepted.')
        return m.hexdigest().upper()

    def getCrc32(type, source):
        if type.lower() == 'file':
            with open(source, 'rb') as f:
               return hex(crc32(f.read())).lstrip('0x').upper()
        elif type.lower() == 'string':
            return hex(crc32(source.encode())).lstrip('0x').upper()
        else:
            raise ValueError('Only file or string is accepted.')

    if mode.lower() == 'md5':
        return getMd5(type, source)
    elif mode.lower() == 'sha1':
        return getSha1(type, source)
    elif mode.lower() == 'crc32':
        return getCrc32(type, source)
    else:
        raise ValueError('Check mode in UCC.')


def lengthofstring(mode, source):
    if mode.lower() == 'single':
        return len(source)
    elif mode.lower() == 'double':
        return len(source) * 2
    elif mode.lower() == 'mix':
        return len(source.encode('gbk'))
    else:
        raise ValueError('Check mode in UCC.')
# </editor-fold>


# ======================================================================================================================
# File functions library
# ======================================================================================================================
# <editor-fold desc="File functions library.">
def my_dir(source):
    try:
        f = open(source)
    except FileNotFoundError:
        return False
    else:
        f.close()
        return True


# TODO(suyako): 文件夹的复制操作还要再看
def filecopy(target, source):
    with open(target, 'w') as f1:
        with open(source) as f2:
            for _ in f2:
                f1.writelines(_)


def fileinfo(source, *param):
    target_info = param[0]
    information = os.stat(source)
    size = information.st_size
    create = time.strftime('%Y/%m/%d %X', time.localtime(information.st_ctime))
    modify = time.strftime('%Y/%m/%d %X', time.localtime(information.st_mtime))
    access = time.strftime('%Y/%m/%d %X', time.localtime(information.st_atime))
    if isinstance(target_info, str):
        if target_info.lower() == 'size':
            return size
        elif target_info.lower() == 'datecreated':
            return create
        elif target_info.lower() == 'datelastmodified':
            return modify
        elif target_info.lower() == 'datelastaccessed':
            return access
        else:
            raise ValueError('Source file have no {0} property.'.format(target_info))
    else:
        infos = [size, create, modify, access]
        for i, _ in enumerate(param):
            _ = infos[i]  # TODO(suyako): 之后还要进行测试


def filemove(target, source):
    with open(target, 'w') as f1:
        with open(source, 'r') as f2:
            for _ in f2:
                f1.writelines(_)
    os.remove(source)


def fileread(source):
    with open(source) as f:
        return f.read()


def filewrite(source, mode, content):
    if not mode:
        mode = 'w'
    elif mode == 1:
        mode = 'a'
    else:
        raise ValueError('Mode Error.')
    with open(source, mode) as f:
        f.writelines(content)
        f.writelines('\n')
    return
# </editor-fold>


if __name__ == '__main__':
    # print(getpartofstring('abcd',2,'2'))
    Tree1 = Tree()
    # Tree1.append('TREE', '', 'ROOT', '中国', 'TreeView.ico')
    # Tree1.append('TREE', 'ROOT', 'C1', '北京', 'TreeView.ico')
    # Tree1.append('TREE', 'ROOT', 'C2', '上海', 'TreeView.ico')
    # Tree1.append('TREE', 'C1', 'C11', '海淀区', 'TreeView.ico')
    # Tree1.append('TREE', 'C2', 'C21', '静安区', 'TreeView.ico')
    # print(Tree1)
    # print(Tree.get(Tree1, 'ID', 'ALL', 'ROOT'))
    DB = db('Access', 'D:\Designer For UCC\Data\PMS2016.mdb', '', 'SQL SELECT * FROM t1100工作包')
    Tree1.bind(DB, 'ROOT', '上级工作包ID', 'ID', '工作包名称', 'FieldOfImage')
    print(Tree1)