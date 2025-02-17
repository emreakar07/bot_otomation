from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
    amounts = []
    
    # 1.000 TL'den 10.000 TL'ye kadar 1.000'er artış
    current = 1000
    while current <= 10000:
        amounts.append(current)
        current += 1000
    
    # 10.000 TL'den 100.000 TL'ye kadar 10.000'er artış
    current = 20000
    while current <= 100000:
        amounts.append(current)
        current += 10000
    
    # 100.000 TL'den 1.000.000 TL'ye kadar 50.000'er artış
    current = 150000
    while current <= 1000000:
        amounts.append(current)
        current += 25000
    
    # 1.000.000 TL'den 9.999.999 TL'ye kadar 500.000'er artış
    current = 1500000
    while current <= 9999999:
        amounts.append(current)
        current += 250000
    
    print(f"Oluşturulan tutar listesi: {amounts}")  # Debug için
    return amounts

def get_available_months():
    return list(range(12, 181, 12))

def get_vade_periods(amount):
    return [3, 6, 9, 12, 18, 24, 30, 36, 48, 60]

def test_loan_scenarios():
    options = Options()
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
    
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    browser.set_window_size(1920, 1080)
    wait = WebDriverWait(browser, 10)
    
    all_results = {}
    
    try:
        loan_amounts = generate_loan_amounts()
        
        for amount in loan_amounts:
            all_results[str(amount)] = {}
            print(f"\nKredi Tutarı: {amount:,} TL")
            
            vade_periods = get_vade_periods(amount)
            
            for vade in vade_periods:
                month_results = []
                print(f"Vade: {vade} ay")
                
                url = f"https://www.hangikredikobi.com/ticari-kredi/sorgulama?amount={amount}&maturity={vade}"
                print(f"URL: {url}")
                
                browser.get(url)
                time.sleep(0.2)
                
                try:
                    bank_rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='product']")))
                    print(f"Bulunan banka sayısı: {len(bank_rows)}")
                    
                    for row in bank_rows:
                        try:
                            browser.execute_script("arguments[0].scrollIntoView(true);", row)
                            time.sleep(0.2)
                            
                            # Debug için element varlığını kontrol et
                            print("Element bulma başlıyor...")
                            
                            bank_element = row.find_element(By.CSS_SELECTOR, "a[href*='/ticari-kredi/']")
                            bank_name = bank_element.find_element(By.CSS_SELECTOR, "img").get_attribute("alt")
                            print(f"Bulunan banka adı: {bank_name}")
                            
                            bank_data = {
                                "banka": bank_element.get_attribute("href"),  # Banka URL'sini al
                                "kredi_adi": row.find_element(By.CSS_SELECTOR, "div[class*='sme-name'] a").text,
                                "faiz_orani": row.find_element(By.CSS_SELECTOR, "div[class*='sme-rate'] span:nth-child(2)").text.strip('%'),
                                "aylik_taksit": row.find_element(By.CSS_SELECTOR, "div[class*='sme-inst'] span:nth-child(2)").text,
                                "toplam_odeme": row.find_element(By.CSS_SELECTOR, "div[class*='sme-total'] span:nth-child(2)").text,
                                "is_sponsored": "sponsored" in row.get_attribute("class")
                            }
                            
                            # Her bir veriyi kontrol et
                            print(f"""
                            Bulunan veriler:
                            - URL: {bank_data['banka']}
                            - Kredi Adı: {bank_data['kredi_adi']}
                            - Faiz Oranı: {bank_data['faiz_orani']}
                            - Aylık Taksit: {bank_data['aylik_taksit']}
                            - Toplam Ödeme: {bank_data['toplam_odeme']}
                            - Sponsored: {bank_data['is_sponsored']}
                            """)
                            
                            month_results.append(bank_data)
                            print(f"Banka: {bank_data['banka']}, "
                                  f"Kredi: {bank_data['kredi_adi']}, "
                                  f"Faiz: %{bank_data['faiz_orani']}, "
                                  f"Aylık Taksit: {bank_data['aylik_taksit']}, "
                                  f"Toplam Ödeme: {bank_data['toplam_odeme']}, "
                                  f"Sponsored: {bank_data['is_sponsored']}")
                            
                        except Exception as e:
                            print(f"Veri çekerken hata: {str(e)}")
                            print(f"Hata konumu: {e.__traceback__.tb_lineno}")
                            continue
                    
                    all_results[str(amount)][f"vade_{vade}"] = month_results
                    print(f"Vade {vade} ay için {len(month_results)} banka bulundu.")
                    
                except Exception as e:
                    print(f"Veri bulunamadı: {vade} ay, {amount} TL - Hata: {str(e)}")
                    continue

    except Exception as e:
        print(f"Genel hata oluştu: {str(e)}")
    
    finally:
        browser.quit()
        output_file = os.path.join(get_data_path(), 'kobi_kredisi_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print(f"\nTüm sonuçlar kaydedildi: {output_file}")

if __name__ == "__main__":
    test_loan_scenarios()