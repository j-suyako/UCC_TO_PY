import re

from Settings import OPERATION_CONVERSION_TABLE, CLASS_NAME, PRE_PROCESS_COMPILE


class Ucc2PyGrammar(object):
    """
    define a class describe the general method to convert UCC to python.
    """
    cop_dicts = {}  # 组件字典
    fun_dicts = {}  # 函数字典
    var_dicts = {}  # 变量字典
    def __init__(self, funname=None, grammar=None, params={}, compile=re.compile('[=,]'), compile_method='split',
                 maxsplit=0, method_type=1):
        """
        对每个转换实例构造一个转换方法，具体是通过grammar和params来实现，grammar为对应的python语法，对应最普通的情况，
        如 {Left} = myfun({Param1}, {Param2})，构建key值为(Left, Param1, Param2)的字典，每个关键字的value通过对原UCC语句
        的正则处理得到，之后将得到的字典再赋予grammar即可。
        实例的初始化需要注意以下几个方面，对于大多数函数，只要对funname进行赋值即可，grammar和params会自动获取，之后再编写
        funname的函数，对于一些特殊的情况（如if,case等各类逻辑函数），需要自行对grammar赋值，params中如果key值顺序与grammar
        一致，可不进行赋值，如果不一致则需要赋值。
        :param funname: 该转换实例用到的函数名称
        :param grammar: 该转换实例的python语法
        :param params: 该转换实例的参数表
        :param compile: 对UCC语句进行处理时用到的正则表达式
        :param compile_method: 正则处理方法
        :param maxsplit: 最大切割次数
        :param method_type: 方法所属类型，1为有返回值方法，0为无返回值方法，-1为类方法
        """
        self.funname = funname
        self.py_grammar = grammar
        self.params = params
        self.compile = compile
        self.compile_method = compile_method
        self.maxsplit = maxsplit
        self.method_type = method_type

    def get_values_of_params(self, sentence):
        """
        由事先定义好的正则表达式对将要处理的语句进行切割，切割后得到的value值一一对应于定义好的params中的key值
        :param sentence: 待处理语句
        :return: 正则处理后的语句，类型为列表
        """
        if self.compile_method == 'split':
            return re.split(self.compile, sentence, self.maxsplit)
        elif self.compile_method == 'match':
            return re.match(self.compile, sentence).groups()
        else:
            raise ValueError('Regex method error: must be split or match.')

    def map_value_to_key(self, sentence):
        """
        将得到的value值赋给params
        :param sentence: UCC语句
        """
        values = self.get_values_of_params(sentence)  # 正则处理
        for i, _ in enumerate(self.params):
            try:
                value = values[i]
            except IndexError:
                pass
            else:
                if value:
                    self.params[_] = value.strip()  # 如果value不为空则覆盖原先params中的值
                else:
                    pass  # 如果value为空则跳过，对UCC语句中函数有默认值的应该在params中预先给定

    def process(self):
        """
        对params中的value进一步加工处理
        """
        length = len(self.params)
        for i, _ in enumerate(self.params):
            # 等号左边不处理
            if 'Left' in _:
                pass
            # 对函数参数用process_param处理
            elif 'Param' in _:
                self.params[_] = Ucc2PyGrammar.process_param(self.params[_])
            # 对于分割符号因为常常与计算符重叠，因此特意专门增加了一个类别
            elif 'Delimiter' in _:
                self.params[_] = "'" + self.params[_] + "'"
            elif 'Block' in _:
                if ':' in self.params[_]:
                    [command, sentence] = re.split(':', self.params[_])
                    self.params[_] = COMMAND_MAPPING_PYFUNCTION[command.lower()].py_sentence(sentence)
                else:
                    self.params[_] = ' '.join([Ucc2PyGrammar.process_param(e) for e in re.split('([^\w\.]+|mod)',
                                                                                                self.params[_])])
            else:
                self.params[_] = Ucc2PyGrammar.process_param(self.params[_])
            # assert self.params[_] is not None, 'Params Error! Check UCC and params.'  # 最后得到的params不应该有None值

    # 得到最终该UCC语句的python形式
    def py_sentence(self, sentence):
        """
        所有函数转换实例最后都只调用该方法来处理语句
        :param sentence: 待处理的UCC语句
        :return: 最终转换得到的python语句
        """
        flag1 = 0  # 用来清除py_grammer
        flag2 = 0  # 用来清除params
        if not self.py_grammar:
            length = self.maxsplit + 1 if self.maxsplit else len(re.split(self.compile, sentence))
            param_list = '{Param1}'
            for i in range(2, length):
                param_list = ', '.join([param_list, '{Param%d}' % i])
            # 有返回值函数，类函数，无返回值函数
            if self.method_type == 1:
                self.py_grammar = '{Left} = ' + self.funname + '(%s)' % param_list
            elif self.method_type == -1:
                self.py_grammar = '{Left}.' + self.funname + '(%s)' % param_list
            else:
                self.py_grammar = self.funname + '(%s, {Param%d})' % (param_list, length)
            # 表示py_grammar最开始为None, 需要在下次转换之前清楚已生成的py_grammar
            flag1 = 1
        if not self.params:
            for _ in re.findall('{(\w+)}', self.py_grammar):
                self.params.setdefault(_, None)
            flag2 = 1
        sentence = Ucc2PyGrammar.pre_process(sentence)
        self.map_value_to_key(sentence)
        self.process()
        py = self.py_grammar.format(**self.params)
        if flag1:
            self.py_grammar = None
        if flag2:
            self.params.clear()
        return py

    @staticmethod
    def isobject(word):
        left = word.split('.')[0]
        if left in Ucc2PyGrammar.cop_dicts:
            return True
        else:
            return False

    @staticmethod
    def process_param(word):
        if not word:
            return "''"
        elif word in Ucc2PyGrammar.var_dicts:
            return word
        elif word in Ucc2PyGrammar.fun_dicts:
            return word + '()'
        elif Ucc2PyGrammar.isobject(word):
            index = word.find('.')
            if index < 0:
                return word
            else:
                return word[:index] + '.' + word[index+1:].lower().capitalize()
        elif word.isdigit():
            return word
        elif word in OPERATION_CONVERSION_TABLE:
            return OPERATION_CONVERSION_TABLE[word]
        elif word in CLASS_NAME:
            return word
        else:
            return "'" + word + "'"

    @staticmethod
    def process_left(word):
        if not word:
            raise ValueError()
        elif Ucc2PyGrammar.isobject(word):
            try:
                my_object, my_property = word.split('.')
            except ValueError:
                return word, 'default_property'
            else:
                return my_object, my_property
        else:
            return word

    # TODO(suyako): 再仔细考虑字符串的影响
    @staticmethod
    def pre_process(sentence):
        return re.sub(PRE_PROCESS_COMPILE, '', sentence)

