# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CoreforyLoyaltyCard(models.Model):

    _name = 'corefory.loyalty.card'
    _description = 'Fory loyalty card'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('corefory.loyalty.card')

    name = fields.Char('Card Name', size=32, required=True,
                       track_visibility='onchange',  default=_get_default_name)

    partner_id = fields.Many2one('res.partner',string='Customer', track_visibility='onchange')

    type_id = fields.Many2one('corefory.loyalty.card.type',string='Type', compute='compute_loyalty_card_type', store= True)

    creation_date = fields.Date(string='Creation Date', track_visibility='onchange')
    activate_date = fields.Date(string='Activated Date', track_visibility='onchange')
    expiry_date = fields.Date(string='Expiry Date', track_visibility='onchange')
    total_point = fields.Float(string='Total Points', inverse="_update_config_and_type")
    convertible_point = fields.Float(string='Convertible Points')
    description = fields.Html('Description')
    state = fields.Selection(selection=[
                                            ('not_active', 'Not Active'),
                                            ('active', 'Active'),
                                        ],
                             string='Active?',
                             track_visibility='onchange',
                             default='not_active')
    history_ids = fields.One2many('corefory.loyalty.card.history', 'card_id',
                               'History',readonly=True,copy=True,track_visibility='onchange')

    point_to_money = fields.Float('Point to Money (100 point = 1000 d)', default = 3)
    money_to_point = fields.Float('Money to Point (10000 d = 1 point)')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    @api.multi
    def _update_config_and_type(self):
        # for card in self:
            type_id = self.get_card_type(self)
            if(type_id):
                point_to_money, money_to_point = self.compute_point2money_and_money2point(self.type_id)

                self.update({
                    'type_id' : type_id.id,
                    'point_to_money' : point_to_money,
                    'money_to_point' : money_to_point

                })


    def get_card_type(self, card):
        card_types = self.env['corefory.loyalty.card.type'].sudo().search([], order='sequence')

        out_type_id = None
        for type in card_types:
            if (card.total_point >= type.point_to_upgrade):
                out_type_id = type
        return out_type_id
    @api.one
    @api.depends('total_point')
    def compute_loyalty_card_type(self):
        type_id = self.get_card_type(self)
        if(type_id):
            self.type_id = type_id.id
    @api.multi
    def action_active(self):
        for r in self:
            if (r.state == 'not_active'):
                expire_after = self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'expire_after')
                current_date = datetime.now()
                self.activate_date = current_date
                new_date = current_date + relativedelta(days=expire_after)
                self.expiry_date = new_date
                r.state = 'active'
            elif(r.state == 'active') :
                r.state = 'not_active'

    @api.onchange('total_point')
    def onchange_total_point(self):
        type_id = self.get_card_type(self)
        self.type_id = type_id

    def compute_point2money_and_money2point(self,type_id):
        # point_to_money = 0
        # money_to_point = 0
        # if (type_id.code == 'membership'):
        #     point_to_money = 3
        #     money_to_point = 10000
        # elif (type_id.code == 'silver'):
        #     point_to_money = 3
        #     money_to_point = 8000
        # elif (type_id.code == 'gold'):
        #     point_to_money = 3
        #     money_to_point = 6667
        point_to_money = type_id.point_to_money
        money_to_point = type_id.money_to_point
        return point_to_money,money_to_point

    @api.onchange('type_id','total_point')
    def onchange_type_id(self):
        point_to_money, money_to_point = self.compute_point2money_and_money2point(self.type_id)
        self.point_to_money = point_to_money
        self.money_to_point =money_to_point


    # @api.onchange('history_ids')
    # def onchange_history_ids(self):
    #     if (len(self.history_ids.ids) > 0):
    #         order = 'create_date'
    #         borrow_search = self.env['corefory.loyalty.card.history'].search([('id','in' ,self.history_ids.ids )], limit = 1,order=order)
    #         self.activate_date = borrow_search.create_date
    #
    #         datetime_object = datetime.strptime(self.activate_date, DEFAULT_SERVER_DATE_FORMAT).date()
    #         new_date = datetime_object + relativedelta(years=1)
    #
    #         self.expiry_date = new_date

    @api.model
    def _get_card(self, partner_id, state='active'):
        args = [('partner_id', '=', partner_id),
                ('state', '=', state)]
        card = self.search(args, limit=1)
        return card

    @api.model
    def convert_amount_to_point(self, amount, card):
        if (card and card.money_to_point > 0):
            money_to_point = card.money_to_point
        else:
            money_to_point = self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'money_to_point')

        if amount < 0:
            return False, 0.00
        res = float(amount)/ money_to_point
        return True, res


    @api.model
    def convert_amount_to_point_with_param(self, amount, money_to_point):
        if amount < 0:
            return False, 0.00
        res = float(amount)/ money_to_point
        return True, res



    @api.model
    def convert_point_to_amount(self, point , card):
        if(card and card.point_to_money > 0):
            point_to_money = card.point_to_money
        else:
            point_to_money = self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'point_to_money')

        if point < 0:
            return False , 0.00
        res = (point / point_to_money) * 1000
        return True, res

    @api.model
    def convert_amount_to_point_base(self, amount,card):
        if (card and card.point_to_money > 0):
            point_to_money = card.point_to_money
        else:
            point_to_money = self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'point_to_money')
        if amount < 0:
            return False , 0.00
        res = (amount / 1000) * point_to_money
        return True, res

    @api.model
    def convert_amount_to_point_base_with_param(self, amount,point_to_money):
        if amount < 0:
            return False , 0.00
        res = (amount / 1000) * point_to_money
        return True, res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = "%s / %s" % (record.name, record.partner_id.name)
            result.append((record.id, name))
        return result

    @api.model
    def auto_deactive_loyalty_card(self):
        current_date = datetime.now()
        cards = self.env['corefory.loyalty.card'].sudo().search([('state', '=', 'active'), ('expiry_date', '<', current_date)])
        for card in cards:
            card.state = 'not_active'

    @api.multi
    def write(self, vals):

        res = super(CoreforyLoyaltyCard, self).write(vals)
        return res


