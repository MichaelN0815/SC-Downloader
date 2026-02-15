#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scalable Capital PDF Downloader
verborgene Passwort Abfrage
gleichnamige Transaktionen trotzdem laden
gleichnamige Dokumente mit Zähler speichern
max Anzahl Dokumente erhöht (ohne Viewport, begrenztes Scrolling)
"""

__version__ = "2.10.2"

import os
import sys
import time
import configparser
import re
import platform
import subprocess
import tempfile
import getpass

from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, unquote

# Plattformspezifische imports
if platform.system() == "Windows":
    import msvcrt
else:
    import tty
    import termios

# --- 1. STANDARDEINSTELLUNGEN ---
TARGET_URL = "https://de.scalable.capital/broker/transactions"
TARGET_URL2 = "https://de.scalable.capital/cockpit/mailbox"
DOWNLOAD_DIR = None  # NEU V2.04b Global
SERVICE_NAME = "scalable_login" # NEU V2.08

DEFAULT_CONFIG = {
    'max_transactions': '20',
    'max_documents': '20',
    'download_directory': 'Scalable_Downloads',
    'use_original_filename': 'False',
    'stop_at_first_duplicate': 'False',
    'logout_after_run': 'True',
    'use_saved_credentials': 'False',
    'get_documents': 'True',
    'only_new_docs': 'True',
    'slow_mo': '100',
    'transaction_types': 'Ausschüttung, Kauf, Verkauf, Sparplan, Steuern',
    'pdf_button_names': 'Wertpapierabrechnung, Wertpapierereignisse, Vorabpauschale',
    'logout_button': 'Abmelden',
    'page_load_wait': '100',
    'transaction_wait': '300',
    'critical_wait': '20',
    'pdf_button_timeout': '1000',
    'pdf_tab_timeout': '5000',
    'click_transaction_timeout': '5000',
    'filter_button_timeout': '500'
}

# --- 2. PFAD-LOGIK ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(sys._MEIPASS, "ms-playwright")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#HIER INI Name anpassen
CONFIG_PATH = os.path.join(BASE_DIR, "SC-Downloader.ini")
SESSION_DIR = os.path.join(BASE_DIR, "scalable_session")

def ensure_browser():
    print(f"=== Scalable Capital PDF Downloader v{__version__} ===")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initialisiere Browser...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("  ✓ Browser bereit.")
    except Exception as e:
        print(f"  ✗ FEHLER: Browser nicht gefunden: {e}")
        input("\nDrücke Enter zum Beenden...")
        sys.exit(1)

# ========== NEU V2.08: Zugangsdaten speichern ======
def ensure_credentials(use_saved_credentials):
    """
    Lädt oder erstellt Zugangsdaten im Windows Credential Manager
    
    Returns:
        tuple: (username, password) oder (None, None) wenn deaktiviert/nicht verfügbar
    """
    # Feature nur für Windows
    if platform.system() != "Windows":
        if use_saved_credentials:
            print("  ⚠ Gespeicherte Credentials nur unter Windows verfügbar")
        return None, None
    
    # Feature deaktiviert
    if not use_saved_credentials:
        return None, None

    # Keyring erst hier importieren (nur wenn benötigt)
    try:
        import keyring
    except ImportError:
        print("  ✗ FEHLER: 'keyring' Modul nicht installiert!")
        print("  → Bitte ausführen: pip install keyring")
        return None, None
        
    try:
        # Versuche Credentials zu laden
        username = keyring.get_password(SERVICE_NAME, "username")
        password = keyring.get_password(SERVICE_NAME, "password")
        
        # Credentials vorhanden
        if username and password:
            print(f"  ✓ Zugangsdaten aus Windows Credential Manager geladen")
            return username, password
        
        # Credentials nicht vorhanden - erstmalig abfragen
        print("\n" + "="*60)
        print("ERSTMALIGE EINRICHTUNG - Zugangsdaten speichern")
        print("="*60)
        print("Die Daten werden verschlüsselt im Windows Credential Manager")
        print("gespeichert und bei zukünftigen Starts automatisch geladen.")
        print("="*60)
        
        username = input("\nBenutzername (E-Mail): ").strip()
        password = getpass.getpass("Passwort: ").strip()
        
        if not username or not password:
            print("  ⚠ Keine gültigen Zugangsdaten eingegeben")
            return None, None
        
        # Im Windows Credential Manager speichern
        keyring.set_password(SERVICE_NAME, "username", username)
        keyring.set_password(SERVICE_NAME, "password", password)
        
        print(f"\n  ✓ Zugangsdaten erfolgreich gespeichert!")
        print(f"\nZum Löschen/Ändern:")
        print(f"Systemsteuerung → Anmeldeinformationsverwaltung → Windows-Anmeldeinformationen")
        print(f"Suche nach: {SERVICE_NAME}\n")
        
        return username, password
        
    except Exception as e:
        print(f"  ✗ Fehler beim Credential Manager: {e}")
        return None, None

# ========== NEU V2.02: WKN-Mapping laden ==========
def load_wkn_mapping(config):
    """
    Lädt die WKN-Zuordnungen aus der INI-Datei.
    Gibt ein Dictionary zurück: {ISIN: WKN}
    """
    wkn_mapping = {}
    if config.has_section('WKN'):
        for isin, wkn in config.items('WKN'):
            wkn_mapping[isin.upper()] = wkn.strip()
        print(f"[v{__version__}] {len(wkn_mapping)} WKN-Zuordnung(en) geladen")
    else:
        print(f"[v{__version__}] Keine [WKN] Sektion in INI gefunden")
    return wkn_mapping

# ========== NEU V2.02: ISIN zu WKN konvertieren ==========
def convert_isin_to_wkn(isin_str, wkn_mapping):
    """
    Prüft ob die ISIN im WKN-Mapping vorhanden ist.
    Wenn ja, wird die WKN zurückgegeben.
    Wenn nein, wird die ursprüngliche ISIN zurückgegeben.
    
    Args:
        isin_str: Die zu prüfende ISIN
        wkn_mapping: Dictionary mit ISIN->WKN Zuordnungen
    
    Returns:
        WKN wenn gefunden, sonst die ursprüngliche ISIN
    """
    isin_upper = isin_str.upper()
    if isin_upper in wkn_mapping:
        return wkn_mapping[isin_upper]
    return isin_str

# NEU V2.07
def sanitize_filename(filename):
    """
    Bereinigt den generierten Dateinamen nach festen Regeln:
    - Dezimalpunkt wird durch "_" ersetzt
    - Punkte von Abkürzungen (z.B. "Pkt.") werden entfernt
    - Trenner ist "-"
    - Aufeinanderfolgende "_" oder "-" werden zu einem Zeichen reduziert
    - "_" hat Vorrang vor "-" (bei aufeinanderfolgenden gemischten Trennern)
    - "_" oder "-" unmittelbar vor .pdf werden entfernt
    """
    # Entferne .pdf temporär
    has_pdf = filename.lower().endswith('.pdf')
    if has_pdf:
        filename = filename[:-4]
    
    # Ersetze Dezimalpunkt durch "_" (nur wenn von Zahlen umgeben)
    filename = re.sub(r'(\d)\.(\d)', r'\1_\2', filename)
    
    # Entferne alle anderen Punkte (z.B. von Abkürzungen wie "Pkt.")
    filename = filename.replace('.', '')
    
    # Normalisiere alle Trennzeichen: aufeinanderfolgende _ und/oder - zu einem Zeichen
    # Dabei hat "_" Vorrang vor "-"
    filename = re.sub(r'[-_]+', lambda m: '_' if '_' in m.group() else '-', filename)
    
    # Entferne Trennzeichen am Ende
    filename = filename.rstrip('_-')
    
    # .pdf wieder anhängen
    if has_pdf:
        filename += '.pdf'
    
    return filename

def load_config():
    # NEU V2.05: Inline Kommentare in INI erlaubt
    config = configparser.ConfigParser(
        inline_comment_prefixes=('#', ';'),
        comment_prefixes=('#', ';')
    )
    if os.path.exists(CONFIG_PATH):
        try:
            config.read(CONFIG_PATH, encoding='utf-8')
            print(f"[v{__version__}] Konfiguration geladen: {CONFIG_PATH}")
        except (configparser.DuplicateOptionError, configparser.ParsingError, Exception) as e:
            # NEU V2.09 INI Fehler abfangen
            print(f"\n{'='*60}")
            print(f" ⚠  FEHLER beim Laden der Konfiguration!  ⚠")
            print(f"{'='*60}")
            print(f"\033[91m{e}\033[0m")
            print(f"\n→ Bitte überprüfe die Datei:")
            print(f"   {CONFIG_PATH}")
            print(f"{'='*60}\n")
            input(" ⚠  Drücke Enter zum Beenden...")
            sys.exit(1)
    else:
        config['General'] = {
            'max_transactions': DEFAULT_CONFIG['max_transactions'],
            'max_documents': DEFAULT_CONFIG['max_documents'],
            'download_directory': DEFAULT_CONFIG['download_directory'],
            'use_original_filename': DEFAULT_CONFIG['use_original_filename'],
            'stop_at_first_duplicate': DEFAULT_CONFIG['stop_at_first_duplicate'],
            'logout_after_run': DEFAULT_CONFIG['logout_after_run'],
            'use_saved_credentials': DEFAULT_CONFIG['use_saved_credentials'],
            'get_documents': DEFAULT_CONFIG['get_documents'],
            'only_new_docs': DEFAULT_CONFIG['only_new_docs']
        }
        config['Keywords'] = {'transaction_types': DEFAULT_CONFIG['transaction_types']}
        # ========== NEU V2.02/V2.09: WKN-Beispiele ==========
        config['WKN'] = {
            'ISIN123': 'WKN123'
        }
        # ========== ENDE: WKN-Beispiele ==========        
        config['ButtonTexts'] = {
            'pdf_button_names': DEFAULT_CONFIG['pdf_button_names'],
            'logout_button': DEFAULT_CONFIG['logout_button']
        }
        config['Timeouts'] = {
            'slow_mo': DEFAULT_CONFIG['slow_mo'],
            'page_load_wait': DEFAULT_CONFIG['page_load_wait'],
            'transaction_wait': DEFAULT_CONFIG['transaction_wait'],
            'critical_wait': DEFAULT_CONFIG['critical_wait'],
            'pdf_button_timeout': DEFAULT_CONFIG['pdf_button_timeout'],
            'pdf_tab_timeout': DEFAULT_CONFIG['pdf_tab_timeout'],
            'click_transaction_timeout': DEFAULT_CONFIG['click_transaction_timeout'],
            'filter_button_timeout': DEFAULT_CONFIG['filter_button_timeout']
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"[v{__version__}] SC-Downloader.ini erstellt: {CONFIG_PATH}")
    
    # ========== NEU V2.02: WKN-Mapping laden ==========
    wkn_mapping = load_wkn_mapping(config)
    
    return {
        'max_transactions': config.getint('General', 'max_transactions', fallback=int(DEFAULT_CONFIG['max_transactions'])),
        'max_documents': config.getint('General', 'max_documents', fallback=int(DEFAULT_CONFIG['max_documents'])),
        'download_dir': config.get('General', 'download_directory', fallback=DEFAULT_CONFIG['download_directory']),
        'use_original_filename': config.getboolean('General', 'use_original_filename', fallback=False),
        'stop_at_first_duplicate': config.getboolean('General', 'stop_at_first_duplicate', fallback=False),
        'logout_after_run': config.getboolean('General', 'logout_after_run', fallback=True),
        'use_saved_credentials': config.getboolean('General', 'use_saved_credentials', fallback=False),
        'get_documents': config.getboolean('General', 'get_documents', fallback=True),
        'only_new_docs': config.getboolean('General', 'only_new_docs', fallback=True),
        'keywords': [k.strip() for k in config.get('Keywords', 'transaction_types', fallback=DEFAULT_CONFIG['transaction_types']).split(',')],
        'pdf_button_names': [k.strip() for k in config.get('ButtonTexts', 'pdf_button_names', fallback=DEFAULT_CONFIG['pdf_button_names']).split(',')],
        'logout_button': config.get('ButtonTexts', 'logout_button', fallback=DEFAULT_CONFIG['logout_button']),
        'slow_mo': config.getint('Timeouts', 'slow_mo', fallback=int(DEFAULT_CONFIG['slow_mo'])),
        'page_load_wait': config.getint('Timeouts', 'page_load_wait', fallback=int(DEFAULT_CONFIG['page_load_wait'])) / 1000,
        'transaction_wait': config.getint('Timeouts', 'transaction_wait', fallback=int(DEFAULT_CONFIG['transaction_wait'])) / 1000,
        'critical_wait': config.getint('Timeouts', 'critical_wait', fallback=int(DEFAULT_CONFIG['critical_wait'])) / 1000,
        'pdf_button_timeout': config.getint('Timeouts', 'pdf_button_timeout', fallback=int(DEFAULT_CONFIG['pdf_button_timeout'])),
        'pdf_tab_timeout': config.getint('Timeouts', 'pdf_tab_timeout', fallback=int(DEFAULT_CONFIG['pdf_tab_timeout'])),
        'click_transaction_timeout': config.getint('Timeouts', 'click_transaction_timeout', fallback=int(DEFAULT_CONFIG['click_transaction_timeout'])),
        'filter_button_timeout': config.getint('Timeouts', 'filter_button_timeout', fallback=int(DEFAULT_CONFIG['filter_button_timeout'])),
        'wkn_mapping': wkn_mapping  # ========== NEU V2.02 ==========
    }


def filename_from_url(url: str):
    #print(f"DEBUG filename_from_url: input url = {url}")

    try:
        path = urlparse(url).path
        #print(f"DEBUG filename_from_url: parsed path = {path}")

        name = os.path.basename(path)
        #print(f"DEBUG filename_from_url: basename = {name}")

        if not name:
            #print("DEBUG filename_from_url: basename ist leer")
            return None

        name = unquote(name)
        #print(f"DEBUG filename_from_url: unquoted name = {name}")

        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        #print(f"DEBUG filename_from_url: sanitized name = {name}")

        if not name.lower().endswith(".pdf"):
            name += ".pdf"
            #print(f"DEBUG filename_from_url: .pdf angehängt → {name}")

        return name

    except Exception as e:
        print(f"DEBUG filename_from_url: Exception aufgetreten: {e}")
        return None

def collect_targets(items, keywords, max_transactions):
    found = []
    for idx, item in enumerate(items):
        if len(found) >= max_transactions:
            break
        try:
            if not item.is_visible():
                continue
            zeit = item.get_attribute('aria-labelledby')
            text = item.inner_text().replace("\n", " ").strip()
            for key in keywords:
                if key in text:
                    found.append((idx, zeit, text, key))
                    break
        except Exception as e:
            print(f"  ⚠ Element {idx} konnte nicht gelesen werden: {e}")
            continue
    return found

def handle_popups(page):
    """Schließt häufige Popup-Dialoge"""
    try:
        # Cookie-Dialog (spezieller Test-ID Selector)
        try:
            cookie_btn = page.get_by_test_id("uc-accept-all-button")
            if cookie_btn.is_visible():
                cookie_btn.click()
                page.wait_for_load_state("networkidle")
                print(f"  ✓ Cookie-Dialog geschlossen")
        except Exception:
            pass
        
        # Popups über Button-Text
        texts = [
            "Schließen und nicht mehr",  # Börsen-Dialog nach Handelsschluss
            "Alle akzeptieren",          # Fallback für Cookie-Dialog
            "Akzeptieren", 
            "Zustimmen", 
            "Verstanden", 
            "Schließen"
        ]
        
        for text in texts:
            try:
                btn = page.get_by_role("button", name=text, exact=False).first
                # print(f"  ✓ Popup versuchen: '{text}'")
                if btn.is_visible():
                    btn.click()
                    print(f"  ✓ Popup geschlossen: '{text}'")
                    break  # Nach erfolgreichem Klick raus
            except Exception:
                pass
                
    except Exception as e:
        print(f"  ⚠ Popup-Handling Fehler: {e}")

# ========== NEU V2.04: Scroll-Funktion zum Nachladen ==========
def scroll_and_load_transactions(page, keywords, max_transactions, settings):
    """
    Scrollt durch die Transaktionsliste und lädt nach, bis max_transactions 
    erreicht ist oder keine neuen Transaktionen mehr erscheinen.
    """
    print(f"[v{__version__}] Starte Scroll-Logik zum Nachladen...")
    
    previous_count = 0
    stable_count = 0
    #wie oft wird Page-down gedrückt und auf neue Transaktionen geprüft?
    max_stable_iterations = 10
    
    while True:
        try:
            all_items = page.locator("div[role='button'], button").all()
        except Exception as e:
            print(f"  ⚠ Fehler beim Laden der Elemente: {e}")
            break
        
        current_targets = collect_targets(all_items, keywords, max_transactions)
        current_count = len(current_targets)
        
        print(f"  → Aktuell sichtbar: {current_count} Transaktionen")
        
        # Prüfen ob max_transactions erreicht
        if current_count >= max_transactions:
            print(f"  ✓ Maximum erreicht ({max_transactions})")
            break
        
        # Prüfen ob sich die Anzahl nicht mehr ändert
        if current_count == previous_count:
            stable_count += 1
            if stable_count >= max_stable_iterations:
                print(f"  ✓ Keine neuen Transaktionen mehr nach {max_stable_iterations} Versuchen")
                break
        else:
            stable_count = 0
        
        previous_count = current_count
        
        # Scrollen mit Page Down
        try:
            page.keyboard.press("PageDown")
            time.sleep(settings['critical_wait'])
        except Exception as e:
            print(f"  ⚠ Scroll fehlgeschlagen: {e}")
            break
    
    print(f"[v{__version__}] Scroll-Logik beendet. Insgesamt {current_count} Transaktionen verfügbar.")
    return current_count
# ========== ENDE NEU V2.04 ==========

def save_error_screenshot(page, download_dir, full_text, error_type, date_str=None, wp_name=None):
    """Speichert einen Error-Screenshot mit aussagekräftigem Namen"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        clean_text = full_text[:40]
        clean_text = re.sub(r'[^\w\s-]', '', clean_text)
        clean_text = clean_text.replace(" ", "_").strip("_")
        
        parts = ["error", error_type, timestamp]
        
        if date_str:
            parts.append(date_str)
        
        if wp_name:
            clean_wp = re.sub(r'[^\w\s-]', '', wp_name[:30])
            clean_wp = clean_wp.replace(" ", "_").strip("_")
            if clean_wp:
                parts.append(clean_wp)
        else:
            parts.append(clean_text)
        
        error_file_name = "_".join(parts) + ".png"
        error_path = os.path.join(download_dir, error_file_name)
        
        page.screenshot(path=error_path)
        print(f"*** ERROR ***  ⚠ Screenshot gespeichert: {error_file_name}") # V2.04b
    except Exception as screenshot_error:
        print(f"  ⚠ Screenshot fehlgeschlagen: {screenshot_error}")

