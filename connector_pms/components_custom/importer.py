# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob

_logger = logging.getLogger(__name__)


class GenericImporterCustom(AbstractComponent):
    """ Generic Synchronizer for importing data from backend to Odoo """

    _name = "generic.importer.custom"
    _inherit = "base.importer"

    def _import_dependency(
        self, external_id, binding_model, importer=None, always=False
    ):
        """Import a dependency.

        The importer class is a class or subclass of
        :class:`<Backend>Importer`. A specific class can be defined.

        :param external_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_component: component to use for import
                                   By default: 'importer'
        :type importer_component: Component
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on Backend since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not external_id:
            return
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(external_id):
            if importer is None:
                importer = self.component(usage=self._usage, model_name=binding_model)
            try:
                importer.run(external_id)
            except NothingToDoJob:
                _logger.info(
                    "Dependency import of %s(%s) has been ignored.",
                    binding_model._name,
                    external_id,
                )

    def _import_dependencies(self):
        """Import the dependencies for the record

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _after_import(self, binding):
        return

    def _must_skip(self, binding):
        """Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        return False

    def _filter_data(self, values, fields=None):
        """
        :param values:
        :param fields:
        :return: exclude from 'values' all the fields not in 'fields'
        """
        if not fields:
            return values
        return {k: v for k, v in values.items() if k in fields}

    def _mapper_options(self, binding):
        return {}

    def run(self, external_id, external_data=None, fields=None):
        if not external_data:
            external_data = {}
        lock_name = "import({}, {}, {}, {})".format(
            self.backend_record._name,
            self.backend_record.id,
            self.work.model_name,
            external_id,
        )

        if not external_data:
            # read external data from Backend
            try:
                external_data = self.backend_adapter.read(external_id)
            except IDMissingInBackend:
                return _("Record does not longer exist in Backend")

        # map_data
        # this one knows how to convert backend data to odoo data
        mapper = self.component(usage="import.mapper")

        # convert to odoo data
        internal_data = mapper.map_record(external_data)

        # get_binding
        # this one knows how to link Baclend/Odoo records
        binder = self.component(usage="binder")

        # find if the external id already exists in odoo
        binding = binder.to_internal(external_id)

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the informations
        # will be updated into Odoo
        self.advisory_lock_or_retry(lock_name, retry_seconds=10)

        # if binding not exists, try to link existing internal object
        if not binding:
            binding = binder.to_binding_from_external_key(internal_data)

        skip = self._must_skip(binding)
        if skip:
            return skip

        # import the missing linked resources
        self._import_dependencies()

        # passing info to the mapper
        opts = self._mapper_options(binding)

        # persist data
        if binding:
            # if exists, we update it
            values = internal_data.values(**opts)
            binding.write(self._filter_data(values, fields=fields))
            _logger.debug("%d updated from Backend %s", binding, external_id)
        else:
            # or we create it
            values = internal_data.values(for_create=True, **opts)
            binding = self.model.create(self._filter_data(values, fields=fields))
            _logger.debug("%d created from Backend %s", binding, external_id)

        # finally, we bind both, so the next time we import
        # the record, we'll update the same record instead of
        # creating a new one
        binder.bind(external_id, binding)

        # last update
        self._after_import(binding)
