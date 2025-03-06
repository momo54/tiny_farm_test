import sqlite3
import pytest
import requests
from datetime import date

BASE_URL = "http://localhost:8080"  # URL of the Spring Boot API

@pytest.fixture
def db_conn():
    """Creates an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")  # Use an in-memory DB
    yield conn
    conn.close()

@pytest.fixture
def setup_db(db_conn):
    """Creates tables in memory before each test."""
    cur = db_conn.cursor()  # Create cursor
    cur.execute("""
        CREATE TABLE ferme (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            solde_ecus INTEGER DEFAULT 1500
        );
    """)
    cur.execute("""
        CREATE TABLE animal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            poids REAL NOT NULL,
            age INTEGER NOT NULL,
            sexe TEXT CHECK(sexe IN ('male', 'femelle')),
            ferme_id INTEGER REFERENCES ferme(id) ON DELETE CASCADE
        );
    """)
    cur.execute("""
        CREATE TABLE alimentation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER REFERENCES animal(id) ON DELETE CASCADE,
            date_nourrissage DATE NOT NULL DEFAULT CURRENT_DATE
        );
    """)
    db_conn.commit()
    cur.close()  # Close cursor

@pytest.fixture
def setup_ferme(db_conn, setup_db):
    """Adds a farm to the in-memory database."""
    cur = db_conn.cursor()
    cur.execute("INSERT INTO ferme (nom) VALUES ('FermeTest');")
    ferme_id = cur.lastrowid  # Remplace RETURNING id
    db_conn.commit()
    cur.close()
    return ferme_id

@pytest.fixture
def setup_poule(db_conn, setup_ferme):
    """Adds a hen to the farm."""
    cur = db_conn.cursor()
    cur.execute("""
        INSERT INTO animal (type, poids, age, sexe, ferme_id) 
        VALUES ('poule', 2.5, 5, 'femelle', ?);
    """, (setup_ferme,))
    animal_id = cur.lastrowid  # Remplace RETURNING id
    db_conn.commit()
    cur.close()
    return animal_id

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
