# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeDelayedBatchImporter(Component):
    _name = "channel.wubook.pms.room.type.delayed.batch.importer"
    _inherit = "channel.wubook.delayed.batch.importer"

    _apply_on = "channel.wubook.pms.room.type"


class ChannelWubookPmsRoomTypeDirectBatchImporter(Component):
    _name = "channel.wubook.pms.room.type.direct.batch.importer"
    _inherit = "channel.wubook.direct.batch.importer"

    _apply_on = "channel.wubook.pms.room.type"


class ChannelWubookPmsRoomTypeImporter(Component):
    _name = "channel.wubook.pms.room.type.importer"
    _inherit = "channel.wubook.importer"

    _apply_on = "channel.wubook.pms.room.type"

    def _mapper_options(self, binding):
        if binding:
            return {"pms_properties_empty": bool(binding.pms_property_ids)}
        return {}
