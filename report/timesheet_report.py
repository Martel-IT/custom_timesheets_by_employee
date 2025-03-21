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
        Get timesheet submission and approval information
        """
        # Query for hr.timesheet records
        domain = [('user_id', '=', user_id)]
        if from_date:
            domain.append(('date_start', '>=', from_date))
        if to_date:
            domain.append(('date_start', '<=', to_date))
        
        timesheet = self.env['hr.timesheet'].search(domain, limit=1)
        
        result = {
            'submitted_date': False,
            'approved_date': False,
            'reviewer_name': 'Not Assigned'
        }
        
        if timesheet:
            # Get submission date from mail.message
            mail_message = self.env['mail.message'].search([
                ('model', '=', 'hr.timesheet'),
                ('res_id', '=', timesheet.id),
                ('subtype_id.name', '=', 'Timesheet Submitted')
            ], limit=1)
            
            if mail_message:
                result['submitted_date'] = mail_message.date
            else:
                # Fallback to create_date if no submission message found
                result['submitted_date'] = timesheet.create_date
            
            # Get approval date from write_date if state is 'approved'
            if timesheet.state == 'approved':
                result['approved_date'] = timesheet.write_date
            
            # Get reviewer information
            if timesheet.reviewer_id:
                reviewer = self.env['hr.employee'].search([('user_id', '=', timesheet.reviewer_id.id)], limit=1)
                if reviewer:
                    result['reviewer_name'] = reviewer.name
                else:
                    result['reviewer_name'] = timesheet.reviewer_id.name
        
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
<<<<<<< HEAD
        
        # Get submission and approval information
        timesheet_info = self.get_timesheet_submission_approval_info(
            docs.user_id[0].id, docs.from_date, docs.to_date
        )
=======
>>>>>>> ee1c3299dc1ff30dfb8401e641f3761c12213ed1

        return {
            'doc_ids': self.ids,
            'doc_model': 'timesheet.report',
            'docs': docs,
            'employee': employee,
            'period': period,
            'timesheet_data': timesheet_data,
            'res_company': company,
            'company_data': company_data,
<<<<<<< HEAD
            'timesheet_submitted_date': timesheet_info['submitted_date'],
            'timesheet_approved_date': timesheet_info['approved_date'],
            'reviewer_name': timesheet_info['reviewer_name'],
=======
>>>>>>> ee1c3299dc1ff30dfb8401e641f3761c12213ed1
        }
