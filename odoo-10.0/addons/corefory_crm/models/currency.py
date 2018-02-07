# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError

from odoo.addons.base.res.res_partner import FormatAddress


to_19 = (u'không', u'một', u'hai', u'ba', u'bốn', u'năm', u'sáu',
         u'bảy', u'tám', u'chín', u'mười', u'mười một', u'mười hai',
         u'mười ba', u'mười bốn', u'mười lăm', u'mười sáu', u'mười bảy',
         u'mười tám', u'mười chín')
tens = (u'hai mươi', u'ba mươi', u'bốn mươi', u'năm mươi',
        u'sáu mươi', u'bảy mươi', u'tám mươi', u'chín mươi')
denom = ('',
         u'nghìn', u'triệu', u'tỷ', u'nghìn tỷ', u'trăm nghìn tỷ',
         'Quintillion', 'Sextillion', 'Septillion', 'Octillion', 'Nonillion',
         'Decillion', 'Undecillion', 'Duodecillion', 'Tredecillion',
         'Quattuordecillion', 'Sexdecillion', 'Septendecillion',
         'Octodecillion', 'Novemdecillion', 'Vigintillion')


class Num2Word_VN_Currency(object):
    is_first_number = False
    def _convert_nn(self, val):
        if val < 20:
            return to_19[val]
        for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
            if dval + 10 > val:
                if val % 10:
                    a = u'lăm'
                    if to_19[val % 10] == u'một':
                        a = u'mốt'
                    else:
                        a = to_19[val % 10]
                    if to_19[val % 10] == u'năm':
                        a = u'lăm'
                    return dcap + ' ' + a
                return dcap

    def _convert_nnn(self, val):
        word = ''
        (mod, rem) = (val % 100, val // 100)

        if rem >= 0:
            if(self.is_first_number == False and rem == 0):
                Test = True
            elif(rem >= 0):
                word = to_19[rem] + u' trăm'
                if mod > 0:
                    word = word + ' '


        if mod > 0 and mod < 10:
            if mod == 5:
                word = word != '' and word + u'linh năm' or word + u'năm'
            else:
                word = word != '' and word + u'linh ' \
                    + self._convert_nn(mod) or word + self._convert_nn(mod)
        if mod >= 10:
            word = word + self._convert_nn(mod)
        return word

    def vietnam_number(self, val):
        if val < 100:
            return self._convert_nn(val)
        if val < 1000:
            return self._convert_nnn(val)
        for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
            if dval > val:
                mod = 1000 ** didx
                lval = val // mod
                r = val - (lval * mod)


                ret = self._convert_nnn(lval) + u' ' + denom[didx]

                if (self.is_first_number == False):
                    self.is_first_number = True

                if 99 >= r > 0:
                    ret = self._convert_nnn(lval) + u' ' + denom[didx] + u' linh'
                if r > 0:
                    ret = ret + ' ' + self.vietnam_number(r)
                return ret

    def number_to_text(self, number , currency = 'VND'):
        self.is_first_number = False
        number = '%.2f' % number
        the_list = str(number).split('.')
        start_word = self.vietnam_number(int(the_list[0]))
        final_result = start_word
        if len(the_list) > 1 and int(the_list[1]) > 0:
            end_word = self.vietnam_number(int(the_list[1]))
            final_result = final_result + ' phẩy ' + end_word

        if(currency == 'VND'):
            currency = _('dong')
        elif(currency == 'USD'):
            currency = _('dolar')
        return final_result + ' ' + str(currency)

    def to_cardinal(self, number):
        return self.number_to_text(number)

    def to_ordinal(self, number):
        return self.to_cardinal(number)
