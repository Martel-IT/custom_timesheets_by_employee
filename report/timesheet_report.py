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
        """Fetch timesheets for the given employee and date range."""
        domain = [('user_id', '=', docs.user_id.id)]
        if docs.from_date:
            domain.append(('date', '>=', docs.from_date))
        if docs.to_date:
            domain.append(('date', '<=', docs.to_date))

        records = self.env['account.analytic.line'].search(domain, order='date')

        timesheets = []
        total = 0.0

        for rec in records:
            # Convert duration to HH:MM format
            hours = int(rec.unit_amount)
            minutes = int((rec.unit_amount - hours) * 60)
            duration_str = f"{hours:02d}:{minutes:02d}"

            timesheets.append({
                'project': rec.project_id.name or 'No Project',
                'user': rec.user_id.partner_id.name,
                'duration': duration_str,
                'date': rec.date,
                'description': rec.name or ''
            })
            total += rec.unit_amount

        # Convert total duration to HH:MM
        total_hours = int(total)
        total_minutes = int((total - total_hours) * 60)
        total_str = f"{total_hours:02d}:{total_minutes:02d}"

        return timesheets, total_str

    @api.model
    def _get_report_values(self, docids, data=None):
        """Fetch report values and ensure required data is included."""
        if data is None:
            data = {}

        # ✅ Ensure `docs` is correctly defined
        docs = self.env['timesheet.report'].browse(docids)

        if not docs:
            raise ValueError("No valid `timesheet.report` records found for given docids.")

        # ✅ Employee Information
        identification = []
        employee = self.env['hr.employee'].search([('user_id', '=', docs.user_id.id)], limit=1)
        if employee:
            identification.append({'id': employee.id, 'name': employee.name})

        # ✅ Period Formatting
        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date} To {docs.to_date}"
        elif docs.from_date:
            period = f"From {docs.from_date}"
        elif docs.to_date:
            period = f"To {docs.to_date}"

        # ✅ Fetch Timesheets
        timesheets, total = self.get_timesheets(docs)

        # ✅ Get Company Data
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

        # ✅ Ensure `timesheet_data` exists
        timesheet_data = {
            'total': total,
            'projects': {}
        }

        for record in timesheets:
            project_name = record['project']
            if project_name not in timesheet_data['projects']:
                timesheet_data['projects'][project_name] = {
                    'entries': [],
                    'subtotal': 0.0
                }
            timesheet_data['projects'][project_name]['entries'].append(record)

            # Convert HH:MM to float and accumulate subtotal
            hours, minutes = map(int, record['duration'].split(':'))
            duration_float = hours + minutes / 60.0
            timesheet_data['projects'][project_name]['subtotal'] += duration_float

        return {
            'doc_ids': docids,
            'docs': docs,
            'timesheets': timesheets,
            'total': total,
            'identification': identification,
            'period': period,
            'company_data': company_data,  # ✅ Now included
            'timesheet_data': timesheet_data  # ✅ Now included
        }