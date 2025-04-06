import streamlit as st
import sqlite3
from datetime import datetime
import random
import pandas as pd

# Title of the app
st.title('Sélection Ultime des Candidats de Top Chef')

# Dropdown menu for user identification
user = st.selectbox('Qui êtes-vous?', ['Xavier', 'Emma', 'Julia', 'Charles', 'Lulu', 'Loultattoo', 'Nonoche'])
st.write(f'Vous êtes: {user}')

# List of candidates
candidates = [
    "Claudio Semedo Borges", "Noé Pellet", "Grégoire Touchard",
    "Margaux Elie", "Sean Gabbiani",
    "Esteban Salazar", "Noémie Cadre", "Steven Thiebaut Pellegrino",
    "Philippine Jaillet", "Charles Neyers"
]

# Initialize connection to SQLite
conn = sqlite3.connect('selections_final.db', check_same_thread=False)
c = conn.cursor()

# Create the table if it doesn't exist
c.execute(''' 
    CREATE TABLE IF NOT EXISTS votes ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user TEXT, 
        first_choice TEXT, 
        second_choice TEXT, 
        timestamp TEXT 
    ) 
''')
conn.commit()

# Session state to remember choices
if 'first_choice' not in st.session_state:
    st.session_state.first_choice = None
if 'second_choice' not in st.session_state:
    st.session_state.second_choice = None

# First choice
if not st.session_state.first_choice:
    st.write('Quel est votre premier choix?')
    for candidate in candidates:
        if st.button(f'1. {candidate}'):
            st.session_state.first_choice = candidate
            st.rerun()

# Second choice
elif not st.session_state.second_choice:
    st.write(f'Votre premier choix: {st.session_state.first_choice}')
    st.write('Quel est votre deuxième choix?')
    for candidate in candidates:
        if candidate != st.session_state.first_choice:
            if st.button(f'2. {candidate}'):
                st.session_state.second_choice = candidate
                st.rerun()
        else:
            st.button(f'2. {candidate}', disabled=True)

# Save to database and confirm
elif st.session_state.first_choice and st.session_state.second_choice:
    # Check if the user already voted
    c.execute("SELECT COUNT(*) FROM votes WHERE user = ?", (user,))
    vote_count = c.fetchone()[0]

    if vote_count > 0:
        st.error("Vous avez déjà voté. Il n'est pas possible de voter une deuxième fois.")
    else:
        st.success(f'Choix enregistré !\n\n1. {st.session_state.first_choice}\n\n2. {st.session_state.second_choice}')
        
        # Insert the choices into the database
        c.execute(''' 
            INSERT INTO votes (user, first_choice, second_choice, timestamp) 
            VALUES (?, ?, ?, ?) 
        ''', (user, st.session_state.first_choice, st.session_state.second_choice, datetime.now().isoformat()))
        conn.commit()

# Display results
st.markdown("---")
st.subheader("Résultats des premiers choix")

if st.button("Afficher les résultats"):
    c.execute(''' 
        SELECT user, first_choice, second_choice 
        FROM votes 
        WHERE id IN ( 
            SELECT MAX(id) 
            FROM votes 
            GROUP BY user 
        ) 
    ''')
    results = c.fetchall()

    if results:
        df = pd.DataFrame(results, columns=["Utilisateur", "Premier Choix", "Deuxième Choix"])
        st.dataframe(df)

    else:
        st.info("Aucun vote enregistré pour le moment.")


import random

# Display final results (first choice of each user)
st.markdown("---")
st.subheader("Résultats finaux des premiers choix")

if st.button("Afficher les résultats finaux"):
    # Select the first choice for each user
    c.execute(''' 
        SELECT user, first_choice 
        FROM votes 
        WHERE id IN ( 
            SELECT MAX(id) 
            FROM votes 
            GROUP BY user 
        ) 
    ''')
    final_results = c.fetchall()

    if final_results:
        # Group users by their first choice
        from collections import defaultdict
        grouped_choices = defaultdict(list)

        for user, first_choice in final_results:
            grouped_choices[first_choice].append(user)

        # Now we need to handle "battles" between users with the same first choice
        final_results_with_comments = []

        for first_choice, users in grouped_choices.items():
            if len(users) > 1:
                # More than one user selected the same first choice, we need to randomly select a winner
                winner = random.choice(users)
                for user in users:
                    if user == winner:
                        final_choice = first_choice
                        comment = f"Premier choix attribué à {user} (gagnant)"
                    else:
                        # If the user is not the winner, assign their second choice
                        c.execute(''' 
                            SELECT second_choice 
                            FROM votes 
                            WHERE user = ? 
                            ORDER BY timestamp DESC LIMIT 1
                        ''', (user,))
                        second_choice = c.fetchone()[0]
                        final_choice = second_choice
                        comment = f"Deuxième choix. Si vous n'êtes pas satisfait, arrangez vous entre vous."

                    final_results_with_comments.append((user, first_choice, final_choice, comment))
            else:
                # Only one user selected this first choice
                for user in users:
                    final_choice = first_choice
                    comment = f"Premier choix attribué à {user}"
                    final_results_with_comments.append((user, first_choice, final_choice, comment))
                          

        # Create a dataframe for the final results with the new "Commentaires" and "Choix Final" columns
        df_final = pd.DataFrame(final_results_with_comments, columns=["Utilisateur", "Premier Choix", "Choix Final", "Commentaires"])
        st.dataframe(df_final)
    else:
        st.info("Aucun vote enregistré pour le moment.")

