#!/usr/bin/env python3
"""
Batch image upload script for NIMC mock data.
Uploads 25 headshot images for all mock identities.
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, List

def get_nin_mapping() -> Dict[str, str]:
    """Get mapping of NIN to name for file naming"""
    return {
        "12345678901": "adeola_ojukwu",
        "12345678902": "ibrahim_mohammed", 
        "12345678903": "funke_adebayo",
        "12345678904": "chidi_okoro",
        "12345678905": "fatima_danladi",
        "12345678906": "osayi_emwantor",
        "12345678907": "aisha_yusuf",
        "12345678908": "chukwuemeka_obi",
        "12345678909": "zainab_ali",
        "12345678910": "babatunde_adeyemi",
        "12345678911": "effiong_udo",
        "12345678912": "hauwa_musa",
        "12345678913": "emeka_okonkwo",
        "12345678914": "khadija_abdullahi",
        "12345678915": "uche_nwankwo",
        "12345678916": "sani_abdullahi",
        "12345678917": "tunde_balogun",
        "12345678918": "aisha_garba",
        "12345678919": "chika_eze",
        "12345678920": "kunle_adekunle",
        "12345678921": "etim_ekpo",
        "12345678922": "amina_suleiman",
        "12345678923": "chinedu_nwosu",
        "12345678924": "aisha_muhammad",
        "12345678925": "david_ogunleye"
    }

def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def find_matching_image(image_dir: str, name_pattern: str, extensions: List[str] = None) -> str:
    """Find image file matching name pattern"""
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.webp']
    
    image_dir_path = Path(image_dir)
    
    # Try exact match first
    for ext in extensions:
        exact_path = image_dir_path / f"{name_pattern}{ext}"
        if exact_path.exists():
            return str(exact_path)
    
    # Try partial match (case insensitive)
    for file_path in image_dir_path.iterdir():
        if file_path.suffix.lower() in extensions:
            if name_pattern.lower() in file_path.stem.lower():
                return str(file_path)
    
    return None

def batch_upload_photos(photo_dir: str = None) -> Dict[str, str]:
    """Batch upload photos for all NINs"""
    if photo_dir is None:
        photo_dir = "app/mock_data/images/photos"
    
    photo_dir_path = Path(photo_dir)
    if not photo_dir_path.exists():
        print(f"Photo directory not found: {photo_dir}")
        print(f"Please create the directory and add your images there.")
        return {}
    
    nin_mapping = get_nin_mapping()
    uploaded_images = {}
    
    print(f"Scanning for photos in: {photo_dir}")
    print(f"Found {len(list(photo_dir_path.glob('*')))} files")
    
    for nin, name_pattern in nin_mapping.items():
        image_path = find_matching_image(photo_dir, name_pattern)
        
        if image_path:
            try:
                base64_image = image_to_base64(image_path)
                uploaded_images[nin] = base64_image
                print(f"  {nin}: {name_pattern} -> {Path(image_path).name}")
            except Exception as e:
                print(f"  {nin}: Error processing {image_path} - {e}")
        else:
            print(f"  {nin}: No image found for '{name_pattern}'")
    
    return uploaded_images

def update_mock_data_with_images(photo_uploads: Dict[str, str]) -> bool:
    """Update mock data with uploaded images"""
    mock_data_path = Path("app/mock_data/nimc_records.json")
    
    try:
        # Load existing mock data
        with open(mock_data_path, 'r') as f:
            data = json.load(f)
        
        updated_count = 0
        for record in data["records"]:
            nin = record.get("nin")
            if nin in photo_uploads:
                record["photo"] = photo_uploads[nin]
                updated_count += 1
        
        # Save updated data
        with open(mock_data_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated {updated_count} records with photos")
        return True
        
    except Exception as e:
        print(f"Error updating mock data: {e}")
        return False

def create_sample_naming_guide():
    """Create a guide for naming images"""
    guide = """
# Image Naming Guide for NIMC Mock Data

Place your images in: app/mock_data/images/photos/

## Naming Convention (Recommended)
Use these exact filenames for automatic matching:

