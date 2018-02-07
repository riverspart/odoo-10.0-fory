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
from odoo.tools import amount_to_text_en
from currency import Num2Word_VN_Currency

class StockMove(models.Model):
    _inherit = "stock.move"

    temp_posted_date = fields.Datetime("Wanted posted date",related='picking_id.temp_posted_date',  default = fields.Datetime.now, copy = True)
    price_unit_before = fields.Float(string='Unit Price Before', help="Unit Price Before converting")
class StockPicking(models.Model):
    _inherit = "stock.picking"

    temp_posted_date = fields.Datetime("Wanted posted date", default = fields.Datetime.now)

    def numToWords(self,num, join=True , currency = 'VND'):
        '''words = {} convert an integer number into words'''
        # num2words(num, to='currency', lang='vi_VN')

        amount_in_words = amount_to_text_en.amount_to_text(num, lang='en', currency=self.company_id.currency_id.name)
        vn = Num2Word_VN_Currency()
        amount = vn.number_to_text(num, currency)
        return amount

        units = ['', _('one'), _('two'), _('three'), _('four'), _('five'), _('six'), _('seven'), _('eight'), _('nine')]
        teens = ['', _('eleven'), _('twelve'), _('thirteen'), _('fourteen'), _('fifteen'), _('sixteen'),
                 _('seventeen'), _('eighteen'), _('nineteen')]
        tens = ['', _('ten'), _('twenty'), _('thirty'), _('forty'), _('fifty'), _('sixty'), _('seventy'),
                _('eighty'), _('ninety')]
        thousands = ['', _('thousand'), _('million'), _('billion'), _('trillion'), _('quadrillion'),
                     _('quintillion'), _('sextillion'), _('septillion'), _('octillion'),
                     _('nonillion'), _('decillion'), _('undecillion'), _('duodecillion'),
                     _('tredecillion'), _('quattuordecillion'), _('sexdecillion'),
                     _('septendecillion'), _('octodecillion'), _('novemdecillion'),
                     _('vigintillion')]
        words = []
        if num == 0:
            words.append(_('zero'))
        else:
            numStr = '%d' % num
            numStrLen = len(numStr)
            groups = (numStrLen + 2) / 3
            numStr = numStr.zfill(groups * 3)
            for i in range(0, groups * 3, 3):
                h, t, u = int(numStr[i]), int(numStr[i + 1]), int(numStr[i + 2])
                g = groups - (i / 3 + 1)
                if h >= 1:
                    words.append(units[h])
                    words.append(_('hundred'))
                if t > 1:
                    words.append(tens[t])
                    if u >= 1: words.append(units[u])
                elif t == 1:
                    if u >= 1:
                        words.append(teens[u])
                    else:
                        words.append(tens[t])
                else:
                    if u >= 1: words.append(units[u])
                if (g >= 1) and ((h + t + u) > 0): words.append(thousands[g] + ',')
        if join: return ' '.join(words)
        return words

    def corefory_get_account_move_line(self,ref, incoming, outcoming):
        # domain = [('origin', '=', ref),('state','=','paid')]
        # if(incoming):
        #     account_invoice = self.env['account.invoice'].sudo().search(domain, limit=1)
        # if(outcoming):
        #     sale_order = self.env['sale.order'].sudo().search([('name','=',ref)], limit=1)
        #     account_invoice = sale_order.invoice_ids
        #     if (len(account_invoice.ids) > 0):
        #         account_invoice = account_invoice[0]
        #     # account_invoice = self.env['account.invoice'].sudo().search(domain, limit=1)
        #
        # account_move = None
        # if(len(account_invoice.ids) > 0):
        #     account_move = account_invoice.move_id
            # domain = [('ref','=', account_invoice.number)]
            # if(debit_credit == 'debit'):
            #     domain.append(('debit', '>' ,0))
            # elif(debit_credit == 'credit'):
            #     domain.append(('credit', '>', 0))
            # account_move_line = self.env['account.move.line'].sudo().search(domain, limit = 1)

        domain = [('ref', '=', ref), ('state', '=', 'posted')]
        account_move = self.env['account.move'].sudo().search(domain, limit=1)

        return account_move

    def corefory_get_order(self,incoming, outcoming ):
        if (incoming):
            order = self.env['purchase.order'].sudo().search([('name', '=', self.origin)], limit=1)
        if (outcoming):
            order = self.env['sale.order'].sudo().search([('name', '=', self.origin)], limit=1)

        return order

    def corefory_get_currency(self,incoming, outcoming) :
        order = self.corefory_get_order(incoming, outcoming)
        if(order):
            return order.currency_id


    def corefory_get_price_unit(self,incoming, outcoming, product_id , quantity):

        order = self.corefory_get_order(incoming, outcoming)
        price_unit = 0
        if(order and len(order.ids) > 0):
            for line in order.order_line:
                product_quantity = 0
                if (incoming):
                    product_quantity = line.product_qty
                if (outcoming):
                    product_quantity = line.product_uom_qty
                if(line.product_id.id == product_id):
                    price_unit = line.price_unit
                    break

        return price_unit

    def get_currency_rate(self,currency,date):
        rate = currency._compute_currency_rate_by_date(currency, date)

        return "{0:.2f}".format(round((1/rate),2))
class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    fory_price_unit = fields.Float(string='Unit Price', help="Unit Price", copy=True)
    fory_price_unit_with_tax = fields.Float(string='Unit Price With Tax', help="Unit Price With Tax")