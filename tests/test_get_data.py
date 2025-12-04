import pytest
from ecox.get_data import get_dupont_analysis_

def test_sample():
    secucode = 'SH601390'
    df = get_dupont_analysis_(secucode)
    print(df)
    assert df is not None