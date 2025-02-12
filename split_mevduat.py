import json
import os

def split_mevduat_data():
    try:
        # Data klasörü yolunu al
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "Data")
        
        # Kaynak dosya yolu
        mevduat_path = os.path.join(data_dir, "mevduat.json")
        
        print(f"Mevduat verisi okunuyor: {mevduat_path}")
        
        # JSON dosyasını oku
        with open(mevduat_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Para birimlerine göre verileri ayır
        tl_data = {"TL": data.get("TL", {})}
        foreign_data = {
            "USD": data.get("USD", {}),
            "EUR": data.get("EUR", {})
        }
        
        # TL verilerini kaydet
        tl_output_path = os.path.join(data_dir, "mevduat_tl.json")
        with open(tl_output_path, 'w', encoding='utf-8') as file:
            json.dump(tl_data, file, ensure_ascii=False, indent=4)
        print(f"TL verileri kaydedildi: {tl_output_path}")
        
        # Döviz verilerini kaydet
        foreign_output_path = os.path.join(data_dir, "mevduat_foreign.json")
        with open(foreign_output_path, 'w', encoding='utf-8') as file:
            json.dump(foreign_data, file, ensure_ascii=False, indent=4)
        print(f"Döviz verileri kaydedildi: {foreign_output_path}")
        
    except FileNotFoundError:
        print(f"Hata: mevduat.json dosyası bulunamadı: {mevduat_path}")
    except json.JSONDecodeError:
        print(f"Hata: mevduat.json dosyası geçerli bir JSON formatında değil")
    except Exception as e:
        print(f"Beklenmeyen hata oluştu: {str(e)}")

if __name__ == "__main__":
    split_mevduat_data()