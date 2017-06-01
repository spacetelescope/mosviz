# Code to provide backward-compatibility with old versions of glue

from __future__ import absolute_import, division, print_function

from glue.core.qt.data_combo_helper import ComponentIDComboHelper as OriginalComponentIDComboHelper
from glue.core.hub import HubListener

__all__ = ['ComponentIDComboHelper']


class ComponentIDComboHelper(OriginalComponentIDComboHelper):

    # TODO: this is a patched version to match glue 0.11 - can be removed once
    # we support glueviz >= 0.11

    def __init__(self, component_id_combo, data_collection=None, data=None,
                 visible=True, numeric=True, categorical=True, default_index=0):

        HubListener.__init__(self)

        self._visible = visible
        self._numeric = numeric
        self._categorical = categorical
        self._component_id_combo = component_id_combo

        if data is None:
            self._data = []
        else:
            self._data = [data]

        self._data_collection = data_collection
        if data_collection is not None:
            if data_collection.hub is None:
                raise ValueError("Hub on data collection is not set")
            else:
                self.hub = data_collection.hub

        self.default_index = default_index

        if data is not None:
            self.refresh()

    def register_to_hub(self, hub):
        pass
