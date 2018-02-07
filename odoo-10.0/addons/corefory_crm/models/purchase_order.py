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


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"
    # partner_id = fields.Many2one('res.partner', string='Vendor', change_default=True, track_visibility='always')
    # currency_id = fields.Many2one('res.currency', 'Currency')
