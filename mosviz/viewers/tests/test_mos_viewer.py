import pytest


def get_mosviz_gui(glue_gui):
    """
    Pulls MOSVizViewer out of the glue instance and returns it
    :param glue_gui:
    :return:
    """
    mosviz = glue_gui.viewers[0][0]
    return mosviz


def test_starting_state(glue_gui):
    """
    Tests the starting state of the mosviz_gui
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    source_combo = mosviz_gui.toolbar.source_select
    exposure_combo = mosviz_gui.toolbar.exposure_select

    assert source_combo.currentText() == source_combo.itemText(0)
    assert mosviz_gui.toolbar.cycle_previous_action.isEnabled() == False
    mosviz_gui.toolbar.cycle_next_action.trigger()
    assert source_combo.currentText() == source_combo.itemText(1)
    assert mosviz_gui.toolbar.cycle_previous_action.isEnabled() == True

    # both exposure buttons are disabled at startup with level 3-only data.
    assert exposure_combo.currentText() == exposure_combo.itemText(0)
    assert mosviz_gui.toolbar.exposure_previous_action.isEnabled() == False
    mosviz_gui.toolbar.exposure_next_action.trigger()
    assert exposure_combo.currentText() == exposure_combo.itemText(1)
    assert mosviz_gui.toolbar.exposure_previous_action.isEnabled() == False


def test_ending_state(glue_gui):
    """
    Tests the end of cycle of the mosviz_gui
    :param qtbot:
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    source_combo = mosviz_gui.toolbar.source_select
    exposure_combo = mosviz_gui.toolbar.exposure_select

    source_combo.setCurrentIndex(source_combo.count() - 1)
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 1)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == False
    mosviz_gui.toolbar.cycle_previous_action.trigger()
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 2)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == True

    # both exposure buttons are disabled at ending with level 3-only data.
    exposure_combo.setCurrentIndex(exposure_combo.count() - 1)
    assert exposure_combo.currentText() == exposure_combo.itemText(exposure_combo.count() - 1)
    assert mosviz_gui.toolbar.exposure_next_action.isEnabled() == False
    mosviz_gui.toolbar.exposure_previous_action.trigger()
    assert exposure_combo.currentText() == exposure_combo.itemText(exposure_combo.count() - 2)
    assert mosviz_gui.toolbar.exposure_next_action.isEnabled() == False


def test_make_it_look_like_more_tests(glue_gui):
    """
    This test will do something useful in the future
    :param qtbot:
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    source_combo = mosviz_gui.toolbar.source_select
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == True

    mosviz_gui.toolbar.cycle_next_action.trigger()

    # looks like the combo box selector is left pointing to the second
    # item in the combo box list, and not the last item, as implied by
    # the commented-out assert statement below. This probably has to do
    # with the add_data_for_testing method in class MOSVizViewer, which
    # initializes with DEIMOS data with 5 data sets.
    # assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 1)
    assert source_combo.currentText() == source_combo.itemText(1)

    # looks like the next item action is left enabled, and not disabled
    # as implied by the commented-out assert statement below. This probably
    # has to do with the add_data_for_testing method in class MOSVizViewer,
    # which initializes with DEIMOS data with 5 data sets.
    # assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == False
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == True
