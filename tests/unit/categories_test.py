from streamlit.testing.v1 import AppTest


def test_initial_state():
    key = "test"
    at = AppTest.from_file("src/srptn/common/components/categories.py").run()
    assert at.text_input(f"{key}-category-0").value == ""


def test_add_and_remove_category():
    key = "test"
    at = AppTest.from_file("src/srptn/common/components/categories.py").run()
    at.text_input(f"{key}-category-0").set_value("test").run()
    assert at.text_input(f"{key}-category-0").value == "test"
    assert f"{key}-category-1" in at.session_state
    at.text_input(f"{key}-category-0").set_value("").run()
    at.run()
    assert f"{key}-category-1" not in at.session_state


def test_add_subcategories():
    key = "test"
    at = AppTest.from_file("src/srptn/common/components/categories.py").run()
    at.text_input(f"{key}-category-0").set_value("test").run()
    at.text_input(f"{key}-category-1").set_value("test").run()
    assert f"{key}-category-2" in at.session_state


def test_remove_intermediate_subcategory():
    key = "test"
    at = AppTest.from_file("src/srptn/common/components/categories.py").run()
    at.text_input(f"{key}-category-0").set_value("test1").run()
    at.text_input(f"{key}-category-1").set_value("test2").run()
    at.text_input(f"{key}-category-2").set_value("test3").run()
    at.text_input(f"{key}-category-1").set_value("").run()
    assert "test2" not in at.session_state["test-categories"]
    assert "test3" in at.session_state["test-categories"]
