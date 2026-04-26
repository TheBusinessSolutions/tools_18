# Copyright 2025 PlantBasedStudio
# License OPL-1 - See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

PRIORITY_LEVELS = [
    ('1_critical', 'Critical'),
    ('2_high', 'High'),
    ('3_medium', 'Medium'),
    ('4_low', 'Low'),
]

class CommandCenterItem(models.Model):
    """Unified item model aggregating activities and tasks.

    This is a SQL view model (_auto = False) that aggregates data from:
    - mail.activity: All user activities
    - project.task: All project tasks assigned to user

    Items are displayed in a unified Kanban/List view with priority scoring.
    """
    _name = 'command.center.item'
    _description = 'Command Center Item'
    _auto = False
    _order = 'priority_sequence ASC, priority_score DESC, date_deadline ASC, id'

    name = fields.Char(string="Name", readonly=True)
    source_type = fields.Selection([
        ('activity', 'Activity'),
        ('task', 'Task'),
    ], string="Type", readonly=True)
    source_model = fields.Char(string="Source Model", readonly=True)
    source_id = fields.Integer(string="Source ID", readonly=True)
    res_id = fields.Integer(string="Related Document ID", readonly=True)

    date_deadline = fields.Date(string="Deadline", readonly=True)
    date_create = fields.Datetime(string="Created On", readonly=True)
    days_until_deadline = fields.Integer(string="Days Until Deadline", readonly=True)
    is_overdue = fields.Boolean(string="Overdue", readonly=True)

    priority_score = fields.Integer(string="Priority Score", readonly=True)
    priority_sequence = fields.Integer(string="Priority Sequence", readonly=True)

    user_id = fields.Many2one('res.users', string="Assigned To", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    project_id = fields.Many2one('project.project', string="Project", readonly=True)
    activity_type_id = fields.Many2one('mail.activity.type', string="Activity Type", readonly=True)

    summary = fields.Char(string="Summary", readonly=True)
    note = fields.Html(string="Note", readonly=True)

    @api.model
    def _read_group_priority_level(self, priorities, domain):
        """Return all priority levels in the correct order for Kanban columns."""
        return [key for key, label in PRIORITY_LEVELS]

    priority_level = fields.Selection(
        PRIORITY_LEVELS,
        string="Priority",
        readonly=True,
        group_expand='_read_group_priority_level',
    )

    def init(self):
        """Create or replace the SQL view for aggregating items."""
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- Activities aggregation
                SELECT
                    -- Unique ID: prefix 1 for activities
                    (10000000 + ma.id) AS id,
                    COALESCE(ma.summary, 'Activity') AS name,
                    'activity' AS source_type,
                    ma.res_model AS source_model,
                    ma.id AS source_id,
                    ma.res_id AS res_id,
                    ma.date_deadline AS date_deadline,
                    ma.create_date AS date_create,
                    -- Days until deadline calculation
                    CASE
                        WHEN ma.date_deadline IS NULL THEN NULL
                        ELSE (ma.date_deadline - CURRENT_DATE)
                    END AS days_until_deadline,
                    -- Is overdue flag
                    CASE
                        WHEN ma.date_deadline IS NULL THEN FALSE
                        ELSE ma.date_deadline < CURRENT_DATE
                    END AS is_overdue,
                    -- Priority score calculation
                    CASE
                        WHEN ma.date_deadline IS NULL THEN 10
                        WHEN ma.date_deadline < CURRENT_DATE THEN 100
                        WHEN ma.date_deadline = CURRENT_DATE THEN 80
                        WHEN ma.date_deadline = CURRENT_DATE + 1 THEN 60
                        WHEN ma.date_deadline <= CURRENT_DATE + 7 THEN 40
                        ELSE 20
                    END AS priority_score,
                    -- Priority sequence for column ordering (1=critical, 2=high, 3=medium, 4=low)
                    CASE
                        WHEN ma.date_deadline IS NULL THEN 4
                        WHEN ma.date_deadline < CURRENT_DATE THEN 1
                        WHEN ma.date_deadline <= CURRENT_DATE + 1 THEN 1
                        WHEN ma.date_deadline <= CURRENT_DATE + 3 THEN 2
                        WHEN ma.date_deadline <= CURRENT_DATE + 7 THEN 3
                        ELSE 4
                    END AS priority_sequence,
                    -- Priority level derived from score (prefixed for correct sorting)
                    CASE
                        WHEN ma.date_deadline IS NULL THEN '4_low'
                        WHEN ma.date_deadline < CURRENT_DATE THEN '1_critical'
                        WHEN ma.date_deadline <= CURRENT_DATE + 1 THEN '1_critical'
                        WHEN ma.date_deadline <= CURRENT_DATE + 3 THEN '2_high'
                        WHEN ma.date_deadline <= CURRENT_DATE + 7 THEN '3_medium'
                        ELSE '4_low'
                    END AS priority_level,
                    ma.user_id AS user_id,
                    -- Try to get partner from the linked record if it's a partner-related model
                    CASE
                        WHEN ma.res_model = 'res.partner' THEN ma.res_id
                        ELSE NULL
                    END AS partner_id,
                    NULL::integer AS project_id,
                    ma.activity_type_id AS activity_type_id,
                    ma.summary AS summary,
                    ma.note AS note
                FROM mail_activity ma
                WHERE ma.active = TRUE

                UNION ALL

                -- Tasks aggregation
                SELECT
                    -- Unique ID: prefix 2 for tasks
                    (20000000 + pt.id) AS id,
                    pt.name AS name,
                    'task' AS source_type,
                    'project.task' AS source_model,
                    pt.id AS source_id,
                    pt.id AS res_id,
                    pt.date_deadline AS date_deadline,
                    pt.create_date AS date_create,
                    -- Days until deadline calculation
                    CASE
                        WHEN pt.date_deadline IS NULL THEN NULL
                        ELSE (pt.date_deadline::date - CURRENT_DATE)
                    END AS days_until_deadline,
                    -- Is overdue flag
                    CASE
                        WHEN pt.date_deadline IS NULL THEN FALSE
                        ELSE pt.date_deadline::date < CURRENT_DATE
                    END AS is_overdue,
                    -- Priority score calculation
                    CASE
                        WHEN pt.date_deadline IS NULL THEN 10
                        WHEN pt.date_deadline::date < CURRENT_DATE THEN 100
                        WHEN pt.date_deadline::date = CURRENT_DATE THEN 80
                        WHEN pt.date_deadline::date = CURRENT_DATE + 1 THEN 60
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 7 THEN 40
                        ELSE 20
                    END AS priority_score,
                    -- Priority sequence for column ordering (1=critical, 2=high, 3=medium, 4=low)
                    CASE
                        WHEN pt.date_deadline IS NULL THEN 4
                        WHEN pt.date_deadline::date < CURRENT_DATE THEN 1
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 1 THEN 1
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 3 THEN 2
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 7 THEN 3
                        ELSE 4
                    END AS priority_sequence,
                    -- Priority level derived from score (prefixed for correct sorting)
                    CASE
                        WHEN pt.date_deadline IS NULL THEN '4_low'
                        WHEN pt.date_deadline::date < CURRENT_DATE THEN '1_critical'
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 1 THEN '1_critical'
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 3 THEN '2_high'
                        WHEN pt.date_deadline::date <= CURRENT_DATE + 7 THEN '3_medium'
                        ELSE '4_low'
                    END AS priority_level,
                    -- Get first assigned user from task
                    (SELECT rel.user_id FROM project_task_user_rel rel
                    WHERE rel.task_id = pt.id LIMIT 1) AS user_id,
                    pt.partner_id AS partner_id,
                    pt.project_id AS project_id,
                    NULL::integer AS activity_type_id,
                    pt.description AS summary,
                    pt.description AS note
                FROM project_task pt
                LEFT JOIN project_task_type ptt ON ptt.id = pt.stage_id
                WHERE pt.active = TRUE
                AND (ptt.fold IS NULL OR ptt.fold = FALSE)
                AND (pt.state IS NULL OR pt.state NOT IN ('1_done', '1_canceled'))
            )
        """ % self._table)

    def action_view_origin(self):
        """Open the original record (activity's linked record or task)."""
        self.ensure_one()

        if self.source_type == 'activity':
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.source_model,
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.source_type == 'task':
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }

        raise UserError(_("Cannot open this item."))

    def action_mark_done(self):
        """Mark the item as done based on its type."""
        self.ensure_one()

        if self.source_type == 'activity':
            return self._mark_activity_done()
        elif self.source_type == 'task':
            return self._mark_task_done()

        raise UserError(_("Cannot mark this item as done."))

    def _mark_activity_done(self):
        """Mark the underlying activity as done by deleting it."""
        activity = self.env['mail.activity'].browse(self.source_id)
        if activity.exists():
            activity.unlink()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _mark_task_done(self):
        """Mark the underlying task as done by setting state to done."""
        task = self.env['project.task'].browse(self.source_id)
        if not task.exists():
            raise UserError(_("Task not found."))

        task.write({'state': '1_done'})

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_cancel(self):
        """Cancel/dismiss the item."""
        self.ensure_one()

        if self.source_type == 'activity':
            activity = self.env['mail.activity'].browse(self.source_id)
            if activity.exists():
                activity.unlink()
        elif self.source_type == 'task':
            task = self.env['project.task'].browse(self.source_id)
            if task.exists():
                task.write({'state': '1_canceled'})

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_archive(self):
        """Archive the item (only for tasks, activities use done/cancel)."""
        self.ensure_one()

        if self.source_type == 'task':
            task = self.env['project.task'].browse(self.source_id)
            if task.exists():
                task.write({'active': False})

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_delegate(self):
        """Open wizard to delegate item to another user."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Delegate'),
            'res_model': 'command.center.delegate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_source_type': self.source_type,
                'default_source_id': self.source_id,
            },
        }

    def _get_source_icon(self):
        """Return the icon class for this item's source type."""
        icons = {
            'activity': 'fa-clipboard',
            'task': 'fa-check',
        }
        return icons.get(self.source_type, 'fa-circle')

    def _get_priority_color(self):
        """Return the color class for this item's priority level."""
        colors = {
            '1_critical': 'danger',
            '2_high': 'warning',
            '3_medium': 'info',
            '4_low': 'secondary',
        }
        return colors.get(self.priority_level, 'secondary')
