from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "src/sunshine_sim/ui/app.py"


def test_geometry_and_beam_modes():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.metric[0].value == "73.75%"
    app.radio[0].set_value("Ideal-support beam & spacing").run()
    assert not app.exception
    assert not app.error
    assert app.dataframe
    assert app.success
    # Increase span to force contact; no physical standoff should be presented.
    app.number_input[5].set_value(12.0).run()
    assert not app.exception
    assert "wall_contact" in app.error[0].value
    assert all(metric.label != "Minimum ideal-support standoff" for metric in app.metric)
    app.text_input[0].set_value("3, broken").run()
    assert app.error
    assert not app.exception
