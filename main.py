import re
import time
from lxml import etree
import os
import win32api
from grammar import Ucc2PyGrammar, COMMAND_MAPPING_PYFUNCTION
from Settings import ENVIRONMENT, semicolon_compile, comments_compile


class Ucc2Py(object):
    """
    处理UCC文件
    """
    def __init__(self, path):
        """
        :param path: UCC文件路径
        """
        self.mycops = {}  # 组件字典
        self.myvars = {}  # 变量字典
        self.myfuns = {}  # 函数字典
        self.myhead = {}  # 头部字典
        self.head = ['# main.py -- put your code here!', 'from ucc_library import *',
                     'import time', ]  # 文件头部分（引入模块）
        self.define = []  # 文件定义部分，包括函数及变量的定义
        self.scripts = []  # 文件主体部分
        self.path = path  # 待读取的UCC文件路径
        self.tree = etree.parse(path)  # 该UCC文件的xml树

    def process_headdict(self):
        """
        对头部字典处理成import形式
        """
        for _ in self.myhead:
            self.head.append('import {0}'.format(_))

    def process_copdict(self):
        """
        对组件字典进行处理
        """
        for _ in self.mycops:
            self.define.append('{0} = {1}'.format(_, self.mycops[_]))

    def process_vardict(self):
        """
        对变量字典进行处理，由于UCC基本为全局变量，这里加上global声明
        """
        for _ in self.myvars:
            self.define.append('global {0}\n{0} = {1}'.format(_, self.myvars[_] if self.myvars[_] else 0))

    # 函数字典处理函数
    def process_fundict(self, indent=1):
        """
        对函数字典进行处理
        :param indent: 缩进量
        """
        for _ in self.myfuns:
            head = 'def {0}():'.format(_)
            body = '\n'.join(map(lambda x: '    ' * indent + x, self.myfuns[_]))
            self.define.append('\n'.join([head, body]))

    def process_cop(self, Type, ID, Title, Action, Value):
        if Action:
            self.myfuns['click_'+ID] = self.process_fun(Action.split(';')[:-1])
        ID = "'" + ID + "'"
        Title = "'" + Title + "'"
        Value = "'" + Value + "'"
        return '{0}({1}, {2}, {3})'.format(Type, ID, Title, Value)

    @staticmethod
    def process_fun(fun_body):
        """
        函数处理函数
        :param fun_body: 组件中的action
        """
        sentences_in_py = []  # 所有函数语句的python形式
        for sentence in fun_body:
            sentence = sentence.strip()
            if re.match(comments_compile, sentence) is not None:  # 如果该语句为注释行
                sentences_in_py.append(re.sub(comments_compile, '# ', sentence))  # 用#替换--
            else:
                module_function_name, private_sentence = sentence.split(':', 1)  # 函数名称用于得到所需要的映射函数
                # 映射函数对语句进行处理
                sentences_in_py.append(COMMAND_MAPPING_PYFUNCTION[module_function_name.lower()].py_sentence(private_sentence))
        return sentences_in_py

    # 变量处理函数
    @staticmethod
    def process_var(var_value):
        return var_value

    # 将组件名存入组件字典，之后赋予Ucc2PyGrammar的组件字典
    def controls2dicts(self):
        controls = self.tree.xpath('//Control')
        # 将所有组件ID存入字典
        for control in controls:
            name_of_control = control.xpath('@ID')[0].strip()
            self.mycops.setdefault(name_of_control, None)
        Ucc2PyGrammar.cop_dicts = self.mycops

    # 对组件进行赋值
    def assign_controls(self):
        controls = self.tree.xpath('//Control')
        # 对变量及函数进行处理
        for control in controls:
            Type = control.xpath('@ShowType')[0]
            ID = control.xpath('@ID')[0].strip()
            Title = control.xpath('@Title')[0].strip()
            Action = control.xpath('@Action')[0].strip()
            Value = control.xpath('@Value')[0].strip()
            self.mycops[ID] = self.process_cop(Type, ID, Title, Action, Value)

    # 将变量及函数名分别存入变量及函数字典，之后赋予Ucc2PyGrammar的变量及函数字典
    def vars2dicts(self):
        my_vars = self.tree.xpath('//Var')
        # 先将所有变量及函数名存入字典
        for var in my_vars:
            name_of_var_or_fun = var.xpath('@ID')[0].strip()
            value_of_var_or_fun = var.xpath('@Value')[0]
            if re.search(semicolon_compile, value_of_var_or_fun) is None:
                self.myvars.setdefault(name_of_var_or_fun, None)
            else:
                self.myfuns.setdefault(name_of_var_or_fun, None)
        Ucc2PyGrammar.var_dicts = self.myvars
        Ucc2PyGrammar.fun_dicts = self.myfuns

    def assign_vars(self):
        my_vars = self.tree.xpath('//Var')
        # 对变量及函数进行处理
        for var in my_vars:
            name_of_var_or_fun = var.xpath('@ID')[0].strip()  # 提取变量或函数名称
            value_of_var_or_fun = var.xpath('@Value')[0]  # 提取变量或函数值，对于函数，其value即为函数语句
            if re.search(semicolon_compile, value_of_var_or_fun) is None:  # 如果找不到分号，则认为是变量，后期需要改进
                self.myvars[name_of_var_or_fun] = self.process_var(value_of_var_or_fun)  # 将变量名及变量值分到变量字典
            else:
                function_body = value_of_var_or_fun.split(';')[:-1]  # 提取该函数所有语句
                self.myfuns[name_of_var_or_fun] = self.process_fun(function_body)

    # 将变量及函数压入定义栈
    def push_vars(self):
        self.controls2dicts()
        self.vars2dicts()
        self.assign_controls()
        self.assign_vars()
        self.process_copdict()
        self.process_vardict()
        self.process_fundict()

    # 将主体语句压入主体栈
    def push_script(self):
        script = self.tree.xpath('//Control[@ID="script"]')  # 提取主体语句
        function_body = script[0].xpath('@Action')[0].split(';')[:-1]
        self.scripts = self.process_fun(function_body)

    # 文件输出
    def file_output(self, filename):
        self.push_vars()
        self.push_script()
        with open(filename, 'w') as f:
            f.writelines('\n'.join(self.head))
            f.writelines('\n')
            f.writelines('\n'.join(self.define))
            f.writelines('\n')
            f.writelines('\n'.join(self.scripts))

    def test(self):
        self.push_vars()
        # self.push_script()
        print('\n'.join(self.head))
        print('\n'.join(self.define))
        print()
        # print('\n'.join(self.scripts))

    def app_version(self):
        return self.tree.xpath('//Project/@version')[0]

    def ucc_version(self):
        info = win32api.GetFileVersionInfo(self.path, os.sep)
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        return '%d.%d.%d.%d' % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls))


if __name__ == '__main__':
    # LED_convertion = Ucc2Py(r'C:\Users\JXT\Desktop\UCC文件及转换\LED_long_circulation.ucc')
    # ENVIRONMENT['app_version'] = LED_convertion.app_version()
    # ENVIRONMENT['ucc_version'] = LED_convertion.ucc_version()
    # LED_convertion.test()
    # LED_convertion.file_output(r'C:\Users\JXT\Desktop\UCC文件及转换\LED_long_circulation.py')
    test = Ucc2Py(r'D:\Designer For UCC\Demos\Demo_GetPartOfString.ucc')
    test.test()