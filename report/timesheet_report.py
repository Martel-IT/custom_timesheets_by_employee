# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Kavya Raveendran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models

class ReportTimesheet(models.AbstractModel):
    _name = 'report.timesheets_by_employee.report_timesheets'
    _description = 'Timesheet Report'

    def get_timesheets(self, docs):
        """input : name of employee, the starting date and ending date
        output: timesheets by that particular employee within that period
        """
        if docs.from_date and docs.to_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '>=', docs.from_date), 
                 ('date', '<=', docs.to_date)],
                order='date')
        elif docs.from_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '>=', docs.from_date)],
                order='date')
        elif docs.to_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '<=', docs.to_date)],
                order='date')
        else:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id)],
                order='date')

        records = []
        total = 0.0

        for rec in record:
            # Converti la durata in formato HH:MM
            hours = int(rec.unit_amount)
            minutes = int((rec.unit_amount - hours) * 60)
            duration_str = f"{hours:02d}:{minutes:02d}"

            vals = {
                'project': rec.project_id.name or '',
                'user': rec.user_id.partner_id.name,
                'duration': duration_str,
                'date': rec.date,
                'description': rec.name or ''  # Aggiunta della descrizione
            }
            total += rec.unit_amount
            records.append(vals)

        # Converti il totale in formato HH:MM
        total_hours = int(total)
        total_minutes = int((total - total_hours) * 60)
        total_str = f"{total_hours:02d}:{total_minutes:02d}"

        return records, total_str

    @api.model
    def _get_report_values(self, docids, data=None):
        def _get_report_values(self, docids, data=None):
            docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        
        # Informazioni dipendente
        identification = []
        for rec in self.env['hr.employee'].search(
                [('user_id', '=', docs.user_id[0].id)]):
            if rec:
                identification.append({
                    'id': rec.id,
                    'name': rec.name
                })

        # Periodo
        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date} To {docs.to_date}"
        elif docs.from_date:
            period = f"From {docs.from_date}"
        elif docs.to_date:
            period = f"To {docs.to_date}"

        timesheets, total = self.get_timesheets(docs)

        company = self.env.company
        company_data = {
            'name': company.name or '',
            'street': company.street or '',
            'city': company.city or '',
            'zip': company.zip or '',
            'state_id': company.state_id.name if company.state_id else '',
            'phone': company.phone or '',
            'email': company.email or '',
            'website': company.website or '',
        }

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'timesheets': timesheets,
            'total': total,
            'identification': identification,
            'period': period,
            'company_data': company_data,
        }