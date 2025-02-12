from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
import time
import json
import signal
import sys
from datetime import datetime

# Global variables
results = {}
is_running = True

def signal_handler(signum, frame):
    global is_running
    print("\nCtrl+C algılandı. Mevcut verileri kaydediyorum...")
    is_running = False

signal.signal(signal.SIGINT, signal_handler)

def generate_amounts(currency_type):
    amounts = []
    
    if currency_type == 'TL':
        # 500'den 10K'ya kadar
        amounts.extend([500])  # Başlangıç
        amounts.extend(range(1000, 5001, 500))  # 1000'den 5000'e 500'er artış
        amounts.extend(range(5000, 10001, 1000))  # 5000'den 10000'e 1000'er artış
        
        # 10K - 50K arası (daha hassas)
        amounts.extend(range(10000, 50001, 5000))
        
        # 50K - 100K arası
        amounts.extend(range(50000, 100001, 10000))
        
        # 100K - 500K arası
        amounts.extend(range(100000, 500001, 50000))
        
        # 500K - 1M arası
        amounts.extend(range(500000, 1000001, 100000))
        
        # 1M - 10M arası
        amounts.extend(range(1000000, 10000001, 1000000))
        
        # 10M - 30M arası
        amounts.extend(range(10000000, 30000001, 10000000))

        # 10M - 100M arası
        #amounts.extend(range(10000000, 100000001, 10000000))
        
        # 100M - 1B arası
        #amounts.extend(range(100000000, 1000000001, 100000000))
        
        # 1B - 5B arası
        #amounts.extend(range(1000000000, 5000000001, 500000000))
        
        # 5B - 10B arası
        #amounts.extend(range(5000000000, 10000000001, 1000000000))
        
    else:  # USD ve EUR için
        # Başlangıç hassas artışlar
        amounts.extend([200])
        amounts.extend(range(500, 2501, 250))  # 500'den 2500'e 250'şer artış
        amounts.extend(range(2500, 5001, 500))  # 2500'den 5000'e 500'er artış
        amounts.extend(range(5000, 10001, 1000))  # 5000'den 10000'e 1000'er artış
        
        # 10K - 50K arası
        amounts.extend(range(10000, 50001, 5000))
        
        # 50K - 100K arası
        amounts.extend(range(50000, 100001, 10000))
        
        # 100K - 500K arası
        amounts.extend(range(100000, 500001, 50000))
        
        # 500K - 1M arası
        amounts.extend(range(500000, 1000001, 100000))
        
        # 1M - 2.5M arası
        amounts.extend(range(1000000, 2500001, 250000))

        # 1M - 10M arası
        #amounts.extend(range(1000000, 10000001, 1000000))
        
        # 10M - 100M arası
        #amounts.extend(range(10000000, 100000001, 10000000))
        
        # 100M - 1B arası
        #amounts.extend(range(100000000, 1000000001, 100000000))
        
        # 1B - 5B arası
        #amounts.extend(range(1000000000, 5000000001, 500000000))
        
        # 5B - 10B arası
        #amounts.extend(range(5000000000, 10000000001, 1000000000))
    
    return amounts

def generate_tl_amounts():
    return generate_amounts('TL')

def generate_foreign_amounts():
    return generate_amounts('FOREIGN')

def get_available_days():
    return [32, 39, 46, 55, 60, 67, 74, 81, 88, 92, 105, 120, 135, 150, 165, 181, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720, 750, 780, 810, 840, 870, 900, 930, 960, 999]

def setup_driver():
    options = webdriver.ChromeOptions()
    # Temel ayarlar
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # SSL hatalarını gidermek için
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--ignore-certificate-errors-spki-list')
    
    # Hata mesajlarını azaltmak için
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    
    # Performans için
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    
    browser = webdriver.Chrome(options=options)
    return browser

