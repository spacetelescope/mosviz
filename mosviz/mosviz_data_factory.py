from __future__ import absolute_import, division, print_function

import numpy as np

from glue.core.data_factories.helpers import has_extension
from glue.core.data import Component, Data
from glue.core.component import CategoricalComponent
from glue.config import data_factory, qglue_parser
from glue.core.data_factories.astropy_table import is_readable_by_astropy, astropy_table_read


@data_factory(label="MOSViz Table (ascii.ecsv)",
              identifier=is_readable_by_astropy,
              priority=3)
def mosviz_tabular_data(*args, **kwargs):
    """
     Build a data set from a table. We restrict ourselves to tables
     with 1D columns.

     All arguments are passed to
         astropy.table.Table.read(...).
     """

    result = Data()

    table = astropy_table_read(*args, **kwargs)

    result.meta = table.meta

    # Loop through columns and make component list
    for column_name in table.columns:
        c = table[column_name]
        u = c.unit if hasattr(c, 'unit') else c.units

        if table.masked:
            # fill array for now
            try:
                c = c.filled(fill_value=np.nan)
            except (ValueError, TypeError):  # assigning nan to integer dtype
                c = c.filled(fill_value=-1)

        dtype = c.dtype.type
        if dtype is np.string_ or dtype is np.str_:
            nc = CategoricalComponent(c, units=u)
        else:
            nc = Component.autotyped(c, units=u)
        result.add_component(nc, column_name)

    return result
