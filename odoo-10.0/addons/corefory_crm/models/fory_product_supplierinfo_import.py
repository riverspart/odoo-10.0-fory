# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import xlrd

import itertools
from odoo import api, fields, models
from odoo.tools import  DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

class Corefory_Product_Supplierinfo_Import(models.TransientModel):
    _name = "corefory.product.supplierinfo.import"
    _description = "Import Product supplierinfo"

    data = fields.Binary('File', required=True)
    filename = fields.Char('File Name', required=True)

    @api.multi
    def import_question(self):
        file_data = self.data.decode('base64')
        wb = xlrd.open_workbook(file_contents=file_data)
        self._read_xls_book(wb)
        return True



    def _read_xls_book(self, book):
        number_of_sheet = book.nsheets
        for sheet_index in range(0,number_of_sheet):
            sheet = book.sheet_by_index(sheet_index)
            index = 0
            for row in itertools.imap(sheet.row, range(sheet.nrows)):
                values = []
                import_data = {}

                cell_index = 0;
                if(index >= 1 and index < (sheet.nrows)):
                    for cell in row:
                        values.append(cell.value)
                        cell_index = cell_index + 1

                    vendor = self.env['res.partner'].sudo().search([('code', '=', values[0])], limit=1)
                    product = self.env['product.template'].sudo().search([('default_code', '=', values[3])], limit=1)
                    currency = self.env['res.currency'].sudo().search([('name', '=', values[6])], limit=1)

                    if(vendor and product and currency):
                        import_data  =  {
                                'name': vendor.id,
                                'product_name': values[2],
                                'product_code': values[1],
                                'product_tmpl_id': product.id,
                                'min_qty':  values[4],
                                'price': values[5],
                                'currency_id': currency.id,
                                'date_start': datetime.strptime(values[7], '%d/%m/%Y'),
                                'date_end': datetime.strptime(values[8], '%d/%m/%Y'),
                        }

                        # product = self.env['product.product'].sudo().search([('default_code', '=', import_data['default_code'])], limit = 1)
                        #
                        # if(product):
                        #     product.write(import_data)
                        # else:

                        self.env['product.supplierinfo'].create(import_data)
                index = index + 1

