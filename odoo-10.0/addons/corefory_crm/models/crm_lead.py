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


class Lead(models.Model):

    _inherit = "crm.lead"
    birth_date = fields.Date(string='Date of birth')

    @api.multi
    def _onchange_partner_id_values(self,partner_id):
        values = super(Lead, self)._onchange_partner_id_values(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        values['birth_date'] = partner.birth_date

        return values

    @api.multi
    def _lead_create_contact(self, name, is_company, parent_id=False):
        values = super(Lead,self)._lead_create_contact(name, is_company, parent_id)
        partner = self.env['res.partner'].browse(values.id)
        partner.write({'birth_date':self.birth_date})

        return partner
