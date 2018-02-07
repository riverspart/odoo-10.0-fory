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


class Quant(models.Model):

    _inherit = "stock.quant"
    life_date = fields.Datetime(string='Life date', related = 'lot_id.life_date')

    can_used_date = fields.Integer(string="Number day can use", compute= '_compute_can_used_date')

    @api.depends('life_date')
    def _compute_can_used_date(self):

        for quant in self:
            if(quant.life_date):
                day_from = datetime.now()
                day_to = fields.Datetime.from_string(quant.life_date)
                nb_of_days = (day_to - day_from).days
                quant.can_used_date = nb_of_days
