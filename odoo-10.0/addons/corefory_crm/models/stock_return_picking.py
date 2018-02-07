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

class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    fory_price_unit = fields.Float(string='Unit Price', help="Unit Price")
    fory_price_unit_with_tax = fields.Float(string='Unit Price With Tax', help="Unit Price With Tax")

class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    fory_price_unit = fields.Float(string='Unit Price', help="Unit Price")
    fory_price_unit_with_tax = fields.Float(string='Unit Price With Tax', help="Unit Price With Tax")
