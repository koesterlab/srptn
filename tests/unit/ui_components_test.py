from streamlit.testing.v1 import AppTest


def test_persistent_text_input():
    key = "test-textinput"
    at = AppTest.from_file("src/srptn/common/components/ui_components.py").run()
    assert at.text_input(key).value == ""
    at.text_input(key).set_value("test1").run()
    assert at.text_input(key).value == "test1"
    """Simulate page swapping, not natively supported with AppTest
    at.switch_page("../../pages/3 New Analysis.py").run()"""
    at.session_state[key] = ""
    at.run()
    # Technically after run the at.text_input(key).value should be "test1"
    # again but this seems to not faithfully replicate streamlits behaviour
    # the tested session_state entry defines the value in a real session so
    # the test should be valid.
    assert at.session_state[key + "-value"] == "test1"


def test_persistent_text_area():
    key = "test-textarea"
    at = AppTest.from_file("src/srptn/common/components/ui_components.py").run()
    assert at.text_area(key).value == ""
    at.text_area(key).set_value("test1").run()
    assert at.text_area(key).value == "test1"
    """Simulate page swapping, not natively supported with AppTest
    at.switch_page("../../pages/3 New Analysis.py").run()"""
    at.session_state[key] = ""
    at.run()
    assert at.session_state[key + "-value"] == "test1"


def test_persistent_multiselect():
    key = "test-multiselect"
    at = AppTest.from_file("src/srptn/common/components/ui_components.py").run()
    assert at.multiselect(key).value == []
    at.multiselect(key).set_value(["test1"]).run()
    assert at.multiselect(key).value == ["test1"]
    """Simulate page swapping, not natively supported with AppTest
    at.switch_page("../../pages/3 New Analysis.py").run()"""
    at.session_state[key] = []
    at.run()
    assert at.session_state[key + "-value"] == ["test1"]


def test_toggle_button():
    key = "test-togglebutton"
    at = AppTest.from_file("src/srptn/common/components/ui_components.py").run()
    assert not at.button(key + "-test").value
    at.button(key + "-test").click().run()
    assert at.button(key + "-test").value
    """Simulate page swapping, not natively supported with AppTest
    at.switch_page("../../pages/3 New Analysis.py").run()"""
    at.session_state[key + "-test"] = False
    at.run()
    assert at.session_state[key + "-state"]
