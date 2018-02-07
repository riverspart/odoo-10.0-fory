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


class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = "sale.advance.payment.inv"

    # advance_payment_method = fields.Selection([
    #     ('delivered', 'Invoiceable lines'),
    #     ('all', 'Invoiceable lines (deduct down payments)'),
    #     ('percentage', 'Down payment (percentage)'),
    #     ('fixed', 'Down payment (fixed amount)')
    # ], string='What do you want to invoice?', default=_get_advance_payment_method, required=True)

    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines')
    ], string='What do you want to invoice?', default='delivered', required=True)

class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    # filter_refund = fields.Selection(
    #     [('refund', 'Create a draft refund'), ('cancel', 'Cancel: create refund and reconcile'),
    #      ('modify', 'Modify: create refund, reconcile and create a new draft invoice')],
    #     default='refund', string='Refund Method', required=True,
    #     help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')

    filter_refund = fields.Selection(
        [('refund', 'Create a draft refund')],
        default='refund', string='Refund Method', required=True,
        help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')