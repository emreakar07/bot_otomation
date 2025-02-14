from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import traceback

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
    browser = None
    all_results = {}
    try:
        options = webdriver.ChromeOptions()
        # Headless mod ve gerekli ayarlar
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-notifications')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        browser = webdriver.Chrome(options=options)
        browser.set_window_size(1920, 1080)
        wait = WebDriverWait(browser, 30)
        
        for car_status in get_car_status():
            all_results[f"arac_durumu_{car_status}"] = {}
            print(f"\nAraç Durumu: {'Sıfır' if car_status == '1' else 'İkinci El'}")

            # Ana sayfaya git ve form doldur
            browser.get("https://www.hangikredi.com/kredi/tasit-kredisi")
            time.sleep(2)

            for loan_amount in generate_loan_amounts():
                amount_results = {}
                print(f"\nKredi Tutarı: {loan_amount} TL")

                for month in get_available_months(loan_amount):
                    print(f"\nVade: {month} ay")
                    
                    try:
                        # Form doldurma
                        set_amount_js = f"""
                            var input = document.getElementById('amount');
                            var setValue = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            setValue.call(input, '{loan_amount}');
                            var event = new Event('input', {{ bubbles: true }});
                            input.dispatchEvent(event);
                        """
                        browser.execute_script(set_amount_js)
                        
                        # Vade seçimi
                        vade_select = wait.until(
                            EC.presence_of_element_located((By.ID, "maturity"))
                        )
                        select = Select(vade_select)
                        select.select_by_value(str(month))
                        
                        # Araç durumu seçimi
                        car_status_select = wait.until(
                            EC.presence_of_element_located((By.ID, "CarStatus"))
                        )
                        select = Select(car_status_select)
                        select.select_by_value(car_status)
                        
                        # Hesapla butonuna tıkla
                        browser.execute_script("""
                            var button = document.querySelector('button[data-testid="submit"]');
                            button.click();
                        """)
                        
                        time.sleep(3)
                        
                        # Banka kartlarının yüklenmesini bekle
                        bank_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card__container")))
                        print(f"Bulunan banka sayısı: {len(bank_cards)}")
                        
                        month_results = []
                        
                        for card in bank_cards:
                            try:
                                bank_data = {
                                    "banka": card.find_element(By.CSS_SELECTOR, ".product-list-card_bank_name__6epoY[data-testid='bank-name']").text,
                                    "faiz_orani": card.find_element(By.CSS_SELECTOR, ".product-list-card_info__Na8Zr").text.replace('%', '').strip(),
                                    "aylik_taksit": card.find_element(By.CSS_SELECTOR, ".product-list-card_info__Na8Zr.product-list-card_info__emphatic__hrdln").text,
                                    "toplam_odeme": card.find_element(By.CSS_SELECTOR, ".product-list-card_info__Na8Zr[data-testid='totalAmount']").text
                                }
                                month_results.append(bank_data)
                                print(f"Banka: {bank_data['banka']}, Faiz Oranı: {bank_data['faiz_orani']}, "
                                      f"Aylık Taksit: {bank_data['aylik_taksit']}, Toplam Ödeme: {bank_data['toplam_odeme']}")
                                
                            except Exception as e:
                                print(f"Banka verisi alınırken hata: {str(e)}")
                                continue
                        
                        if month_results:  # Sadece sonuç varsa kaydet
                            amount_results[f"vade_{month}"] = month_results
                            
                        # Ana sayfaya geri dön
                        browser.get("https://www.hangikredi.com/kredi/tasit-kredisi")
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Bu kombinasyon atlanıyor: {str(e)}")
                        browser.get("https://www.hangikredi.com/kredi/tasit-kredisi")
                        time.sleep(2)
                        continue
                
                if amount_results:  # Sadece sonuç varsa kaydet
                    all_results[f"arac_durumu_{car_status}"][str(loan_amount)] = amount_results
    
    except Exception as e:
        print(f"Genel hata oluştu: {str(e)}")
        print("Hata detayı:")
        print(traceback.format_exc())
    finally:
        if browser:
            try:
                browser.quit()
            except:
                print("Browser kapatılırken hata oluştu")
        
        # Her durumda kaydet
        try:
            with open('../Data/tasit_kredisi_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=4)
            print("\nMevcut sonuçlar kaydedildi.")
        except Exception as e:
            print(f"Sonuçlar kaydedilirken hata oluştu: {str(e)}")
            print("Kaydetme hatası detayı:")
            print(traceback.format_exc())

if __name__ == "__main__":
    try:
        test_loan_scenarios()
    except Exception as e:
        print(f"Program çalışırken hata oluştu: {str(e)}")
        print("Ana program hatası detayı:")
        print(traceback.format_exc())
        # Hata olsa bile 0 döndür ki GitHub Actions devam etsin
        exit(0)