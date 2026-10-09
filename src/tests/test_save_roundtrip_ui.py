"""What you enter in the editor survives Save and Open, and a browser reload (browser tests)."""
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

DETAILS = {"phdg": "Penny Black", "pcat": "SG#1", "pdenom": "1/2D", "pperf": "Imperforate"}


def _fill_details(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("StampAlbum.select(StampAlbum.E.find(e => e.t === 'stamp').id)")
    for field, value in DETAILS.items():
        page.fill("#" + field, value)
        page.dispatch_event("#" + field, "change")
    page.select_option("#pcond", "Used")
    page.select_option("#pbs", "double")


def _properties(page):
    return page.evaluate("""(() => {
        const v = id => document.getElementById(id).value;
        return {phdg: v('phdg'), pcat: v('pcat'), pdenom: v('pdenom'), pperf: v('pperf'), pcond: v('pcond'), pbs: v('pbs')};
    })()""")


def test_stamp_details_survive_save_and_open(page):
    _fill_details(page)
    dsl = page.evaluate("StampAlbum.buildDSL()")
    page.on("dialog", lambda d: d.accept())
    page.evaluate("StampAlbum.newAlbum()")
    assert page.evaluate("StampAlbum.E.length") == 0
    page.evaluate("dsl => StampAlbum.parseDSL(dsl)", dsl)
    page.evaluate("StampAlbum.select(StampAlbum.E.find(e => e.lbl === 'Penny Black — 1840').id)")
    assert _properties(page) == dict(DETAILS, pcond="Used", pbs="double")


def test_page_border_survives_a_reload(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.select_option("#def-bdr", "double")
    page.wait_for_timeout(800)  # the draft is saved 500 ms after a change
    page.reload()
    page.wait_for_function("window.StampAlbum && document.getElementById('page')")
    assert page.evaluate("StampAlbum._pageBorder") == "double"
    assert page.input_value("#def-bdr") == "double"
    assert page.evaluate("!!document.getElementById('page-border')")
