#!/usr/bin/env python3
"""
Script to add real images to NIMC mock data.
Converts image files to base64 and updates the mock records.
"""

import base64
import json
import argparse
from pathlib import Path


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def update_mock_data(nin: str, photo_path: str = None, signature_path: str = None):
    """Update mock data with new images for specific NIN"""
    
    mock_data_path = Path("app/mock_data/nimc_records.json")
    
    # Load existing mock data
    with open(mock_data_path, 'r') as f:
        data = json.load(f)
    
    # Find the record with matching NIN
    updated = False
    for record in data["records"]:
        if record["nin"] == nin:
            if photo_path:
                record["photo"] = image_to_base64(photo_path)
                print(f"Updated photo for NIN {nin}")
                updated = True
            
            if signature_path:
                record["signature"] = image_to_base64(signature_path)
                print(f"Updated signature for NIN {nin}")
                updated = True
            
            break
    
    if not updated:
        print(f"No record found with NIN {nin}")
        return
    
    # Save updated data
    with open(mock_data_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Mock data updated successfully!")


def list_available_nins():
    """List all available NINs in mock data"""
    mock_data_path = Path("app/mock_data/nimc_records.json")
    
    with open(mock_data_path, 'r') as f:
        data = json.load(f)
    
    print("Available NINs:")
    for record in data["records"]:
        name = f"{record['firstname']} {record['surname']}"
        print(f"  {record['nin']} - {name} ({record['gender']}, {record['residence_state']})")


def main():
    parser = argparse.ArgumentParser(description="Add images to NIMC mock data")
    parser.add_argument("--list", action="store_true", help="List available NINs")
    parser.add_argument("--nin", help="NIN to update")
    parser.add_argument("--photo", help="Path to photo image file")
    parser.add_argument("--signature", help="Path to signature image file")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_nins()
    elif args.nin:
        if not args.photo and not args.signature:
            print("Error: Must provide --photo or --signature")
            return
        
        update_mock_data(args.nin, args.photo, args.signature)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
