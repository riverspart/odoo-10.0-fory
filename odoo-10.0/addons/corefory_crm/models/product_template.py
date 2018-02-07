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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fory_brand = fields.Many2one('corefory.product.brand',string='Brand')
    fory_hot = fields.Boolean(default=False, string="Hot?")
    fory_how_to_use = fields.Html(string='How to use?')
    @api.multi
    def toggle_hot(self):
        if(self.fory_hot == False):
            self.fory_hot = True
        else:
            self.fory_hot = False


    # @api.multi
    # def toggle_website_published(self):
    #     if(self.website_published == False):
    #         self.website_published = True
    #     else:
    #         self.website_published = False

