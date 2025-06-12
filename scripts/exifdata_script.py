''' 
Dette script er istand til at hive geotags og geolocation data lagret i EXIF-data i billeder.
Brug dette til hvis der skal importeres billeder ind i ArcGIS som attachments i en File Geodatabase Point Dataset feature class
Data bliver lagret i Excel, men kan ændres til CSV eller JSON

Scriptet skal køres fra terminalen eller på Windows Command Prompt. I terminalen kan der vælges at angive ouput filnavnet eller bruge det standard angivet. 
'''

import argparse
from multiprocessing import Value
import os
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pandas as pd
from datetime import datetime

def get_decimal_coordinates(info):
    '''
    Konverterer GPS koordinater fra dd/mm/ss til decimal format
    '''

    if "GPSInfo" not in info:
        return None, None
    
    gps_info = info["GPSInfo"]

    # tjekker for tags i exif-data
    required_tags = [1, 2, 3, 4] #GPSLATReference, GPSLAT, GPSLongReference, GPSLong
    if not all(tag in gps_info for tag in required_tags):
        return None, None
    
    # henter breddegrad
    lat_ref = gps_info[1]
    lat = gps_info[2]
    lat_d, lat_m, lat_s = [float(x.num) / float(x.den) for x in lat.values]
    latitude = lat_d + (lat_m / 60.0) + (lat_s / 3600.0)
    if lat_ref != "S":
        latitude = -latitude

    # henter længdegrad info
    lon_ref = gps_info[3]
    lon = gps_info[4]
    lon_d, lon_m, lon_s = [float(x.num) / float(x.den) for x in lon.values]
    longitude = lon_d + (lon_m / 60.0) + (lon_s / 3600.0)
    if lon_ref != "W":
        longitude = -longitude
    
    return latitude, longitude

def get_name(filepath):
    '''
    Trækker navnet af billedet ud af filnavnet
    Bruges til at give et navn til hvert billedes koordinater. Linking
    '''

    return os.path.splitext(os.path.basename(filepath))[0]

def extract_metadata(image_path):
    '''
    Hiver metadata ud af billedet
    Hiver kun relevante data ud: navn, breddegrad, længdegrad og filstien til billedet
    '''

    result = {
        "name": get_name(image_path),
        "latitude": None,
        "longitude": None,
        "filepath": image_path
    }

    try:
        # henter exif data
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f)

            if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                lat_ref = tags.get("GPS GPSLatitudeRef").values
                lat = tags.get("GPS GPSLatitude").values
                lon_ref = tags.get("GPS GPSLongitudeRef").values
                lon = tags.get("GPS GPSLongitude").values

                # konverter til decimal
                lat_decimal = float(lat[0].num) / float(lat[0].den) + (float(lat[1].num) / float(lat[1].den) / 60) + (float(lat[2].num) / float(lat[2].den) / 3600)
                if lat_ref == "S":
                    lat_decimal = -lat_decimal

                lon_decimal = float(lon[0].num) / float(lon[0].den) + (float(lon[1].num) / float(lon[1].den) / 60) + (float(lon[2].num) / float(lon[2].den) / 3600)
                if lon_ref == "W":
                    lon_decimal = -lon_decimal
                
                result["latitude"] = lat_decimal
                result["longitude"] = lon_decimal
            
            # alternativ this exifread ikke virker
            if result["latitude"] is None:
                img = Image.open(image_path)
                exif_data = img._getexif()

                if exif_data:
                    labeled_exif = {
                        TAGS.get(key, key): value
                        for key, value in exif_data.items()
                    }

                    lat, lon = get_decimal_coordinates(labeled_exif)
                    if lat is not None and lon is not None:
                        result["latitude"] = lat
                        result["longitude"] = lon
    
    except Exception as e:
        print(f"fejl ved processering {image_path}: {e}")

    return result


def process_billeder(directory_path):
    '''
    Processerer alle billederne i et directory
    '''

    results = []
    supported_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.heic')

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(supported_extensions):
            file_path = os.path.join(directory_path, filename)
            result = extract_metadata(file_path)
            results.append(result)

            #udksirv resultat. Bruges som tjeksum til at tjekke scriptets funktionalitet
            print(f"Fil: {filename}")
            print(f"  Navn: {result["name"]}")
            print(f"  Breddegrad: {result["latitude"]}")
            print(f"  Længdegrad: {result["longitude"]}")
            print("-" * 40)
    
    return results

def gem_excel(results, output_path=None):
    '''
    Gem resultater i en excel-fil der kan bruges efterfølgende
    '''

    # ny dataframe
    df = pd.DataFrame(results)

    #gemmer kiun relevante kolonner
    df = df[["name", "latitude", "longitude", "filepath"]]

    #hvis der ikke er lavet en output_sti, så laves der en
    if output_path is None:
        timestamp = datetime.no().strftime("%Y%m%d_%H%M%S")
        output_path = f"geotagged_billeder_{timestamp}.xlsx"
    
    # gem til excel
    df.to_excel(output_path, index=False, sheet_name="Billeder med geotagged data")
    print(f"Data gemt til {output_path}")
    return output_path


def main():
    # main 
    parser = argparse.ArgumentParser(description="Hent geolocation data fra billeder og gem til excel-fil") # 
    parser.add_argument("path", help="sti til mappen med billeder (directory)") # 
    parser.add_argument("-o", "--output", help="sti til output excel-fil (directory)") # 
    args = parser.parse_args() 

    path = args.path
    results = []


    if os.path.isdir(path):# hvis det er en mappe
        print(f"Behandler directory: {path}")
        results = process_billeder(path)
    elif os.path.isfile(path): # hvis et er en fil
        print(f"Behandler fil: {path}")
        result = extract_metadata(path)
        results = [result]
        print(f"Name: {result['name']}")
        print(f"Breddegrad: {result['latitude']}")
        print(f"Længdegrads: {result['longitude']}")
    else:
        print(f"Fejl: {path} er ikke gyldig")
        return
    
    if results:
        gem_excel(results, args.output)

# kør script
# dette script skal køres gennem command prompt med "python geotag_extraction.py /sti/til/billeder"
if __name__ == "__main__":
    main()
