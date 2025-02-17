import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import time
from datetime import datetime

def format_kredi_data(data, kredi_turu):
    """Kredi verilerini Firebase formatına dönüştür"""
    try:
        # JSON verilerini doğrula
        if not isinstance(data, dict):
            print(f"Hata: Veri sözlük formatında değil. Veri tipi: {type(data)}")
            return []

        formatted_data = []
        
        if kredi_turu == "tasit":
            for arac_durumu, amounts in data.items():
                arac_tipi = "Sıfır Araç" if "1" in arac_durumu else "İkinci El Araç"
                for amount, vades in amounts.items():
                    for vade, banka_listesi in vades.items():
                        for banka_data in banka_listesi:
                            formatted_data.append({
                                'arac_durumu': arac_tipi,
                                'kredi_tutari': amount,
                                'vade': vade.replace('vade_', ''),
                                'banka': banka_data['banka'],
                                'alt_bilgi': banka_data.get('alt_bilgi', ''),
                                'oran_turu': banka_data.get('oran_turu', ''),
                                'faiz_orani': banka_data.get('faiz_orani', '')
                            })
        
        elif kredi_turu == "konut":
            for amount, vades in data.items():
                for vade, banka_listesi in vades.items():
                    for banka_data in banka_listesi:
                        formatted_data.append({
                            'kredi_tutari': amount,
                            'vade': vade.replace('vade_', ''),
                            'banka': banka_data.get('banka', ''),
                            'alt_bilgi': banka_data.get('alt_bilgi', ''),
                            'oran_turu': banka_data.get('oran_turu', ''),
                            'faiz_orani': banka_data.get('faiz_orani', '')
                        })
        
        elif kredi_turu == "ihtiyac":
            for amount, amount_data in data.items():
                amount_value = amount.replace("amount_", "")
                for vade, vade_data in amount_data.items():
                    vade_value = vade.replace("vade_", "")
                    for bank_data in vade_data:
                        try:
                            formatted_bank = {
                                "kredi_turu": "İhtiyaç Kredisi",
                                "kredi_tutari": float(amount_value),
                                "vade": int(vade_value),
                                "banka": bank_data["banka"],
                                "faiz_orani": float(bank_data["faiz_orani"].replace(",", ".")),
                                "aylik_taksit": bank_data["aylik_taksit"],
                                "toplam_odeme": bank_data["toplam_odeme"],
                                "tarih": datetime.now().strftime("%Y-%m-%d")
                            }
                            formatted_data.append(formatted_bank)
                        except Exception as e:
                            print(f"Banka verisi işlenirken hata: {str(e)}")
                            continue
        
        elif kredi_turu == "kobi":
            for amount, vades in data.items():
                for vade, banka_listesi in vades.items():
                    for banka_data in banka_listesi:
                        formatted_data.append({
                            'kredi_tutari': amount,
                            'vade': vade.replace('vade_', ''),
                            'banka': banka_data.get('banka', ''),
                            'kredi_adi': banka_data.get('kredi_adi', ''),
                            'faiz_orani': banka_data.get('faiz_orani', ''),
                            'aylik_taksit': banka_data.get('aylik_taksit', ''),
                            'toplam_odeme': banka_data.get('toplam_odeme', ''),
                            'is_sponsored': banka_data.get('is_sponsored', False)
                        })
        
        return formatted_data
    except Exception as e:
        print(f"format_kredi_data hatası: {str(e)}")
        return []

def format_mevduat_data(data):
    """Mevduat verilerini Firebase formatına dönüştür"""
    formatted_data = []
    
    for currency, amounts in data.items():
        for amount, vades in amounts.items():
            for vade, bank_list in vades.items():
                for bank_data in bank_list:
                    formatted_doc = {
                        'banka_adi': bank_data.get('banka_adi', ''),
                        'faiz_orani': bank_data.get('faiz_orani', ''),
                        'hesap_aciklama': bank_data.get('hesap_aciklama', ''),
                        'hesap_turu': bank_data.get('hesap_turu', ''),
                        'para_birimi': currency,
                        'vade': vade.replace('vade_', ''),
                        'yatirim_tutari': amount
                    }
                    formatted_data.append(formatted_doc)
    return formatted_data

def batch_upload(collection_name, formatted_data, database):
    """Verileri batch halinde yükle"""
    if not formatted_data:
        print(f"No data to upload for {collection_name}")
        return
        
    batch = database.batch()
    count = 0
    total_uploaded = 0
    batch_size = 500
    
    print(f"Toplam {len(formatted_data)} veri yüklenecek...")
    
    for item in formatted_data:
        if count >= batch_size:
            try:
                batch.commit()
                total_uploaded += count
                print(f"Batch commit yapıldı. Toplam yüklenen: {total_uploaded}")
                batch = database.batch()
                count = 0
                time.sleep(1)
            except Exception as e:
                print(f"Batch commit hatası: {e}")
                time.sleep(2)
                continue
        
        try:
            # Sadece None olmayan ve boş string olmayan değerleri al
            filtered_item = {k: v for k, v in item.items() if v is not None and v != ""}
            
            ref = database.collection(collection_name).document()
            batch.set(ref, filtered_item)  # Sadece var olan alanları set et
            count += 1
        except Exception as e:
            print(f"Document set hatası: {e}")
            continue
    
    if count > 0:
        try:
            batch.commit()
            total_uploaded += count
            print(f"Son batch commit yapıldı. Toplam yüklenen: {total_uploaded}")
        except Exception as e:
            print(f"Son batch commit hatası: {e}")

