#!/usr/bin/env python3
"""
ФАЗА 3: Маппинг из staging в care_homes
================================================================
Цель: Преобразовать parsed_json из staging в формат care_homes и сохранить

Использование:
    python phase3_map_to_care_homes.py --min-quality 60 --batch-size 100

Требования:
    - PostgreSQL подключение настроено
    - SQL функции нормализации установлены (safe_latitude, safe_longitude, etc.)
    - parsed_json уже загружен в staging (Фаза 2)
"""

import os
import sys
import json
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv
from typing import Dict, Optional, List, Tuple
import logging
from datetime import datetime

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
DEFAULT_BATCH_SIZE = 100
DEFAULT_MIN_QUALITY = 60


def get_db_connection():
    """Получить подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'care_homes'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )


def map_autumna_to_db(parsed_json: Dict) -> Dict:
    """
    Маппинг Autumna JSON Schema v2.4 → care_homes структура
    
    Args:
        parsed_json: Парсированный JSON из OpenAI (188 полей)
    
    Returns:
        Dict с данными для INSERT в care_homes
    """
    identity = parsed_json.get('identity', {})
    contact = parsed_json.get('contact', {})
    location = parsed_json.get('location', {})
    pricing = parsed_json.get('pricing', {})
    care_services = parsed_json.get('care_services', {})
    licenses = parsed_json.get('licenses', {})
    user_categories = parsed_json.get('user_categories', {})
    funding = parsed_json.get('funding', {})
    cqc_ratings = parsed_json.get('cqc_ratings', {})
    reviews = parsed_json.get('reviews', {})
    building_and_facilities = parsed_json.get('building_and_facilities', {})
    capacity = parsed_json.get('capacity', {})
    extraction_metadata = parsed_json.get('extraction_metadata', {})
    source_metadata = parsed_json.get('source_metadata', {})
    
    # Извлечь regulated_activities
    regulated_activities = parsed_json.get('regulated_activities', {})
    
    return {
        # ГРУППА 1: ИДЕНТИФИКАТОРЫ
        'cqc_location_id': identity.get('cqc_location_id'),
        'location_ods_code': identity.get('location_ods_code'),
        
        # ГРУППА 2: БАЗОВАЯ ИНФОРМАЦИЯ
        'name': identity.get('name'),
        'provider_name': identity.get('provider_name'),
        'provider_id': identity.get('provider_id'),
        'brand_name': identity.get('brand_name'),
        
        # ГРУППА 3: КОНТАКТЫ
        'telephone': contact.get('telephone'),
        'email': contact.get('email'),
        'website': contact.get('website'),
        
        # ГРУППА 4: ЛОКАЦИЯ
        'city': location.get('city'),
        'county': location.get('county'),
        'postcode': location.get('postcode'),
        'latitude': location.get('latitude'),
        'longitude': location.get('longitude'),
        'region': location.get('region'),
        'local_authority': location.get('local_authority'),
        
        # ГРУППА 5: ВМЕСТИМОСТЬ
        'beds_total': capacity.get('beds_total'),
        'beds_available': capacity.get('beds_available'),
        'has_availability': capacity.get('has_availability'),
        'availability_status': capacity.get('availability_status'),
        'availability_last_checked': capacity.get('availability_last_checked'),
        'year_opened': capacity.get('year_opened'),
        'year_registered': capacity.get('year_registered'),
        
        # ГРУППА 6: ТИПЫ УХОДА
        'care_residential': care_services.get('care_residential'),
        'care_nursing': care_services.get('care_nursing'),
        'care_dementia': care_services.get('care_dementia'),
        'care_respite': care_services.get('care_respite'),
        
        # ГРУППА 7: ЛИЦЕНЗИИ
        'has_nursing_care_license': licenses.get('has_nursing_care_license'),
        'has_personal_care_license': licenses.get('has_personal_care_license'),
        'has_surgical_procedures_license': licenses.get('has_surgical_procedures_license'),
        'has_treatment_license': licenses.get('has_treatment_license'),
        'has_diagnostic_license': licenses.get('has_diagnostic_license'),
        
        # ГРУППА 8: SERVICE USER BANDS (12 полей)
        'serves_older_people': user_categories.get('serves_older_people'),
        'serves_younger_adults': user_categories.get('serves_younger_adults'),
        'serves_mental_health': user_categories.get('serves_mental_health'),
        'serves_physical_disabilities': user_categories.get('serves_physical_disabilities'),
        'serves_sensory_impairments': user_categories.get('serves_sensory_impairments'),
        'serves_dementia_band': user_categories.get('serves_dementia_band'),
        'serves_children': user_categories.get('serves_children'),
        'serves_learning_disabilities': user_categories.get('serves_learning_disabilities'),
        'serves_detained_mha': user_categories.get('serves_detained_mha'),
        'serves_substance_misuse': user_categories.get('serves_substance_misuse'),
        'serves_eating_disorders': user_categories.get('serves_eating_disorders'),
        'serves_whole_population': user_categories.get('serves_whole_population'),
        
        # ГРУППА 9: ЦЕНООБРАЗОВАНИЕ
        'fee_residential_from': pricing.get('fee_residential_from'),
        'fee_nursing_from': pricing.get('fee_nursing_from'),
        'fee_dementia_from': pricing.get('fee_dementia_from'),
        'fee_respite_from': pricing.get('fee_respite_from'),
        
        # ГРУППА 10: ФИНАНСИРОВАНИЕ
        'accepts_self_funding': funding.get('accepts_self_funding'),
        'accepts_local_authority': funding.get('accepts_local_authority'),
        'accepts_nhs_chc': funding.get('accepts_nhs_chc'),
        'accepts_third_party_topup': funding.get('accepts_third_party_topup'),
        
        # ГРУППА 11: CQC РЕЙТИНГИ
        'cqc_rating_overall': cqc_ratings.get('cqc_rating_overall'),
        'cqc_rating_safe': cqc_ratings.get('cqc_rating_safe'),
        'cqc_rating_effective': cqc_ratings.get('cqc_rating_effective'),
        'cqc_rating_caring': cqc_ratings.get('cqc_rating_caring'),
        'cqc_rating_responsive': cqc_ratings.get('cqc_rating_responsive'),
        'cqc_rating_well_led': cqc_ratings.get('cqc_rating_well_led'),
        'cqc_last_inspection_date': cqc_ratings.get('cqc_last_inspection_date'),
        'cqc_publication_date': cqc_ratings.get('cqc_publication_date'),
        'cqc_latest_report_url': cqc_ratings.get('cqc_latest_report_url'),
        
        # ГРУППА 12: ОТЗЫВЫ
        'review_average_score': reviews.get('review_average_score'),
        'review_count': reviews.get('review_count'),
        'google_rating': reviews.get('google_rating'),
        
        # ГРУППА 13: УДОБСТВА
        'wheelchair_access': building_and_facilities.get('wheelchair_access'),
        'ensuite_rooms': building_and_facilities.get('ensuite_rooms'),
        'secure_garden': building_and_facilities.get('secure_garden'),
        'wifi_available': building_and_facilities.get('wifi_available'),
        'parking_onsite': building_and_facilities.get('parking_onsite'),
        
        # ГРУППА 14: СТАТУС
        'is_dormant': extraction_metadata.get('is_dormant', False),
        'data_quality_score': extraction_metadata.get('data_quality_score'),
        
        # ГРУППА 15: JSONB ПОЛЯ (17 полей)
        'regulated_activities': json.dumps(regulated_activities) if regulated_activities else None,
        'source_urls': json.dumps({
            'autumna_url': source_metadata.get('source_url'),
            'cqc_profile_url': cqc_ratings.get('cqc_latest_report_url')
        }) if source_metadata.get('source_url') else None,
        'service_types': json.dumps({
            'services': care_services.get('service_types_list', [])
        }) if care_services.get('service_types_list') else None,
        'service_user_bands': json.dumps({
            'bands': user_categories.get('service_user_bands_list', [])
        }) if user_categories.get('service_user_bands_list') else None,
        'medical_specialisms': json.dumps(parsed_json.get('medical_specialisms', {})),
        'dietary_options': json.dumps(parsed_json.get('dietary_options', {})),
        'activities': json.dumps(parsed_json.get('activities', {})),
        'pricing_details': json.dumps(pricing),
        'staff_information': json.dumps(parsed_json.get('staff_information', {})),
        'reviews_detailed': json.dumps(reviews),
        'media': json.dumps(parsed_json.get('media', {})),
        'location_context': json.dumps(location.get('location_context', {})),
        'building_info': json.dumps(building_and_facilities.get('building_details', {})),
        'accreditations': json.dumps(parsed_json.get('accreditations', {})),
        'source_metadata': json.dumps(source_metadata),
        'extra': json.dumps({}),  # Пустой для будущего расширения
        
        # ВРЕМЕННЫЕ МЕТКИ
        'last_scraped_at': source_metadata.get('scraped_at')
    }


def validate_record(db_data: Dict) -> Tuple[bool, List[str]]:
    """Валидация данных перед вставкой"""
    errors = []
    
    # Критические поля
    if not db_data.get('cqc_location_id'):
        errors.append('Missing cqc_location_id')
    if not db_data.get('name'):
        errors.append('Missing name')
    if not db_data.get('city'):
        errors.append('Missing city')
    if not db_data.get('postcode'):
        errors.append('Missing postcode')
    
    # Валидация координат
    lat = db_data.get('latitude')
    lon = db_data.get('longitude')
    if lat is not None and (lat < 49.0 or lat > 61.0):
        errors.append(f'Latitude out of UK range: {lat}')
    if lon is not None and (lon < -8.0 or lon > 2.0):
        errors.append(f'Longitude out of UK range: {lon}')
    
    # Валидация beds
    beds_total = db_data.get('beds_total')
    beds_available = db_data.get('beds_available')
    if beds_total is not None and beds_available is not None:
        if beds_available > beds_total:
            errors.append(f'beds_available ({beds_available}) > beds_total ({beds_total})')
    
    return len(errors) == 0, errors


def get_ready_records(conn, batch_size: int, min_quality: int) -> List[Dict]:
    """Получить записи готовые для маппинга"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            id,
            parsed_json,
            source_url,
            cqc_location_id,
            data_quality_score,
            extraction_confidence
        FROM autumna_staging
        WHERE parsed_json IS NOT NULL
          AND processed = FALSE
          AND (data_quality_score IS NULL OR data_quality_score >= %(min_quality)s)
        ORDER BY data_quality_score DESC NULLS LAST, created_at ASC
        LIMIT %(batch_size)s
    """, {
        'min_quality': min_quality,
        'batch_size': batch_size
    })
    
    records = cursor.fetchall()
    cursor.close()
    return [dict(record) for record in records]


def insert_into_care_homes(conn, db_data: Dict) -> Optional[int]:
    """Вставить запись в care_homes используя SQL функции нормализации"""
    cursor = conn.cursor()
    
    try:
        # Большой INSERT с SQL функциями для нормализации
        cursor.execute("""
            INSERT INTO care_homes (
                cqc_location_id,
                location_ods_code,
                name,
                name_normalized,
                provider_name,
                provider_id,
                brand_name,
                telephone,
                email,
                website,
                city,
                county,
                postcode,
                latitude,
                longitude,
                region,
                local_authority,
                beds_total,
                beds_available,
                has_availability,
                availability_status,
                availability_last_checked,
                year_opened,
                year_registered,
                care_residential,
                care_nursing,
                care_dementia,
                care_respite,
                has_nursing_care_license,
                has_personal_care_license,
                has_surgical_procedures_license,
                has_treatment_license,
                has_diagnostic_license,
                serves_older_people,
                serves_younger_adults,
                serves_mental_health,
                serves_physical_disabilities,
                serves_sensory_impairments,
                serves_dementia_band,
                serves_children,
                serves_learning_disabilities,
                serves_detained_mha,
                serves_substance_misuse,
                serves_eating_disorders,
                serves_whole_population,
                fee_residential_from,
                fee_nursing_from,
                fee_dementia_from,
                fee_respite_from,
                accepts_self_funding,
                accepts_local_authority,
                accepts_nhs_chc,
                accepts_third_party_topup,
                cqc_rating_overall,
                cqc_rating_safe,
                cqc_rating_effective,
                cqc_rating_caring,
                cqc_rating_responsive,
                cqc_rating_well_led,
                cqc_last_inspection_date,
                cqc_publication_date,
                cqc_latest_report_url,
                review_average_score,
                review_count,
                google_rating,
                wheelchair_access,
                ensuite_rooms,
                secure_garden,
                wifi_available,
                parking_onsite,
                is_dormant,
                data_quality_score,
                last_scraped_at,
                regulated_activities,
                source_urls,
                service_types,
                service_user_bands,
                medical_specialisms,
                dietary_options,
                activities,
                pricing_details,
                staff_information,
                reviews_detailed,
                media,
                location_context,
                building_info,
                accreditations,
                source_metadata,
                extra
            ) VALUES (
                %(cqc_location_id)s,
                %(location_ods_code)s,
                clean_text(%(name)s),
                LOWER(TRIM(%(name)s)),
                clean_text(%(provider_name)s),
                %(provider_id)s,
                clean_text(%(brand_name)s),
                %(telephone)s,
                %(email)s,
                %(website)s,
                clean_text(%(city)s),
                clean_text(%(county)s),
                %(postcode)s,
                safe_latitude(%(latitude)s::TEXT),
                safe_longitude(%(longitude)s::TEXT),
                clean_text(%(region)s),
                clean_text(%(local_authority)s),
                %(beds_total)s,
                %(beds_available)s,
                COALESCE(%(has_availability)s, FALSE),
                %(availability_status)s,
                %(availability_last_checked)s,
                %(year_opened)s,
                %(year_registered)s,
                COALESCE(%(care_residential)s, FALSE),
                COALESCE(%(care_nursing)s, FALSE),
                COALESCE(%(care_dementia)s, FALSE),
                COALESCE(%(care_respite)s, FALSE),
                COALESCE(%(has_nursing_care_license)s, FALSE),
                COALESCE(%(has_personal_care_license)s, FALSE),
                COALESCE(%(has_surgical_procedures_license)s, FALSE),
                COALESCE(%(has_treatment_license)s, FALSE),
                COALESCE(%(has_diagnostic_license)s, FALSE),
                COALESCE(%(serves_older_people)s, FALSE),
                COALESCE(%(serves_younger_adults)s, FALSE),
                COALESCE(%(serves_mental_health)s, FALSE),
                COALESCE(%(serves_physical_disabilities)s, FALSE),
                COALESCE(%(serves_sensory_impairments)s, FALSE),
                COALESCE(%(serves_dementia_band)s, FALSE),
                COALESCE(%(serves_children)s, FALSE),
                COALESCE(%(serves_learning_disabilities)s, FALSE),
                COALESCE(%(serves_detained_mha)s, FALSE),
                COALESCE(%(serves_substance_misuse)s, FALSE),
                COALESCE(%(serves_eating_disorders)s, FALSE),
                COALESCE(%(serves_whole_population)s, FALSE),
                %(fee_residential_from)s,
                %(fee_nursing_from)s,
                %(fee_dementia_from)s,
                %(fee_respite_from)s,
                COALESCE(%(accepts_self_funding)s, FALSE),
                COALESCE(%(accepts_local_authority)s, FALSE),
                COALESCE(%(accepts_nhs_chc)s, FALSE),
                COALESCE(%(accepts_third_party_topup)s, FALSE),
                normalize_cqc_rating(%(cqc_rating_overall)s),
                normalize_cqc_rating(%(cqc_rating_safe)s),
                normalize_cqc_rating(%(cqc_rating_effective)s),
                normalize_cqc_rating(%(cqc_rating_caring)s),
                normalize_cqc_rating(%(cqc_rating_responsive)s),
                normalize_cqc_rating(%(cqc_rating_well_led)s),
                safe_date(%(cqc_last_inspection_date)s),
                safe_date(%(cqc_publication_date)s),
                %(cqc_latest_report_url)s,
                %(review_average_score)s,
                COALESCE(%(review_count)s, 0),
                %(google_rating)s,
                COALESCE(%(wheelchair_access)s, FALSE),
                COALESCE(%(ensuite_rooms)s, FALSE),
                COALESCE(%(secure_garden)s, FALSE),
                COALESCE(%(wifi_available)s, FALSE),
                COALESCE(%(parking_onsite)s, FALSE),
                COALESCE(%(is_dormant)s, FALSE),
                %(data_quality_score)s,
                %(last_scraped_at)s,
                %(regulated_activities)s::jsonb,
                %(source_urls)s::jsonb,
                %(service_types)s::jsonb,
                %(service_user_bands)s::jsonb,
                %(medical_specialisms)s::jsonb,
                %(dietary_options)s::jsonb,
                %(activities)s::jsonb,
                %(pricing_details)s::jsonb,
                %(staff_information)s::jsonb,
                %(reviews_detailed)s::jsonb,
                %(media)s::jsonb,
                %(location_context)s::jsonb,
                %(building_info)s::jsonb,
                %(accreditations)s::jsonb,
                %(source_metadata)s::jsonb,
                %(extra)s::jsonb
            )
            ON CONFLICT (cqc_location_id) DO UPDATE
            SET 
                name = EXCLUDED.name,
                name_normalized = EXCLUDED.name_normalized,
                provider_name = EXCLUDED.provider_name,
                provider_id = EXCLUDED.provider_id,
                brand_name = EXCLUDED.brand_name,
                telephone = EXCLUDED.telephone,
                email = EXCLUDED.email,
                website = EXCLUDED.website,
                city = EXCLUDED.city,
                county = EXCLUDED.county,
                postcode = EXCLUDED.postcode,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                region = EXCLUDED.region,
                local_authority = EXCLUDED.local_authority,
                beds_total = EXCLUDED.beds_total,
                beds_available = EXCLUDED.beds_available,
                has_availability = EXCLUDED.has_availability,
                availability_status = EXCLUDED.availability_status,
                availability_last_checked = EXCLUDED.availability_last_checked,
                year_opened = EXCLUDED.year_opened,
                year_registered = EXCLUDED.year_registered,
                care_residential = EXCLUDED.care_residential,
                care_nursing = EXCLUDED.care_nursing,
                care_dementia = EXCLUDED.care_dementia,
                care_respite = EXCLUDED.care_respite,
                has_nursing_care_license = EXCLUDED.has_nursing_care_license,
                has_personal_care_license = EXCLUDED.has_personal_care_license,
                has_surgical_procedures_license = EXCLUDED.has_surgical_procedures_license,
                has_treatment_license = EXCLUDED.has_treatment_license,
                has_diagnostic_license = EXCLUDED.has_diagnostic_license,
                serves_older_people = EXCLUDED.serves_older_people,
                serves_younger_adults = EXCLUDED.serves_younger_adults,
                serves_mental_health = EXCLUDED.serves_mental_health,
                serves_physical_disabilities = EXCLUDED.serves_physical_disabilities,
                serves_sensory_impairments = EXCLUDED.serves_sensory_impairments,
                serves_dementia_band = EXCLUDED.serves_dementia_band,
                serves_children = EXCLUDED.serves_children,
                serves_learning_disabilities = EXCLUDED.serves_learning_disabilities,
                serves_detained_mha = EXCLUDED.serves_detained_mha,
                serves_substance_misuse = EXCLUDED.serves_substance_misuse,
                serves_eating_disorders = EXCLUDED.serves_eating_disorders,
                serves_whole_population = EXCLUDED.serves_whole_population,
                fee_residential_from = EXCLUDED.fee_residential_from,
                fee_nursing_from = EXCLUDED.fee_nursing_from,
                fee_dementia_from = EXCLUDED.fee_dementia_from,
                fee_respite_from = EXCLUDED.fee_respite_from,
                accepts_self_funding = EXCLUDED.accepts_self_funding,
                accepts_local_authority = EXCLUDED.accepts_local_authority,
                accepts_nhs_chc = EXCLUDED.accepts_nhs_chc,
                accepts_third_party_topup = EXCLUDED.accepts_third_party_topup,
                cqc_rating_overall = EXCLUDED.cqc_rating_overall,
                cqc_rating_safe = EXCLUDED.cqc_rating_safe,
                cqc_rating_effective = EXCLUDED.cqc_rating_effective,
                cqc_rating_caring = EXCLUDED.cqc_rating_caring,
                cqc_rating_responsive = EXCLUDED.cqc_rating_responsive,
                cqc_rating_well_led = EXCLUDED.cqc_rating_well_led,
                cqc_last_inspection_date = EXCLUDED.cqc_last_inspection_date,
                cqc_publication_date = EXCLUDED.cqc_publication_date,
                cqc_latest_report_url = EXCLUDED.cqc_latest_report_url,
                review_average_score = EXCLUDED.review_average_score,
                review_count = EXCLUDED.review_count,
                google_rating = EXCLUDED.google_rating,
                wheelchair_access = EXCLUDED.wheelchair_access,
                ensuite_rooms = EXCLUDED.ensuite_rooms,
                secure_garden = EXCLUDED.secure_garden,
                wifi_available = EXCLUDED.wifi_available,
                parking_onsite = EXCLUDED.parking_onsite,
                is_dormant = EXCLUDED.is_dormant,
                data_quality_score = EXCLUDED.data_quality_score,
                last_scraped_at = EXCLUDED.last_scraped_at,
                regulated_activities = EXCLUDED.regulated_activities,
                source_urls = EXCLUDED.source_urls,
                service_types = EXCLUDED.service_types,
                service_user_bands = EXCLUDED.service_user_bands,
                medical_specialisms = EXCLUDED.medical_specialisms,
                dietary_options = EXCLUDED.dietary_options,
                activities = EXCLUDED.activities,
                pricing_details = EXCLUDED.pricing_details,
                staff_information = EXCLUDED.staff_information,
                reviews_detailed = EXCLUDED.reviews_detailed,
                media = EXCLUDED.media,
                location_context = EXCLUDED.location_context,
                building_info = EXCLUDED.building_info,
                accreditations = EXCLUDED.accreditations,
                source_metadata = EXCLUDED.source_metadata,
                extra = EXCLUDED.extra,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, db_data)
        
        care_homes_id = cursor.fetchone()[0]
        conn.commit()
        return care_homes_id
        
    except Exception as e:
        logger.error(f"Ошибка при вставке в care_homes: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()


def update_staging_processed(conn, staging_id: int, care_homes_id: Optional[int], errors: List[str]):
    """Обновить staging запись после маппинга"""
    cursor = conn.cursor()
    
    try:
        if care_homes_id:
            cursor.execute("""
                UPDATE autumna_staging
                SET 
                    processed = TRUE,
                    processed_at = CURRENT_TIMESTAMP,
                    care_homes_id = %(care_homes_id)s,
                    mapping_errors = NULL,
                    needs_validation = FALSE
                WHERE id = %(staging_id)s
            """, {
                'staging_id': staging_id,
                'care_homes_id': care_homes_id
            })
        else:
            cursor.execute("""
                UPDATE autumna_staging
                SET 
                    mapping_errors = %(errors)s::jsonb,
                    needs_validation = TRUE
                WHERE id = %(staging_id)s
            """, {
                'staging_id': staging_id,
                'errors': json.dumps({'errors': errors, 'timestamp': datetime.now().isoformat()})
            })
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении staging ID {staging_id}: {e}")
        conn.rollback()
    finally:
        cursor.close()


def process_batch(conn, records: List[Dict], min_quality: int):
    """Обработать батч записей"""
    success_count = 0
    failed_count = 0
    
    for record in records:
        staging_id = record['id']
        url = record['source_url']
        parsed_json_str = record['parsed_json']
        
        logger.info(f"🔄 Маппинг: {url} (ID: {staging_id})")
        
        try:
            # Парсинг JSON
            parsed_json = json.loads(parsed_json_str) if isinstance(parsed_json_str, str) else parsed_json_str
            
            # Маппинг в структуру БД
            db_data = map_autumna_to_db(parsed_json)
            
            # Валидация
            is_valid, errors = validate_record(db_data)
            
            if not is_valid:
                logger.warning(f"⚠️  Валидация не пройдена {url}: {', '.join(errors)}")
                update_staging_processed(conn, staging_id, None, errors)
                failed_count += 1
                continue
            
            # Вставка в care_homes
            care_homes_id = insert_into_care_homes(conn, db_data)
            
            if care_homes_id:
                logger.info(f"✅ Успешно: {url} → care_homes ID: {care_homes_id}")
                update_staging_processed(conn, staging_id, care_homes_id, [])
                success_count += 1
            else:
                logger.error(f"❌ Ошибка вставки: {url}")
                update_staging_processed(conn, staging_id, None, ['Database insert failed'])
                failed_count += 1
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {url}: {e}")
            update_staging_processed(conn, staging_id, None, [str(e)])
            failed_count += 1
    
    return success_count, failed_count


def main():
    parser = argparse.ArgumentParser(description='Фаза 3: Маппинг из staging в care_homes')
    parser.add_argument('--min-quality', type=int, default=DEFAULT_MIN_QUALITY, 
                        help=f'Минимальный quality score (по умолчанию: {DEFAULT_MIN_QUALITY})')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Размер батча (по умолчанию: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый запуск без сохранения')
    
    args = parser.parse_args()
    
    # Подключиться к БД
    logger.info("🔌 Подключение к БД...")
    conn = get_db_connection()
    logger.info("   ✅ Подключено")
    
    total_success = 0
    total_failed = 0
    
    # Обработка батчами
    while True:
        # Получить следующий батч
        records = get_ready_records(conn, args.batch_size, args.min_quality)
        
        if not records:
            logger.info("✅ Все записи обработаны!")
            break
        
        logger.info(f"\n📦 Обработка батча из {len(records)} записей...")
        
        if args.dry_run:
            logger.info("🧪 DRY RUN - результаты не будут сохранены")
            for record in records:
                logger.info(f"  - {record['source_url']} (quality: {record.get('data_quality_score')})")
            break
        
        # Обработать батч
        success, failed = process_batch(conn, records, args.min_quality)
        
        total_success += success
        total_failed += failed
        
        logger.info(f"📊 Батч завершен: ✅ {success}, ❌ {failed}")
        
        # Если обработаны не все записи, продолжить
        if len(records) < args.batch_size:
            break
    
    conn.close()
    
    logger.info(f"\n✅ Завершено! Всего: ✅ {total_success}, ❌ {total_failed}")


if __name__ == '__main__':
    main()