1. adeola_ojukwu.jpg (Female, Lagos)
2. ibrahim_mohammed.jpg (Male, Kano)  
3. funke_adebayo.jpg (Female, Oyo)
4. chidi_okoro.jpg (Male, Rivers)
5. fatima_danladi.jpg (Female, Plateau)
6. osayi_emwantor.jpg (Male, Edo)
7. aisha_yusuf.jpg (Female, Kaduna)
8. chukwuemeka_obi.jpg (Male, Anambra)
9. zainab_ali.jpg (Female, Borno)
10. babatunde_adeyemi.jpg (Male, Osun)
11. effiong_udo.jpg (Male, Akwa Ibom)
12. hauwa_musa.jpg (Female, Niger)
13. emeka_okonkwo.jpg (Male, Delta)
14. khadija_abdullahi.jpg (Female, Kwara)
15. uche_nwankwo.jpg (Male, Abia)
16. sani_abdullahi.jpg (Male, Borno)
17. tunde_balogun.jpg (Male, Lagos)
18. aisha_garba.jpg (Female, Kano)
19. chika_eze.jpg (Female, Enugu)
20. kunle_adekunle.jpg (Male, Oyo)
21. etim_ekpo.jpg (Male, Cross River)
22. amina_suleiman.jpg (Female, FCT)
23. chinedu_nwosu.jpg (Male, Imo)
24. aisha_muhammad.jpg (Female, Sokoto)
25. david_ogunleye.jpg (Male, Lagos)

## Alternative Naming
The system will also match partial names, so these work too:
- adeola.jpg (for Adeola Ojukwu)
- ibrahim.jpg (for Ibrahim Mohammed)
- funke.jpg (for Funke Adebayo)

## Supported Formats
- JPG, JPEG, PNG, WebP
- Recommended size: 200x200px
- Max file size: 1MB per image
"""
    
    guide_path = Path("app/mock_data/images/NAMING_GUIDE.md")
    with open(guide_path, 'w') as f:
        f.write(guide)
    
    print(f"Created naming guide: {guide_path}")

def main():
    """Main function for batch image upload"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch upload images for NIMC mock data")
    parser.add_argument("--photo-dir", default="app/mock_data/images/photos", 
                       help="Directory containing photos")
    parser.add_argument("--create-guide", action="store_true",
                       help="Create naming guide")
    parser.add_argument("--list-missing", action="store_true",
                       help="List missing images")
    
    args = parser.parse_args()
    
    if args.create_guide:
        create_sample_naming_guide()
        return
    
    # Create directories if they don't exist
    Path(args.photo_dir).mkdir(parents=True, exist_ok=True)
    Path("app/mock_data/images/signatures").mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("NIMC Mock Data - Batch Image Upload")
    print("=" * 60)
    
    # Check if directory exists and has images
    photo_dir_path = Path(args.photo_dir)
    if not photo_dir_path.exists():
        print(f"Photo directory not found: {args.photo_dir}")
        print("Creating directory...")
        photo_dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Please place your images in: {args.photo_dir}")
        create_sample_naming_guide()
        return
    
    image_files = list(photo_dir_path.glob("*"))
    image_files = [f for f in image_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
    
    if len(image_files) == 0:
        print(f"No images found in: {args.photo_dir}")
        print("Please add your headshot images and run this script again.")
        create_sample_naming_guide()
        return
    
    print(f"Found {len(image_files)} images in directory")
    
    # Batch upload photos
    photo_uploads = batch_upload_photos(args.photo_dir)
    
    if photo_uploads:
        print(f"\nSuccessfully processed {len(photo_uploads)} photos")
        
        # Update mock data
        if update_mock_data_with_images(photo_uploads):
            print("Mock data updated successfully!")
            print("\nNext steps:")
            print("1. Restart the backend server")
            print("2. Test verification in frontend")
            print("3. Images will appear in verification results")
        else:
            print("Failed to update mock data")
    else:
        print("No photos were processed")
        create_sample_naming_guide()

if __name__ == "__main__":
    main()
