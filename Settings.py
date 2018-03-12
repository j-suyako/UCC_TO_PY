import logging
import re

# 环境变量（包括System模块中用到的剪贴板内容也会放到这里），其中第一个数值为APP版本号，第二个数值为UCC版本号
ENVIRONMENT = {'app_version': 0, 'ucc_version': 0, 'clipboard': None}

# 用于分割逻辑运算符
LOGICAL_OPERATION_COMPILE = re.compile('([<>=][=>]?)')

# 编译待解析符号
semicolon_compile = re.compile(';')  # 分号编译
comments_compile = re.compile('--')  # UCC注释符号编译

# 对于所有UCC语句，消除其中的所有空格，@，单双引号
# 之所以要消除引号是因为会有'@Object.property'的情况，这种情况下引号是无用的，对于参数实际为字符串的情况，会首先对参数类型
# 进行判断，只要参数不与变量、类及函数重名，即认为参数是字符串
PRE_PROCESS_COMPILE = re.compile('[@\'\"]')

# UCC运算符对应的python运算符
OPERATION_CONVERSION_TABLE = {
    '+': '+', '-': '-', '*': '*', '/': '/', '\\': '//', '^': '**', 'mod': '%', '==': '==', '=': '=', 'None': 'None'
}

# 已有的class类名称
CLASS_NAME = ['Label', 'TextBox', 'Image', 'CommandButton', 'Menu', 'ComboBox', 'ListBox', 'CheckBox',
              'OptionButton', 'Timer', 'Report', 'Tree']