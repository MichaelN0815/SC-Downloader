> [!WARNING]
># ACHTUNG
>
>Scalable hat die Website geändert<br>
>**Der Quellcode V2.15.2 steht bereit. Ein aktualisierter EXE-Build folgt.**
>
<br>


![SC-Icon](https://github.com/user-attachments/assets/c9fdfd75-ba4b-47e6-bdbd-eb000ce26566)
# Scalable Capital PDF Downloader  ![GitHub Release](https://img.shields.io/github/v/release/MichaelN0815/SC-Downloader)
![Downloads](https://img.shields.io/github/downloads/MichaelN0815/SC-Downloader/total?style=flat-square&color=blue) ![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/MichaelN0815/SC-Downloader/latest/total)

Deutsch | English see below

Ein Tool zum automatisierten Herunterladen von Wertpapierabrechnungen (Kauf, Verkauf, Sparplan, Ausschüttung, etc.) und der Mailbox-Dokumente von Scalable Capital.

# Features

- Lädt Transaktion-Dokumente basierend auf konfigurierbaren Keywords herunter
- Intelligente Benennung: Dateien werden nach dem Schema YYYY-MM-DD-Typ-ISIN-Name-Betrag.pdf benannt
- Wahlweise kann die ISIN durch die WKN ersetzt werden
- Unterstützt mehrere Depots mit nur einem Login; konfigurierbare Depot-Bezeichner in generierten Transaktions-Dateinamen und optionale Unterverzeichnisse
- Lädt neue (oder alle) Dokumente aus der Mailbox herunter
- Duplikats-Prüfung: Bereits heruntergeladene Dokumente werden anhand ihrer Dokument-ID in einer CSV-Historie erkannt, auch wenn die PDFs verschoben oder gelöscht wurden
- Abbruch-Option: Optional beim ersten gefundenen Duplikat im jeweiligen Depot stoppen (stop_at_first_duplicate)
- Unterstützt den manuellen Login inklusive Zwei-Faktor-Authentifizierung
- Optional Auto-Login mit Speicherung im Windows Credential Manager (nur Windows)
- Als EXE-Version inklusive Browser verfügbar (keine Python-Installation nötig)

# Update-Hinweis

>[!IMPORTANT]
>Sollte die EXE Datei nach einem Update abstürzen, dann kann es helfen den scalable_session Ordner zu löschen.
>
>Da sich teilweise der Funktionsumfang ändert und damit einhergehend Einträge in der INI ergänzt wurden, empfehle ich bei einem Update auch die neuste INI runterzuladen und die geänderten Einstellungen dort nochmal vorzunehmen. 
>
>Zum Download der PDFs für Vorabpauschale wird Programm und INI ab der **Version 2.06** benötigt!
>
>**Version 2.07** generiert nun sauberere Dateinamen ohne unnötige Sonderzeichen - dadurch bedingt wird der erste Abruf auch mit der Einstellung `stop_at_first_duplicate = True` nochmal die gleichen PDFs runterladen - weil sich der selbst erstellte Dateiname leicht geändert hat. 
>
>**Version 2.08** optional können nun die Login-Daten gespeichert werden. Dazu wird der Windows Credential Manager genutzt. Daher ist diese Funktion nur unter Windows verfügbar. Das Skript greift nur auf den Passwort-Safe von Windows zu, es speichert intern keine Login-Daten ab. Diese Funktion wird nur aktiviert, wenn dies ausdrücklich in der INI-Datei eingetragen wird - siehe Abschnitt INI Parameter. Siehe auch das Issue zu dieser Funktion. (https://github.com/MichaelN0815/SC-Downloader/issues/8#issuecomment-3849121778) 
>
>**Version 2.11** standardmäßig werden nur noch Transaktionen im Ausgeführt-Status gesucht, da erfahrungsgemäß die anderen keine PDF enthalten.  
>vermeintlich doppelte Transaktionen werden nicht mehr übersprungen  
>die Dokumente sind nun nicht mehr auf die sichtbaren begrenzt und gleichnamige Dokumente werden durchnummeriert  
>Das Passwort für die use_saved_credentials Option wird nun unsichtbar abgefragt  
>Diverse kleine Probleme behoben  
>
>**Version 2.15** unterstützt mehrere Depots (Issue #25) und führt automatisch eine CSV-Download-Historie (Issue #23). Bestehende INI-Dateien funktionieren weiterhin. Beim erstmaligen Aufbau der Historie werden vorhandene Dateien anhand der bisherigen Dateinamen erkannt und beim Abruf in die Historie übernommen. Dokumente, die dabei nicht verarbeitet werden, können später erneut heruntergeladen werden. Für den ersten Lauf empfiehlt es sich daher, `stop_at_first_duplicate = False` zu setzen und die Abrufgrenzen ausreichend hoch einzustellen. Bei geänderten Dateinamen oder Zielverzeichnissen (z. B. durch die neue Depot-Konfiguration) können vorhandene PDFs erneut geladen werden. Die bestehenden PDFs werden nicht automatisch umbenannt oder verschoben.
>

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
Alles was mit `#` beginnt ist ein Kommentar und hat keine Funktion. 

>[!TIP]
>Hinweis: 
>Ich verstehe, wenn man ein ungutes Gefühl hat eine unbekannte EXE auf seinen Rechner und noch dazu sein Depot loszulassen. 
>Daher steht auch der Python Quellcode zur Verfügung. Diesen kann man auch als Python Unkundiger von einer KI der Wahl einem Code-Review unterziehen
>und prüfen lassen, was der Code wirklich macht. 
	
# Für Poweruser (Skript-Modus)

* Python 3.12+ installieren.

* Projekt-Ordner erstellen und downloader.py sowie start_downloader.bat hineinkopieren.
Ggf. auch die INI wenn man vor dem ersten Start bereits Parameter anpassen will. Ansonsten wird die INI automatisch erstellt.

* Bibliotheken installieren: 

	`pip install playwright==1.62.0`

* Browser installieren:

	`playwright install chromium`

* nur für Auto-Login unter Windows:

	`pip install keyring`

* Starten über

	`python downloader.py`
	
* oder die SC-Downloader.bat

# Hinweise

- Wenn die INI Datei noch nicht existiert, wird sie mit Standard-Werten angelegt
- Wenn kein Download-Ordner definiert wurde, wird im Start-Ordner ein Verzeichnis Scalable_Downloads angelegt, in dem die PDFs landen
- Das Skript legt einen Order scalable_session an, in dem die Laufzeit-Daten des integrierten Browsers abgelegt werden
- Wenn das Skript ordnungsgemäß durchläuft loggt es sich am Ende aus. Stürzt das Skript ab oder hat man die Logout-Option deaktiviert, 
  dann ist es möglich ohne Login mit diesen Session Daten Scalable aufzurufen, bis das Timeout bei Scalable greift. 
  Das könnte ein Sicherheits-Problem in einer Multi-User-Umgebung sein. In diesen Fällen immer mit Logout arbeiten und notfalls den Session-Ordner manuell löschen 
	
# INI Parameter

**[General]**

`max_transactions` Maximale Anzahl der PDF aus dem Bereich Transaktionen, die je Depot verarbeitet werden sollen (Standard: 20; getestet bis 500 in früheren Versionen)

`download_directory` Name des Ordners oder kompletter Pfad, in dem die PDFs gespeichert werden (Standard: Scalable_Downloads)

`download_directory_mailbox` optionale Angabe eines extra Speicherpfad für die Mailbox-PDFs (Standard: nicht genutzt). Hat Vorrang vor `use_subdirectories`.

`use_subdirectories` Wenn "True", werden im Download-Verzeichnis Unterordner für die konfigurierten Depot-Bezeichner und für Mailbox-Dokumente (`Mailbox`) genutzt. Ohne konfiguriertes Depot bleiben Transaktions-PDFs im Hauptverzeichnis. Bei "False" werden keine automatischen Unterordner angelegt (Standard: False).

`stop_at_first_duplicate` Wenn "True", bricht das Skript die Transaktionsverarbeitung des jeweiligen Depots ab, sobald das erste bereits heruntergeladene Dokument erkannt wird. Weitere Depots und die Mailbox werden weiterhin verarbeitet (Standard: False)

`only_executed` Wenn "True" dann wird der Status-Filter auf "ausgeführt" gesetzt (Standard: True)

`use_original_filename` Bei "True" wird der Name von Scalable beibehalten; bei "False" wird die sprechende Benennung für Transaktionens-PDFs genutzt und Dokument-PDFs erhalten ein besser lesbares Datumsformat (Standard: False)

`get_documents` Bei "True" werden auch die Dokumente aus dem Bereich Mailbox heruntergeladen (Standard: True)

`only_new_docs` Bei "True" werden nur die als neu markierten Dokumente geladen (Standard: True)

`max_documents` maximale Anzahl der Dokumente aus der Mailbox, die geladen werden sollen (Standard: 20)

`logout_after_run` Meldet den Benutzer nach Abschluss aller Aktionen automatisch ab (Standard: True)

`use_saved_credentials` Wenn True, dann wird ein Auto-Login durchgeführt. Die Zugangsdaten werden beim ersten Mal im Skript-Fenster (nicht im Browser!) abgefragt und sicher im Windows Credential Manager gespeichert. Dort sind sie unter scalable_login zu finden und können dort auch wieder gelöscht werden. Im Standard werden vom Skript keine Login-Daten gespeichert, diese Funktion ist rein optional. (Standard: False)

**[Portfolios]**

Optionale Sektion für ein oder mehrere Depots. Das gewünschte Depot bei Scalable öffnen, zur Transaktionsansicht wechseln und die ID hinter `portfolioId=` aus der URL übernehmen. Links steht ein frei wählbarer Depot-Bezeichner, rechts die Portfolio-ID. Groß- und Kleinschreibung des Bezeichners und der ID bleiben erhalten.

```ini
[Portfolios]
Altersvorsorge = 123456ABcde
Sparplan = 789012FGhij
#Trading = 345678KLmno
```

- Depots werden in der angegebenen Reihenfolge in derselben Browser-Session verarbeitet. Die Mailbox wird einmal am Ende abgearbeitet.
- `max_transactions` und `stop_at_first_duplicate` gelten pro Depot.
- Bei `use_original_filename = False` wird der Depot-Bezeichner an den generierten Transaktions-Dateinamen angehängt: `YYYY-MM-DD-Typ-ISIN-Name-Betrag-Depot.pdf`. Dies gilt auch für die generierten Vorabpauschale-Dateinamen. Mailbox-Dateinamen ändern sich dadurch nicht.
- Der Depot-Bezeichner muss als Datei- und Ordnername zulässig und eindeutig sein. `Mailbox` ist als Bezeichner reserviert.
- Wenn die Sektion fehlt oder keine aktiven Einträge enthält, wird die bisherige Standard-Transaktionsseite ohne vorgegebene Portfolio-ID verwendet.

**[Keywords]**

`transaction_types` Komma-getrennte Liste der Begriffe, die heruntergeladen werden sollen (Standard: Ausschüttung, Kauf, Verkauf, Sparplan, Steuern)

Die Namen der Typen entsprechen dem Filter "Typ" in Scalable

Bei manchen Transaktionen gibt es kein PDF - dann wird das Programm einen Fehler-Screenshot speichern!

Es gibt Transaktionen, die haben in der Filterliste einen anderen Namen, als dann in der gefilterten Liste angezeigt wird. 
z.B. "Depotübertrag" im Filter und "Einlieferung" in der Liste. Dann muss man unter transaction_types beide eintragen.  

**[WKN]**

- diese Sektion kann mit einer Übersetzungstabelle ISIN zu WKN gefüllt werden 
- Sie kommt nur zum Einsatz wenn die Option use_original_filename = False ist 
- Wird eine ISIN gefunden, dann wird sie durch die angegebene WKN ersetzt. 
- Wird die ISIN nicht gefunden, wird weiterhin die ISIN von Scalable genutzt
- Es ist hier zulässig Kommentare mit # oder ; anzufügen

Beispiel:

	LU2572257124 = ETF018 # Amundi Core MSCI World
	LU0496786657 = LYX0FZ ; Amundi Core S&P 500

**[ButtonTexts]**

Wenn Scalable mal die Texte in der Webseite ändert, kann man die hier anpassen. Ansonsten gilt: Finger weg!

**[Timeouts]**

Auch hier besser Finger weg!
Wenn es zu einem Abbruch wegen Timeout kommt, kann man hier die Zeiten experimentell verlängern

# Download-Historie (ab V2.15)

Die Datei `SC-Downloader-History.csv` wird automatisch neben dem Programm angelegt. Sie enthält eine Zeile pro erfasstem Dokument und verwendet Semikolon als Trennzeichen sowie UTF-8 mit BOM als Zeichensatz.

```csv
DocumentType;DocumentId;DownloadDate;Filename;Status
Transaction;AAAAAAAAAAAAAAAAAAAAAA;2026-11-25 10:15:23;2026-11-24-Kauf-A2N6CW-ETF-250_00-Altersvorsorge.pdf;
Mailbox;BBBBBBBBBBBBBBBBBBBBBB;2026-11-25 10:15:25;20261125 Produktuebersicht.pdf;
```

Die Kombination aus `DocumentType` und `DocumentId` ist der Schlüssel zur Duplikatsprüfung. Eine bekannte Dokument-ID wird unabhängig vom Dateinamen und Speicherort übersprungen. Der Anwender kann daher heruntergeladene PDFs archivieren, verschieben oder löschen, ohne dass sie beim nächsten Lauf erneut geladen werden. Änderungen an den Depot-Bezeichnern oder WKN-Zuordnungen beeinflussen die Duplikatsprüfung anhand der ID nicht.

Ein Eintrag wird nach erfolgreichem Download geschrieben. Beim ersten Lauf ohne CSV werden auch anhand der bisherigen Dateinamensprüfung erkannte PDFs in die Historie übernommen; `DownloadDate` ist in diesem Fall der Zeitpunkt der Aufnahme in die Historie. Ist keine verwendbare Dokument-ID verfügbar, greift weiterhin die bisherige Dateinamensprüfung. Haben unterschiedliche, noch nicht registrierte Dokumente denselben Dateinamen, wird bei einem Namenskonflikt eine Nummer angehängt, damit keine PDF überschrieben wird.

Die Historie kann bei beendetem Programm mit einem Texteditor oder Excel bearbeitet werden. Das Feld `Status` ist frei verwendbar und hat keinen Einfluss auf die Duplikatsprüfung. Beim Speichern in Excel müssen UTF-8, Semikolon und die Spaltenüberschriften erhalten bleiben. Die Dokument-IDs und den Dokumenttyp nicht verändern. Bei Bedarf können Zeilen entfernt oder die CSV-Datei gelöscht werden. Sind die PDFs noch vorhanden, können diese insbesondere beim erstmaligen Aufbau einer neuen Historie erneut als vorhanden erkannt werden. Bei einem Fehler beim Lesen oder Schreiben der Historie wird der Programmlauf beendet; die CSV sollte regelmäßig gesichert werden.

# ===  english version ==== 

A tool for automated downloading transaction files (Buy, Sell, Savings Plan, Dividend) and document files from Scalable Capital.
Features

- Automated Download: Downloads documents based on configurable keywords.
- Smart Naming: Files are named using the schema Date-Type-ISIN-Name-Amount.pdf.
- Multiple portfolios: Process configured portfolios in one session, append portfolio names to generated transaction filenames, and optionally use separate subdirectories.
- Duplicate Detection: Detects previously downloaded documents by document ID using a persistent CSV history, even if the PDF files have been moved or deleted.
- Early Stop: Optional stop upon finding the first duplicate in each portfolio (stop-at-first-duplicate).
- 2FA Support: Handles manual login including Two-Factor Authentication.
- Portability: Available as an EXE version including a portable browser (no Python installation required).

# Installation & Usage
# For Beginners (EXE Mode)

Download the ready-to-use EXE file from the Releases section.
Run the EXE. During the first launch, it may take 10-20 seconds to start, as the integrated browser is being unpacked.

I understand if you feel uneasy about running an unknown EXE on your computer, especially when it involves your brokerage account.
Therefore, the Python source code is also available. Even if you are not familiar with Python, you can have the code reviewed by an AI of your choice to verify what the code actually does.

# For Power Users (Script Mode)

* Python 3.12+ installieren.

* Create a project folder and copy downloader.py and start_downloader.bat into it.
If necessary, also copy the INI file if you want to adjust parameters before the first start. Otherwise, the INI will be created automatically.

* Install libraries: 

	`pip install playwright==1.62.0`

* Install browser:

	`playwright install chromium`



* Start via
	`python downloader.py`
	
or the SC-Downloader.bat.

# Notes

* If the INI file does not exist yet, it will be created with default values.
* If no download folder is defined, a directory named Scalable_Downloads will be created in the startup folder where the PDFs will be stored.
* The script creates a folder named scalable_session, where the runtime data of the integrated browser is stored.
* If the script completes correctly, it will log out at the end. If the script crashes or if you have deactivated the logout option, it is possible to access Scalable without a login using these session data until the Scalable timeout takes effect. You may want to delete the folder if you want to be absolutely safe.
* V2.15 introduces multiple portfolios and a persistent download history. Existing INI files still work. During the first run without a CSV history, existing files encountered under their original configured paths are registered by document ID. Set `stop_at_first_duplicate = False` and use sufficiently high download limits for the first run. Previously downloaded files that were not registered, or files with changed names or paths, may be downloaded again. Existing PDFs are not renamed or moved automatically.

# === INI Parameters ===

**[General]**

max_transactions: Maximum number of transactions the script attempts to load per portfolio (Default: 20).

download_directory: Name of the folder or full path where the PDFs will be saved (Default: Scalable_Downloads).

download_directory_mailbox: Optional separate directory for Mailbox PDFs. Takes precedence over use_subdirectories.

use_subdirectories: If "True", use subdirectories named after the configured portfolios and a `Mailbox` subdirectory within download_directory. Without configured portfolios, transaction PDFs remain in the main directory (Default: False).

stop_at_first_duplicate: If "True", the script stops processing the current portfolio as soon as the first previously downloaded document is found. Other portfolios and the Mailbox are still processed (Default: False).

use_original_filename: If "True", the original Scalable filename is kept; if "False", a descriptive naming convention is used (Default: False).

get_documents: If "True" load also documents in Mailbox Section (Default: True)

only_new_docs: If "True" load only as "new" marked documents (Default: True)

max_documents = Maximum number of documents the script will load (Standard: 20)

logout_after_run: Automatically logs the user out after completing all actions (Default: True).

**[Portfolios]**

Optional section for one or more portfolios. Open the desired portfolio's transaction page in Scalable and copy the value of the `portfolioId` URL parameter. Use a freely chosen portfolio name on the left and the ID on the right. The case of both names and IDs is preserved.

```ini
[Portfolios]
Retirement = 123456ABcde
Savings = 789012FGhij
#Trading = 345678KLmno
```

Portfolios are processed in the configured order with a single login. Both `max_transactions` and `stop_at_first_duplicate` apply per portfolio. The Mailbox is processed once afterwards.

If `use_original_filename = False`, the portfolio name is appended to generated transaction filenames, using the scheme `YYYY-MM-DD-Type-ISIN-Name-Amount-Portfolio.pdf`. This also applies to generated advance tax filenames. Mailbox filenames are unaffected. Choose distinct, valid file/directory names; `Mailbox` is reserved. If no portfolios are configured, the default transaction page is used as before.

**[Keywords]**

transaction_types: Comma-separated list of terms to be downloaded (Default: Ausschüttung, Kauf, Verkauf, Sparplan, Steuern).

The names of the types correspond to the "Type" filter in Scalable.  
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

# Download History (V2.15 onwards)

`SC-Downloader-History.csv` is created automatically next to the program. It uses semicolon-separated fields and UTF-8 with a BOM. The fields are `DocumentType`, `DocumentId`, `DownloadDate`, `Filename` and `Status`. Document type and document ID together identify a previously downloaded document independently of its filename or location.

New PDFs are registered only after successful saving. During the initial run without a CSV file, matching existing PDFs are registered using the previous filename-based duplicate detection. For those files, DownloadDate is the registration date. If no usable document ID is available, the previous filename-based check is used as a fallback. Distinct documents with colliding filenames are saved with a numeric suffix rather than overwriting existing files.

PDFs can be moved to an archive or deleted after download without being downloaded again. With the program closed, the optional Status field can be edited in a text editor or Excel; it does not affect duplicate detection. Preserve UTF-8, semicolon delimiters and the column headers. Do not edit the document IDs or document types. Removing a history entry or deleting the CSV allows the respective IDs to be considered again; existing PDFs can still be recognized when rebuilding the history. If the history cannot be read or written, the run is stopped. Keep a backup of this file.

## V2.15.2 - Browser / Playwright

DE: Für den Skript-Modus wird vorerst Playwright 1.62.0 empfohlen. Der EXE-Build wird separat angepasst. Playwright 1.63.0 führte unter Windows bei wiederverwendetem Browserprofil zu Chromium-Abstürzen beim Mailbox-Download. Version 1.62.0 funktionierte in drei Praxistests. Neuere Versionen erst nach erneutem Test freigeben. Bei unerwarteter Login-Weiterleitung während der Navigation wird einmal pro Lauf eine erneute Anmeldung versucht; 2FA bleibt erforderlich.

EN: Playwright 1.62.0 is currently recommended for script mode. The EXE build will be updated separately. Playwright 1.63.0 caused Chromium crashes on Windows during Mailbox downloads with a reused browser profile. Version 1.62.0 passed three live tests. Verify newer versions before upgrading. Unexpected login redirects during navigation trigger at most one reauthentication attempt per run; 2FA remains required.
