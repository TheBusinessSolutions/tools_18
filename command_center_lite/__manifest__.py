# Copyright 2025 PlantBasedStudio
# License OPL-1 - See LICENSE file for full copyright and licensing details.

{
    'name': 'Command Center Lite - Unified Tasks & Activities Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'All-in-one Kanban dashboard for tasks, activities and to-dos with priority management',
    'description': """
Command Center Lite - Unified Tasks & Activities Dashboard
==========================================================

Stop switching between apps! Command Center Lite aggregates all your Odoo Activities
and Project Tasks into a single, priority-based Kanban board.

Key Features
------------
* **Unified Dashboard**: See all activities (calls, meetings, to-dos) and project tasks in one view
* **Smart Priority System**: Automatic organization by urgency (Critical, High, Medium, Low)
* **Quick Actions**: Mark as Done, Cancel, Delegate, Archive - without leaving the board
* **Powerful Filters**: Filter by deadline, type, project, partner, and more
* **Time-based Views**: Today, Overdue, This Week, No Deadline

Perfect For
-----------
* Project Managers tracking multiple projects
* Consultants juggling client activities
* Team Leaders monitoring team workload
* Anyone who wants to stay organized in Odoo

Compatibility
-------------
* Odoo 18 Community Edition
* Odoo 18 Enterprise Edition
* Odoo.sh

Looking for more? Check out Command Center Pro for CRM integration, calendar events, and advanced features!
    """,
    'author': 'PlantBasedStudio',
    'website': 'https://github.com/PlantBasedStudio',
    'license': 'OPL-1',
    'depends': [
        'base',
        'mail',
        'project',
    ],
    'data': [
        'security/command_center_security.xml',
        'security/ir.model.access.csv',
        'wizard/delegate_wizard_views.xml',
        'views/command_center_item_views.xml',
        'views/command_center_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'command_center_lite/static/src/scss/command_center.scss',
        ],
    },
    'images': [
        'images/main.gif',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
