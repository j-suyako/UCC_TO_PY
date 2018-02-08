import re
import time
from lxml import etree
import convertion_class


# 由ucc的函数名映射需要用到的转换函数
COMMAND_MAPPING_PYFUNCTION = convertion_class.COMMAND_MAPPING_PYFUNCTION


# 编译待解析符号
semicolon_compile = re.compile(';')  # 分号编译
comments_compile = re.compile('--')  # UCC注释符号编译
# hashtag_compile = re.compile('#')  # python注释符号编译

class UCC_to_python(object):

    def __init__(self, path):
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
        for _ in self.myhead.keys():
            self.head.append('import {0}'.format(_))

    # 变量字典处理函数
    def process_vardict(self):
        for e in self.myvars.keys():
            self.define.append('global {0}\n{0} = {1}'.format(e, self.myvars[e]))

    # 函数字典处理函数
    def process_fundict(self, indent=1):
        for e in self.myfuns.keys():
            head = 'def {0}():'.format(e)
            body = '\n'.join(map(lambda x: '    ' * indent + x, self.myfuns[e]))
            self.define.append('\n'.join([head, body]))

    # 函数处理函数
    def process_fun(self, fun_body):
        sentences_in_py = []  # 所有函数语句的python形式
        for sentence in fun_body:
            sentence = sentence.strip()
            if re.match(comments_compile, sentence) is not None:  # 如果该语句为注释行
                sentences_in_py.append(re.sub(comments_compile, '# ', sentence))  # 用#替换--
            else:
                module_function_name, private_sentece = sentence.split(':', 1)  # 函数名称用于得到所需要的映射函数
                # 映射函数对语句进行处理
                sentences_in_py.append(COMMAND_MAPPING_PYFUNCTION[module_function_name.lower()].py_sentence(
                    private_sentece, self.myfuns)
                )
        return sentences_in_py

    # 变量处理函数
    def process_var(self, var_value):
        return var_value

    # 将变量及函数分别存入变量及函数字典，之后压入定义栈
    def push_Vars(self):
        Vars = self.tree.xpath('//Var')
        # 先将所有变量及函数名存入字典
        for Var in Vars:
            name_of_var_or_fun = Var.xpath('@ID')[0].strip()
            value_of_var_or_fun = Var.xpath('@Value')[0]
            if re.search(semicolon_compile, value_of_var_or_fun) is None:
                self.myvars.setdefault(name_of_var_or_fun, None)
            else:
                self.myfuns.setdefault(name_of_var_or_fun, None)
        # 对变量及函数进行处理
        for Var in Vars:
            name_of_var_or_fun = Var.xpath('@ID')[0].strip()  # 提取变量或函数名称
            value_of_var_or_fun = Var.xpath('@Value')[0]  # 提取变量或函数值，对于函数，其value即为函数语句
            if re.search(semicolon_compile, value_of_var_or_fun) is None:  # 如果找不到分号，则认为是变量，后期需要改进
                self.myvars[name_of_var_or_fun] = self.process_var(value_of_var_or_fun)  # 将变量名及变量值分到变量字典
            else:
                function_body = value_of_var_or_fun.split(';')[:-1]  # 提取该函数所有语句
                self.myfuns[name_of_var_or_fun] = self.process_fun(function_body)
        self.process_vardict()
        self.process_fundict()

    # 将主体语句压入主体栈
    def push_Script(self):
        Script = self.tree.xpath('//Control[@ID="script"]')  # 提取主体语句
        function_body = Script[0].xpath('@Action')[0].split(';')[:-1]
        self.scripts = self.process_fun(function_body)

    # 文件输出
    def file_output(self, filename):
        self.push_Vars()
        self.push_Script()
        with open(filename, 'w') as f:
            f.writelines('\n'.join(self.head))
            f.writelines('\n')
            f.writelines('\n'.join(self.define))
            f.writelines('\n')
            f.writelines('\n'.join(self.scripts))

    def test(self):
        self.push_Vars()
        self.push_Script()
        print('\n'.join(self.head))
        print('\n'.join(self.define))
        print()
        print('\n'.join(self.scripts))


if __name__ == '__main__':
    LED_convertion = UCC_to_python(r'C:\Users\JXT\Desktop\UCC文件及转换\LED_long_circulation.ucc')
    LED_convertion.test()
    # LED_convertion.file_output(r'C:\Users\JXT\Desktop\UCC文件及转换\LED_long_circulation.py')