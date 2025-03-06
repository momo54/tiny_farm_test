import sqlite3
import pytest
import requests
from datetime import date

from test_setup import db_conn,setup_db, setup_poule, setup_ferme


def test_creation_ferme(db_conn, setup_db):
    """Tests farm creation in SQLite."""
    cur = db_conn.cursor()
    cur.execute("INSERT INTO ferme (nom) VALUES ('MaFermeTest');")
    ferme_id = cur.lastrowid  # Remplace RETURNING id

    cur.execute("SELECT nom, solde_ecus FROM ferme WHERE id = ?;", (ferme_id,))
    result = cur.fetchone()

    cur.close()
    assert result == ("MaFermeTest", 1500)

def test_ajout_animal(db_conn, setup_ferme):
    """Tests adding an animal."""
    cur = db_conn.cursor()
    cur.execute("""
        INSERT INTO animal (type, poids, age, sexe, ferme_id) 
        VALUES ('poule', 2.5, 5, 'femelle', ?);
    """, (setup_ferme,))
    animal_id = cur.lastrowid  # Remplace RETURNING id

    cur.execute("SELECT type, poids FROM animal WHERE id = ?;", (animal_id,))
    result = cur.fetchone()

    cur.close()
    assert result == ("poule", 2.5)

def test_poule_nourrie_une_fois(db_conn, setup_poule):
    """Tests that a hen can only be fed once per day."""
    cur = db_conn.cursor()
    cur.execute("INSERT INTO alimentation (animal_id, date_nourrissage) VALUES (?, ?);", (setup_poule, date.today()))
    db_conn.commit()

    with pytest.raises(sqlite3.IntegrityError):  # Verify that duplicate feeding is blocked
        cur.execute("INSERT INTO alimentation (animal_id, date_nourrissage) VALUES (?, ?);", (setup_poule, date.today()))
        db_conn.commit()

    cur.close()

def test_mortalite_si_non_nourrie(db_conn, setup_poule):
    """Tests if a hen dies after 4 days without food."""
    cur = db_conn.cursor()

    for _ in range(4):  # Simulate 4 days without food
        cur.execute("UPDATE animal SET poids = poids - 0.5 WHERE id = ?;", (setup_poule,))
    
    cur.execute("DELETE FROM animal WHERE poids <= 0;")  # Apply mortality rule
    cur.execute("SELECT COUNT(*) FROM animal WHERE id = ?;", (setup_poule,))
    result = cur.fetchone()[0]

    cur.close()
    assert result == 0  # The animal should be deleted
