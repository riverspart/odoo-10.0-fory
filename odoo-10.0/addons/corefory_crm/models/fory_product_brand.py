# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CoreforyProductBrand(models.Model):

    _name = 'corefory.product.brand'
    _description = 'Fory Product Brand'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', default=20)
    description = fields.Html('Description')