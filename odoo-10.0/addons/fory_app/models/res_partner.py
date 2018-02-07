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


class Partner(models.Model):

    _inherit = "res.partner"

    vat = fields.Char(string='TIN', help="Tax Identification Number. "
                                         "Fill it if the company is subjected to taxes. "
                                         "Used by the some of the legal statements.", required=False)
    phone = fields.Char(required=True)
    mobile = fields.Char(required=False)
    email = fields.Char(required=True)

    _sql_constraints = [
        ('phone_uniq', 'unique (phone)', "Phone already existed!"),
        ('email_uniq', 'unique (email)', "Email already existed!"),
        ('vat_uniq', 'unique (vat)', 'The TIN is existed !')
    ]