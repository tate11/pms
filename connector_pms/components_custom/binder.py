# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import models

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import InvalidDataError

_logger = logging.getLogger(__name__)


class BinderCustom(AbstractComponent):
    _name = "base.binder.custom"
    _inherit = "base.binder"

    _internal_alt_id_field = "_internal_alt_id"
    _external_alt_id_field = "_external_alt_id"

    def wrap_record(self, relation, force=False):
        """Give the real record

        :param relation: Odoo real record for which we want to get its binding
        :param force: if this is True and not binding found it creates an
                      empty binding
        :return: binding corresponding to the real record or
                 empty recordset if the record has no binding
        """
        if isinstance(relation, models.BaseModel):
            relation.ensure_one()
        else:
            if not isinstance(relation, int):
                raise InvalidDataError(
                    "The real record (relation) must be a "
                    "regular Odoo record or an id (integer)"
                )
            relation = self.model.browse(relation)
            if not relation:
                raise InvalidDataError("The real record (relation) does not exist")

        binding = self.model.with_context(active_test=False).search(
            [
                (self._odoo_field, "=", relation.id),
                (self._backend_field, "=", self.backend_record.id),
            ]
        )
        if not binding:
            if force:
                binding = self.model.create(
                    {
                        self._odoo_field: relation.id,
                        self._backend_field: self.backend_record.id,
                    }
                )
            else:
                binding = self.model

        if len(binding) > 1:
            raise InvalidDataError("More than one binding found")

        return binding

    def _get_internal_record_domain(self, values):
        return [(k, "=", v) for k, v in values.items()]

    def _get_internal_record_alt(self, model_name, values):
        domain = self._get_internal_record_domain(values)
        return self.env[model_name].search(domain)

    def to_binding_from_external_key(self, mapper):
        """
        :param mapper:
        :return: binding with alternate external key
        """
        internal_alt_id = getattr(self, self._internal_alt_id_field, None)
        if internal_alt_id:
            if isinstance(internal_alt_id, str):
                internal_alt_id = [internal_alt_id]
            all_values = mapper.values(for_create=True)
            if any([x not in all_values for x in internal_alt_id]):
                raise InvalidDataError(
                    "The alternative id (_internal_alt_id) '%s' must exist on mapper"
                    % internal_alt_id
                )
            model_name = self.unwrap_model()
            id_values = {x: all_values[x] for x in internal_alt_id}
            record = self._get_internal_record_alt(model_name, id_values)
            if len(record) > 1:
                raise InvalidDataError(
                    "More than one internal records found. "
                    "The alternate internal id field '%s' is not unique"
                    % (internal_alt_id,)
                )
            if record:
                values = {
                    k: all_values[k]
                    for k in set(self.model._model_fields) & set(all_values)
                }
                if self._odoo_field in values:
                    if values[self._odoo_field] != record.id:
                        raise InvalidDataError(
                            "The id found on the mapper ('%i') "
                            "is not the one expected ('%i')"
                            % (values[self._odoo_field], record.id)
                        )
                else:
                    values[self._odoo_field] = record.id

                binding = self.wrap_record(record)
                if not binding:
                    binding = self.model.create(values)
                _logger.debug("%d linked from Backend", binding)
                return binding

        return self.model

    def _get_external_record_domain(self, values):
        return [(k, "=", v) for k, v in values.items()]

    def _get_external_record_alt(self, values):
        domain = self._get_external_record_domain(values)
        adapter = self.component(usage="backend.adapter")
        return adapter.search_read(domain)

    def to_binding_from_internal_key(self, relation):
        """
        :param relation:
        :return: binding
        """
        alt_id = getattr(self, self._external_alt_id_field, None)
        if alt_id:
            if isinstance(alt_id, str):
                alt_id = [alt_id]
            virtual_binding = {
                x: getattr(relation, x, self.model[x]) for x in self.model._fields
            }
            export_mapper = self.component(usage="export.mapper")
            mapper_external_data = export_mapper.map_record(virtual_binding)
            all_external_values = mapper_external_data.values(for_create=True)
            if any([x not in all_external_values for x in alt_id]):
                raise InvalidDataError(
                    "The alternative id (_internal_alt_id) '%s' must exist on mapper"
                    % alt_id
                )
            id_values = {x: all_external_values[x] for x in alt_id}
            record = self._get_external_record_alt(id_values)
            if record:
                if len(record) > 1:
                    raise InvalidDataError(
                        "More than one external records found. "
                        "The alternate external id field '%s' is not "
                        "unique in the backend" % (alt_id,)
                    )
                record = record[0]
                import_mapper = self.component(usage="import.mapper")
                mapper_internal_data = import_mapper.map_record(record)
                all_internal_values = mapper_internal_data.values(for_create=True)
                include_fields = set(self.model._model_fields) & set(
                    all_internal_values
                )

                adapter = self.component(usage="backend.adapter")
                external_id = record[adapter._id]

                importer = self.component(usage="direct.record.importer")

                binding = self.wrap_record(relation)
                if binding:
                    current_external_id = self.to_external(binding)
                    if not current_external_id:
                        self.bind(external_id, binding)
                    else:
                        if current_external_id != external_id:
                            raise InvalidDataError(
                                "Integrity error: The current external_id '%s' "
                                "should be the same as the one we are trying "
                                "to assign '%s'" % (current_external_id, external_id)
                            )
                else:
                    importer.run(
                        external_id, external_data=record, fields=include_fields
                    )
                    binding = self.to_internal(external_id)
                if not binding:
                    raise InvalidDataError(
                        "The binding with external id '%s' "
                        "not found and it should be" % external_id
                    )
                _logger.debug("%d linked to Backend", binding)
                return binding

        return self.model


# TODO: naming the methods more intuitively
# TODO: unify both methods, they have a lot of common code
# TODO: extract parts to smaller and common methods reused by the main mothods
