# -*- coding: utf-8 -*-

import json
from lxml import etree
from xlwt import XFStyle

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

import time

import logging
import pprint
_logger = logging.getLogger(__name__)

import xlwt
from cStringIO import StringIO
import base64

import lxml
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class Inventory_excel_extended(models.Model):

    _name= "inventory.excel.extended"

    finished_date_from = fields.Datetime(string = u'Từ ngày', required=True, default = fields.Datetime.now())
    finished_date_to = fields.Datetime(string = u'đến ngày', required=True, default = fields.Datetime.now())
    excel_file = fields.Binary(u'Tải báo cáo Excel')
    file_name = fields.Char(u'File báo cáo', size=64)

    company_name = fields.Char(string=u'Tên công ty:', default = u'Công ty TNHH Fory')
    company_address = fields.Char(string=u'Địa chỉ:', default = u'24 Quang Trung, Hoàn Kiếm, Hà Nội')

    stock_locations = fields.Many2many('stock.location', 'inventory_excel_extended_stock_location_rel',
                                       'inventory_excel_extended_id', 'stock_location_id', required=True, string='Locations',
                                       domain=[('usage', '!=', 'supplier')])

    @api.model
    def create(self, vals):
        filename = u'Báo cáo nhập xuất tồn Hàng hóa.xls'
        date_from = datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)
        if 'finished_date_from' in vals:
            date_from = datetime.strptime(vals['finished_date_from'], DEFAULT_SERVER_DATETIME_FORMAT)
        if 'finished_date_to' in vals:
            date_to = datetime.strptime(vals['finished_date_to'], DEFAULT_SERVER_DATETIME_FORMAT)

        res_company = self.env['res.company'].search([])
        company_name = ''
        company_address = ''
        if res_company:
            res_company = res_company[0]
            company_name = res_company.display_name #u'Công ty TNHH Fory'
            company_address = res_company.street #u'24 Quang Trung, Hoàn Kiếm, Hà Nội'

        locations = []
        if ('stock_locations' in vals) and len(vals['stock_locations']) > 0:
            locations = self.env['stock.location'].browse(vals['stock_locations'][0][2])

        report = self.create_excel_report(date_from, date_to, company_name, company_address, locations)
        vals.update({'excel_file': report, 'file_name': filename})

        excel = super(Inventory_excel_extended, self).create(vals)
        return excel
        # return {
        #     'view_mode': 'form',
        #     'res_id': export_id.id,
        #     'res_model': 'excel.extended',
        #     'view_type': 'form',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        # }


    @api.model_cr
    def create_view(self):
        tools.drop_view_if_exists(self._cr, 'stock_history_view_for_stock_inventory')
        self._cr.execute("""
            CREATE VIEW stock_history_view_for_stock_inventory AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                product_template_id,
                product_template_name,
                product_template_default_code,
                product_template_pos_categ_id,
                product_uom_name,
                SUM(quantity) as quantity,
                SUM(quantity_export) as quantity_export,
                SUM(quantity_import) as quantity_import,
                date,
                COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                COALESCE(SUM(price_unit_on_quant * quantity_export) / NULLIF(SUM(quantity_export), 0), 0) as price_unit_on_quant_export,
                COALESCE(SUM(price_unit_on_quant * quantity_import) / NULLIF(SUM(quantity_import), 0), 0) as price_unit_on_quant_import,
                SUM(price_unit_on_quant * quantity) as sum_cost,
                SUM(price_unit_on_quant * quantity_export) as sum_cost_export,
                SUM(price_unit_on_quant * quantity_import) as sum_cost_import,
                source,
                string_agg(DISTINCT serial_number, ', ' ORDER BY serial_number) AS serial_number
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.id AS product_template_id,
                    product_template.name AS product_template_name,
                    product_template.default_code AS product_template_default_code,
                    product_template.pos_categ_id AS product_template_pos_categ_id,
                    product_template.categ_id AS product_categ_id,
                    product_uom.id AS product_uom_id,
                    product_uom.name AS product_uom_name,
                    quant.qty AS quantity,
                    quant.qty AS quantity_import,
                    0 AS quantity_export,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source,
                    stock_production_lot.name AS serial_number
                FROM
                    stock_quant as quant
                JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                LEFT JOIN
                    stock_production_lot ON stock_production_lot.id = quant.lot_id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                JOIN
                    product_uom ON product_uom.id = product_template.uom_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.id AS product_template_id,
                    product_template.name AS product_template_name,
                    product_template.default_code AS product_template_default_code,
                    product_template.pos_categ_id AS product_template_pos_categ_id,
                    product_template.categ_id AS product_categ_id,
                    product_uom.id AS product_uom_id,
                    product_uom.name AS product_uom_name,
                    - quant.qty AS quantity,
                    0 AS quantity_import,
                    quant.qty AS quantity_export,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source,
                    stock_production_lot.name AS serial_number
                FROM
                    stock_quant as quant
                JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                LEFT JOIN
                    stock_production_lot ON stock_production_lot.id = quant.lot_id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                JOIN
                    product_uom ON product_uom.id = product_template.uom_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_categ_id, date, source, product_template_id, product_template_default_code, product_template_name, product_template_pos_categ_id, product_uom_name
            )""")


    @api.model
    def create_excel_report(self, date_from, date_to, company_name, company_address, locations):
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet(u'Báo cáo nhập xuất tồn Hàng hóa', cell_overwrite_ok=True)
        style_content = xlwt.easyxf(
            'font:height 240, bold False, name Times New Roman; align: horiz left, vert center, wrap false;borders: top thin,right thin,bottom thin,left thin')
        style_content_header = xlwt.easyxf(
            'font:height 240, bold True, name Times New Roman; align: horiz left, vert center, wrap false;borders: top thin,right thin,bottom thin,left thin')
        style_content_center = xlwt.easyxf(
            'font:height 240, bold False, name Times New Roman; align: horiz center, vert center, wrap false;borders: top thin,right thin,bottom thin,left thin')
        style_content_shrink = xlwt.easyxf(
            'font:height 240, bold False, name Times New Roman; align: horiz center, vert center, wrap true, shri true;borders: top thin,right thin,bottom thin,left thin')
        style_header = xlwt.easyxf(
            'font:height 240, bold True, name Times New Roman; align: horiz center, vert center; borders: top thin,right thin,bottom thin,left thin')
        style_header_top = xlwt.easyxf(
            'font:height 240, bold True, name Times New Roman; align: horiz left, vert center;')
        style_header_bottom = xlwt.easyxf(
            'font:height 240, bold False, name Times New Roman; align: horiz center, vert center; borders: top thin,right thin,bottom thin,left thin')
        style_caption = xlwt.easyxf(
            'font:height 240, bold True, name Times New Roman; align: horiz center, vert center;')
        style_caption_description = xlwt.easyxf(
            'font:height 240, bold False, name Times New Roman; align: horiz center, vert center;')


        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN
        style_font_bold = xlwt.Font()
        style_font_bold.bold = True

        style_currency = xlwt.XFStyle()
        style_currency.num_format_str = '#,##0'
        style_currency.borders = borders

        style_currency_bold = xlwt.XFStyle()
        style_currency_bold.num_format_str = '#,##0'
        style_currency_bold.borders = borders
        style_currency_bold.font = style_font_bold

        style_quantity = xlwt.XFStyle()
        style_quantity.num_format_str = '#,##0'
        style_quantity.borders = borders

        style_quantity_bold = xlwt.XFStyle()
        style_quantity_bold.num_format_str = '#,##0'
        style_quantity_bold.borders = borders
        style_quantity_bold.font = style_font_bold

        style = style_header_top
        row = 0
        worksheet.write_merge(row, row, 0, 4, company_name, style)
        row = row + 1
        worksheet.write_merge(row, row, 0, 4, company_address, style)

        row = row + 1
        worksheet.write_merge(row, row, 0, 14, u'BÁO CÁO NHẬP XUẤT TỒN KHO HÀNG HÓA', style_caption)
        str_date_from = _(u"Từ ngày %s đến %s") % ((date_from + tools.timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), (date_to + tools.timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"))
        row = row + 1
        worksheet.write_merge(row, row, 0, 14, str_date_from, style_caption_description)

        style = style_header
        col = 0
        row = row + 1
        worksheet.col(col).width = 256 * 5
        worksheet.write_merge(row, row + 1, col, col, u'STT', style)
        worksheet.write(row + 2, col, u'A', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'Ngành hàng cấp 1', style)
        worksheet.write(row + 2, col, u'', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'Ngành hàng cấp 2', style)
        worksheet.write(row + 2, col, u'', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'Ngành hàng cấp 3', style)
        worksheet.write(row + 2, col, u'', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'Mã hàng', style)
        worksheet.write(row + 2, col, u'B', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'Tên hàng', style)
        worksheet.write(row + 2, col, u'C', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row + 1, col, col, u'ĐVT', style)
        worksheet.write(row + 2, col, u'D', style_header_bottom)
        col = col + 1
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row, col, col + 1, u'Số tồn đầu', style)
        worksheet.write(row + 1, col, u'Số lượng', style)
        worksheet.write(row + 2, col, u'(1)', style_header_bottom)
        worksheet.write(row + 1, col + 1, u'Giá trị', style)
        worksheet.write(row + 2, col + 1, u'(2)', style_header_bottom)
        col = col + 2
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row, col, col + 1, u'Nhập trong kỳ', style)
        worksheet.write(row + 1, col, u'Số lượng', style)
        worksheet.write(row + 2, col, u'(3)', style_header_bottom)
        worksheet.write(row + 1, col + 1, u'Giá trị', style)
        worksheet.write(row + 2, col + 1, u'(4)', style_header_bottom)
        col = col + 2
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row, col, col + 1, u'Xuất trong kỳ', style)
        worksheet.write(row + 1, col, u'Số lượng', style)
        worksheet.write(row + 2, col, u'(5)', style_header_bottom)
        worksheet.write(row + 1, col + 1, u'Giá trị', style)
        worksheet.write(row + 2, col + 1, u'(6)', style_header_bottom)
        col = col + 2
        worksheet.col(col).width = 256 * 20
        worksheet.write_merge(row, row, col, col + 1, u'Số tồn cuối', style)
        worksheet.write(row + 1, col, u'Số lượng', style)
        worksheet.write(row + 2, col, u'(7)=(1)+(3)-(5)', style_header_bottom)
        worksheet.write(row + 1, col + 1, u'Giá trị', style)
        worksheet.write(row + 2, col + 1, u'(8)=(2)+(4)-(6)', style_header_bottom)
        row = row + 2

        if locations:
            for location in locations:

                self.create_view();
                self._cr.execute("""SELECT product_id AS id, 
                                          product_template_default_code AS default_code,
                                          product_template_name AS name,
                                          product_template_pos_categ_id AS pos_categ_id,
                                          product_uom_name AS uom_name,
                                          sum(quantity) AS quantity,
                                          sum(quantity_import) AS quantity_import,
                                          sum(quantity_export) AS quantity_export,
                                          sum(sum_cost) AS sum_cost,
                                          sum(sum_cost_import) AS sum_cost_import,
                                          sum(sum_cost_export) AS sum_cost_export
                                          FROM stock_history_view_for_stock_inventory
                                          WHERE (location_id = %s) AND (date >= %s) AND (date <= %s)
                                          GROUP BY product_id, product_template_default_code, product_template_name, pos_categ_id, product_uom_name""", (location.id, date_from, date_to))

                products_interm = {}
                for data_row in self.env.cr.dictfetchall():
                    products_interm[data_row.pop('id')] = data_row

                self._cr.execute("""SELECT product_id AS id, 
                                      sum(quantity) AS quantity,
                                      sum(sum_cost) AS sum_cost
                                      FROM stock_history_view_for_stock_inventory
                                      WHERE (location_id = %s) AND (date < %s)
                                      GROUP BY product_id""",
                                 (location.id, date_from))
                previous_data = {}
                for data_row in self.env.cr.dictfetchall():
                    previous_data[data_row.pop('id')] = data_row

                self._cr.execute("""SELECT product_id AS id, 
                                      product_template_default_code AS default_code,
                                      product_template_name AS name,
                                      product_template_pos_categ_id AS pos_categ_id,
                                      product_uom_name AS uom_name,
                                      sum(quantity) AS quantity,
                                      sum(quantity_import) AS quantity_import,
                                      sum(quantity_export) AS quantity_export,
                                      sum(sum_cost) AS sum_cost,
                                      sum(sum_cost_import) AS sum_cost_import,
                                      sum(sum_cost_export) AS sum_cost_export
                                      FROM stock_history_view_for_stock_inventory
                                      WHERE (location_id = %s)
                                      GROUP BY product_id, product_template_default_code, product_template_name, pos_categ_id, product_uom_name""",
                                 (location.id,))

                ppps = self.env.cr.dictfetchall()
                products = []
                for p in ppps:
                    if ((p['id'] in previous_data.keys()) and (int(previous_data[p['id']]['quantity']) != 0)) \
                            or ((p['id'] in products_interm.keys()) and (int(products_interm[p['id']]['quantity_import']) != 0)):
                        products.append(p)

                row = row + 1
                for col in range(0, 15):
                    worksheet.write(row, col, '', style_content)

                p_len = len(products)
                col = 0
                worksheet.write_merge(row, row, col, col + 6, location.complete_name, style_content_header)

                if p_len > 0:
                    col = col + 7
                    worksheet.write(row, col, xlwt.Formula(_('SUM(H%s:H%s)') % (row + 2, row + 1 + p_len)),
                                    style_quantity_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(I%s:I%s)') % (row + 2, row + 1 + p_len)),
                                    style_currency_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(J%s:J%s)') % (row + 2, row + 1 + p_len)),
                                    style_quantity_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(K%s:K%s)') % (row + 2, row + 1 + p_len)),
                                    style_currency_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(L%s:L%s)') % (row + 2, row + 1 + p_len)),
                                    style_quantity_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(M%s:M%s)') % (row + 2, row + 1 + p_len)),
                                    style_currency_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(N%s:N%s)') % (row + 2, row + 1 + p_len)),
                                    style_quantity_bold)
                    col = col + 1
                    worksheet.write(row, col, xlwt.Formula(_('SUM(O%s:O%s)') % (row + 2, row + 1 + p_len)),
                                    style_currency_bold)

                stt = 0
                for p in products:
                    p_pos_cat_obj = self.env['pos.category'].browse(p['pos_categ_id'])
                    p_pos_cat_name = ['','','']
                    if p_pos_cat_obj:
                        p_pos_cat_name = p_pos_cat_obj[0].name_get()
                        p_pos_cat_name = p_pos_cat_name[0][1].split(' / ')
                        p_pos_cat_name.extend(['','',''])

                    row = row + 1
                    stt = stt + 1

                    for col in range(0, 15):
                        worksheet.write(row, col, '', style_content)

                    col = 0
                    worksheet.write(row, col, stt, style_content)

                    col += 1
                    worksheet.write(row, col, p_pos_cat_name[0], style_content)
                    col += 1
                    worksheet.write(row, col, p_pos_cat_name[1], style_content)
                    col += 1
                    worksheet.write(row, col, p_pos_cat_name[2], style_content)

                    col += 1
                    worksheet.write(row, col, p['default_code'], style_content)
                    col += 1
                    worksheet.write(row, col, p['name'], style_content)
                    col += 1
                    worksheet.write(row, col, p['uom_name'], style_content)

                    if p['id'] in previous_data.keys():
                        col += 1
                        worksheet.write(row, col, previous_data[p['id']]['quantity'], style_quantity)
                        col += 1
                        worksheet.write(row, col, previous_data[p['id']]['sum_cost'], style_quantity)
                    else:
                        col += 1
                        worksheet.write(row, col, 0, style_quantity)
                        col += 1
                        worksheet.write(row, col, 0, style_currency)

                    # is_pre = None
                    # for pre in previous_data:
                    #     if pre['id'] == p['id']:
                    #         worksheet.write(row, col, pre['quantity'], style_quantity)
                    #         col += 1
                    #         worksheet.write(row, col, pre['sum_cost'], style_currency)
                    #         is_pre = True
                    #         break;
                    # if not is_pre:
                    #     worksheet.write(row, col, 0, style_quantity)
                    #     col += 1
                    #     worksheet.write(row, col, 0, style_currency)

                    if p['id'] in products_interm.keys():
                        col += 1
                        worksheet.write(row, col, products_interm[p['id']]['quantity_import'], style_quantity)
                        col += 1
                        worksheet.write(row, col, products_interm[p['id']]['sum_cost_import'], style_currency)
                        col += 1
                        worksheet.write(row, col, products_interm[p['id']]['quantity_export'], style_quantity)
                        col += 1
                        worksheet.write(row, col, products_interm[p['id']]['sum_cost_export'], style_currency)
                    else:
                        col += 1
                        worksheet.write(row, col, 0, style_quantity)
                        col += 1
                        worksheet.write(row, col, 0, style_currency)
                        col += 1
                        worksheet.write(row, col, 0, style_quantity)
                        col += 1
                        worksheet.write(row, col, 0, style_currency)

                    col += 1
                    worksheet.write(row, col, xlwt.Formula(_('H%s+J%s-L%s') % (row + 1, row + 1, row + 1)), style_quantity)
                    col += 1
                    worksheet.write(row, col, xlwt.Formula(_('I%s+K%s-M%s') % (row + 1, row + 1, row + 1)), style_currency)
                    # worksheet.write_merge(row, row, col, col + 6, p['name'], style_content)


        row = row + 1
        for col in range(0, 15):
            worksheet.write(row, col, '', style_content)


        col = 0
        worksheet.write_merge(row, row, col, col + 6, u'TỔNG', style_content_header)

        col = col + 7
        worksheet.write(row, col, xlwt.Formula(_('SUM(H%s:H%s)/2') % (8, row)), style_quantity_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(I%s:I%s)/2') % (8, row)), style_currency_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(J%s:J%s)/2') % (8, row)), style_quantity_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(K%s:K%s)/2') % (8, row)), style_currency_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(L%s:L%s)/2') % (8, row)), style_quantity_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(M%s:M%s)/2') % (8, row)), style_currency_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(N%s:N%s)/2') % (8, row)), style_quantity_bold)
        col = col + 1
        worksheet.write(row, col, xlwt.Formula(_('SUM(O%s:O%s)/2') % (8, row)), style_currency_bold)

        row = row + 2
        col = 0
        worksheet.write_merge(row, row, col + 10, col + 11, u'Ngày... tháng... năm...', style_caption_description)
        row = row + 1
        col = 0
        worksheet.write_merge(row, row, col + 0, col + 5, u'Kế toán', style_caption)
        worksheet.write_merge(row, row, col + 8, col + 13, u'Người lập', style_caption)
        row = row + 1
        col = 0
        worksheet.write_merge(row, row, col + 0, col + 5, u'(Ký, họ tên)', style_caption_description)
        worksheet.write_merge(row, row, col + 8, col + 13, u'(Ký, họ tên)', style_caption_description)


        fp = StringIO()
        workbook.save(fp)
        # export_id = self.pool.get('excel.extended').create(self._cr, self._uid, {'excel_file': base64.encodestring(fp.getvalue()),
        #                                                              'file_name': filename}, self.env.context)
        # export_id = self.env['excel.extended'].create(
        #     {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        report = base64.encodestring(fp.getvalue())
        fp.close()
        return report

    @api.multi
    def write(self, vals):
        date_from = datetime.strptime(self.finished_date_from, DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = datetime.strptime(self.finished_date_to, DEFAULT_SERVER_DATETIME_FORMAT)
        if 'finished_date_from' in vals:
            date_from = datetime.strptime(vals['finished_date_from'], DEFAULT_SERVER_DATETIME_FORMAT)
        if 'finished_date_to' in vals:
            date_to = datetime.strptime(vals['finished_date_to'], DEFAULT_SERVER_DATETIME_FORMAT)

        excel = super(Inventory_excel_extended, self).write(vals)

        if not 'excel_file' in vals:
            report = self.create_excel_report(date_from, date_to, self.company_name, self.company_address, self.stock_locations)
            vals = {'excel_file': report}
            excel = super(Inventory_excel_extended, self).write(vals)

        return excel
