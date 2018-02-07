# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import datetime
from dateutil.relativedelta import relativedelta
import uuid

class CoreforyCcoupon(models.Model):
    _name = "corefory.coupon"
    _description = "Corefory Coupon"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code',default=lambda self: str(uuid.uuid4().hex[:6].upper()),)
    sequence = fields.Integer('Sequence', default=20)
    description = fields.Html('Description')
    start_date = fields.Datetime('Start Date',default = fields.Datetime.now,)
    end_date = fields.Datetime('End Date', default = fields.Datetime.now,)
    category_id = fields.Many2one('corefory.coupon.category', string="Category")
    max_use = fields.Integer('Max Use', default = 1)
    partner_ids = fields.Many2many('res.partner', 'corefory_coupon_partner_rel', 'coupon_id', 'partner_id', string='Partner(s)')

    number_product_can_apply = fields.Integer('Number product can apply?', default=1)
    total_amount_can_apply = fields.Float('Total amount can apply?', default=0)
    number_order_for_each_customer = fields.Integer('Number order for each customer?', default=1)
    gifts = fields.Many2many('product.product', 'corefory_coupon_gift_rel', 'coupon_id','product_id',string='Gift(s)')
    apply_golden_hour = fields.Boolean('Apply golden hour?', default= False)
    start_time = fields.Float("Start time")
    end_time = fields.Float("End time")
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product')], "Apply On",
        default='3_global', required=True,
        help='Coupon applicable on selected option')
    categ_id = fields.Many2one('product.category', 'Product Category', ondelete='cascade',
        help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.")
    product_ids = fields.Many2many('product.template', 'corefory_coupon_product_template_rel', 'coupon_id',
                                   'product_template_id',
                                   string='Product(s)')
    price_discount = fields.Float('Price Discount', default=0, digits=(16, 2))
    price_surcharge = fields.Float(
        'Price Surcharge', digits=dp.get_precision('Product Price'),
        help='Specify the fixed amount to add or substract(if negative) to the amount calculated with the discount.')
    price_round = fields.Float(
        'Price Rounding', digits=dp.get_precision('Product Price'),
        help="Sets the price so that it is a multiple of this value.\n"
             "Rounding is applied after the discount and before the surcharge.\n"
             "To have prices that end in 9.99, set rounding 10, surcharge -0.01")
    price_min_margin = fields.Float(
        'Min. Price Margin', digits=dp.get_precision('Product Price'),
        help='Specify the minimum amount of margin over the base price.')
    price_max_margin = fields.Float(
        'Max. Price Margin', digits=dp.get_precision('Product Price'),
        help='Specify the maximum amount of margin over the base price.')

    order_ids = fields.One2many('sale.order', 'coupon_id', 'Order')
    pos_order_ids = fields.One2many('pos.order', 'coupon_id', 'Pos Order')

    number_of_use = fields.Integer('Number of Use', compute='compute_number_of_use', store=True)
    number_of_remaining_use = fields.Integer('Number of Remaining Use', compute='compute_number_of_remaining_use')
    can_use = fields.Boolean('Can Use?', compute='compute_can_use')

    compute_price = fields.Selection([
        ('fixed', 'Fix Price'),
        ('percentage', 'Percentage (discount)')], index=True, default='fixed')
    percentage = fields.Float('Percentage', default=0.0)
    fixed_price = fields.Float('Fixed Price', digits=dp.get_precision('Product Price'))


    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        if(self.applied_on == '3_global'):
            self.categ_id = None
            self.product_ids = None
        elif(self.applied_on == '2_product_category'):
            self.product_ids = None
        elif (self.applied_on == '1_product'):
            self.categ_id = None

    @api.onchange('compute_price')
    def _onchange_compute_price(self):
        if self.compute_price != 'fixed':
            self.fixed_price = 0.0
        if self.compute_price != 'percentage':
            self.percentage = 0.0
        if self.compute_price != 'formula':
            self.update({
                'price_discount': 0.0,
                'price_surcharge': 0.0,
                'price_round': 0.0,
                'price_min_margin': 0.0,
                'price_max_margin': 0.0,
            })

    @api.one
    @api.depends('number_of_use','max_use', 'start_date' , 'end_date')
    def compute_can_use(self):
        current_date = datetime.datetime.now()
        can_use_1 = False
        if(self.start_date and self.end_date):
            if(datetime.datetime.strptime(self.start_date, DEFAULT_SERVER_DATETIME_FORMAT)  <= current_date
               and datetime.datetime.strptime(self.end_date, DEFAULT_SERVER_DATETIME_FORMAT) >= current_date
               and self.number_of_use < self.max_use):
                can_use_1 = True
        # check golden hour
        can_use_2 = self.check_start_time_end_time()
        self.can_use = can_use_1 and can_use_2


    @api.one
    @api.depends('number_of_use')
    def compute_number_of_remaining_use(self):
        self.number_of_remaining_use = self.max_use - self.number_of_use

    @api.one
    @api.depends('order_ids.state' , 'pos_order_ids.state')
    def compute_number_of_use(self):
        number_of_use = 0
        for order in self.order_ids:
            if(order.state == 'done'):
                number_of_use+= 1

        for pos_order in self.pos_order_ids:
            if (pos_order.state == 'done' or pos_order.state == 'paid'  or pos_order.state == 'invoiced' ):
                number_of_use += 1

        self.number_of_use = number_of_use

    @api.multi
    def generate_code(self):
        self.code = str(uuid.uuid4().hex[:6].upper())

    @api.multi
    def count_number_of_use(self):
        return

    @api.multi
    def get_coupon(self,domain):
        coupon = self.env['corefory.coupon'].search(domain,limit = 1)
        return coupon

    @api.multi
    def check_start_time_end_time(self):
        if(self.apply_golden_hour):
            mynow = fields.Datetime.context_timestamp(self, datetime.datetime.now())
            hour_to = int(self.end_time)
            min_to = int((self.end_time - hour_to) * 60)
            to_alert = datetime.time(hour_to, min_to)
            hour_from = int(self.start_time)
            min_from = int((self.start_time - hour_from) * 60)
            from_alert = datetime.time(hour_from, min_from)
            if from_alert <= mynow.time() <= to_alert:
                return True
            return False
        else:
            return True

    def compute_number_of_use_each_customer(self, partner_id):

        count = 0
        for order in self.order_ids:
            if(order.partner_id.id == partner_id and order.state == 'done'):
                count += 1

        for pos_order in self.pos_order_ids:
            if(pos_order.partner_id.id == partner_id and (pos_order.state == 'done' or pos_order.state == 'paid'  or pos_order.state == 'invoiced' )):
                count += 1

        return count
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code already exists !"),
        ('check_start_time', 'check(start_time >= 0 and start_time < 24)','The start time should be between 0% and 24%!'),
        ('check_end_time', 'check(end_time >= 0 and end_time < 24)','The end time should be between 0% and 24%!'),
    ]


class CoreforyCcouponCategory(models.Model):
    _name = "corefory.coupon.category"
    _description = "Corefory Ccoupon Category"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', default=20)
    description = fields.Html('Description')