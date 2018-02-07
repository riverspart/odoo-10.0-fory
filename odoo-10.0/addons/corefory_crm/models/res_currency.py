# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import math
import re
import time

from odoo import api, fields, models, tools, _

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')


class Currency(models.Model):

    _inherit = "res.currency"



    @api.multi
    def _compute_currency_rate_by_date(self,currency,date):
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        rate = currency_rates.get(currency.id) or 1.0

        return rate

    @api.model
    def _get_conversion_rate_2(self, from_currency, to_currency, date):
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)

        return self._compute_currency_rate_by_date(to_currency,date) / self._compute_currency_rate_by_date(from_currency,date)


    @api.multi
    def compute_2(self, from_amount, to_currency, round=True, date= fields.Datetime.now()):
        """ Convert `from_amount` from currency `self` to `to_currency`. """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "compute from unknown currency"
        assert to_currency, "compute to unknown currency"
        # apply conversion rate
        if self == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate_2(self, to_currency, date)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