# ======================================================================================================================
# System functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse System module in UCC.">

# colorbrowse，涉及到UI不进行设计


CLIPBOARD = Ucc2PyGrammar(funname='clipboard')

EXIT = Ucc2PyGrammar(grammar='sys.exit()')

# getcursorpos，涉及到UI不进行设计

GETDATEADD = Ucc2PyGrammar(funname='getdateadd')

GETDATETIME = Ucc2PyGrammar(funname='getdatetime')

GETDATEDIFF = Ucc2PyGrammar(funname='getdatediff')

GETVERSION = Ucc2PyGrammar(funname='getversion')

GETIP = Ucc2PyGrammar(grammar='{Left} = socket.gethostbyname_ex(socket.gethostname())[2][2]')

GETHOST = Ucc2PyGrammar(grammar='{Left} = socket.gethostbyaddr({Param})[0]')

# TODO(suyako): Message

RUN = Ucc2PyGrammar(grammar='run({Param})')

STOP = Ucc2PyGrammar(grammar='os.popen("taskkill.exe /pid:{Param}")')

SLEEP = Ucc2PyGrammar(grammar='pyb.delay({Param})')

# TODO(suyako): FreeCPU
# </editor-fold>


# ======================================================================================================================
# UI functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse Logic module in UCC.">
HIDECONTROL = Ucc2PyGrammar(grammar='pass')

SHOWCONTROL = Ucc2PyGrammar(grammar='pass')
# </editor-fold>


# ======================================================================================================================
# Logic functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse Logic module in UCC.">
CASE = Ucc2PyGrammar(
    grammar='{TrueBlock} if {LogicalBlock} else {FalseBlock}',
    params={'LogicalBlock': None, 'TrueBlock': None, 'FalseBlock': 'None'},
    compile=re.compile('Then|Else')
)

FOR = Ucc2PyGrammar(
    grammar='\n'.join(['for {VarName} in range({Start}, {End}, {Step}):', ' ' * 4 + '{Block}']),
    params={'VarName': 'i', 'Start': None, 'End': None, 'Step': '1', 'Block': None},
    compile=re.compile('(\w*)[\s,]*(\d+)[\s,]*(\d+)[\s,]*(\d*)[\s=]*(.+)'),
    compile_method='match'
)

