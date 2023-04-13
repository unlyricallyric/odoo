# -*- coding: utf-8 -*-
# Odoo E-commerce Cartrover connector developed by Digital Star.

{
    "name": "DigitalStar Connector - Cartrover",
    "version": "1.1.0",
    "author": "Digital Star",
    "website": "www.digitalstar.ca",
    "summary": """Cartrover connector developed by Digital Star""",
    "description": """
          This module is developed to connect Odoo and Cartrover platform.
     """,
    "category": "Sales/Sales",
    "depends": [
        "base",
        "sale_management",  # Sales
        "stock",  # Inventory
        "purchase",  # Purchase
        "contacts",  # Contacts
        "account",  # Invoicing
    ],
    "data": [
        'views/res_config_settings_views.xml'
    ],
    "demo": [],
    "images": [],
    "license": "AGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
