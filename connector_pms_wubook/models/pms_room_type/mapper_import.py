# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsRoomTypeMapperImport(Component):
    _name = "channel.wubook.pms.room.type.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.room.type"

    direct = [
        ("occupancy", "occupancy"),
        ("availability", "default_availability"),
        ("board", "default_board"),
        ("name", "name"),
        ("price", "list_price"),
        ("min_price", "min_price"),
        ("max_price", "max_price"),
    ]

    @only_create
    @mapping
    def code_type(self, record):
        return {
            "code_type": record["shortname"],
        }

    @mapping
    def property_ids(self, record):
        if self.options.for_create or self.options.get("pms_properties_empty"):
            return {
                "pms_property_ids": [(4, self.backend_record.pms_property_id.id, 0)]
            }
