import re

LOGICAL_OPERATION_COMPILE = re.compile('([<>=][=>]?)')
LOOP_COMPILE = re.compile('[,=]')

OPERATION_CONVERTION_TABLE = {
    '+': '+', '-': '-', '*': '*', '/': '/', 'mod': '%'
}

DEFAULT_PROPERTY = {'Label1': 'Caption'}
# OBJECT_PYCLASS = {
#     'LED1': 'LED', 'LED2': 'LED', 'LED3': 'LED', 'LED4': 'LED',
# }
#
# OBJECT_PYMETHOD = {
#     'LED': {
#         'value': {'py_method': 'intensity', '0': '0', '1': '255'},
#     },
# }



# 左值为UCC对象的属性时的处理
# def object_ucc_to_py(left, right):
#     [name, property] = re.split('\.', left)  # 先拆分为UCC对象及属性名称
#     value = right
#     pyname = name.strip('@')  # 获取UCC对象在python中对应的对象，这里默认两者是相同的，只是有无@
#     pyclass = OBJECT_PYCLASS[pyname]  # 获取对象所属的类
#     pymethod = OBJECT_PYMETHOD[pyclass][property]['py_method']  # 属性所对应的方法
#     pyvalue = OBJECT_PYMETHOD[pyclass][property][value]  # 属性值对应的值
#     return pyname, pymethod, pyvalue

# 对逻辑语句进行加工
# def process_logical(logical_sentence):
#     sentence = logical_sentence.strip()
#     # 先通过逻辑运算符号对逻辑语句切割，分为左值，逻辑运算符，右值三个部分
#     [left, logical_operation, right] = re.split(LOGICAL_OPERATION_COMPILE, sentence)
#     # 如果左值为UCC对象的属性，要先在python中找到对应的对象，获取其私有属性须通过该对象的方法
#     if '.' in left:  # 如果左值为UCC对象的属性
#         object_pyname, object_pymethod, object_pyvalue = object_ucc_to_py(left, right)
#         return ''.join([object_pyname, '.', object_pymethod, '()', logical_operation, object_pyvalue])
#     else:
#         return ''.join([left, logical_operation, right]).strip('@')


# 对VarName及Value(包括TrueValue及FalseValue)进行预处理
# def process_val(val_sentence):
#     sentence = val_sentence.strip()
#     # try:
#     #     [left, operation, right] = re.split('(=)', sentence)  # 通过运算符号进行切割
#     # except:
#     #         return sentence.strip('@')  # 没有运算符时只做去掉@处理
#     if '.' in left:
#         object_pyname, object_pymethod, object_pyvalue = object_ucc_to_py(left, right)
#         return ''.join([object_pyname, '.', object_pymethod, '({0})'.format(object_pyvalue)])  # 赋值方法
#     else:
#         return ''.join([left, operation, right]).strip('@')

def process_word(val_sentence, fundicts):
    sentence = val_sentence.strip()
    if '@' in sentence or '.' in sentence:  # ucc代码中在提取属性值时，若属性值为字符串，可能会存在'@object.property'这种形式，在转换为python时需要去掉引号
        sentence = re.sub('[\'\"]', '', sentence)
    sentence = sentence.strip('@')
    if sentence in fundicts.keys():
        return sentence + '()'
    else:
        return sentence


