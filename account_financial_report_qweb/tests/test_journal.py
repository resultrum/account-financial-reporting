# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestJournalReport(TransactionCase):

    def setUp(self):
        super(TestJournalReport, self).setUp()
        self.AccountObj = self.env['account.account']
        self.InvoiceObj = self.env['account.invoice']
        self.JournalObj = self.env['account.journal']
        self.JournalReportObj = self.env['journal.report.wizard']
        self.MoveObj = self.env['account.move']
        self.ReportJournalQweb = self.env['report_journal_qweb']
        self.TaxObj = self.env['account.tax']

        self.company = self.env.ref('base.main_company')

        today = datetime.today()
        last_year = today - relativedelta(years=1)

        self.previous_fy_date_start = Date.to_string(
            last_year.replace(month=1, day=1))
        self.previous_fy_date_end = Date.to_string(
            last_year.replace(month=12, day=31))
        self.fy_date_start = Date.to_string(
            today.replace(month=1, day=1))
        self.fy_date_end = Date.to_string(
            today.replace(month=12, day=31))

        self.receivable_account = self.AccountObj.search([
            ('user_type_id.name', '=', 'Receivable')
        ], limit=1)
        self.income_account = self.AccountObj.search([
            ('user_type_id.name', '=', 'Income')
        ], limit=1)

        self.journal_sale = self.JournalObj.create({
            'name': "Test journal sale",
            'code': "TST-JRNL-S",
            'type': 'sale',
            'company_id': self.company.id,
        })
        self.journal_purchase = self.JournalObj.create({
            'name': "Test journal purchase",
            'code': "TST-JRNL-P",
            'type': 'sale',
            'company_id': self.company.id,
        })

        self.tax_15 = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 15.0,
            'amount_type': 'percent',
            'include_base_amount': False,
        })

        self.tax_20 = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 15.0,
            'amount_type': 'percent',
            'include_base_amount': False,
        })

    def _add_move(
            self, date, journal,
            receivable_debit, receivable_credit, income_debit, income_credit):
        move_name = 'move name'
        move_vals = {
            'journal_id': journal.id,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': receivable_debit,
                    'credit': receivable_credit,
                    'account_id': self.receivable_account.id
                }),
                (0, 0, {
                    'name': move_name,
                    'debit': income_debit,
                    'credit': income_credit,
                    'account_id': self.income_account.id
                }),
            ]
        }
        return self.MoveObj.create(move_vals)

    def check_report_debit_credit(
            self, report, expected_debit, expected_credit):
        self.assertEqual(
            expected_debit,
            sum([journal.debit for journal in report.report_journal_ids])
        )

        self.assertEqual(
            expected_credit,
            sum([journal.credit for journal in report.report_journal_ids])
        )

    def test_01_test_total(self):
        today_date = Date.today()
        last_year_date = Date.to_string(
            datetime.today() - relativedelta(years=1))

        move1 = self._add_move(
            today_date, self.journal_sale,
            0, 100, 100, 0)
        move2 = self._add_move(
            last_year_date, self.journal_sale,
            0, 100, 100, 0)

        report = self.ReportJournalQweb.create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'company_id': self.company.id,
            'journal_ids': [(6, 0, [self.journal_sale.ids])]
        })
        report.compute_data_for_report()

        self.check_report_debit_credit(report, 100, 100)

        move3 = self._add_move(
            today_date, self.journal_sale,
            0, 100, 100, 0)

        report.refresh()
        self.check_report_debit_credit(report, 200, 200)

        report.move_target = 'posted'
        report.refresh()
        self.check_report_debit_credit(report, 0, 0)

        move1.post()
        report.refresh()
        self.check_report_debit_credit(report, 100, 100)

        move2.post()
        report.refresh()
        self.check_report_debit_credit(report, 100, 100)

        move3.post()
        report.refresh()
        self.check_report_debit_credit(report, 200, 200)

        report.date_from = self.previous_fy_date_start
        report.refresh()
        self.check_report_debit_credit(report, 300, 300)

    def test_02_test_taxes(self):
        #TODO
        invoice_values = {}
