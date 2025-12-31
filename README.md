# Scalable Capital PDF Downloader (v0.83)

Deutsch | English see below

Ein automatisiertes Tool zum Herunterladen von Wertpapierabrechnungen (Kauf, Verkauf, Sparplan, Ausschüttung, etc.) von Scalable Capital.

# Features

    Automatischer Download: Lädt Dokumente basierend auf konfigurierbaren Keywords herunter.

    Intelligente Benennung: Dateien werden nach dem Schema Datum-Typ-ISIN-Name-Betrag.pdf benannt.

    Duplikats-Prüfung: Bereits vorhandene Dateien werden erkannt und übersprungen.

    Abbruch-Option: Kann beim ersten gefundenen Duplikat stoppen (stop-at-first-duplicate).

    2FA-Support: Unterstützt den manuellen Login inklusive Zwei-Faktor-Authentifizierung.

    Portabilität: Als EXE-Version inklusive Browser verfügbar (keine Python-Installation nötig).

# Installation & Nutzung
Für Poweruser (Skript-Modus)

    Python 3.12+ installieren.

    Projekt-Ordner erstellen und downloader.py sowie start_downloader.bat hineinkopieren.

    Bibliotheken installieren: pip install playwright.

    Browser installieren: playwright install chromium.

    Starten über die start_downloader.bat.

# Für Einsteiger (EXE-Modus)

    Lade die fertige EXE-Datei aus dem Bereich Releases herunter.

    Starte die EXE. Beim ersten Start kann es 10-20 Sekunden dauern, bis sich das Fenster öffnet, da der integrierte Browser entpackt wird.
	
# === INI Parameter ===	

[General]

    max_transactions: Maximale Anzahl der Transaktionen, die das Skript versucht zu laden (Standard: 20).

    download_directory: Name des Ordners oder kompletter Pfad, in dem die PDFs gespeichert werden (Standard: Scalable_Downloads).

    stop_at_first_duplicate: Wenn "True", bricht das Skript ab, sobald die erste bereits vorhandene Datei gefunden wird (Standard: False).

    use_original_filename: Bei "True" wird der Name von Scalable beibehalten; bei "False" wird die sprechende Benennung genutzt (Standard: False).

    logout_after_run: Meldet den Benutzer nach Abschluss aller Aktionen automatisch ab (Standard: True).

[Keywords]

    transaction_types: Komma-getrennte Liste der Begriffe, die heruntergeladen werden sollen (Standard: Ausschüttung, Kauf, Verkauf, Sparplan)
	Die Namen der Typen entsprechen dem Filter "Auftragstyp" in Scalable

[Timeouts]

    page_load_wait: Wartezeit in Millisekunden nach dem ersten Laden der Transaktionsseite (Standard: 1000).

    transaction_wait: Kurze Pause zwischen den einzelnen Downloads zur Stabilisierung (Standard: 50).

    critical_wait: Sicherheits-Wartezeit vor der Suche nach Dokument-Elementen (Standard: 50).

    pdf_button_timeout: Zeitlimit, wie lange auf das Erscheinen des Download-Buttons gewartet wird (Standard: 100)

# ===  english version ====

An automated tool for downloading brokerage statements (Buy, Sell, Savings Plan, Dividend) from Scalable Capital.
Features

    Automated Download: Downloads documents based on configurable keywords.

    Smart Naming: Files are named using the schema Date-Type-ISIN-Name-Amount.pdf.

    Duplicate Detection: Detects and skips existing files in the download folder.

    Early Stop: Optional stop upon finding the first duplicate (stop-at-first-duplicate).

    2FA Support: Handles manual login including Two-Factor Authentication.

    Portability: Available as an EXE version including a portable browser (no Python installation required).

# Installation & Usage
For Power Users (Script Mode)

    Install Python 3.12+.

    Create a project folder and copy downloader.py and start_downloader.bat into it.

    Install libraries: pip install playwright.

    Install browser: playwright install chromium.

    Launch via start_downloader.bat.

# For Beginners (EXE Mode)

    Download the pre-built EXE file from the Releases section.

    Run the EXE. The first launch may take 10-20 seconds to open as the integrated browser is unpacked.
	
# === INI Parameter ===	

[General]

    max_transactions: Maximum number of transactions the script will check in the list (Default: 20).

    download_directory: Name of the folder or full path where PDFs are stored (Default: Scalable_Downloads).

    stop_at_first_duplicate: If "True", the script stops as soon as it encounters the first already existing file (Default: False).

    use_original_filename: If "True", keeps Scalable's original name; if "False", uses descriptive naming (Default: False).

    logout_after_run: Automatically logs out the user after the script completes all actions (Default: True).

[Keywords]

    transaction_types: Comma-separated list of terms to be downloaded (Default: Ausschüttung, Kauf, Verkauf, Sparplan).

[Timeouts]

    page_load_wait: Wait time in milliseconds after initially loading the transaction page (Default: 1000).

    transaction_wait: Short pause between individual downloads for stabilization (Default: 50).

    critical_wait: Safety wait time before searching for document elements (Default: 50).

    pdf_button_timeout: Time limit to wait for the download button to appear (Default: 100).
	

