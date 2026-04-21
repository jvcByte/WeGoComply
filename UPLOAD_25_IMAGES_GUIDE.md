# Upload 25 Headshot Images Guide

## Quick Setup

I've created everything you need to upload 25 headshot images for all the NIMC mock identities.

## Step 1: Where to Place Your Images

**Directory**: `backend/app/mock_data/images/photos/`

This directory has already been created for you. Just place your 25 headshot images there.

## Step 2: Image Naming (Easy Options)

### Option A: Simple Names (Easiest)
Just name your files with the first name:
```
adeola.jpg
ibrahim.jpg  
funke.jpg
chidi.jpg
fatima.jpg
osayi.jpg
aisha.jpg
chukwuemeka.jpg
zainab.jpg
babatunde.jpg
effiong.jpg
hauwa.jpg
emeka.jpg
khadija.jpg
uche.jpg
sani.jpg
tunde.jpg
aisha2.jpg (for second Aisha)
chika.jpg
kunle.jpg
etim.jpg
amina.jpg
chinedu.jpg
zainab2.jpg (for second Zainab)
david.jpg
```

### Option B: Full Names (More Specific)
```
adeola_ojukwu.jpg
ibrahim_mohammed.jpg
funke_adebayo.jpg
chidi_okoro.jpg
fatima_danladi.jpg
osayi_emwantor.jpg
aisha_yusuf.jpg
chukwuemeka_obi.jpg
zainab_ali.jpg
babatunde_adeyemi.jpg
effiong_udo.jpg
hauwa_musa.jpg
emeka_okonkwo.jpg
khadija_abdullahi.jpg
uche_nwankwo.jpg
sani_abdullahi.jpg
tunde_balogun.jpg
aisha_garba.jpg
chika_eze.jpg
kunle_adekunle.jpg
etim_ekpo.jpg
amina_suleiman.jpg
chinedu_nwosu.jpg
aisha_muhammad.jpg
david_ogunleye.jpg
```

## Step 3: Upload Your Images

### Method 1: Drag and Drop
1. Open your file manager
2. Navigate to: `WeGoComply/backend/app/mock_data/images/photos/`
3. Drag and drop all 25 images there

### Method 2: Command Line
```bash
# Navigate to the photos directory
cd backend/app/mock_data/images/photos/

# Copy images from your location
cp /path/to/your/images/*.jpg .
# or
cp /path/to/your/images/*.png .
```

## Step 4: Run the Batch Upload Script

Once your images are in place, run this command:

```bash
cd backend
source venv/bin/activate
python scripts/batch_upload_images.py
```

The script will:
- Automatically find and match your images to the 25 identities
- Convert them to base64 format
- Update the mock data file
- Show you which images were successfully uploaded

## Step 5: Test Your Images

1. **Restart the backend** (if it's running)
2. **Open the frontend**: http://localhost:5173
3. **Go to KYC Verification**
4. **Test any of these NINs**:

| NIN | Name | Image Filename |
|-----|------|----------------|
| 12345678901 | Adeola Ojukwu | adeola.jpg or adeola_ojukwu.jpg |
| 12345678902 | Ibrahim Mohammed | ibrahim.jpg or ibrahim_mohammed.jpg |
| 12345678903 | Funke Adebayo | funke.jpg or funke_adebayo.jpg |
| 12345678904 | Chidi Okoro | chidi.jpg or chidi_okoro.jpg |
| 12345678905 | Fatima Danladi | fatima.jpg or fatima_danladi.jpg |

## What You'll See

After successful upload and testing:
- Each verified identity will show their headshot photo
- Photos appear as 64x64px thumbnails in the results
- All 25 identities will have unique photos
- The system maintains the mock functionality

## Image Requirements

- **Format**: JPG, PNG, JPEG, or WebP
- **Size**: 200x200px recommended (any size works, will be resized)
- **File size**: Under 1MB each
- **Content**: Headshot photos of people (matching the demographic data)

## Troubleshooting

### Images Not Found
- Check that images are in the correct directory
- Verify filenames match the naming convention
- Run the script again to see matching results

### Script Errors
```bash
# Check if directory exists
ls -la backend/app/mock_data/images/photos/

# Check file permissions
chmod 644 backend/app/mock_data/images/photos/*.jpg
```

### Images Not Displaying
1. Restart the backend server
2. Clear browser cache
3. Test with a different NIN

## Quick Test Command

To test if your images are working without the full frontend:

```bash
cd backend
source venv/bin/activate
python -c "
from app.services.identity.providers.nimc_mock_provider import NIMCMockProvider
provider = NIMCMockProvider()
record = provider._find_record_by_nin('12345678901')
if record and record.photo:
    print('Photo found! Length:', len(record.photo))
else:
    print('No photo found')
"
```

## Success Indicators

When everything works correctly:
- Script reports: "Successfully processed X photos"
- Backend shows: "Mock data updated successfully!"
- Frontend displays photos in verification results
- All 25 NINs show unique headshots

The system is now ready for your 25 headshot images! Just place them in the directory and run the batch upload script.