def scrape_bank_data(browser):
    try:
        wait = WebDriverWait(browser, 30)
        banka_kartlari = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.relative.rounded-lg.border.border-gray-300.bg-white"))
        )
        
        sonuclar = []
        for kart in banka_kartlari:
            try:
                info_section = kart.find_element(By.CSS_SELECTOR, "div.relative.flex.flex-col.items-start")
                banka_section = info_section.find_element(By.CSS_SELECTOR, "div.flex.w-full.items-center")
                
                try:
                    banka_adi = banka_section.find_element(By.CSS_SELECTOR, "img[src*='bank']").get_attribute("alt")
                    hesap_div = banka_section.find_element(By.CSS_SELECTOR, "div.border-gray-300.md\\:border-r")
                    hesap_turu = hesap_div.find_element(By.CSS_SELECTOR, "p:first-child").text
                    hesap_aciklama = hesap_div.find_element(By.CSS_SELECTOR, "p:last-child").text
                    
                    bilgi_section = info_section.find_element(By.CSS_SELECTOR, "div.flex.w-full.grow.flex-wrap")
                    faiz = bilgi_section.find_element(By.CSS_SELECTOR, "div.text-left.font-semibold p:first-child").text

                except:
                    try:
                        banka_adi = banka_section.find_element(By.CSS_SELECTOR, "img[data-nimg]").get_attribute("alt")
                        hesap_div = banka_section.find_element(By.CSS_SELECTOR, "div div")
                        hesap_bilgileri = hesap_div.find_elements(By.TAG_NAME, "p")
                        hesap_turu = " ".join([p.text for p in hesap_bilgileri])
                        hesap_aciklama = ""
                        
                        bilgi_section = info_section.find_element(By.CSS_SELECTOR, "div.flex.w-full.grow.flex-wrap")
                        faiz = bilgi_section.find_element(By.CSS_SELECTOR, "div:first-child").text
                    except:
                        continue

                veri = {
                    "banka_adi": banka_adi,
                    "hesap_turu": hesap_turu,
                    "hesap_aciklama": hesap_aciklama,
                    "faiz_orani": faiz
                }
                sonuclar.append(veri)
            except Exception as e:
                continue
                
        return sonuclar
    except Exception as e:
        return []

def scrape_single_combination(params):
    if not is_running:
        return None
        
    currency, amount, day = params
    max_retries = 3  # Add retry limit
    retry_count = 0
    
    while retry_count < max_retries:
        browser = None
        try:
            browser = setup_driver()
            currency_val = {"TL": "1", "USD": "2", "EUR": "3"}[currency]
            result_url = (
                f"https://www.hangikredi.com/yatirim-araclari/mevduat-faiz-oranlari/hesaplama?"
                f"amount={amount}&"
                f"currencyType={currency_val}&"
                f"maturity={day}&"
                f"maturityType=1&"
                f"isCurrencyProtected=False"
            )
            
            browser.get(result_url)
            
            wait = WebDriverWait(browser, 30)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.relative.rounded-lg")))
            
            bank_results = scrape_bank_data(browser)
            browser.quit()
            return {
                'currency': currency,
                'amount': amount,
                'day': day,
                'results': bank_results
            }
        except Exception as e:
            retry_count += 1
            print(f"Hata oluştu: {currency}-{amount}-{day}. Deneme {retry_count}/{max_retries}")
            print(f"Hata detayı: {str(e)}")
            
            if browser:
                try:
                    browser.quit()
                except:
                    pass
                    
            if retry_count >= max_retries:
                print(f"Maksimum deneme sayısına ulaşıldı: {currency}-{amount}-{day}")
                return {
                    'currency': currency,
                    'amount': amount,
                    'day': day,
                    'results': []  # Return empty results after max retries
                }
                
            time.sleep(2)  # Add delay between retries

def scrape_deposit_rates_parallel(max_workers=5):
    global results
    currencies = ['TL', 'USD', 'EUR']
    all_combinations = []
    results = {currency: {} for currency in currencies}
    
    for currency in currencies:
        amounts = generate_tl_amounts() if currency == 'TL' else generate_foreign_amounts()
        for amount in amounts:
            for day in get_available_days():
                all_combinations.append((currency, amount, day))

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_params = {executor.submit(scrape_single_combination, params): params for params in all_combinations}
            
            for future in future_to_params:
                if not is_running:
                    executor.shutdown(wait=False)
                    break
                    
                try:
                    result = future.result()
                    if result:
                        currency = result['currency']
                        amount = result['amount']
                        day = result['day']
                        
                        if str(amount) not in results[currency]:
                            results[currency][str(amount)] = {}
                        
                        results[currency][str(amount)][f"vade_{day}"] = result['results']
                        print(f"Tamamlandı: {currency}-{amount}-{day}")
                except Exception as e:
                    print(f"İşlem hatası: {str(e)}")
    
    except Exception as e:
        print(f"Genel hata: {str(e)}")
    
    finally:
        save_results()

def save_results():
    try:
        with open('Data/mevduat.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("\nVeriler kaydedildi: mevduat.json")
    except Exception as e:
        print(f"\nDosya kaydedilirken hata oluştu: {str(e)}")

if __name__ == "__main__":
    try:
        scrape_deposit_rates_parallel(max_workers=5)
    except KeyboardInterrupt:
        print("\nProgram sonlandırılıyor...")
    finally:
        save_results()