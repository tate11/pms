# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PMS Connector Wubook",
    "summary": "Channel PMS connector Wubook",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "category": "Connector",
    "website": "https://github.com/OCA/pms",
    "author": "Eric Antones <eantones@nuobit.com>,Odoo Community Association (OCA)",
    "depends": [
        "connector_pms",
    ],
    "data": [
        "data/queue_data.xml",
        "data/queue_job_function_data.xml",
        "security/ir.model.access.csv",
        "views/channel_wubook_backend_views.xml",
        "views/pms_room_type_views.xml",
    ],
    "demo": [],
}
