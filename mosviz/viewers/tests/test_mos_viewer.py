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


def test_exposure_at_start_state(glue_gui):
    """
    Tests the exposure combobox when at the first index
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    exposure_combo = mosviz_gui.toolbar.exposure_select

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

    source_combo.setCurrentIndex(source_combo.count() - 1)
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 1)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == False
    mosviz_gui.toolbar.cycle_previous_action.trigger()
    assert source_combo.currentText() == source_combo.itemText(source_combo.count() - 2)
    assert mosviz_gui.toolbar.cycle_next_action.isEnabled() == True


def test_exposure_at_end_state(glue_gui):
    """
    Test the exposure combobox when at the last index
    :param glue_gui:
    :return:
    """
    mosviz_gui = get_mosviz_gui(glue_gui)
    exposure_combo = mosviz_gui.toolbar.exposure_select
    source_combo = mosviz_gui.toolbar.source_select

    # both exposure buttons are disabled at ending with level 3-only data.
    source_combo.setCurrentIndex(source_combo.count() - 1)
    exposure_combo.setCurrentIndex(exposure_combo.count() - 1)
    assert exposure_combo.currentText() == exposure_combo.itemText(exposure_combo.count() - 1)
    assert mosviz_gui.toolbar.exposure_next_action.isEnabled() == False
    mosviz_gui.toolbar.exposure_previous_action.trigger()
    assert exposure_combo.currentText() == exposure_combo.itemText(exposure_combo.count() - 2)
    assert mosviz_gui.toolbar.exposure_next_action.isEnabled() == True
