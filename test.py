import unittest

import grammar
from grammar import Ucc2PyGrammar
from ucc_library import my_json, TextBox


class mytest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Json(self):
        temp = grammar.JSON.py_sentence("""var = VALUE,'idcard.idno','{"result":{"code":"0","msg":"Success in IDCard! "} , "idcard":{"name":"瞿福长","sex":"男","idno":"530325199510230518","addr":"云南省曲靖市富源县后所镇老牛场村委会坡底下村29号"}}'""")
        value = eval(temp.split('=')[1].strip())
        self.assertEqual(value, '530325199510230518')

    def test_TextBox(self):
        temp = TextBox('txt字符串', 'txt字符串', 'A,B,C,D,E,F,G')
        self.assertEqual(temp.Text, 'A,B,C,D,E,F,G')
        self.assertEqual(temp.default_property, 'A,B,C,D,E,F,G')
        temp.clear()
        self.assertEqual(temp.Text, '')


if __name__ == '__main__':
    unittest.main()