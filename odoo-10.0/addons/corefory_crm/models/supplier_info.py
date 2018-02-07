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
import odoo.addons.decimal_precision as dp

class SuppliferInfo(models.Model):

    _inherit = "product.supplierinfo"
    delay = fields.Integer(
        'Delivery Lead Time', default=1, required=True, invisible=True,
        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")

    min_qty = fields.Float(
        'Minimal Quantity', default=0.0, required=True, digits=dp.get_precision('Product Unit of Measure'),
        help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")