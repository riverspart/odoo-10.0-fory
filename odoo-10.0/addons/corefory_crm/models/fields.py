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


class MonetaryConverter(models.AbstractModel):

    _inherit = "ir.qweb.field.monetary"

    @api.model
    def value_to_html(self, value, options):
        res = super(MonetaryConverter, self).value_to_html(value, options)

        if('corefory_report' in options):
            if(options.get('corefory_report')):
                res = res[:-1]

        return res



