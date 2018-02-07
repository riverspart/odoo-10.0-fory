# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTrialBalance(models.AbstractModel):
    _inherit = 'report.account.report_trialbalance'

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result_before = {}
        tables, where_clause, where_params = self.env['account.move.line']._query_get_before_date_from()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = (
        "SELECT account_id AS id, SUM(debit) AS debit_before, SUM(credit) AS credit_before, (SUM(debit) - SUM(credit)) AS balance_before" + \
        " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result_before[row.pop('id')] = row


        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        account_res_sum = {'debit_before': 0.0, 'credit_before': 0.0, 'debit': 0.0, 'credit':0.0, 'debit_balance': 0.0, 'credit_balance':0.0}
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result_before.keys():
                res['debit_before'] = account_result_before[account.id].get('debit_before')
                res['credit_before'] = account_result_before[account.id].get('credit_before')
                res['balance_before'] = account_result_before[account.id].get('balance_before')
            else:
                res['debit_before'] = 0
                res['credit_before'] = 0
                res['balance_before'] = 0

            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            else:
                res['debit'] = 0
                res['credit'] = 0
                res['balance'] = 0

            if not str(account.code)[:3] in ['131', '331', '138', '334', '333', '338']:
                x = float(res['debit_before']) - float(res['credit_before'])
                if x >= 0:
                    res['debit_before'] = x
                    res['credit_before'] = 0.0
                else :
                    res['debit_before'] = 0.0
                    res['credit_before'] = -x

            res['balance'] = float(res['debit_before']) - float(res['credit_before']) + float(res['debit']) - float(res['credit'])

            account_res_sum['debit_before'] += float(res['debit_before'])
            account_res_sum['credit_before'] += float(res['credit_before'])
            account_res_sum['debit'] += float(res['debit'])
            account_res_sum['credit'] += float(res['credit'])
            if float(res['balance']) > 0 :
                account_res_sum['debit_balance'] += float(res['balance'])
            else:
                account_res_sum['credit_balance'] += float(res['balance'])

            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res, account_res_sum


    @api.model
    def render_html(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res, account_res_sum = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            'Accounts_sum': account_res_sum
        }
        return self.env['report'].render('fory_app.report_trialbalance', docargs)