# 从UCC转换到python的类，从该类出发构造多个转换方法的实例
class UCC_TO_PY(object):
    '''
    define a class describe the common method to convert UCC to python.
    '''
    def __init__(self, grammer, params, compile=re.compile('[=,]'), compile_method='split', maxsplit=0):
        self.py_grammer = grammer  # 该转换实例的python语法
        self.params = params  # 该转换实例的参数表
        self.compile = compile  # 对UCC语句进行处理时用到的正则表达式
        self.compile_method = compile_method  # 正则处理方法
        self.maxsplit = maxsplit  # 最大切割次数

    # 由事先定义好的正则表达式对将要处理的语句进行切割，切割后得到的value值一一对应于定义好的params中的key值
    def get_values_of_params(self, sentence):
        if self.compile_method == 'split':
            return re.split(self.compile, sentence.strip(), self.maxsplit)
        elif self.compile_method == 'match':
            return re.match(self.compile, sentence.strip()).groups()
        else:
            raise ValueError('Regex method error: must be split or match.')

    # 将得到的value值赋给params
    def map_value_to_key(self, sentence, fundicts):
        '''
        :param sentence: UCC语句
        :param fundicts: 存储函数名的字典
        :return:
        '''
        values = self.get_values_of_params(sentence)  # 正则处理
        for i, _ in enumerate(self.params.keys()):
            try:
                value = values[i]
            except IndexError:
                pass
            else:
                if value:
                    self.params[_] = value.strip()  # 如果value不为空则覆盖原先params中的值
                else:
                    pass  # 如果value为空则跳过，对UCC语句中函数有默认值的应该在params中预先给定
            # assert self.params[_] is not None, 'Params Error! Check UCC and params.'  # 最后得到的params不应该有None值

    # 对params中的value进一步加工处理
    def process(self, fundicts):
        for _ in self.params.keys():
            if _ == 'TimeValue':
                try:
                    float(self.params[_])  # 时间值可能为某个属性值或者一个数字，对其进行分类处理
                except ValueError:
                    value = self.params[_].strip('@') + ' / 1000'
                else:
                    value = float(self.params[_]) / 1000
                self.params[_] = value
            elif _ == 'End':
                self.params[_] = int(self.params[_]) + 1  # UCC中的end值与python中的end值不对应
            elif _ == 'Operation':
                self.params[_] = OPERATION_CONVERTION_TABLE[self.params[_]]  # 加减乘除等符号运算对应关系
            elif _ == 'Property':
                if self.params[_]:
                    pass
                else:
                    self.params[_] = DEFAULT_PROPERTY[self.params['Object']]
            elif _ == 'Mode' or _ == 'Type':
                self.params[_] = "'" + self.params[_] + "'"
            elif 'Block' in _:
                if ':' in self.params[_]:
                    [command, sentence] = re.split(':', self.params[_])
                    self.params[_] = COMMAND_MAPPING_PYFUNCTION[command.strip().lower()].py_sentence(sentence, fundicts)
                else:
                    self.params[_] = process_word(self.params[_], fundicts)
            else:
                self.params[_] = process_word(self.params[_], fundicts)
            assert self.params[_] is not None, 'Params Error! Check UCC and params.'  # 最后得到的params不应该有None值

    # 得到最终该UCC语句的python形式
    def py_sentence(self, sentence, fundicts={}):
        '''
        所有函数转换实例最后都只调用该方法来处理语句
        :param sentence: 待处理的UCC语句
        :param fundicts: 存储函数名的字典，用来构造最后的括号
        :return: 最终转换得到的python语句
        '''
        self.map_value_to_key(sentence, fundicts)
        self.process(fundicts)
        return self.py_grammer.format(**self.params)

# ======================================================================================================================
# System functions
# ======================================================================================================================
SLEEP = UCC_TO_PY(
    grammer='time.sleep({TimeValue})',
    params={'TimeValue': None},
    compile=re.compile('\s+')
)

# ======================================================================================================================
# Logic functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse Logic module in UCC.">
CASE = UCC_TO_PY(
    grammer='{TrueBlock} if {LogicalPara} else {FalseBlock}',
    params={'LogicalPara': None, 'TrueBlock': None, 'FalseBlock': 'None'},
    compile=re.compile('Then|Else')
)

FOR = UCC_TO_PY(
    grammer='\n'.join(['for {VarName} in range({Start}, {End}, {Step}):', ' ' * 4 + '{Block}']),
    params={'VarName': 'i', 'Start': None, 'End': None, 'Step': '1', 'Block': None},
    compile=re.compile('(\w*)[\s,]*(\d+)[\s,]*(\d+)[\s,]*(\d*)[\s=]*(.+)'),
    compile_method='match'
)

IF = UCC_TO_PY(
    grammer='{VarName} {Equals} {True} if {Left} {LogicalOperation} {Right} else {False}',
    params={'VarName': None, 'Equals': None, 'Left': None, 'LogicalOperation': None, 'Right': None, 'Then': None,
            'True': None, 'Else': None, 'False': None},
    compile=re.compile('([<>=][>=]?|Then|Else)')
)

# TODO(suyako): ExitAction

RUNACTION = UCC_TO_PY(
    grammer='{Sentence}',
    params={'Sentence': None},
    compile=re.compile('(.+)'),
    compile_method='match'
)
# </editor-fold>

# ======================================================================================================================
# Object functions
# ======================================================================================================================
SET = UCC_TO_PY(
    grammer='{Object}.{Property} = {Value}',
    params={'Object': None, 'Property': None, 'Value': None},
    compile=re.compile('(\w+)\.?(\w*)\s*=(.+)'),
    compile_method='match'
)

# ======================================================================================================================
# Data functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse data module in UCC.">
CALC = UCC_TO_PY(
    grammer='{VarName} {Equals} {Left} {Operation} {Right}',
    params={'VarName': None, 'Equals': None, 'Left': None, 'Operation': None, 'Right': None},
    compile=re.compile('([\*=+/]|mod)')
)

