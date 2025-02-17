from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os

def get_data_path():
    # Bot dizininden bir üst dizine çık ve Data klasörüne gir
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'Data')
    # Data dizininin varlığını kontrol et
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

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

def test_loan_scenarios():
    options = webdriver.ChromeOptions()
    # Headless mod ve gerekli ayarlar
    options.add_argument('--headless=new')  # Yeni headless modu
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
    wait = WebDriverWait(browser, 10)
    
    all_results = {}
    
    try:
        browser.get("https://www.hangikredi.com/kredi/konut-kredisi")
        time.sleep(2)
        
        for loan_amount in generate_loan_amounts():
            all_results[str(loan_amount)] = {}
            print(f"\nKredi Tutarı: {loan_amount:,} TL")

            for month in get_available_months():
                print(f"\nVade: {month} ay")
                
                set_amount_js = f"""
                    var input = document.getElementById('amount');
                    var setValue = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setValue.call(input, '{loan_amount}');
                    var event = new Event('input', {{ bubbles: true }});
                    input.dispatchEvent(event);
                """
                browser.execute_script(set_amount_js)
                
                vade_select = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="maturity"]'))
                )
                select = Select(vade_select)
                select.select_by_value(str(month))
                
                browser.execute_script("""
                    var button = document.querySelector('button[data-testid="submit"]');
                    button.click();
                """)
                
                time.sleep(3)
                
                bank_cards = browser.find_elements(By.CLASS_NAME, "product-list-card_card_content__IutDY")
                print(f"Bulunan banka sayısı: {len(bank_cards)}")
                
                month_results = []
                
                for card in bank_cards:
                    try:
                        try:
                            bank_name = card.find_element(By.CSS_SELECTOR, "img[data-testid='bank-image']").get_attribute("alt")
                        except:
                            try:
                                bank_name = card.find_element(By.CSS_SELECTOR, "span[data-testid='bank-name']").text
                            except:
                                continue

                        bank_data = {
                            "banka": bank_name,
                            "alt_bilgi": card.find_element(By.CSS_SELECTOR, "[data-testid='content']").text,
                            "oran_turu": card.find_element(By.CSS_SELECTOR, ".product-list-card_info_title__XF_Pm.order-1").text,
                            "faiz_orani": card.find_element(By.CSS_SELECTOR, ".product-list-card_info__Na8Zr.order-2.md\\:order-3").text.replace('%', '').strip()
                        }
                        month_results.append(bank_data)
                        print(f"Banka: {bank_data['banka']}, {bank_data['oran_turu']}: {bank_data['faiz_orani']}")
                        
                    except Exception as e:
                        continue
                
                all_results[str(loan_amount)][f"vade_{month}"] = month_results
                browser.get("https://www.hangikredi.com/kredi/konut-kredisi")
                time.sleep(2)
    
    except Exception as e:
        print(f"Genel hata oluştu: {str(e)}")
    
    finally:
        browser.quit()
        output_file = os.path.join(get_data_path(), 'konut_kredisi_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print(f"\nTüm sonuçlar kaydedildi: {output_file}")

if __name__ == "__main__":
    test_loan_scenarios()
