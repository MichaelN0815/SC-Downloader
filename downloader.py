#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scalable Capital PDF Downloader
Version: 0.87
Feature: Nummerierte Error-Screenshots im Download-Verzeichnis
"""

__version__ = "0.87"

import os
import sys
import time
import configparser
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- 1. STANDARDEINSTELLUNGEN ---
DEFAULT_CONFIG = {
    'max_transactions': '20',
    'download_directory': 'Scalable_Downloads',
    'use_original_filename': 'False',
    'stop_at_first_duplicate': 'False',
    'logout_after_run': 'True',
    'transaction_types': 'Ausschüttung, Kauf, Verkauf, Sparplan',
    'page_load_wait': '1000',
    'transaction_wait': '50',
    'critical_wait': '50',
    'pdf_button_timeout': '100'
}

# --- 2. PFAD-LOGIK ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(sys._MEIPASS, "ms-playwright")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    except Exception:
        print("  ✗ FEHLER: Browser nicht gefunden.")
        input("\nDrücke Enter zum Beenden...")
        sys.exit(1)

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding='utf-8')
    else:
        config['General'] = {
            'max_transactions': DEFAULT_CONFIG['max_transactions'],
            'download_directory': DEFAULT_CONFIG['download_directory'],
            'use_original_filename': DEFAULT_CONFIG['use_original_filename'],
            'stop_at_first_duplicate': DEFAULT_CONFIG['stop_at_first_duplicate'],
            'logout_after_run': DEFAULT_CONFIG['logout_after_run']
        }
        config['Keywords'] = {'transaction_types': DEFAULT_CONFIG['transaction_types']}
        config['Timeouts'] = {
            'page_load_wait': DEFAULT_CONFIG['page_load_wait'],
            'transaction_wait': DEFAULT_CONFIG['transaction_wait'],
            'critical_wait': DEFAULT_CONFIG['critical_wait'],
            'pdf_button_timeout': DEFAULT_CONFIG['pdf_button_timeout']
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            config.write(f)
    
    return {
        'max_transactions': config.getint('General', 'max_transactions', fallback=int(DEFAULT_CONFIG['max_transactions'])),
        'download_dir': config.get('General', 'download_directory', fallback=DEFAULT_CONFIG['download_directory']),
        'use_original_filename': config.getboolean('General', 'use_original_filename', fallback=False),
        'stop_at_first_duplicate': config.getboolean('General', 'stop_at_first_duplicate', fallback=False),
        'logout_at_end': config.getboolean('General', 'logout_after_run', fallback=True),
        'keywords': [k.strip() for k in config.get('Keywords', 'transaction_types', fallback='').split(',')],
        'page_load_wait': config.getint('Timeouts', 'page_load_wait', fallback=100) / 1000,
        'transaction_wait': config.getint('Timeouts', 'transaction_wait', fallback=50) / 1000,
        'critical_wait': config.getint('Timeouts', 'critical_wait', fallback=50) / 1000,
        'pdf_button_timeout': config.getint('Timeouts', 'pdf_button_timeout', fallback=100)
    }

def handle_popups(page):
    try:
        texts = ["Akzeptieren", "Alle akzeptieren", "Zustimmen", "Verstanden", "Schließen", "Später", "Zum Broker"]
        for text in texts:
            btn = page.get_by_role("button", name=text, exact=False).first
            if btn.is_visible():
                btn.click()
                time.sleep(0.5)
    except: pass

def run_downloader():
    settings = load_config()
    KEYWORDS = settings['keywords']
    TARGET_URL = "https://de.scalable.capital/broker/transactions"
    
    DOWNLOAD_DIR = settings['download_dir'] if os.path.isabs(settings['download_dir']) else os.path.join(BASE_DIR, settings['download_dir'])
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Zielordner: {DOWNLOAD_DIR}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            SESSION_DIR, headless=False, slow_mo=1000, accept_downloads=True
        )
        page = context.new_page()
        page.goto(TARGET_URL)
        
        time.sleep(2)
        handle_popups(page)

        if "login" in page.url:
            print("Warte auf manuellen Login (2FA)...")
            page.wait_for_url(re.compile(r".*/(cockpit|transactions|dashboard|broker)/.*"), timeout=0)
            print("  ✓ Login erkannt.")
            
            time.sleep(2)
            handle_popups(page)
            
            if TARGET_URL not in page.url:
                print("  -> Navigiere automatisch zu den Transaktionen...")
                page.goto(TARGET_URL)
                time.sleep(2)
                handle_popups(page)
        
        page.wait_for_load_state("networkidle")
        time.sleep(settings['page_load_wait'])

        # --- Filter ---
        try:
            filter_button = page.get_by_text("Auftragstyp").first
            filter_button.click(timeout=3000)
            dropdown = page.locator("[role='listbox'], [role='menu'], div[class*='dropdown'][class*='menu']").first
            for keyword in KEYWORDS:
                try:
                    dropdown.get_by_text(keyword, exact=False).first.click(timeout=1000, no_wait_after=True)
                except: pass
            page.keyboard.press("Escape")
        except: pass

        time.sleep(settings['critical_wait'])
        all_items = page.locator("div[role='button'], button").all()
        targets = []
        for idx, item in enumerate(all_items):
            if len(targets) >= settings['max_transactions']: break
            try:
                if not item.is_visible(): continue
                text = item.inner_text().replace("\n", " ").strip()
                for key in KEYWORDS:
                    if key in text:
                        targets.append((idx, text, key))
                        break
            except: continue

        print(f"Suche beendet. {len(targets)} relevante Dokumente gefunden.")
        
        # --- Download Schleife ---
        downloaded = skipped = 0
        for target_idx, (idx, full_text, keyword) in enumerate(targets):
            file_name = "unknown_transaction.pdf" 
            try:
                print(f"[{target_idx+1}/{len(targets)}] {full_text[:50]}...")
                current_items = page.locator("div[role='button'], button").all()
                for item in current_items:
                    if item.inner_text().replace("\n", " ").strip() == full_text:
                        item.get_by_text(keyword, exact=False).first.click(timeout=5000)
                        break
                
                time.sleep(settings['transaction_wait'])
                
                pdf_btn = None
                for btn_text in ["Wertpapierabrechnung", "Wertpapierereignisse"]:
                    try:
                        pdf_btn = page.get_by_text(btn_text).first
                        pdf_btn.wait_for(state="visible", timeout=settings['pdf_button_timeout'])
                        break
                    except: continue
                
                if not pdf_btn: 
                    page.keyboard.press("Escape")
                    continue

                pdf_url = pdf_btn.get_attribute("href")
                if not pdf_url:
                    with context.expect_page(timeout=15000) as new_page_info:
                        pdf_btn.click()
                    new_tab = new_page_info.value
                    pdf_url = new_tab.url
                    new_tab.close()
                
                # Namenslogik
                match = re.search(r'(\d{4}-\d{2}-\d{2})-.+?-([A-Z]{2}[A-Z0-9]{10})', pdf_url or "")
                date_str = match.group(1) if match else datetime.now().strftime("%Y-%m-%d")
                isin_str = match.group(2) if match else "UNKNOWN"

                wp_name = re.sub(r'\(.*?\)', '', full_text)
                betrag_m = re.findall(r'(-?\d+[\.,]\d{2})', full_text)
                betrag = betrag_m[-1].replace(",", "-").replace(".", "-") if betrag_m else "0-00"
                wp_name = re.sub(r'-?\d+[\.,]\d{2}.*$', '', wp_name).strip()
                if wp_name.startswith(keyword): wp_name = wp_name[len(keyword):].strip()
                wp_name = "_".join(wp_name.replace("€", "").replace(",", "-").replace(":", "").replace("/", "-").split())
                
                file_name = f"{date_str}-{keyword[:4]}-{isin_str}-{wp_name}-{betrag}.pdf"
                target_path = os.path.join(DOWNLOAD_DIR, file_name)
                
                if os.path.exists(target_path):
                    print(f"  -> ✓ Bereits vorhanden: {file_name}")
                    skipped += 1
                    if settings['stop_at_first_duplicate']:
                        print(f"  -> [STOP] Breche ab (Duplikat gefunden).")
                        page.keyboard.press("Escape")
                        break
                else:
                    response = page.request.get(pdf_url)
                    if response.status == 200:
                        with open(target_path, "wb") as f: f.write(response.body())
                        print(f"  -> ✓ Gespeichert: {file_name}")
                        downloaded += 1
                
                page.keyboard.press("Escape")
                time.sleep(0.1)
            except Exception as e: 
                # NEU: Fehler-Screenshot mit Nummerierung im Download-Verzeichnis
                error_count = 1
                base_error_name = file_name.replace('.pdf', '.png')
                
                # Prüfe auf freie Nummer
                while os.path.exists(os.path.join(DOWNLOAD_DIR, f"error_{error_count}_{base_error_name}")):
                    error_count += 1
                
                error_file_name = f"error_{error_count}_{base_error_name}"
                error_path = os.path.join(DOWNLOAD_DIR, error_file_name)
                
                try:
                    page.screenshot(path=error_path)
                    print(f"  ✗ FEHLER. Screenshot gespeichert: {error_file_name}")
                except:
                    print(f"  ✗ FEHLER. Screenshot fehlgeschlagen: {e}")
                
                try: page.keyboard.press("Escape")
                except: pass

        if settings['logout_at_end']:
            try:
                page.get_by_text("Abmelden").first.click(timeout=3000)
                print("Abgemeldet.")
            except: pass
        context.close()
        print(f"\nFERTIG. Neu geladen: {downloaded}, Übersprungen: {skipped}")

if __name__ == "__main__":
    ensure_browser()
    run_downloader()
    input("\nProgramm beendet. Drücke Enter zum Schließen...")
