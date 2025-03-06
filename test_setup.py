import sqlite3
import pytest
import requests
from datetime import date

@pytest.fixture
def db_conn():
    """Creates an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")  # Use an in-memory DB
    yield conn
    conn.close()


@pytest.fixture
def setup_db(db_conn):
    """Crée toutes les tables nécessaires avant les tests."""
    cur = db_conn.cursor()

    # Table Ferme
    cur.execute("""
        CREATE TABLE ferme (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            solde_ecus INTEGER DEFAULT 1500
        );
    """)

    # Table Animal
    cur.execute("""
        CREATE TABLE animal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            poids REAL NOT NULL,
            age INTEGER NOT NULL,
            sexe TEXT CHECK(sexe IN ('male', 'femelle')),
            ferme_id INTEGER NOT NULL,
            FOREIGN KEY (ferme_id) REFERENCES ferme(id) ON DELETE CASCADE
        );
    """)

    # Table Stock (Stock de nourriture pour chaque ferme)
    cur.execute("""
        CREATE TABLE stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            ferme_id INTEGER NOT NULL,
            FOREIGN KEY (ferme_id) REFERENCES ferme(id) ON DELETE CASCADE
        );
    """)

    # Table Alimentation (Enregistre les nourrissages quotidiens des animaux)
    cur.execute("""
        CREATE TABLE alimentation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL,
            date_nourrissage DATE NOT NULL DEFAULT CURRENT_DATE,
            FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE
        );
    """)

    # Table Production (Stockage des produits générés par les animaux)
    cur.execute("""
        CREATE TABLE production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            ferme_id INTEGER NOT NULL,
            FOREIGN KEY (ferme_id) REFERENCES ferme(id) ON DELETE CASCADE
        );
    """)

    db_conn.commit()
    cur.close()


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


@pytest.fixture
def setup_ferme(db_conn, setup_db):
    """Adds a farm to the in-memory database."""
    cur = db_conn.cursor()
    cur.execute("INSERT INTO ferme (nom) VALUES ('FermeTest');")
    ferme_id = cur.lastrowid  # Remplace RETURNING id
    db_conn.commit()
    cur.close()
    return ferme_id
