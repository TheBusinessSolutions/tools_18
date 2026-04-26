# Copyright 2025 PlantBasedStudio
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CommandCenterDelegateWizard(models.TransientModel):
    """Wizard to delegate an item to another user."""
    _name = 'command.center.delegate.wizard'
    _description = 'Delegate Item Wizard'

    source_type = fields.Selection([
        ('activity', 'Activity'),
        ('task', 'Task'),
    ], string="Type", required=True)
    source_id = fields.Integer(string="Source ID", required=True)
    user_id = fields.Many2one(
        'res.users',
        string="Delegate To",
        required=True,
        domain=[('share', '=', False)],
    )

    def action_delegate(self):
        """Delegate the item to the selected user."""
        self.ensure_one()

        if self.source_type == 'activity':
            activity = self.env['mail.activity'].browse(self.source_id)
            if activity.exists():
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get_id(activity.res_model),
                    'res_id': activity.res_id,
                    'activity_type_id': activity.activity_type_id.id,
                    'summary': activity.summary,
                    'note': activity.note,
                    'date_deadline': activity.date_deadline,
                    'user_id': self.user_id.id,
                })
                activity.unlink()
        elif self.source_type == 'task':
            task = self.env['project.task'].browse(self.source_id)
            if task.exists():
                task.write({'user_ids': [(6, 0, [self.user_id.id])]})

        return {'type': 'ir.actions.client', 'tag': 'reload'}
