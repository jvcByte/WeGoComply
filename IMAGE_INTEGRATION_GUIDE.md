# Image Integration Guide for NIMC Mock

## Overview

The NIMC mock system now supports real images for photos and signatures. You can add your own images to the mock records and they will be displayed in the frontend verification results.

## Quick Start

### Option 1: Use the Script (Recommended)

1. **Place your images** in the backend directory:
   ```
   backend/
   - my_photo.jpg
   - my_signature.png
   ```

2. **List available NINs**:
   ```bash
   cd backend
   source venv/bin/activate
   python scripts/add_image_to_mock.py --list
   ```

3. **Add images to a specific NIN**:
   ```bash
   # Add photo only
   python scripts/add_image_to_mock.py --nin 12345678901 --photo my_photo.jpg
   
   # Add signature only
   python scripts/add_image_to_mock.py --nin 12345678901 --signature my_signature.png
   
   # Add both
   python scripts/add_image_to_mock.py --nin 12345678901 --photo my_photo.jpg --signature my_signature.png
   ```

### Option 2: Manual Update

1. **Convert your image to base64**:
   ```bash
   # Using base64 command
   base64 -w 0 my_photo.jpg > photo_base64.txt
   
   # Or use Python
   python -c "
   import base64
   with open('my_photo.jpg', 'rb') as f:
       print(base64.b64encode(f.read()).decode())
   "
   ```

2. **Update the JSON file**:
   - Open `backend/app/mock_data/nimc_records.json`
   - Find the record with your target NIN
   - Replace the `photo` and/or `signature` fields with your base64 string

## Image Requirements

- **Format**: PNG, JPG, JPEG
- **Size**: Under 1MB recommended
- **Dimensions**: 
  - Photo: 200x200px recommended
  - Signature: 300x100px recommended
- **Quality**: Clear and readable

## Testing Images

### Step 1: Add Your Image
```bash
cd backend
python scripts/add_image_to_mock.py --nin 12345678901 --photo /path/to/your/photo.jpg
```

### Step 2: Restart Backend
```bash
# Stop current backend (Ctrl+C)
source venv/bin/activate
python main.py
```

### Step 3: Test in Frontend
1. Open http://localhost:5173
2. Go to KYC Verification
3. Use NIN: `12345678901`, First Name: `Adeola`, Last Name: `Ojukwu`, DOB: `15/03/1985`
4. Click "Verify Identity"
5. Look for the photo and signature in the results

## Frontend Display

Images will appear in the verification results as:
- **Photo**: 64x64px rounded thumbnail
- **Signature**: 128x64px with white background

## Available Test NINs

Use these NINs to add your images:

| NIN | Name | Gender | State |
|-----|------|--------|-------|
| 12345678901 | Adeola Ojukwu | Female | Lagos |
| 12345678902 | Ibrahim Mohammed | Male | Kano |
| 12345678903 | Funke Adebayo | Female | Oyo |
| 12345678904 | Chidi Okoro | Male | Rivers |
| 12345678905 | Fatima Danladi | Female | Plateau |
| 12345678906 | Osayi Emwantor | Male | Edo |
| 12345678907 | Aisha Yusuf | Female | Kaduna |
| 12345678908 | Chukwuemeka Obi | Male | Anambra |
| 12345678909 | Zainab Ali | Female | Borno |
| 12345678910 | Babatunde Adeyemi | Male | Osun |

## Troubleshooting

### Image Not Showing
1. Check if base64 string is valid
2. Verify image format is supported
3. Ensure backend is restarted after updating mock data

### Base64 Issues
```bash
# Test if base64 is valid
echo "your_base64_string" | base64 -d > test_output.jpg
```

### Large Images
- Compress images before adding
- Use appropriate dimensions
- Keep file size under 1MB

## Advanced Usage

### Bulk Image Updates
Create a script to update multiple records:

```python
import json
import base64
from pathlib import Path

def bulk_update_images():
    # Load mock data
    with open("app/mock_data/nimc_records.json", 'r') as f:
        data = json.load(f)
    
    # Update each record
    for record in data["records"]:
        # Add your logic here
        pass
    
    # Save updated data
    with open("app/mock_data/nimc_records.json", 'w') as f:
        json.dump(data, f, indent=2)
```

### Custom Image Generation
Use Python to generate placeholder images:

```python
from PIL import Image, ImageDraw
import base64
import io

def create_placeholder_image(width, height, text):
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()
```

## API Integration

The images are now included in the unified API response:

```json
{
  "identity": {
    "photo": "base64_encoded_image_string",
    "signature": "base64_encoded_signature_string"
  }
}
```

Frontend automatically displays these as base64 data URLs.
