# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ChannelBackend(models.Model):
    _inherit = "channel.backend"

    @api.model
    def _get_channel_backend_model_names(self):
        res = super(ChannelBackend, self)._get_channel_backend_model_names()
        res.append("channel.wubook.backend")
        return res


class ChannelWubookBackend(models.Model):
    _name = "channel.wubook.backend"
    _inherit = "connector.backend"
    _inherits = {"channel.backend": "parent_id"}
    _description = "Channel Wubook PMS Backend"

    parent_id = fields.Many2one(
        comodel_name="channel.backend",
        string="Parent Channel Backend",
        required=True,
        ondelete="cascade",
    )

    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)

    url = fields.Char(
        string="Url", default="https://wired.wubook.net/xrws/", required=True
    )
    property_code = fields.Char(string="Property code", required=True)
    pkey = fields.Char(string="PKey", required=True)

    def import_room_types(self):
        for rec in self:
            rec.env["channel.wubook.pms.room.type"].with_delay().import_data(
                backend_record=rec
            )

    def export_room_types(self):
        for rec in self:
            rec.env["channel.wubook.pms.room.type"].with_delay().export_data(
                backend_record=rec
            )

    _sql_constraints = [
        (
            "backend_parent_uniq",
            "unique(parent_id)",
            "Only one backend child is allowed for each generic backend.",
        ),
    ]
