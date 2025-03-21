from odoo import api, fields, models
from collections import defaultdict
from datetime import datetime


class ReportTimesheet(models.AbstractModel):
    _name = 'report.timesheets_by_employee.report_timesheets'
    _description = 'Timesheet Report'

    def format_time_24h(self, hours):
        """Convert float hours to 24h format string"""
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def get_timesheets(self, docs):
        domain = [('user_id', '=', docs.user_id[0].id)]
        if docs.from_date:
            domain.append(('date', '>=', docs.from_date))
        if docs.to_date:
            domain.append(('date', '<=', docs.to_date))

        record = self.env['account.analytic.line'].search(domain, order='project_id, task_id, date')

        timesheet_data = {
            'projects': defaultdict(lambda: {'tasks': defaultdict(lambda: {'entries': [], 'subtotal': 0.0}), 'subtotal': 0.0}),
            'total': 0.0,
            'total_hours_display': '00:00'
        }

        for rec in record:
            project_name = rec.project_id.name or 'No Project'
            task_name = rec.task_id.name or 'No Task'

            entry = {
                'date': rec.date,
                'description': rec.name or '',
                'duration': self.format_time_24h(rec.unit_amount),
                'hours': rec.unit_amount
            }

            timesheet_data['projects'][project_name]['tasks'][task_name]['entries'].append(entry)
            timesheet_data['projects'][project_name]['tasks'][task_name]['subtotal'] += rec.unit_amount
            timesheet_data['projects'][project_name]['subtotal'] += rec.unit_amount
            timesheet_data['total'] += rec.unit_amount

        # Format subtotals
        for project in timesheet_data['projects'].values():
            project['subtotal_display'] = self.format_time_24h(project['subtotal'])
            for task in project['tasks'].values():
                task['subtotal_display'] = self.format_time_24h(task['subtotal'])

        timesheet_data['total_hours_display'] = self.format_time_24h(timesheet_data['total'])

        return timesheet_data

    def get_timesheet_submission_approval_info(self, user_id, from_date, to_date):
        """
        Get timesheet submission and approval information from hr_timesheet.sheet
        """
        result = {
            'submitted_date': False,
            'approved_date': False,
            'reviewer_name': 'Not Assigned'
        }
        
        # Find timesheet sheet data
        domain = [('user_id', '=', user_id)]
        if from_date:
            domain.append(('date_start', '>=', from_date))
        if to_date:
            domain.append(('date_end', '<=', to_date))
        
        # If no specific date range, just get the latest timesheet for the user
        if not from_date and not to_date:
            domain = [('user_id', '=', user_id)]
        
        timesheet_sheet = self.env['hr_timesheet.sheet'].search(domain, order='date_end DESC', limit=1)
        
        if timesheet_sheet:
            # For submission date, check when the state changed to 'confirm'
            if timesheet_sheet.state in ['confirm', 'done']:
                result['submitted_date'] = timesheet_sheet.write_date
            else:
                result['submitted_date'] = timesheet_sheet.create_date
            
            # For approval date, check if state is 'done'
            if timesheet_sheet.state == 'done':
                result['approved_date'] = timesheet_sheet.write_date
            
            # Get reviewer information
            if hasattr(timesheet_sheet, 'reviewer_id') and timesheet_sheet.reviewer_id:
                reviewer = self.env['hr.employee'].search([('user_id', '=', timesheet_sheet.reviewer_id.id)], limit=1)
                result['reviewer_name'] = reviewer.name if reviewer else timesheet_sheet.reviewer_id.name
            elif hasattr(timesheet_sheet, 'manager_id') and timesheet_sheet.manager_id:
                result['reviewer_name'] = timesheet_sheet.manager_id.name
        
        # If no timesheet sheet found or no reviewer found, try to get from employee's manager
        if not result['reviewer_name'] or result['reviewer_name'] == 'Not Assigned':
            employee = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
            if employee and employee.parent_id:
                result['reviewer_name'] = employee.parent_id.name
            elif employee and employee.department_id and employee.department_id.manager_id:
                result['reviewer_name'] = employee.department_id.manager_id.name
        
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        company = self.env.company.sudo()
        logo = False
        if company.logo:
            logo = company.logo
        company_data = {
            'name': company.name,
            'email': company.email,
            'city': company.city,
            'street': company.street,
            'zip': company.zip,
            'state_id': company.state_id and company.state_id.name,
            'phone': company.phone,
            'website': company.website,
        }

        employee = self.env['hr.employee'].search([('user_id', '=', docs.user_id[0].id)], limit=1)

        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date} To {docs.to_date}"
        elif docs.from_date:
            period = f"From {docs.from_date}"
        elif docs.to_date:
            period = f"To {docs.to_date}"

        timesheet_data = self.get_timesheets(docs)
        
        # Get submission and approval information
        timesheet_info = self.get_timesheet_submission_approval_info(
            docs.user_id[0].id, docs.from_date, docs.to_date
        )

        return {
            'doc_ids': self.ids,
            'doc_model': 'timesheet.report',
            'docs': docs,
            'employee': employee,
            'period': period,
            'timesheet_data': timesheet_data,
            'res_company': company,
            'company_data': company_data,
            'timesheet_submitted_date': timesheet_info['submitted_date'],
            'timesheet_approved_date': timesheet_info['approved_date'],
            'reviewer_name': timesheet_info['reviewer_name'],
        }
