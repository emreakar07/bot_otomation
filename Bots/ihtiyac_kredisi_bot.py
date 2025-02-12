from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def generate_loan_amounts():
    amounts = [1000]
    
    current = 25000
    while current <= 100000:
        amounts.append(current)
        current += 25000
    
    current = 150000
    while current <= 500000:
        amounts.append(current)
        current += 50000
    
    current = 600000
    while current <= 2000000:
        amounts.append(current)
        current += 100000
    
    current = 2250000
    while current <= 5000000:
        amounts.append(current)
        current += 250000
    
    current = 5500000
    while current <= 10000000:
        amounts.append(current)
        current += 500000
    
    return amounts

def get_available_months():
    return list(range(12, 181, 12))

def get_vade_periods(amount):
    if amount <= 50000:
        return [3, 6, 9, 12, 18, 24, 30, 36]
    elif amount <= 100000:
        return [3, 6, 9, 12, 18, 24]
    else:
        return [3, 6, 9, 12]

def test_loan_scenarios():
    options = webdriver.ChromeOptions()
    # Headless mod ayarları
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # Diğer ayarlar
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-notifications')
    options.add_argument('--window-size=1920,1080')
    
    browser = webdriver.Chrome(options=options)
    browser.set_window_size(1920, 1080)
    wait = WebDriverWait(browser, 10)
    
    all_results = {}
    loan_amounts = [
        10000, 20000, 30000, 40000, 50000,
        60000, 70000, 80000, 90000, 100000,
        150000, 200000, 250000, 300000, 400000, 500000,
        600000, 700000, 800000, 900000, 999999
    ]
    
    first_iteration = True
    
    try:
        for amount in loan_amounts:
            amount_results = {}
            vade_periods = get_vade_periods(amount)
            
            for vade in vade_periods:
                base_url = f"https://www.hangikredi.com/kredi/ihtiyac-kredisi/sorgulama/{vade}-ay-{amount}-tl-kredi"
                browser.get(base_url)
                time.sleep(2)
                
                if first_iteration:
                    try:
                        # Try to find and close the popup
                        popup_close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-close-button")))
                        popup_close.click()
                    except:
                        print("Pop-up bulunamadı veya zaten kapalı.")
                    first_iteration = False

                print(f"\nTutar: {amount} TL, Vade: {vade} ay")
                
                # Scroll to load all content
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Wait for content to load
                
                bank_cards = browser.find_elements(By.CLASS_NAME, "product-card__container")
                print(f"Bulunan banka sayısı: {len(bank_cards)}")
                
                vade_results = []
                
                for card in bank_cards:
                    try:
                        # Scroll element into view before interacting
                        browser.execute_script("arguments[0].scrollIntoView(true);", card)
                        time.sleep(0.5)  # Small delay after scroll
                        
                        bank_name = card.find_element(By.CSS_SELECTOR, "img[data-testid='bankImage']").get_attribute("alt")
                        faiz_orani = card.find_element(By.CSS_SELECTOR, "[data-testid='rate']").text.replace('%', '')
                        aylik_taksit = card.find_element(By.CSS_SELECTOR, "[data-testid='monthlyInstallment']").text
                        toplam_odeme = card.find_element(By.CSS_SELECTOR, "[data-testid='totalAmount']").text

                        bank_data = {
                            "banka": bank_name,
                            "faiz_orani": faiz_orani,
                            "aylik_taksit": aylik_taksit,
                            "toplam_odeme": toplam_odeme
                        }
                        vade_results.append(bank_data)
                        print(f"Banka: {bank_data['banka']}, Faiz Oranı: {bank_data['faiz_orani']}, "
                              f"Aylık Taksit: {bank_data['aylik_taksit']}, Toplam Ödeme: {bank_data['toplam_odeme']}")
                        
                    except Exception as e:
                        print(f"Banka verisi alınırken hata: {str(e)}")
                        continue
                
                amount_results[f"vade_{vade}"] = vade_results
            
            all_results[f"amount_{amount}"] = amount_results
    
    except Exception as e:
        print(f"Genel hata oluştu: {str(e)}")
    
    finally:
        browser.quit()
        with open('Data/ihtiyac_kredisi_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print("\nTüm sonuçlar kaydedildi.")

if __name__ == "__main__":
    test_loan_scenarios()