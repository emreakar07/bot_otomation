from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json

def generate_loan_amounts():
    amounts = [1000, 20000]
    current = 20000
    
    while current <= 400000:
        current += 20000
        if current <= 400000:
            amounts.append(current)
    
    return amounts

def get_available_months(loan_amount):
    if loan_amount >= 300000:
        return [3, 6, 9, 12, 18, 24, 30, 36]
    else:
        return [3, 6, 9, 12, 18, 24, 30, 36, 42, 48]

def get_car_status():
    return ["1", "2"]  # 1: Sıfır Km, 2: İkinci El

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
    
    def try_get_url(url, max_retries=2):
        for _ in range(max_retries):
            try:
                browser.get(url)
                time.sleep(2)  # İhtiyaç kredisi botundaki gibi 2 saniye bekle
                return True
            except:
                print("Sayfa yüklenemedi, tekrar deneniyor...")
                time.sleep(2)
                continue
        return False

    all_results = {}
    first_iteration = True

    try:
        for car_status in get_car_status():
            all_results[f"arac_durumu_{car_status}"] = {}
            print(f"\nAraç Durumu: {'Sıfır' if car_status == '1' else 'İkinci El'}")

            for loan_amount in generate_loan_amounts():
                amount_results = {}
                print(f"\nKredi Tutarı: {loan_amount} TL")

                for month in get_available_months(loan_amount):
                    print(f"\nVade: {month} ay")
                    
                    try:
                        url = f"https://www.hangikredi.com/kredi/tasit-kredisi/sorgulama?amount={loan_amount}&maturity={month}&CarStatus={car_status}"
                        if not try_get_url(url):
                            print("Sayfa yüklenemedi, sonraki kombinasyona geçiliyor...")
                            continue
                        
                        if first_iteration:
                            try:
                                # Pop-up'ı bul ve kapat
                                popup_close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-close-button")))
                                popup_close.click()
                            except:
                                print("Pop-up bulunamadı veya zaten kapalı.")
                            first_iteration = False

                        # Scroll to load all content
                        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)  # Wait for content to load
                        
                        bank_cards = browser.find_elements(By.CLASS_NAME, "product-card__container")
                        print(f"Bulunan banka sayısı: {len(bank_cards)}")
                        
                        month_results = []
                        
                        for card in bank_cards:
                            try:
                                # Scroll element into view before interacting
                                browser.execute_script("arguments[0].scrollIntoView(true);", card)
                                time.sleep(0.5)  # Small delay after scroll
                                
                                bank_data = {
                                    "banka": card.find_element(By.CSS_SELECTOR, "[data-testid='bankImage']").get_attribute("alt"),
                                    "faiz_orani": card.find_element(By.CSS_SELECTOR, "[data-testid='rate']").text.replace('%', '').strip(),
                                    "aylik_taksit": card.find_element(By.CSS_SELECTOR, "[data-testid='monthlyInstallment']").text,
                                    "toplam_odeme": card.find_element(By.CSS_SELECTOR, "[data-testid='totalAmount']").text
                                }
                                month_results.append(bank_data)
                                print(f"Banka: {bank_data['banka']}, Faiz Oranı: {bank_data['faiz_orani']}, "
                                      f"Aylık Taksit: {bank_data['aylik_taksit']}, Toplam Ödeme: {bank_data['toplam_odeme']}")
                                
                            except Exception as e:
                                print(f"Banka verisi alınırken hata: {str(e)}")
                                continue
                        
                        amount_results[f"vade_{month}"] = month_results
                        
                    except Exception as e:
                        print(f"Bu kombinasyon atlanıyor: {str(e)}")
                        time.sleep(2)
                        continue
                
                if amount_results:  # Sadece sonuç varsa kaydet
                    all_results[f"arac_durumu_{car_status}"][str(loan_amount)] = amount_results
    
    except Exception as e:
        print(f"Genel hata oluştu: {str(e)}")
    
    finally:
        browser.quit()
        if all_results:
            with open('Data/tasit_kredisi_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=4)
            print("\nTüm sonuçlar kaydedildi.")

if __name__ == "__main__":
    test_loan_scenarios()