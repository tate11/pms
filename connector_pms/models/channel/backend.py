# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ChannelBackend(models.Model):
    _name = "channel.backend"
    _description = "Channel PMS Backend"

    name = fields.Char("Name", required=True)

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        required=True,
        ondelete="cascade",
    )

    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Referenced Model",
        required=True,
        ondelete="cascade",
        domain=lambda self: [("model", "in", self._get_channel_backend_model_names())],
    )

    @property
    def child(self):
        self.ensure_one()
        child_backends = self.env[self.model_id.model].search(
            [
                ("parent_id", "=", self.id),
            ]
        )
        if len(child_backends) > 1:
            raise ValidationError(
                _(
                    "Inconsistency detected. More than one "
                    "backend's child found for the same parent"
                )
            )
        return child_backends

    @api.model
    def _get_channel_backend_model_names(self):
        res = []
        return res

    def channel_data(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_id.model,
            "views": [[False, "form"]],
            "context": not self.child and {"default_parent_id": self.id},
            "res_id": self.child.id,
            "target": "new",
        }
