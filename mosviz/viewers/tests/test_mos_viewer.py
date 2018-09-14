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

    assert source_combo.currentText() == source_combo.itemText(0)
    assert mosviz_gui.toolbar.cycle_previous_action.isEnabled() == False

    mosviz_gui.toolbar.cycle_next_action.trigger()
    assert source_combo.currentText() == source_combo.itemText(1)
    assert mosviz_gui.toolbar.cycle_previous_action.isEnabled() == True


def test_ending_state(glue_gui):
    """
    Tests the end of cycle of the mosviz_gui
    :param qtbot:
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    source_combo = mosviz_gui.toolbar.source_select

    source_combo.setCurrentIndex(source_combo.count() - 1)
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 1)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == False

    mosviz_gui.toolbar.cycle_previous_action.trigger()
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 2)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == True