JSON = UCC_TO_PY(
    grammer='{VarName} = my_json({Mode}, {Param2}, {Source})',
    params={'VarName': None, 'Mode': None, 'Param2': None, 'Source': None},
    maxsplit=3,
)
# </editor-fold>

# ======================================================================================================================
# String functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse string module in UCC.">
CONVERT = UCC_TO_PY(
    grammer='{VarName} = convert({Param1}, {Param2}, {Param3})',
    params={'VarName': None, 'Param1': None, 'Param2': None, 'Param3': None},
)

# TODO(suyako): Decode
# TODO(suyako): Encode

FILLSTRING = UCC_TO_PY(
    grammer='{VarName} = fillstring({Param1}, {Param2}, {Param3}, {Param4})',
    params={'VarName': None, 'Param1': None, 'Param2': None, 'Param3': '*', 'Param4': '0'},
)

FINDSTRING = UCC_TO_PY(
    grammer='{VarName} = findstring({Param1}, {Param2}, {Param3})',
    params={'VarName': None, 'Param1': None, 'Param2': None, 'Param3': None},
)

GETASC = UCC_TO_PY(
    grammer='{VarName} = getasc({Param1}, {Param2})',
    params={'VarName': None, 'Param1': None, 'Param2': '-'},
)

GETCHR = UCC_TO_PY(
    grammer='{VarName} = getchr({Param1}, {Param2})',
    params={'VarName': None, 'Param1': None, 'Param2': '-'},
)

GETPARTOFSTRING = UCC_TO_PY(
    grammer='{VarName} = getpartofstring({Param1}, {Param2}, {Mode})',
    params={'VarName': None, 'Param1': None, 'Param2': None, 'Mode': None},
)

HASH = UCC_TO_PY(
    grammer='{VarName} = hash({Type}, {Mode}, {Param3})',
    params={'VarName': None, 'Type': None, 'Mode': None, 'Param3': None},
)

INSERTSTRING = UCC_TO_PY(
    grammer='{VarName} = {Source}[:{Index}] + {Target} + {Source}[{Index}:]',
    params={'VarName':None, 'Source': None, 'Target': None, 'Index': None},
)

LENGTHOFSTRING = UCC_TO_PY(
    grammer='{VarName} = lengthofstring({Mode},{Source})',
    params={'VarName': None, 'Mode': None, 'Source': None},
)

LINKSTRING = UCC_TO_PY(
    grammer='{VarName} = {Delimiter}.join([{Source}])',
    params={'VarName': None, 'Delimiter': None, 'Source': None},
    maxsplit=2
)

REPLACE = UCC_TO_PY(
    grammer='{VarName} = re.sub({Pattern}, {Repl}, {Source})',
    params={'VarName': None, 'Source': None, 'Pattern': None, 'Repl': None},
)
# </editor-fold>

# ======================================================================================================================
# File functions
# ======================================================================================================================
DIR = UCC_TO_PY(
    grammer='{VarName} = dir({Source})',
    params={'VarName': None, 'Source': None},
)

# ======================================================================================================================
# Mapping
# ======================================================================================================================
COMMAND_MAPPING_PYFUNCTION = {
    'calc': CALC,
    'sleep': SLEEP,
    'if': IF,
    'for': FOR,
    'runaction': RUNACTION,
    'case': CASE,
    'set': SET,
    'convert': CONVERT,
    'fillstring': FILLSTRING,
}

if __name__ == '__main__':
    # print(CALC.py_sentence('temp=@i mod 4'))
    # print(SLEEP.py_sentence('  1000  '))
    # print(FOR.py_sentence('i,1,4=RunAction: i = 1'))
    # print(CASE.py_sentence('@i==1 Then RunAction:LED1_toggle', {'LED1_toggle': None}))
    # print(IF.py_sentence('LED1.value= LED1.value==1 Then 0 Else 1'))
    # print(SET.py_sentence("Label1='Hello World'"))
    # print(FILLSTRING.py_sentence("txt结果.Text='@txt源字符串.Text',@txt目标长度.Text,'@txt填充字符.Text'"))
    # print(INSERTSTRING.py_sentence("var = 'abde', 'c', 2"))
    # print(HASH.py_sentence("var = STRING,MD5,'上海陆家嘴'"))
    # print(LENGTHOFSTRING.py_sentence("txtCountSingle=SINGLE,txt文字"))
    # print(LINKSTRING.py_sentence("var = '_','1982','01','10'"))
    # print(REPLACE.py_sentence("Text2.text=Text1.text,'h','*'"))
    print(GETPARTOFSTRING.py_sentence("var = 'abcd', 2, 2"))