# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CoreforyProductSlider(models.Model):

    _name = 'corefory.product.slider'
    _description = 'Product Slider'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', size=32, required=True,track_visibility='onchange')
    type_id = fields.Many2one('corefory.product.slider.type',string='Type')
    description = fields.Html('Description')
    product_ids = fields.Many2many('product.product', 'corefory_product_slider_rel', 'product_slider_id', 'product_id', string='Product(s)')

class CoreforyProductSliderType(models.Model):
    _name = 'corefory.product.slider.type'
    _description = 'Product Slider Type'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', size=32, required=True, track_visibility='onchange')
    code = fields.Char(string='Code')
    description = fields.Html('Description')