class CoreforyLoyaltyCardType(models.Model):
    _name = "corefory.loyalty.card.type"
    _description = "Corefory Loyalty Card Type"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', default=20)
    description = fields.Html('Description')
    point_to_upgrade = fields.Float(string='Point To Upgrade')
    point_to_money = fields.Float('Point to Money (100 point = 1000 d)', default=0)
    money_to_point = fields.Float('Money to Point (10000 d = 1 point)', default=0)

class CoreforyLoyaltyCardHistory(models.Model):

    _name = "corefory.loyalty.card.history"
    _description = "Corefory loyalty card history"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    card_id = fields.Many2one('corefory.loyalty.card', 'Card Id', readonly=True)
    changed_point = fields.Float(string='Changed Points')
    user_id = fields.Many2one('res.users',string='Responsibility')
    description = fields.Text('Description')
    type = fields.Selection(selection=[
                                ('plus', 'PLus'),
                                ('minus', 'Minus'),
                            ],
                            string='PLus/Minus?',
                            track_visibility='onchange',
                            default='plus')
    order_id = fields.Many2one('sale.order',string='Order')
    origin = fields.Char(string='Source Document')
    point_to_money = fields.Float('Point to Money (100 point = 1000 d)', default=0)
    money_to_point = fields.Float('Money to Point (10000 d = 1 point)', default=0)


class CoreforyLoyaltyCardConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'corefory.loyalty.card.settings'

    point_to_money = fields.Float('Point to Money (100 point = 1000 d)')
    money_to_point = fields.Float('Money to Point (10000 d = 1 point)')
    expire_after = fields.Integer('Expire after (days)')

    @api.model
    def get_default_point_to_money(self, fields):
        return {
            'point_to_money': self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'point_to_money'),
            'money_to_point': self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'money_to_point'),
            'expire_after': self.env['ir.values'].get_default('corefory.loyalty.card.settings', 'expire_after')

        }

    @api.multi
    def set_default_point_to_money(self):
        IrValues = self.env['ir.values']
        IrValues = IrValues.sudo()
        IrValues.set_default('corefory.loyalty.card.settings', 'point_to_money', self.point_to_money)
        IrValues.set_default('corefory.loyalty.card.settings', 'money_to_point', self.money_to_point)
        IrValues.set_default('corefory.loyalty.card.settings', 'expire_after', self.expire_after)