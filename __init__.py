from aqt import mw
from aqt.qt import QAction, QFileDialog
from aqt.utils import showInfo
import re

def count_indentation(line):
    # Count leading spaces. If using tabs, switch logic accordingly.
    # Here we assume 4 spaces per indentation level.
    count = 0
    for ch in line:
        if ch == ' ':
            count += 1
        else:
            break
    return count // 4

def create_decks_and_cards_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    hierarchy = []
    deck_ids = {}  # Cache deck IDs to avoid repeated lookups
    notes_created = 0

    # Fetch the Basic model
    model = mw.col.models.byName("Basic")
    if not model:
        showInfo("Error: 'Basic' model not found. Please ensure the Basic note type is present.")
        return

    for original_line in lines:
        line = original_line.rstrip('\n')
        if not line.strip():
            # Ignore empty or whitespace-only lines
            continue
        
        level = count_indentation(line)
        stripped_line = line[level*4:].rstrip()  # Remove the indentation from the line

        if stripped_line.startswith('.'):
            # This is a card line
            if len(hierarchy) == 0:
                showInfo(f"Warning: Found a card line '{line}' without any deck defined.")
                continue

            # The full deck name based on the current hierarchy
            full_deck_name = "::".join(hierarchy)

            # Parse the card format: `.question;answer`
            card_content = stripped_line[1:]  # remove the leading '.'
            parts = card_content.split(';', 1)
            if len(parts) != 2:
                showInfo(f"Warning: Card line '{line}' does not have a valid 'question;answer' format.")
                continue
            question, answer = parts[0].strip(), parts[1].strip()

            # Create or get deck ID
            if full_deck_name not in deck_ids:
                deck_ids[full_deck_name] = mw.col.decks.id(full_deck_name)
            did = deck_ids[full_deck_name]

            # Create a new note
            note = mw.col.newNote()
            note.model()['did'] = did
            # Assuming fields "Front" and "Back" for the Basic model
            note["Front"] = question
            note["Back"] = answer

            # Add the note to the collection
            mw.col.addNote(note)
            notes_created += 1

        else:
            # This is a deck line
            deck_name = stripped_line.strip()

            # Adjust the hierarchy to match the current indentation
            if level > len(hierarchy):
                # More indented than expected, structure error
                showInfo(f"Error: Line '{line}' is indented more than one level deeper than previous.")
                return
            else:
                # Pop off extra levels if we have too many
                while len(hierarchy) > level:
                    hierarchy.pop()

            # Add the current deck to the hierarchy
            hierarchy.append(deck_name)

            # Create or get deck ID for this deck
            full_deck_name = "::".join(hierarchy)
            if full_deck_name not in deck_ids:
                deck_ids[full_deck_name] = mw.col.decks.id(full_deck_name)

    mw.reset()
    showInfo(f"Decks and cards created successfully.\nNotes created: {notes_created}")

def on_import_decks_and_cards():
    filepath, _ = QFileDialog.getOpenFileName(mw, "Select Deck Hierarchy File", "", "Text Files (*.txt);;All Files (*)")
    if filepath:
        create_decks_and_cards_from_file(filepath)

# Add a menu item to trigger the import
action = QAction("Import Deck Hierarchy and Cards", mw)
action.triggered.connect(on_import_decks_and_cards)
mw.form.menuTools.addAction(action)