# NEU V2.06
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00a0", " ")          # NBSP
    s = re.sub(r'\s+', ' ', s)            # Whitespace normalisieren
    s = s.replace("\n", " ").strip()
    return s

# NEU V2.09
def resolve_and_prepare_download_dir(raw_dir: str) -> str:
    """
    Bereinigt, validiert und erstellt das Download-Verzeichnis.
    """
    # 1) Basis-Kandidat bestimmen
    candidate = raw_dir.strip() if raw_dir else DEFAULT_CONFIG['download_directory']
    candidate = os.path.expanduser(candidate)  # ~ auflösen
    if not os.path.isabs(candidate):
        candidate = os.path.join(BASE_DIR, candidate)
    candidate = os.path.normpath(candidate)

    # 2) Plattform-spezifische Plausibilitätsprüfung
    if platform.system() == "Windows":
        invalid_chars = set('<>"/\\|?*')  # Doppelpunkt entfernt
        parts = candidate.split(os.sep)
        
        # Laufwerksbuchstabe (z.B. 'c:') überspringen
        start_index = 0
        if len(parts) > 0 and len(parts[0]) == 2 and parts[0][1] == ':':
            start_index = 1
        
        # Restliche Segmente prüfen
        for part in parts[start_index:]:
            if not part or part.endswith('.'):  # leere Segmente oder Endpunkt
                raise ValueError(f"Ungültiger Segmentname: '{part}'")
            if any(ch in invalid_chars for ch in part):
                raise ValueError(f"Ungültiges Zeichen in Segment '{part}'")

    try:
        # 3) Erstellen (falls nötig)
        os.makedirs(candidate, exist_ok=True)

        # 4) Schreibtest (Temp-Datei)
        fd, tmp_path = tempfile.mkstemp(prefix=".__writetest__", dir=candidate)
        os.close(fd)
        os.remove(tmp_path)

        return candidate
    except Exception as e:
        # 5) Fallback
        fallback = os.path.join(BASE_DIR, DEFAULT_CONFIG['download_directory'])
        try:
            os.makedirs(fallback, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(prefix=".__writetest__", dir=fallback)
            os.close(fd)
            os.remove(tmp_path)
            print(f"⚠ Download-Verzeichnis '{candidate}' nicht verfügbar: {e}")
            print(f"  → Fallback: {fallback}")
            return fallback
        except Exception as e2:
            print(" ✗ Kritischer Fehler: Konnte kein gültiges Download-Verzeichnis anlegen.")
            print(f"   Primär: {candidate} -> {e}")
            print(f"   Fallback: {fallback} -> {e2}")
            input(" Drücke Enter zum Beenden...")
            sys.exit(1)

# ==========================================================================================
#
# ========================================= START ==========================================
#
# ==========================================================================================

def run_downloader():
    global DOWNLOAD_DIR # NEU V2.04b
    settings = load_config()
    KEYWORDS = settings['keywords']
    PDF_BUTTON_NAMES = settings['pdf_button_names']
    WKN_MAPPING = settings['wkn_mapping']  # ========== NEU V2.02 ==========
    
    # NEU V2.09 fehlerhaften Pfad abfangen
    DOWNLOAD_DIR = resolve_and_prepare_download_dir(settings['download_dir'])
    print(f"[v{__version__}] Zielordner: {DOWNLOAD_DIR}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            SESSION_DIR, 
            headless=False,
            slow_mo=settings['slow_mo'],
            accept_downloads=True
        )
        page = context.new_page()

        try:
            page.goto(TARGET_URL)
        except Exception as e:
            print(f"  ✗ Fehler beim Öffnen der Seite: {e}")
            context.close()
            return
        
        # wichtig damit ein ggf benötigter Login erkannt wird
        page.wait_for_load_state("networkidle")

        if "login" in page.url:
            # NEU V2.08 Versuche Auto-Fill falls aktiviert
            if settings['use_saved_credentials']:
                username, password = ensure_credentials(settings['use_saved_credentials'])
                
                if username and password:
                    try:
                        print("  → Fülle Login-Daten aus...")
                        page.wait_for_selector("#username", timeout=10000)
                        page.fill('#username', username, timeout=2000)
                        page.fill('#password', password, timeout=1000)
                        # Login-Button klicken
                        page.get_by_role("button", name="Login").click() # Selektor über Text
                        print("  ✓ Login-Daten ausgefüllt - Bitte 2FA in der App bestätigen")
                    except Exception as e:
                        print(f"  ⚠ Auto-Fill fehlgeschlagen: {e}")
                        print("  → Bitte komplett manuell einloggen")
                else:
                    print("  → Bitte manuell einloggen")
            else:
                print("Warte auf manuellen Login (2FA)...")
            
            # Warte auf erfolgreichen Login (wie bisher)
            try:
                page.wait_for_url(re.compile(r".*/(cockpit|transactions|dashboard|broker)/.*"), timeout=90000) # 90 Sekunden warten
                print("  ✓ Login erkannt.")
            except Exception as e:
                if "Timeout" in type(e).__name__ or "Timeout" in str(e):
                    # NEU V2.09 
                    print(" ⚠  TIMEOUT: Kein Login innerhalb von 1 Minute")
                    context.close()
                    input(" ⏸  Drücke Enter zum Beenden...")
                    sys.exit(1)
                else:
                    print(f"  ⚠ Login-Warnung: {e}")
                    
            # Debug V2.09 STOP zum manuellen Debuggen
            # page.pause()

            page.wait_for_load_state("networkidle")
            handle_popups(page)
            
            if TARGET_URL not in page.url:
                print("  -> Navigiere zu Transaktionen...")
                try:
                    page.goto(TARGET_URL)
                    #handle_popups(page)
                except Exception as e:
                    print(f"  ⚠ Navigation fehlgeschlagen: {e}")
        
        try:
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"  ⚠ Warnung beim Laden: {e}")
        
        time.sleep(settings['page_load_wait'])

        print(f"[v{__version__}] Setze Filter...")
        try:
            filter_button = page.get_by_text("Auftragstyp").first
            filter_button.click(timeout=settings['filter_button_timeout'])
            print("  ✓ Filter-Dropdown geöffnet")
            
            try:
                dropdown = page.locator("[role='listbox'], [role='menu'], div[class*='dropdown'][class*='menu']").first
                for keyword in KEYWORDS:
                    try:
                        dropdown.get_by_text(keyword, exact=False).first.click(timeout=1000, no_wait_after=True)
                        print(f"  ✓ Filter gesetzt: {keyword}")
                    except Exception as e:
                        print(f"  ⚠ Filter '{keyword}' nicht gefunden: {e}")
                
                page.keyboard.press("Escape")
                print("  ✓ Filter angewendet")
            except Exception as e:
                print(f"  ⚠ Dropdown-Fehler: {e}")
        except Exception as e:
            print(f"  ⚠ Filter-Button nicht gefunden: {e}")
            print("  → Fahre ohne Filter fort")

        time.sleep(settings['critical_wait'])

        try:
            all_items = page.locator("div[role='button'], button").all()
        except Exception as e:
            print(f"  ✗ Fehler beim Laden der Transaktionen: {e}")
            context.close()
            return

        targets = collect_targets(all_items, KEYWORDS, settings['max_transactions'])

        if not targets:
            print("  ⚠ Keine relevanten Dokumente gefunden, warte kurz und versuche erneut...")
            time.sleep(settings['transaction_wait'])
            try:
                all_items = page.locator("div[role='button'], button").all()
            except Exception:
                all_items = []
            targets = collect_targets(all_items, KEYWORDS, settings['max_transactions'])

        # ========== NEU V2.04: Scroll-Logik aktivieren ==========
        if len(targets) < settings['max_transactions']:
            total_visible = scroll_and_load_transactions(page, KEYWORDS, settings['max_transactions'], settings)
            # Nach dem Scrollen erneut alle Targets sammeln
            try:
                all_items = page.locator("div[role='button'], button").all()
                targets = collect_targets(all_items, KEYWORDS, settings['max_transactions'])
            except Exception as e:
                print(f"  ⚠ Fehler beim erneuten Sammeln nach Scroll: {e}")
        # ========== ENDE NEU V2.04 ==========

        print(f"[v{__version__}] Suche beendet. {len(targets)} relevante Dokumente gefunden.")
        
        downloaded = skipped = 0
        for target_idx, (idx, zeit, full_text, keyword) in enumerate(targets):
            file_name = "unknown_transaction.pdf" 
            try:
                print(f"\n[{target_idx+1}/{len(targets)}] {full_text[:50]}...")
                
                # Transaktion öffnen
                try:
                    clicked = False
                    normalized_target = normalize_text(full_text)
                    items = page.locator("div[role='button'], button")
                    count = items.count()

                    for i in range(count):
                        item = items.nth(i)
                        try:
                            item_zeit = item.get_attribute('aria-labelledby')
                            ui_text = normalize_text(item.inner_text())
                            if ui_text != normalized_target:
                                continue
                            if item_zeit != zeit:
                                continue
                            type_element = item.get_by_text(keyword, exact=True).first
                            type_element.scroll_into_view_if_needed(timeout=2000)
                            time.sleep(0.1)
                            type_element.click(timeout=settings['click_transaction_timeout'])
                            clicked = True
                            print("  ✓ Transaktion geöffnet")
                            break
                        except Exception:
                            continue

                    if not clicked:
                        print("  ✗ Transaktion nicht gefunden, überspringe")
                        save_error_screenshot(page, DOWNLOAD_DIR, full_text, "missing_transaction")
                        continue
                except Exception as e:
                    print(f"  ✗ Klick fehlgeschlagen: {e}")
                    save_error_screenshot(page, DOWNLOAD_DIR, full_text, "missing_transaction")
                    continue
                
                time.sleep(settings['transaction_wait'])
                
                # PDF-Button finden
                pdf_btn = None
                found_button_name = None
                for btn_text in PDF_BUTTON_NAMES:
                    try:
                        pdf_btn = page.get_by_text(btn_text).first
                        pdf_btn.wait_for(state="visible", timeout=settings['pdf_button_timeout'])
                        found_button_name = btn_text
                        print(f"  ✓ PDF-Button gefunden: '{found_button_name}'")
                        break
                    except Exception as e:
                        continue
                
                if not pdf_btn or not found_button_name:
                    print(f"  ✗ Kein PDF-Button gefunden (versucht: {', '.join(PDF_BUTTON_NAMES)})")
                    wp_extract = re.sub(r'\(.*?\)', '', full_text)
                    pattern = r'-?\d+[\.,]\d{2}.*$'
                    wp_extract = re.sub(pattern, '', wp_extract).strip()
                    if wp_extract.startswith(keyword):
                        wp_extract = wp_extract[len(keyword):].strip()
                    save_error_screenshot(page, DOWNLOAD_DIR, full_text, "missing_pdf", None, wp_extract)
                    page.keyboard.press("Escape")
                    continue

                # === NEU V2.06 ==============================================
                # VORABPAUSCHALE: Spezielles Element klicken
                # ============================================================
                is_vorabpauschale = (keyword == "Steuern" and found_button_name == "Vorabpauschale")
                
                if is_vorabpauschale:
                    print("  -> Vorabpauschale erkannt, verwende speziellen Selektor...")
                    try:
                        # Spezial-Element für Vorabpauschale finden
                        vp_element = page.locator('[data-testid="value-Vorabpauschale"]').first
                        vp_element.wait_for(state="visible", timeout=2000)
                        
                        # PDF-Tab öffnen
                        with context.expect_page(timeout=settings['pdf_tab_timeout']) as new_page_info:
                            vp_element.click(timeout=settings['pdf_button_timeout'])
                        new_tab = new_page_info.value
                        pdf_url = new_tab.url
                        print(f"  ✓ PDF-URL aus Tab: {pdf_url[:60]}...")
                        new_tab.close()
                    except Exception as e:
                        print(f"  ✗ Vorabpauschale-Element nicht gefunden: {e}")
                        try:
                            page.keyboard.press("Escape")
                        except:
                            pass
                        continue
                
                # ============================================================
                # STANDARD: Normaler PDF-Button
                # ============================================================
                else:
                    pdf_url = None
                    try:
                        print(f"  -> Öffne PDF-Tab...")
                        with context.expect_page(timeout=settings['pdf_tab_timeout']) as new_page_info:
                            pdf_btn.click(timeout=settings['pdf_button_timeout'])
                        new_tab = new_page_info.value
                        pdf_url = new_tab.url
                        print(f"  ✓ PDF-URL aus Tab: {pdf_url[:60]}...")
                        new_tab.close()
                    except Exception as e:
                        print(f"  ✗ PDF-Tab konnte nicht geöffnet werden: {e}")
                        try:
                            page.keyboard.press("Escape")
                        except:
                            pass
                        continue
                
                # ============================================================
                # AB HIER: Gemeinsame Logik für alle PDFs
                # ============================================================
                
                # Dateiname erstellen
                url_without_params = pdf_url.split("?")[0] if pdf_url else ""
                
                # Vorabpauschale: Spezielle Namenslogik
                if is_vorabpauschale:
                    vp_text = full_text
                    if vp_text.startswith("Steuern "):
                        vp_text = vp_text[8:].strip()
                    
                    isin_match = re.search(r'\(([A-Z]{2}[A-Z0-9]{10})\)', vp_text)
                    isin_str = isin_match.group(1) if isin_match else "UNKNOWN"
                    identifier_str = convert_isin_to_wkn(isin_str, WKN_MAPPING)
                    
                    wp_name = re.sub(r'\(.*?\)', '', vp_text)
                    wp_name = wp_name.replace("Vorabpauschale:", "").strip()
                    wp_name_clean = "_".join(wp_name.split())
                    wp_name_clean = re.sub(r'[^\w\s-]', '_', wp_name_clean)
                    
                    # Original-Dateiname vom Server holen
                    original_name = filename_from_url(url_without_params)
                    if original_name:
                        # Original-Name ohne .pdf Extension
                        original_base = original_name.rsplit('.pdf', 1)[0] if original_name.endswith('.pdf') else original_name
                        final_file_name = f"{original_base}-{identifier_str}-{wp_name_clean}.pdf"
                    else:
                        # Fallback falls kein Original-Name verfügbar
                        current_year = datetime.now().year
                        date_str = f"{current_year}-01-02"
                        final_file_name = f"{date_str}-Vorabpauschale-{identifier_str}-{wp_name_clean}.pdf"
                
                
                # Standard: Normale Namenslogik
                else:
                    match = re.search(r'(\d{4}-\d{2}-\d{2})-.+?-([A-Z]{2}[A-Z0-9]{10})', url_without_params)
                    date_str = match.group(1) if match else datetime.now().strftime("%Y-%m-%d")
                    isin_str = match.group(2) if match else "UNKNOWN"
                    
                    if not match:
                        print(f"  ⚠ Konnte Datum/ISIN nicht aus URL parsen: {url_without_params}")

                    wp_name = re.sub(r'\(.*?\)', '', full_text)
                    betrag_m = re.findall(r'(-?\d+[\.,]\d{2})', full_text)
                    betrag = betrag_m[-1].replace(",", "_").replace(".", "_") if betrag_m else "0_00"
                    pattern2 = r'-?\d+[\.,]\d{2}.*$'
                    wp_name = re.sub(pattern2, '', wp_name).strip()
                    if wp_name.startswith(keyword): 
                        wp_name = wp_name[len(keyword):].strip()
                    wp_name_clean = "_".join(wp_name.replace("€", "").replace(",", "-").replace(":", "").replace("/", "-").split())
                    
                    identifier_str = convert_isin_to_wkn(isin_str, WKN_MAPPING)
                    final_file_name = f"{date_str}-{keyword[:4]}-{identifier_str}-{wp_name_clean}-{betrag}.pdf"
                
                # NEU V2.07 Dateinamen bereinigen
                final_file_name = sanitize_filename(final_file_name)
                
                # Optional: Original-Dateiname verwenden (NICHT bei Vorabpauschale!)
                if settings['use_original_filename'] and not is_vorabpauschale:
                    original_name = filename_from_url(url_without_params)
                    if original_name:
                        final_file_name = original_name

                target_path = os.path.join(DOWNLOAD_DIR, final_file_name)

                # Duplikatsprüfung
                if os.path.exists(target_path):
                    print(f"  -> ✓ Bereits vorhanden: {final_file_name}")
                    skipped += 1
                    if settings['stop_at_first_duplicate']:
                        print("  -> [STOP] Breche ab (Duplikat gefunden).")
                        try:
                            page.keyboard.press("Escape")
                        except Exception:
                            pass
                        break
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
                    continue

                # PDF herunterladen
                try:
                    print("  -> Lade PDF herunter...")
                    response = page.request.get(pdf_url)

                    if response.status != 200:
                        print(f"  ✗ HTTP-Fehler: Status {response.status}")
                        page.keyboard.press("Escape")
                        continue

                    content_type = response.headers.get('content-type', '').lower()
                    if 'pdf' not in content_type:
                        print(f"  ⚠ Warnung: Content-Type ist kein PDF: {content_type}")

                    pdf_bytes = response.body()

                    if pdf_bytes[:4] != b'%PDF':
                        print("  ✗ Fehler: Keine gültige PDF-Datei")
                        page.keyboard.press("Escape")
                        continue

                    with open(target_path, "wb") as f:
                        f.write(pdf_bytes)

                    file_size = len(pdf_bytes) / 1024
                    print(f"  -> ✓ Gespeichert: {final_file_name} ({file_size:.1f} KB)")
                    downloaded += 1

                except Exception as e:
                    print(f"  ✗ Download fehlgeschlagen: {e}")
                
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.1)
                except Exception as e:
                    print(f"  ⚠ Escape fehlgeschlagen: {e}")
                    
            except Exception as e: 
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                wp_extract = re.sub(r'\(.*?\)', '', full_text)
                pattern3 = r'-?\d+[\.,]\d{2}.*$'
                wp_extract = re.sub(pattern3, '', wp_extract).strip()
                if keyword and wp_extract.startswith(keyword):
                    wp_extract = wp_extract[len(keyword):].strip()
                
                clean_wp = wp_extract[:30].replace(' ', '_')
                clean_wp = re.sub(r'[^\w\s-]', '', clean_wp).replace(' ', '_')
                error_file_name = f"error_unexpected_{timestamp}_{clean_wp}.png"
                error_path = os.path.join(DOWNLOAD_DIR, error_file_name)
                
                try:
                    page.screenshot(path=error_path)
                    print(f"  ✗ FEHLER: {e}")
                    print(f"  ⚠ Screenshot gespeichert: {error_file_name}")
                except Exception as screenshot_error:
                    print(f"  ✗ FEHLER: {e}")
                    print(f"  ⚠ Screenshot fehlgeschlagen: {screenshot_error}")
                
                try:
                    page.keyboard.press("Escape")
                except Exception as esc_error:
                    print(f"  ⚠ Escape fehlgeschlagen: {esc_error}")
                    
        # ENDE for Schleife Transaktionen
        
        # Start Download Dokumente
        docs_downloaded = 0
        docs_skipped = 0
                
        if settings['get_documents']:
            print(f"\n[v{__version__}] ...suche nach Dokumenten (max. {settings['max_documents']})")
            
            try:
                print(f"  -> Navigiere zur Mailbox...")
                page.goto(TARGET_URL2)
                # sicherstellen das die Seite geladen ist
                time.sleep(2)
                
                try:
                    page.wait_for_load_state("networkidle")
                except Exception as e:
                    print(f"  ⚠ Warnung beim Laden der Mailbox: {e}")
                
                time.sleep(settings['page_load_wait'])
                print(f"  ✓ Mailbox geladen")
                
                # V2.10.2 neue Scrolllogik - Hole Gesamthöhe und sichtbare Höhe dynamisch
                try:
                    scroll_container = page.locator('div[role="list"][aria-label="Mailbox"] > div').first
                    total_height = scroll_container.evaluate("element => element.scrollHeight")
                    viewport_height = scroll_container.evaluate("element => element.clientHeight")
                    
                    #print(f"  Gesamthöhe: {total_height}px, sichtbar: {viewport_height}px")
                    print(f"  ℹ️ max. mögliche Anzahl Dokumente ca. {int(total_height/60)}")
                    
                    # Schätze Dokumente pro Viewport (~9-10 Dokumente)
                    docs_per_viewport = 7
                    
                    # Berechne benötigte Scroll-Steps basierend auf max_documents
                    needed_steps = (settings['max_documents'] // docs_per_viewport) + 2  # +2 als Puffer
                    max_possible_steps = int(total_height / viewport_height) + 1
                    
                    scroll_steps = min(needed_steps, max_possible_steps)
                    
                    #print(f"  Benötigte Scroll-Steps für {settings['max_documents']} Dokumente: {scroll_steps}")
                except Exception as e:
                    print(f"  ⚠ Fehler: {e}")
                    scroll_steps = (settings['max_documents'] // 9) + 2  # Fallback
                    viewport_height = 800
                
                # Download-Loop
                processed_ids = set()  # Vermeide Duplikate
                
                # Scrolle in Viewport-großen Schritten
                for step in range(scroll_steps):
                    if docs_downloaded + docs_skipped >= settings['max_documents']:
                        print(f"  ✓ Maximum erreicht ({settings['max_documents']})")
                        break
                    
                    scroll_pos = step * viewport_height
                    
                    try:
                        scroll_container.evaluate(f"element => element.scrollTop = {scroll_pos}")
                        time.sleep(0.5)
                        
                        #print(f"  Scroll-Position: {scroll_pos}/{total_height}px")
                        
                        # Verarbeite alle aktuell sichtbaren Dokumente
                        if not settings['only_new_docs']:
                            # Alle Dokumente mit Download-Symbol
                            visible_docs = page.locator('[data-mailbox-item-subject]').filter(
                                has=page.locator('[data-testid="mailbox-download"]')
                            ).all()
                        else:
                            # Nur neue Dokumente (mit Neu-Kennzeichnung)
                            candidate_rows = page.locator('[data-mailbox-item-subject]').filter(
                                has=page.locator('[data-testid="mailbox-download"]')
                            )
                            
                            visible_docs = []
                            for i in range(candidate_rows.count()):
                                row = candidate_rows.nth(i)
                                try:
                                    status_cell = row.locator('div.MuiGrid-grid-xs-1').last
                                    indicator = status_cell.locator('*')
                                    if indicator.count() > 0 and indicator.first.is_visible():
                                        visible_docs.append(row)
                                except Exception:
                                    continue
                        
                        # Download jedes sichtbaren Dokuments
                        for row in visible_docs:
                            # Prüfe ob bereits verarbeitet
                            try:
                                doc_id = row.get_attribute('data-testid')
                                if doc_id in processed_ids:
                                    continue
                                processed_ids.add(doc_id)
                            except:
                                continue
                            
                            if docs_downloaded + docs_skipped >= settings['max_documents']:
                                break
                            
                            try:
                                print(f"\n[Dokument {docs_downloaded + docs_skipped + 1}/{settings['max_documents']}]")
                                
                                # Suche das Download-Element innerhalb dieser Zeile
                                download_element = None
                                try:
                                    download_element = row.locator('[data-testid="mailbox-download"]').first
                                    download_element.wait_for(state="visible", timeout=settings['pdf_button_timeout'])
                                    print(f"  ✓ Download-Symbol gefunden")
                                except Exception as e:
                                    print(f"  ✗ Download-Symbol nicht gefunden: {e}")
                                    continue
                                
                                # Klick auf das Download-Element
                                try:
                                    print(f"  -> Öffne Dokument...")
                                    
                                    # Fange den direkten Download ab
                                    download_info = None
                                    try:
                                        with page.expect_download(timeout=settings['pdf_tab_timeout']) as download_info_promise:
                                            # Finde das klickbare Element (könnte das SVG oder ein Parent sein)
                                            clickable = row.locator('[data-testid="mailbox-download"] svg, [data-testid="mailbox-download"]').first
                                            clickable.click()
                                        
                                        download_info = download_info_promise.value
                                        print(f"  ✓ Download gestartet: {download_info.suggested_filename}")
                                        
                                    except Exception as download_error:
                                        print(f"  ✗ Download-Event nicht gefangen: {download_error}")
                                        continue
                                    
                                except Exception as e:
                                    print(f"  ✗ Dokument konnte nicht geöffnet werden: {e}")
                                    continue
                                
                                # Original-Dateiname ermitteln
                                final_file_name = download_info.suggested_filename
                                if not final_file_name.lower().endswith('.pdf'):
                                    final_file_name += '.pdf'
                                
                                # Zielpfad festlegen
                                target_path = os.path.join(DOWNLOAD_DIR, final_file_name)
                                
                                # Duplikatsprüfung mit Datumsprüfung
                                if os.path.exists(target_path):
                                    
                                    # Datum der existierenden Datei prüfen
                                    existing_mtime = os.path.getmtime(target_path)
                                    age_seconds = time.time() - existing_mtime
                                    
                                    if age_seconds > 600:  # Älter als 10 Minuten
                                        # Alte Datei = Duplikat, überspringen
                                        print(f"  -> ✓ Bereits vorhanden: {final_file_name}")
                                        docs_skipped += 1
                                        # Download-Objekt verwerfen
                                        try:
                                            temp_path = download_info.path()
                                            if temp_path and os.path.exists(temp_path):
                                                os.remove(temp_path)
                                        except Exception:
                                            pass
                                        continue
                                    else:
                                        # Frische Datei = anderes Dokument mit gleichem Namen
                                        base_name = final_file_name[:-4]  # ohne .pdf
                                        counter = 1
                                        while os.path.exists(target_path):
                                            final_file_name = f"{base_name}_{counter}.pdf"
                                            target_path = os.path.join(DOWNLOAD_DIR, final_file_name)
                                            counter += 1
                                        print(f"  -> Gleichnamiges Dokument, speichere als: {final_file_name}")
                                
                                # PDF herunterladen
                                try:
                                    print("  -> Lade PDF herunter...")
                                    
                                    # Direkter Download - Datei verschieben
                                    download_info.save_as(target_path)
                                    file_size = os.path.getsize(target_path) / 1024
                                    
                                    print(f"  -> ✓ Gespeichert: {final_file_name} ({file_size:.1f} KB)")
                                    docs_downloaded += 1
                                    
                                except Exception as e:
                                    print(f"  ✗ Download fehlgeschlagen: {e}")
                                    # Aufräumen falls Download-Datei teilweise existiert
                                    try:
                                        temp_path = download_info.path()
                                        if temp_path and os.path.exists(temp_path):
                                            os.remove(temp_path)
                                    except Exception:
                                        pass
                            
                            except Exception as e:
                                print(f"  ✗ FEHLER bei Dokument: {e}")
                                continue
                            
                    except Exception as e:
                        print(f"  ⚠ Fehler bei Scroll-Position {scroll_pos}: {e}")
                        continue
                
                print(f"\n[v{__version__}] Dokumente-Download abgeschlossen: {docs_downloaded} heruntergeladen, {docs_skipped} übersprungen")
                
            except Exception as e:
                print(f"  ✗ Fehler beim Mailbox-Zugriff: {e}")
        
        # Start Logout
        if settings['logout_after_run']:
            try:
                # Screenshot zur Diagnose
                #debug_screenshot = os.path.join(DOWNLOAD_DIR, f"debug_before_logout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                #page.screenshot(path=debug_screenshot)
                #print(f"  ℹ Debug-Screenshot: {os.path.basename(debug_screenshot)}")
                
                logout_btn = page.get_by_text(settings['logout_button']).first
                # die Timeout Zeit darf nicht zu kurz sein
                logout_btn.wait_for(state="visible", timeout=settings['filter_button_timeout'])
                logout_btn.click(no_wait_after=True)
                print(f"\n[v{__version__}] ✓ Abgemeldet")
            except Exception as e:
                msg = str(e).lower()
                if "logout" in msg or "navigated to" in msg:
                    print("✓ Abgemeldet (Navigation gestartet)")
                else:
                    print(f"⚠ Abmeldung fehlgeschlagen: {e}")
        
        context.close()
        print(f"\n[v{__version__}] *** Ergebnis ***")
        print(f"[v{__version__}] Download-Verzeichnis: {DOWNLOAD_DIR}")
        print(f"[v{__version__}] Transaktionen neu geladen: {downloaded}, Übersprungen: {skipped}")
        print(f"[v{__version__}] Dokumente     neu geladen: {docs_downloaded}, Übersprungen: {docs_skipped}")

# =========== NEU V2.04b ===============
def open_download_folder(download_dir):
    """Öffnet den Download-Ordner im Dateimanager"""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(download_dir)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", download_dir])
        else:  # Linux und andere Unix-Systeme
            subprocess.run(["xdg-open", download_dir])
        print(f"  ✓ Ordner geöffnet: {download_dir}")
    except Exception as e:
        print(f"  ⚠ Ordner konnte nicht geöffnet werden: {e}")
# ========== ENDE NEU V2.04b ==========

if __name__ == "__main__":
    ensure_browser()
    run_downloader()
    
    # NEU V2.04b Download-Ordner zum öffnen anbieten
    print("="*30)
    print("ENTER  = Ordner öffnen und beenden")
    print("ESC    = Sofort beenden")
    print("="*30)
    
    # Plattformübergreifende Tastatureingabe
    if platform.system() == "Windows":
        print("Warte auf Tastendruck...")
        key = msvcrt.getch()
        if key in [b'\r', b'\n']:  # ENTER
            open_download_folder(DOWNLOAD_DIR)
    else:
        # Unix/Linux/macOS
        print("Warte auf Tastendruck...")
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            if key in ['\r', '\n']:  # ENTER
                print()  # Neue Zeile für saubere Ausgabe
                open_download_folder(DOWNLOAD_DIR)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