IF = Ucc2PyGrammar(
    grammar='{Left1} {Equals} {True} if {Left2} {Operation} {Right} else {False}',
    params={'Left1': None, 'Equals': None, 'Left2': None, 'Operation': None, 'Right': None, 'Then': None,
            'True': None, 'Else': None, 'False': None},
    compile=re.compile('([<>=][>=]?|Then|Else)')
)

# TODO(suyako): ExitAction

RUNACTION = Ucc2PyGrammar(
    grammar='{Block}',
    compile=re.compile('(.+)'),
    compile_method='match'
)
# </editor-fold>


# ======================================================================================================================
# Object functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse Object module in UCC.">
APPEND = Ucc2PyGrammar(funname='append', method_type=-1)

# TODO(suyako): App

# TODO(suyako): Call

CLEAR = Ucc2PyGrammar(funname='clear', method_type=0)

CLONE = Ucc2PyGrammar(funname='clone', method_type=0)

# Move，涉及到UI不设计

NEW = Ucc2PyGrammar(funname='new')

REMOVE = Ucc2PyGrammar(funname='remove', method_type=-1)

REPORTGET = Ucc2PyGrammar(funname='Report.get')

REPORTSET = Ucc2PyGrammar(funname='set', method_type=-1)

SET = Ucc2PyGrammar(grammar='{Left} = {Param}')

TREEGET = Ucc2PyGrammar(funname='Tree.get')

TREESET = Ucc2PyGrammar(funname='set', method_type=-1)
# </editor-fold>


# ======================================================================================================================
# Data functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse data module in UCC.">
# TODO(suyako): 还没对所有该有bind函数的类写完bind函数
BINDINGDATATO = Ucc2PyGrammar(funname='bind', method_type=-1)

CALC = Ucc2PyGrammar(grammar='{Left} = {Block}')

# TODO(suyako): Console，改成记录日志

COUNT = Ucc2PyGrammar(grammar='{Left} = count({Param})')

DB = Ucc2PyGrammar(funname='db')

GETRECORDCOUNT = Ucc2PyGrammar(funname='varDB.count')

GETRANDOMNUMBER = Ucc2PyGrammar(grammar='{Left} = random.randint(0, {Param})')

GETFIELDVALUE = Ucc2PyGrammar(funname='getfieldvalue')

# GetSelectedIndex，涉及到UI不设计

JSON = Ucc2PyGrammar(grammar='{Left} = my_json({Param1}, {Param2}, {Dic})', maxsplit=3)

INPUTBOX = Ucc2PyGrammar(funname='my_input')

# MsgBox，涉及到UI不设计

MATH = Ucc2PyGrammar(funname='my_math')

RETURN = Ucc2PyGrammar(funname='my_return')

WEBSERVICE = Ucc2PyGrammar(funname='webservice')
# </editor-fold>


# ======================================================================================================================
# String functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse string module in UCC.">
CONVERT = Ucc2PyGrammar(funname='convert')

DECODE = Ucc2PyGrammar(funname='mydecode')

ENCODE = Ucc2PyGrammar(funname='myencode')

FILLSTRING = Ucc2PyGrammar(funname='fillstring')

FINDSTRING = Ucc2PyGrammar(funname='findstring')

GETASC = Ucc2PyGrammar(funname='getasc')

GETCHR = Ucc2PyGrammar(funname='getchr')

GETPARTOFSTRING = Ucc2PyGrammar(funname='getpartofstring')

HASH = Ucc2PyGrammar(funname='hash')

INSERTSTRING = Ucc2PyGrammar(
    grammar='{Left} = {Param1}[:{Param3}] + {Param2} + {Param1}[{Param3}:]',
    params={'Left': None, 'Param1': None, 'Param2': None, 'Param3': None},
)

LENGTHOFSTRING = Ucc2PyGrammar(funname='lengthofstring')

LINKSTRING = Ucc2PyGrammar(
    grammar="{Left} = re.sub(',', {Delimiter}, {Param2})",
    maxsplit=2
)

REPLACE = Ucc2PyGrammar(
    grammar='{Left} = re.sub({Param1}, {Delimiter}, {Param3})',
    params={'Left': None, 'Param3': None, 'Param1': None, 'Delimiter': None},
)
# </editor-fold>


