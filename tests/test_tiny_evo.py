import sqlite3
import pytest
import requests
from datetime import date
from test_setup import db_conn,setup_db, setup_poule, setup_ferme

def test_evolution_nuit(db_conn, setup_db):
    """Test simulant une nuit et ses effets sur toutes les fermes."""

    cur = db_conn.cursor()

    # Création de plusieurs fermes
    cur.execute("INSERT INTO ferme (nom) VALUES ('Ferme Alpha');")
    ferme1_id = cur.lastrowid  # Récupération manuelle de l'ID

    cur.execute("INSERT INTO ferme (nom) VALUES ('Ferme Beta');")
    ferme2_id = cur.lastrowid  # Récupération manuelle de l'ID

    # Ajout d'animaux : Une poule nourrie, une poule affamée, une vache
    cur.execute("""
        INSERT INTO animal (type, poids, age, sexe, ferme_id) 
        VALUES ('poule', 2.5, 5, 'femelle', ?),
               ('poule', 2.5, 5, 'femelle', ?),
               ('vache', 80, 10, 'femelle', ?);
    """, (ferme1_id, ferme2_id, ferme1_id))

    db_conn.commit()  # Commit nécessaire pour récupérer les IDs avec une requête `SELECT`

    # Récupérer les IDs des animaux
    cur.execute("SELECT id FROM animal WHERE ferme_id = ? AND type = 'poule' LIMIT 1;", (ferme1_id,))
    poule_nourrie_id = cur.fetchone()[0]

    cur.execute("SELECT id FROM animal WHERE ferme_id = ? AND type = 'poule' LIMIT 1;", (ferme2_id,))
    poule_affamee_id = cur.fetchone()[0]

    cur.execute("SELECT id FROM animal WHERE ferme_id = ? AND type = 'vache' LIMIT 1;", (ferme1_id,))
    vache_id = cur.fetchone()[0]

    # Ajout de stock pour nourrir uniquement la première ferme
    #cur.execute("INSERT INTO stock (type, quantite, ferme_id) VALUES ('grain', 5, ?);", (ferme1_id,))
    cur.execute("INSERT INTO stock (type, quantite, ferme_id) VALUES ('paille', 5, ?);", (ferme1_id,))

    # Nourrir la poule et la vache de la première ferme
    cur.execute("INSERT INTO alimentation (animal_id, date_nourrissage) VALUES (?, ?);", (poule_nourrie_id, date.today()))
    cur.execute("INSERT INTO alimentation (animal_id, date_nourrissage) VALUES (?, ?);", (vache_id, date.today()))

    db_conn.commit()

    # === Simuler le passage d'une nuit ===
    # Vieillissement des animaux
    cur.execute("UPDATE animal SET age = age + 1;")

    # Perte de poids pour les animaux non nourris
    cur.execute("""
        UPDATE animal 
        SET poids = poids - 0.2 
        WHERE id NOT IN (SELECT animal_id FROM alimentation WHERE date_nourrissage = CURRENT_DATE);
    """)

    # Suppression des animaux morts (poids <= 0)
    cur.execute("DELETE FROM animal WHERE poids <= 0;")

    # Production d'œufs pour les poules pondeuses
    cur.execute("""
        INSERT INTO production (type, quantite, ferme_id)
        SELECT 'oeuf', COUNT(*), ferme_id 
        FROM animal 
        WHERE type = 'poule' AND poids >= 2.5 AND age >= 5
        GROUP BY ferme_id;
    """)

    # Production de lait pour la vache si elle a été nourrie
    cur.execute("""
        INSERT INTO production (type, quantite, ferme_id)
        SELECT 'lait', 8, ferme_id
        FROM animal 
        WHERE type = 'vache' AND poids >= 80
        GROUP BY ferme_id;
    """)

    db_conn.commit()

    # Vérification des résultats après la nuit
    cur.execute("SELECT age FROM animal WHERE id = ?;", (poule_nourrie_id,))
    age_poule_nourrie = cur.fetchone()[0]

    cur.execute("SELECT poids FROM animal WHERE id = ?;", (poule_nourrie_id,))
    poids_poule_nourrie = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM animal WHERE id = ?;", (poule_affamee_id,))
    poule_affamee_existe = cur.fetchone()[0]

    cur.execute("SELECT quantite FROM production WHERE type = 'oeuf' AND ferme_id = ?;", (ferme1_id,))
    oeufs_produits = cur.fetchone()

    cur.execute("SELECT quantite FROM production WHERE type = 'lait' AND ferme_id = ?;", (ferme1_id,))
    lait_produit = cur.fetchone()

    cur.close()

    # Vérifications
    assert age_poule_nourrie == 6  # La poule a vieilli
    assert poids_poule_nourrie == 2.5  # La poule nourrie n'a pas perdu de poids
    assert poule_affamee_existe == 0  # La poule affamée est morte
    assert oeufs_produits is not None and oeufs_produits[0] >= 1  # Au moins 1 œuf produit
    assert lait_produit is not None and lait_produit[0] == 8  # La vache produit bien du lait
