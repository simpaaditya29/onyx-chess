To add more variations or completely new opening systems in the future, you just need to follow the exact same structural pattern. Because the file is written in JSON, you can expand it endlessly as long as you keep the syntax correct.

Here is the exact step-by-step method to add new lines or new openings.

Scenario A: Adding a New Line to an Existing Repertoire
If you want to add a new line to White Repertoire (for example, the Reti Opening):

Open your openings.json file.

Find the "lines" block under "White Repertoire".

Go to the very end of the last line currently inside that block (in this case, it's the Example Game).

Put a comma (,) after its closing curly brace }.

Paste your new variation right after it.

It will look like this:

JSON
            "Example Game": {
                "name": "A Game Example",
                "moves": [...]
            },  <-- ADD A COMMA HERE
            "Reti Opening": {
                "name": "Reti Opening: Classic",
                "moves": ["Nf3", "d5", "c4"]
            }
Scenario B: Adding a Completely New Master Category
If you want to create a brand new category (for example, if you want to separate your repertoire into "Blitz Openings" or "Tournament Prep"):

Scroll to the very bottom of your openings.json file.

Put a comma (,) after the final closing curly brace of your "Black Repertoire" block.

Define your new category just like the others.

JSON
    }, <-- COMMA AFTER THE BLACK REPERTOIRE CLOSING BRACE
    "My Secret Repertoire": {
        "link": "https://notion.so/secret-link",
        "lines": {
            "Surprise Line": {
                "name": "The Grob",
                "moves": ["g4", "d5"]
            }
        }
    }
} <-- This remains the absolute final closing brace of the file
⚠️ The Golden Rules of JSON Formatting
If your Python script crashes after you edit the JSON, it is almost always due to one of these three syntax mistakes:

The Dangling Comma Rule: Every item in a list or dictionary must be separated by a comma except for the very last one. Never put a comma after the last move in your list, or the last variation in your lines.

Double Quotes Only: JSON strictly requires double quotes ("e4"). If you use single quotes ('e4'), Python will fail to read the file.

Matching Brackets: Every opening { or [ must have a matching closing } or ].