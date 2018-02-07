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
    birth_date = fields.Date(string='Date of birth')
    membership_card = fields.Many2one('corefory.loyalty.card', string='Loyalty Card',compute='compute_current_loyalty_card')
    membership_card_list = fields.One2many('corefory.loyalty.card', 'partner_id', string='Loyalty Card')
    preferred_product_ids = fields.One2many('corefory.partner.prefer.product.line', 'partner_id', 'Preferred Product')

    @api.one
    @api.depends('membership_card_list')
    def compute_current_loyalty_card(self):
        if (len(self.membership_card_list.ids) > 0):
            borrow_search = self.env['corefory.loyalty.card'].search([('id','in' ,self.membership_card_list.ids ),('state' , '=' , 'active') ])
            if (len(borrow_search.ids ) > 0):
                borrow_ids = self.env['corefory.loyalty.card'].browse(borrow_search.ids[len(borrow_search.ids) - 1])
                self.membership_card = borrow_ids.id
            else:
                self.membership_card = None
        else:
            self.membership_card = None
    @api.model
    def default_code(self):
        self._cr.execute('SELECT MAX(id) FROM res_partner')
        max_id = self.env.cr.dictfetchall()
        if max_id[0]['max']:
            id = max_id[0]['max'] + 1
        else:
            id = 1

        return '{}{:05}'.format('KH', id)

    @api.depends('supplier','customer')
    def _compute_default_code(self):
        code = ''
        id = 0
        res_partner = None
        if(self.supplier):
            res_partner = self.env['res.partner'].search([('supplier' ,'=' , True)])
            code = 'NCC'
        if (self.customer):
            res_partner = self.env['res.partner'].search([('customer', '=', True)])
            code = 'KH'
        if(res_partner):
            id = len(res_partner.ids) + 1
        self.code = '{}{:05}'.format(code, id)
    code = fields.Char(string='Code', index=True, track_visibility='always', compute='_compute_default_code', store=True)
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code already exists !"),
    ]

class PartnerPreferProductLine(models.Model):
    _name = 'corefory.partner.prefer.product.line'
    _description = 'Partner Prefer Product Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    product_id = fields.Many2one('product.template', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    is_love = fields.Boolean(string='Love or Not ?')



class ResCompany(models.Model):
    _inherit = "res.company"

    slogan = fields.Char(string='Sologan')
    google_map = fields.Char(string='Map')
