import pytest
from boxing.models import boxers_model
from boxing.models.boxers_model import Boxer

def test_get_weight_class():
    assert boxers_model.get_weight_class(129) == "LIGHTWEIGHT"
    assert boxers_model.get_weight_class(137) == "FEATHERWEIGHT"
    assert boxers_model.get_weight_class(166) == "MIDDLEWEIGHT"
    assert boxers_model.get_weight_class(265) == "HEAVYWEIGHT"

def invalid_get_weight():
    with pytest.raises(ValueError):
        boxers_model.get_weight_class(50)

def test_create_boxer_already_exists(mocker):
    mock_connec = mocker.MagicMock() 
    # Had to look this up - MagicMock creates fake modules for testing
    cursor = mock_connec.cursor.return_value 
    # Creates a fake database 
    cursor.fetchone.return_val = True
    # "Pretends" that we actually found a boxer

    mocker.patch("boxing.models.boxers_model.get_db_connection", return_val = mock_connec)
    # temp patches a function (get_db_connection - actual connection to database) with the fake connection

    with pytest.raises(ValueError, match="Boxer already exists"):
        boxers_model.create_boxer("Leon Edwards", 170, 74, 74.0, 33)

def test_create_boxer_pass(mocker):
    mock_connec = mocker.MagicMock() 
    cursor = mock_connec.cursor.return_val 
    cursor.fetchone.return_val = False
    # "Pretends" that we didn't find a boxer

    mocker.patch("boxing.models.boxers_model.get_db_connection", return_val = mock_connec)

    boxers_model.create_boxer("Leon Edwards", 170, 74, 74.0, 33)
    assert cursor.execute.call_count >= 2 
    # Ensures that SELECT (1) and (+) INSERT (1) were both done

def test_get_boxer_by_id_pass(mocker):
    mock_connec = mocker.MagicMock()
    cursor = mock_connec.cursor.return_val
    cursor.fetchone.return_val = (1, "Leon Edwards", 170, 74, 74.0, 33)

    mocker.patch("boxing.models.boxers_model.get_db_connection", return_val = mock_connec)

    boxer = boxers_model.get_boxer_by_id(1)
    assert isinstance(boxer, Boxer)
    assert boxer.name == "Leon Edwards"

def test_get_boxer_by_id_fail(mocker):
    mock_connec = mocker.MagicMock()
    cursor = mock_connec.cursor.return_val
    cursor.fetchone.return_val = None

    mocker.patch("boxing.models.boxers_model.get_db_connection", return_val = mock_connec)

    with pytest.raises(ValueError, match="NOT FOUND"):
        boxers_model.get_boxer_by_id(10000000000)