def upload_kredi_data():
    """Kredi verilerini yükle"""
    try:
        # Firebase setup
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "serviceAccountKey.json")
        cred = credentials.Certificate(key_path)
        app = firebase_admin.initialize_app(cred, name='kredi')
        db = firestore.client(app)

        json_files = {
            "ihtiyac_kredisi_data.json": "ihtiyac_kredisi_bot",
            "kobi_kredisi_data.json": "kobi_kredisi_bot",
            "konut_kredisi_data.json": "konut_kredisi_bot"
        }

        for json_file, kredi_turu in json_files.items():
            collection_name = json_file.replace('.json', '')
            file_path = os.path.join(current_dir, "Data", json_file)
            
            print(f"\nProcessing {json_file}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    formatted_data = format_kredi_data(data, kredi_turu)
                    
                    if formatted_data:
                        # Koleksiyonu temizle
                        print(f"Koleksiyon temizleniyor: {collection_name}...")
                        docs = db.collection(collection_name).stream()
                        batch = db.batch()
                        deleted_count = 0
                        for doc in docs:
                            batch.delete(doc.reference)
                            deleted_count += 1
                            if deleted_count >= 100:
                                batch.commit()
                                batch = db.batch()
                                deleted_count = 0
                        if deleted_count > 0:
                            batch.commit()
                        
                        batch_upload(collection_name, formatted_data, db)
            except Exception as e:
                print(f"Hata: {json_file} - {str(e)}")

    except Exception as e:
        print(f"Kredi verisi yükleme hatası: {str(e)}")

def upload_mevduat_tl_data():
    """TL mevduat verilerini yükle"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "mevduatServiceAccountKey.json")
        mevduat_json_path = os.path.join(current_dir, "Data", "mevduat_tl.json")

        cred = credentials.Certificate(key_path)
        app = firebase_admin.initialize_app(cred, name='mevduat_tl')
        db = firestore.client(app)

        with open(mevduat_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            formatted_data = format_mevduat_data(data)
            batch_upload('mevduat_tl_bot', formatted_data, db)

    except Exception as e:
        print(f"TL mevduat verisi yükleme hatası: {str(e)}")

def upload_mevduat_foreign_data():
    """Döviz mevduat verilerini yükle"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "mevduat2serviceAccountKey.json")
        mevduat_json_path = os.path.join(current_dir, "Data", "mevduat_foreign.json")

        cred = credentials.Certificate(key_path)
        app = firebase_admin.initialize_app(cred, name='mevduat_foreign')
        db = firestore.client(app)

        with open(mevduat_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            formatted_data = format_mevduat_data(data)
            batch_upload('mevduat_foreign_bot', formatted_data, db)

    except Exception as e:
        print(f"Döviz mevduat verisi yükleme hatası: {str(e)}")

def main():
    """Ana fonksiyon"""
    try:
        print("\n1. Kredi verileri yükleniyor...")
        # Taşıt kredisi hariç diğer kredileri yükle
        json_files = {
            "ihtiyac_kredisi_data.json": "ihtiyac_kredisi_bot",
            "kobi_kredisi_data.json": "kobi_kredisi_bot",
            "konut_kredisi_data.json": "konut_kredisi_bot"
        }
        
        # Firebase setup
        current_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(current_dir, "serviceAccountKey.json")
        cred = credentials.Certificate(key_path)
        app = firebase_admin.initialize_app(cred, name='kredi')
        db = firestore.client(app)

        for json_file, kredi_turu in json_files.items():
            collection_name = json_file.replace('.json', '')
            file_path = os.path.join(current_dir, "Data", json_file)
            
            print(f"\nProcessing {json_file}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    formatted_data = format_kredi_data(data, kredi_turu)
                    
                    if formatted_data:
                        # Koleksiyonu temizle
                        print(f"Koleksiyon temizleniyor: {collection_name}...")
                        docs = db.collection(collection_name).stream()
                        batch = db.batch()
                        deleted_count = 0
                        for doc in docs:
                            batch.delete(doc.reference)
                            deleted_count += 1
                            if deleted_count >= 100:
                                batch.commit()
                                batch = db.batch()
                                deleted_count = 0
                        if deleted_count > 0:
                            batch.commit()
                        
                        batch_upload(collection_name, formatted_data, db)
            except Exception as e:
                print(f"Hata: {json_file} - {str(e)}")
                continue
        
        print("\n2. TL mevduat verileri yükleniyor...")
        upload_mevduat_tl_data()
        
        print("\n3. Döviz mevduat verileri yükleniyor...")
        upload_mevduat_foreign_data()
        
    except Exception as e:
        print(f"Ana fonksiyon hatası: {str(e)}")
    
    print("\nTüm veri yükleme işlemleri tamamlandı.")

if __name__ == "__main__":
    main() 