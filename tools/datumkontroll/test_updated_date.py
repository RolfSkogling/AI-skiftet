#!/usr/bin/env python3
"""Regressionsprov for updated_date.py.

Provet som betyder nagot ar test_glidning_fangas: det ateskapar exakt felet
fran 2026-09-11 - faltet sager 8 september, oversta dagsgruppen ar den 10:e -
och kraver att kontrollen fallerar. Utan det provet kan spar ren tyst slutas
fungera vid nasta mallandring och ingen skulle marka det.

Kor: python3 tools/datumkontroll/test_updated_date.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import updated_date as U

SIDA = """<div class="sect-head">
  <h2>Nyheter</h2>
  <time datetime="{iso}"><span class="sect-updated__label">Senast uppdaterat</span>
  <span class="sect-updated__date">{txt}</span></time>
</div>
<div class="strip news-audio">
  <source src="/audio/dagens.m4a?v={av}" type="audio/mp4">
  <p class="strip__foot"><span class="news-audio__note">Ett engelskt spar. &middot; Upplasning {anote}</span></p>
</div>
<div class="news-list" id="newsList">
  <div class="day news-date-group" id="dag-{g}" data-date="{g}">
    <p class="day__label news-date">{glabel}</p>
  </div>
  <div class="day news-date-group" id="dag-2026-09-04" data-date="2026-09-04">
    <p class="day__label news-date">4 september 2026</p>
  </div>
</div>"""

BAS = dict(iso="2026-09-10", txt="10 september 2026", g="2026-09-10",
           glabel="10 september 2026", av="2026-09-08", anote="8 september 2026")


def sida(**kw):
    d = dict(BAS)
    d.update(kw)
    return SIDA.format(**d)


def run(name, fn):
    try:
        fn()
        print("  ok   " + name)
        return 0
    except AssertionError as e:
        print("  FEL  %s: %s" % (name, e))
        return 1


def test_ratt_satt_ger_rent():
    assert U.check(sida()) == [], "korrekt sida ska ge noll problem"


def test_glidning_fangas():
    """Exakt felet fran 2026-09-11: faltet 8 sept, nyheterna 10 sept."""
    p = U.check(sida(iso="2026-09-08", txt="8 september 2026"), "sv")
    assert len(p) == 2, "bade datetime och synlig text ska flaggas, fick %r" % p
    assert any("2026-09-08" in x and "2026-09-10" in x for x in p), p
    assert any('"8 september 2026"' in x for x in p), p


def test_bara_attributet_glider():
    p = U.check(sida(iso="2026-09-08"), "sv")
    assert len(p) == 1 and "datetime" in p[0], p


def test_bara_synliga_texten_glider():
    p = U.check(sida(txt="9 september 2026"), "sv")
    assert len(p) == 1 and "9 september 2026" in p[0], p


def test_saknad_span_ar_ett_fel():
    """Utan spans finns inget att binda - det ska INTE passera tyst."""
    h = sida().replace('<span class="sect-updated__date">10 september 2026</span>',
                       "10 september 2026")
    p = U.check(h, "sv")
    assert any("sect-updated__date" in x for x in p), p


def test_ljudnotis_mats_mot_ljudfilen_inte_nyheterna():
    """Aldre ljud an nyheter ar INTE ett fel - notisen ska saga sanningen."""
    assert U.check(sida()) == [], "ljud 8 sept + nyheter 10 sept ska vara rent"
    p = U.check(sida(anote="10 september 2026"), "sv")
    assert any("ljudnotisen" in x for x in p), "notis som ljuger om ljudet ska flaggas"


def test_fix_skriver_om_bada_leden():
    ny = U.fix(sida(iso="2026-09-08", txt="8 september 2026"))
    assert U.check(ny) == [], U.check(ny)
    assert 'datetime="2026-09-10"' in ny
    assert ">10 september 2026<" in ny


def test_fix_ror_inte_ljudblocket():
    ny = U.fix(sida(iso="2026-09-08", txt="8 september 2026"))
    assert "dagens.m4a?v=2026-09-08" in ny, "fix far inte datera om ljudet"
    assert "Upplasning 8 september 2026" in ny


def test_fix_vagrar_utan_dagsgrupp():
    try:
        U.fix('<time datetime="2026-09-08"><span class="sect-updated__date">x</span></time>')
    except ValueError:
        return
    raise AssertionError("fix ska vagra nar det inte finns nagon dagsgrupp")


def test_norska_och_engelska_etiketter():
    for txt in ("September 10, 2026", "10. september 2026"):
        assert U.check(sida(txt=txt, glabel=txt)) == [], txt
        assert U.check(sida(txt="fel", glabel=txt), "x") != []


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    print("test_updated_date: %d prov" % len(tests))
    fails = sum(run(k, v) for k, v in tests)
    print("RESULTAT:", "alla gick igenom" if not fails else "%d FALLERADE" % fails)
    sys.exit(1 if fails else 0)
