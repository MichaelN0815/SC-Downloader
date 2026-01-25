![SC-Icon](https://github.com/user-attachments/assets/c9fdfd75-ba4b-47e6-bdbd-eb000ce26566)
# Scalable Capital PDF Downloader  ![Downloads](https://img.shields.io/github/downloads/MichaelN0815/SC-Downloader/total?style=flat-square&color=blue)

Deutsch | English see below

Ein Tool zum automatisierten Herunterladen von Wertpapierabrechnungen (Kauf, Verkauf, Sparplan, Ausschüttung, etc.) und der Mailbox-Dokumente von Scalable Capital.

# Features

- Lädt Transaktion-Dokumente basierend auf konfigurierbaren Keywords herunter
- Intelligente Benennung: Dateien werden nach dem Schema Datum-Typ-ISIN-Name-Betrag.pdf benannt
- Wahlweise kann die ISIN durch die WKN ersetzt werden
- Lädt neue (oder alle) Dokumente aus der Mailbox herunter (immer mit dem Original-Dateinamen)
- Duplikats-Prüfung: Bereits vorhandene Dateien werden erkannt und übersprungen
- Abbruch-Option: Kann beim ersten gefundenen Duplikat stoppen (stop-at-first-duplicate)
- Unterstützt den manuellen Login inklusive Zwei-Faktor-Authentifizierung
- Als EXE-Version inklusive Browser verfügbar (keine Python-Installation nötig)


![Screenshot1](https://github.com/user-attachments/assets/b19e3dd1-a223-451a-9c71-e818014113f3)
![Screenshot2](https://github.com/user-attachments/assets/adfc9cc7-d083-4464-b9a9-a215537dde52)

# Installation & Nutzung
# Für Einsteiger (EXE-Modus)

Lade die fertige EXE-Datei aus dem Bereich Releases herunter.
Starte die EXE. Beim ersten Start kann es 10-20 Sekunden dauern, bis sich das Fenster öffnet, da der integrierte Browser entpackt wird.

In der INI-Datei kann man verschiedene Optionen konfigurieren, siehe Abschnitt INI-Parameter.
Hierzu lädt man sich am besten die kommentierte INI-Datei aus dem Projekt runter. 
Damit lässt es sich bequemer arbeiten, als mit der automatisch generierten. 
Die INI-Datei kann einfach mit dem Texteditor bearbeitet werden. 
Alles was mit # beginnt ist ein Kommentar und hat keine Funktion. 

Hinweis: 
Ich verstehe, wenn man ein ungutes Gefühl hat eine unbekannte EXE auf seinen Rechner und noch dazu sein Depot loszulassen. 
Daher steht auch der Python Quellcode zur Verfügung. Diesen kann man auch als Python Unkundiger von einer KI der Wahl einem Code-Review unterziehen
und prüfen lassen, was der Code wirklich macht. 

# Update-Hinweis

Da sich teilweise der Funktionsumfang ändert und damit einhergehend Einträge in der INI ergänzt wurden, empfehle ich bei einem Update auch die neuste INI runterzuladen und die Einträge aus der alten zu übertragen
Zum Download der PDFs für Vorabpauschale wird Programm und INI der Version 2.06 benötigt!
	
# Für Poweruser (Skript-Modus)

Python 3.12+ installieren.

Projekt-Ordner erstellen und downloader.py sowie start_downloader.bat hineinkopieren.
ggf. auch die INI wenn man vor dem ersten Start bereits Parameter anpassen will. Ansonsten wird die INI automatisch erstellt.

Bibliotheken installieren: 

	pip install playwright

Browser installieren:

	playwright install chromium

Starten über

	python downloader.py
	
oder die SC-Downloader.bat

# Hinweise

- Wenn die INI Datei noch nicht existiert, wird sie mit Standard-Werten angelegt
- Wenn kein Download-Ordner definiert wurde, wird im Start-Ordner ein Verzeichnis Scalable_Downloads angelegt, in dem die PDFs landen
- Das Skript legt einen Order scalable_session an, in dem die Laufzeit-Daten des integrierten Browsers abgelegt werden
- Wenn das Skript ordnungsgemäß durchläuft loggt es sich am Ende aus. Stürzt das Skript ab oder hat man die Logout-Option deaktiviert, 
  dann ist es möglich ohne Login mit diesen Session Daten Scalable aufzurufen, bis das Timeout bei Scalable greift. 
  Ggf. sollte man den Ordner löschen, wenn man absolut sicher gehen will. 
	
# === INI Parameter ===	

**[General]**

max_transactions: Maximale Anzahl der Transaktionen, die das Skript versucht zu laden (Standard: 20).

download_directory: Name des Ordners oder kompletter Pfad, in dem die PDFs gespeichert werden (Standard: Scalable_Downloads).

stop_at_first_duplicate: Wenn "True", bricht das Skript ab, sobald die erste bereits vorhandene Datei gefunden wird (Standard: False).

use_original_filename: Bei "True" wird der Name von Scalable beibehalten; bei "False" wird die sprechende Benennung genutzt (Standard: False).

get_documents: Bei "True" werden auch die Dokumente aus der Mailbox heruntergeladen (Standard: True)

only_new_docs: Bei "True" werden nur die als neu markierten Dokumente geladen (Standard: True)

max_documents = Anzahl der Dokumente die maximal aus der Mailbox geladen werden sollen (Standard: 20)

logout_after_run: Meldet den Benutzer nach Abschluss aller Aktionen automatisch ab (Standard: True).

**[Keywords]**

transaction_types: Komma-getrennte Liste der Begriffe, die heruntergeladen werden sollen (Standard: Ausschüttung, Kauf, Verkauf, Sparplan, Steuern)
Die Namen der Typen entsprechen dem Filter "Auftragstyp" in Scalable
Bei manchen Transaktionen gibt es kein PDF - dann wird das Programm einen Fehler-Screenshot speichern!
Es gibt Transaktionen, die haben in der Filterliste einen anderen Namen, als dann in der gefilterten Liste angezeigt wird. 
z.B. "Depotübertrag" im Filter und "Einlieferung" in der Liste. Dann muss man unter transaction_types beide eintragen.  

**[WKN]**

diese Sektion kann mit einer Übersetzungstabelle ISIN zu WKN gefüllt werden
Sie kommt nur zum Einsatz wenn die Option use_original_filename = False ist
Wird eine ISIN gefunden, dann wird sie durch die angegebene WKN ersetzt
Wird die ISIN nicht gefunden, wird weiterhin die ISIN von Scalable genutzt

Beispiel:

	LU2572257124 = ETF018
	LU0496786657 = LYX0FZ

**[ButtonTexts]**

Wenn Scalable mal die Texte in der Webseite ändert, kann man die hier anpassen. Ansonsten gilt: Finger weg!

**[Timeouts]**

Auch hier besser Finger weg!
Wenn es zu einem Abbruch wegen Timeout kommt, kann man hier die Zeiten experimentell verlängern

# ===  english version ====

A tool for automated downloading transaction files (Buy, Sell, Savings Plan, Dividend) and document files from Scalable Capital.
Features

- Automated Download: Downloads documents based on configurable keywords
- Smart Naming: Files are named using the schema Date-Type-ISIN-Name-Amount.pdf.
- Duplicate Detection: Detects and skips existing files in the download folder.
- Early Stop: Optional stop upon finding the first duplicate (stop-at-first-duplicate).
- 2FA Support: Handles manual login including Two-Factor Authentication.
- Portability: Available as an EXE version including a portable browser (no Python installation required).

# Installation & Usage

# For Beginners (EXE Mode)

Download the ready-to-use EXE file from the Releases section.
Run the EXE. During the first launch, it may take 10-20 seconds for the window to open while the integrated browser is being unpacked.

I understand if you feel uneasy about running an unknown EXE on your computer, especially when it involves your brokerage account.
Therefore, the Python source code is also available. Even if you are not familiar with Python, you can have the code reviewed by an AI of your choice to verify what the code actually does.

# For Power Users (Script Mode)

Install Python 3.12+.

Create a project folder and copy downloader.py and start_downloader.bat into it.
If necessary, also copy the INI file if you want to adjust parameters before the first start. Otherwise, the INI will be created automatically.

Install libraries:


	pip install playwright


Install browser:


	playwright install chromium

Start via

	python downloader.py

or the SC-Downloader.bat.

# Notes

* If the INI file does not exist yet, it will be created with default values.
* If no download folder is defined, a directory named Scalable_Downloads will be created in the startup folder where the PDFs will be stored.
* The script creates a folder named scalable_session, where the runtime data of the integrated browser is stored.
* If the script completes correctly, it will log out at the end. If the script crashes or if you have deactivated the logout option, it is possible to access Scalable without a login using these session data until the Scalable timeout takes effect. You may want to delete the folder if you want to be absolutely safe.

# === INI Parameters ===

**[General]**

max_transactions: Maximum number of transactions the script attempts to load (Default: 20).

download_directory: Name of the folder or full path where the PDFs will be saved (Default: Scalable_Downloads).

stop_at_first_duplicate: If "True", the script stops as soon as the first already existing file is found (Default: False).

use_original_filename: If "True", the original Scalable filename is kept; if "False", a descriptive naming convention is used (Default: False).

get_documents: If "True" load also documents in Mailbox Section (Default: True)

only_new_docs: If "True" load only as "new" marked documents (Default: True)

max_documents = Maximum number of documents the script will load (Standard: 20)

logout_after_run: Automatically logs the user out after completing all actions (Default: True).

**[Keywords]**

transaction_types: Comma-separated list of terms to be downloaded (Default: Ausschüttung, Kauf, Verkauf, Sparplan, Steuern).
The names of the types correspond to the "Order Type" filter in Scalable.  
For some transactions, there is no PDF – in this case, the program will save an error screenshot!
There are transactions that have a different name in the filter list than what is displayed in the filtered list.
For example, "Depotübertrag" in the filter and "Einlieferung" in the list. In such cases, both must be entered under transaction_types.

**[WKN]**

This section can be filled with a translation table from ISIN to WKN.
It is only used if the option use_original_filename = False.
If an ISIN is found, it is replaced by the specified WKN.
If the ISIN is not found, the ISIN continues to be used.

Example:

	LU2572257124 = ETF018
	LU0496786657 = LYX0FZ

**[ButtonTexts]**

If Scalable changes the text on the website, you can adjust them here. Otherwise: Hands off!

**[Timeouts]**

It’s best to leave these alone as well!
If a timeout occurs, you can experimentally increase the times here.


