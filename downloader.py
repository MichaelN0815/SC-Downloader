#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scalable Capital PDF Downloader
Scroll-Funktion für große Transactions Zahl
Ordner aufrufen
Inline Kommentare
"""

__version__ = "2.05"

import os
import sys
import time
import configparser
import re
# NEU V2.04b
import platform
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, unquote


# --- 1. STANDARDEINSTELLUNGEN ---
TARGET_URL = "https://de.scalable.capital/broker/transactions"
TARGET_URL2 = "https://de.scalable.capital/cockpit/mailbox"
DOWNLOAD_DIR = None  # NEU V2.04b Global

DEFAULT_CONFIG = {
    'max_transactions': '20',
    'max_documents': '20',
    'download_directory': 'Scalable_Downloads',
    'use_original_filename': 'False',
    'stop_at_first_duplicate': 'False',
    'logout_after_run': 'True',
    'get_documents': 'True',
    'only_new_docs': 'True',
    'slow_mo': '100',
    'transaction_types': 'Ausschüttung, Kauf, Verkauf, Sparplan, Steuern',
    'pdf_button_names': 'Wertpapierabrechnung, Wertpapierereignisse',
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

def load_config():
    # NEU V2.05: Inline Kommentare in INI erlaubt
    config = configparser.ConfigParser(
        inline_comment_prefixes=('#', ';'),
        comment_prefixes=('#', ';')
    )
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding='utf-8')
        print(f"[v{__version__}] Konfiguration geladen: {CONFIG_PATH}")
    else:
        config['General'] = {
            'max_transactions': DEFAULT_CONFIG['max_transactions'],
            'max_documents': DEFAULT_CONFIG['max_documents'],
            'download_directory': DEFAULT_CONFIG['download_directory'],
            'use_original_filename': DEFAULT_CONFIG['use_original_filename'],
            'stop_at_first_duplicate': DEFAULT_CONFIG['stop_at_first_duplicate'],
            'logout_after_run': DEFAULT_CONFIG['logout_after_run'],
            'get_documents': DEFAULT_CONFIG['get_documents'],
            'only_new_docs': DEFAULT_CONFIG['only_new_docs']
        }
        config['Keywords'] = {'transaction_types': DEFAULT_CONFIG['transaction_types']}
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
        # ========== NEU V2.02: WKN-Beispiele ==========
        config['WKN'] = {
            '# Beispiel-Zuordnungen ISIN = WKN': '',
            '# LU2572257124': 'ETF018',
            '# LU0496786657': 'LYX0FZ'
        }
        # ========== ENDE: WKN-Beispiele ==========
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
            text = item.inner_text().replace("\n", " ").strip()
            for key in keywords:
                if key in text:
                    found.append((idx, text, key))
                    break
        except Exception as e:
            print(f"  ⚠ Element {idx} konnte nicht gelesen werden: {e}")
            continue
    return found

def handle_popups(page):
    """Schließt häufige Popup-Dialoge"""
    try:
        texts = ["Akzeptieren", "Alle akzeptieren", "Zustimmen", "Verstanden", "Schließen", "Später", "Zum Broker"]
        for text in texts:
            try:
                btn = page.get_by_role("button", name=text, exact=False).first
                if btn.is_visible():
                    btn.click()
                    print(f"  ✓ Popup geschlossen: '{text}'")
                    time.sleep(0.5)
            except Exception as e:
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

def run_downloader():
    global DOWNLOAD_DIR # NEU V2.04b
    settings = load_config()
    KEYWORDS = settings['keywords']
    PDF_BUTTON_NAMES = settings['pdf_button_names']
    WKN_MAPPING = settings['wkn_mapping']  # ========== NEU V2.02 ==========
    
    DOWNLOAD_DIR = settings['download_dir'] if os.path.isabs(settings['download_dir']) else os.path.join(BASE_DIR, settings['download_dir'])
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
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
        time.sleep(2)
        handle_popups(page)

        if "login" in page.url:
            print("Warte auf manuellen Login (2FA)...")
            try:
                page.wait_for_url(re.compile(r".*/(cockpit|transactions|dashboard|broker)/.*"), timeout=0)
                print("  ✓ Login erkannt.")
            except Exception as e:
                print(f"  ⚠ Login-Warnung: {e}")
            
            handle_popups(page)
            
            if TARGET_URL not in page.url:
                print("  -> Navigiere zu Transaktionen...")
                try:
                    page.goto(TARGET_URL)
                    handle_popups(page)
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
        for target_idx, (idx, full_text, keyword) in enumerate(targets):
            file_name = "unknown_transaction.pdf" 
            try:
                print(f"\n[{target_idx+1}/{len(targets)}] {full_text[:50]}...")
                
                try:
                    current_items = page.locator("div[role='button'], button").all()
                    clicked = False
                    for item in current_items:
                        try:
                            if item.inner_text().replace("\n", " ").strip() == full_text:
                                item.get_by_text(keyword, exact=False).first.click(timeout=settings['click_transaction_timeout'])
                                clicked = True
                                print(f"  ✓ Transaktion geöffnet")
                                break
                        except Exception as e:
                            continue
                    
                    if not clicked:
                        print(f"  ✗ Transaktion nicht gefunden, überspringe")
                        save_error_screenshot(page, DOWNLOAD_DIR, full_text, "missing_transaction")
                        continue
                except Exception as e:
                    print(f"  ✗ Klick fehlgeschlagen: {e}")
                    save_error_screenshot(page, DOWNLOAD_DIR, full_text, "missing_transaction")
                    continue
                
                time.sleep(settings['transaction_wait'])
                
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

                pdf_url = None

                try:
                    print(f"  -> Öffne PDF-Tab...")
                    with context.expect_page(timeout=settings['pdf_tab_timeout']) as new_page_info:
                        pdf_btn.click()
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
                
                url_without_params = pdf_url.split("?")[0] if pdf_url else ""
                match = re.search(r'(\d{4}-\d{2}-\d{2})-.+?-([A-Z]{2}[A-Z0-9]{10})', url_without_params)
                date_str = match.group(1) if match else datetime.now().strftime("%Y-%m-%d")
                isin_str = match.group(2) if match else "UNKNOWN"
                
                if not match:
                    print(f"  ⚠ Konnte Datum/ISIN nicht aus URL parsen: {url_without_params}")

                wp_name = re.sub(r'\(.*?\)', '', full_text)
                betrag_m = re.findall(r'(-?\d+[\.,]\d{2})', full_text)
                betrag = betrag_m[-1].replace(",", "-").replace(".", "-") if betrag_m else "0-00"
                pattern2 = r'-?\d+[\.,]\d{2}.*$'
                wp_name = re.sub(pattern2, '', wp_name).strip()
                if wp_name.startswith(keyword): 
                    wp_name = wp_name[len(keyword):].strip()
                wp_name_clean = "_".join(wp_name.replace("€", "").replace(",", "-").replace(":", "").replace("/", "-").split())
                
                # ========== NEU V2.02 GEÄNDERT: identifier_str statt isin_str ==========
                identifier_str = convert_isin_to_wkn(isin_str, WKN_MAPPING)
                final_file_name = f"{date_str}-{keyword[:4]}-{identifier_str}-{wp_name_clean}-{betrag}.pdf"
                # optional: Original-Dateiname vom Server ermitteln
                if settings['use_original_filename']:
                    final_file_name = filename_from_url(url_without_params) or final_file_name

                # Zielpfad festlegen
                target_path = os.path.join(DOWNLOAD_DIR, final_file_name)

                # Duplikatsprüfung vor Download
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

                # erst jetzt PDF herunterladen
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
                
                # Alle Zeilen mit der spezifischen Hintergrundfarbe finden
                try:
                    if not settings['only_new_docs']:
                        # Finde alle Zeilen mit Download-Symbol, egal welche Farbe
                        print(f"  Finde ALLE Zeilen mit Download-Symbol")
                        # Finde das äußere Container-Element jeder Zeile mit Download
                        all_rows = page.locator('[data-mailbox-item-subject]').filter(has=page.locator('[data-testid="mailbox-download"]')).all()
                        print(f"[v{__version__}] {len(all_rows)} Dokument(e) gefunden.")
                    else:
                        # PRODUKTIV-MODUS: Nur Zeilen mit spezifischer Farbe
                        # Finde das äußere Presentation-Div und prüfe auf Farbe
                        all_presentation_divs = page.locator('div[role="presentation"][style*="background-color"]').all()
                        all_rows = []
                        for div in all_presentation_divs:
                            try:
                                style = div.get_attribute('style')
                                if style and ('#28EBCF' in style or 'rgb(40, 235, 207)' in style):
                                    # Prüfe ob diese Zeile ein Download-Symbol hat
                                    if div.locator('[data-testid="mailbox-download"]').count() > 0:
                                        all_rows.append(div)
                            except Exception:
                                continue
                        print(f"[v{__version__}] {len(all_rows)} Dokument(e) mit Neu-Kennzeichnung gefunden.")
                except Exception as e:
                    print(f"  ✗ Fehler beim Laden der Dokumentenliste: {e}")
                    all_rows = []
                
                # Begrenze auf max_documents
                rows_to_process = all_rows[:settings['max_documents']]
                
                for doc_idx, row in enumerate(rows_to_process):
                    try:
                        print(f"\n[Dokument {doc_idx+1}/{len(rows_to_process)}]")
                        
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
                        
                        # Duplikatsprüfung vor Download
                        if os.path.exists(target_path):
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
                        print(f"  ✗ FEHLER bei Dokument {doc_idx+1}: {e}")
                        continue
                
                print(f"\n[v{__version__}] Dokumente-Download abgeschlossen.")
                
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
        import msvcrt
        print("Warte auf Tastendruck...")
        key = msvcrt.getch()
        if key in [b'\r', b'\n']:  # ENTER
            open_download_folder(DOWNLOAD_DIR)
    else:
        # Unix/Linux/macOS
        import sys
        import tty
        import termios
        
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
            