# ======================================================================================================================
# File functions
# ======================================================================================================================
# <editor-fold desc="These are instances generated from class UCC_TO_PY to parse File module in UCC.">
DIR = Ucc2PyGrammar(funname='my_dir')

# TODO(suyako): download，需要了解pyboard上关于网络的部分

# decode与encode函数一起放在string里

# TODO(suyako): 文件夹浏览器，无法做到可视化，后期可能会打印出当前文件夹目录然后让用户选择

FILECOPY = Ucc2PyGrammar(funname='filecopy', method_type=0)

FILEDELETE = Ucc2PyGrammar(
    grammar='try:\n    os.remove({Param})\nexcept FileNotFoundError:\n    {Left} = False\nelse:\n    {Left} = True',
    params={'Left': None, 'Param': None},
)

FILEINFO = Ucc2PyGrammar(funname='fileinfo')

FILEMOVE = Ucc2PyGrammar(grammar='filemove({Param1}, {Param2})')

FILERENAME = Ucc2PyGrammar(
    grammar='os.rename({Param2}, {Param1})',
    params={'Param1': None, 'Param2': None},
)

FILEREAD = Ucc2PyGrammar(funname='fileread')

FILEWRITE = Ucc2PyGrammar(funname='filewrite')

# TODO(suyako): FTP，需要看pyboard的网络部分

GETFILENAMEFROMURL = Ucc2PyGrammar(grammar='{Left} = os.path.basename({Param})')

# HASH函数在String中

# TODO(suyako): INIWRITE

# TODO(suyako): INIREAD
# </editor-fold>


# ======================================================================================================================
# Mapping
# ======================================================================================================================
COMMAND_MAPPING_PYFUNCTION = {
    # System
    'clipboard': CLIPBOARD, 'exit': EXIT, 'getdateadd': GETDATEADD, 'getdatetime': GETDATETIME,
    'getdatediff': GETDATEDIFF, 'getversion': GETVERSION, 'getip': GETIP, 'gethost': GETHOST,
    'run': RUN, 'stop': STOP, 'sleep': SLEEP,
    # UI
    'hidecontrol': HIDECONTROL, 'showcontrol': SHOWCONTROL,
    # Logic
    'case': CASE, 'for': FOR, 'if': IF, 'runaction': RUNACTION,
    # Object(app, call, move, var)
    'append': APPEND, 'clear': CLEAR, 'clone': CLONE, 'new': NEW, 'remove': REMOVE, 'reportget': REPORTGET,
    'reportset': REPORTSET, 'set': SET, 'treeget': TREEGET, 'treeset': TREESET,
    # Data(console, getselectedindex, msgbox)
    'bindingdatato': BINDINGDATATO, 'calc': CALC, 'count': COUNT, 'db': DB, 'getrecordcount': GETRECORDCOUNT,
    'getrandomnumber': GETRANDOMNUMBER, 'getfieldvalue': GETFIELDVALUE, 'json': JSON, 'inputbox': INPUTBOX,
    'math': MATH, 'return': RETURN, 'webservice': WEBSERVICE,
    # String
    'convert': CONVERT, 'decode': DECODE, 'encode': ENCODE, 'fillstring': FILLSTRING, 'findstring': FINDSTRING,
    'getasc': GETASC, 'getchr': GETCHR, 'getpartofstring': GETPARTOFSTRING, 'hash': HASH,
    'insertstring': INSERTSTRING, 'lengthofstring': LENGTHOFSTRING, 'linkstring': LINKSTRING, 'replace': REPLACE,
    # File(Download, filebrowse, ftp, iniwrite, iniread, savepicture)
    'dir': DIR, 'filecopy': FILECOPY, 'filedelete': FILEDELETE, 'fileinfo': FILEINFO, 'filemove': FILEMOVE,
    'filerename': FILERENAME, 'fileread': FILEREAD, 'filewrite': FILEWRITE, 'getfilenamefromurl': GETFILENAMEFROMURL,
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
    # print(GETPARTOFSTRING.py_sentence("var = 'abcd', 2, 2"))
    # print(DB.py_sentence("db数据集=Access,'D:\Designer For UCC\Demos\Data\PMS2016.mdb','',SQL SELECT * FROM t1100工作包"))
    print(JSON.py_sentence("""var = VALUE,'idcard.idno','{"result":{"code":"0","msg":"Success in IDCard! "} , 
    "idcard":{"name":"瞿福长","sex":"男","idno":"530325199510230518","addr":"云南省曲靖市富源县后所镇老牛场村委会坡底下村29号"}}'
    """))