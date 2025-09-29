# Deployment Guide - Introduction to Cancer Biology App

This application has been configured for Linux deployment with pre-loaded "Introduction to Cancer Biology" content.

## Changes Made for Deployment

### ✅ **Removed Windows Dependencies**
- **PowerPoint automation** (win32com, pythoncom) - disabled for Linux compatibility
- **Whisper transcription** - disabled, uses pre-transcribed content instead
- **Windows-specific libraries** removed from requirements.txt

### ✅ **Pre-loaded Content**
- **27 Cancer Biology slides** automatically loaded from `uploads/ppt/fixed/picture/`
- **Complete transcription** automatically loaded from `transcriptions/turbo_transcription_Introduction to Cancer Biology.txt`
- **Default student profile** configured for Cancer Biology learning

### ✅ **No Upload Required**
- File upload functionality replaced with status indicators
- Content loads automatically when app starts
- No user interaction needed to access materials

## File Structure

```
├── uploads/ppt/fixed/picture/          # Cancer Biology slides (27 slides)
│   ├── Slide_1 Genetics of Cancer.jpg
│   ├── Slide_2 Genetics of Cancer.jpg
│   └── ... (25 more slides)
├── transcriptions/                     # Pre-transcribed audio
│   └── turbo_transcription_Introduction to Cancer Biology.txt
├── Gemini_UI.py                       # Main application (modified)
├── requirements.txt                   # Updated dependencies
└── DEPLOYMENT_GUIDE.md               # This file
```

## Deployment Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Google Gemini API**
   - Set your Google Gemini API key as environment variable:
     ```bash
     export GOOGLE_API_KEY="your_api_key_here"
     ```

3. **Run the Application**
   ```bash
   streamlit run Gemini_UI.py
   ```

4. **Verify Content Loading**
   - App should automatically load 27 slides
   - Transcription should be available
   - No file uploads required

## Key Features

- **✅ Linux Compatible**: No Windows-specific dependencies
- **✅ Pre-loaded Content**: Cancer Biology slides and transcription ready
- **✅ Default Profile**: Optimized for Cancer Biology learning
- **✅ No Upload UI**: Streamlined interface for deployment
- **✅ Lightweight**: Removed heavy ML dependencies

## Environment Variables Required

- `GOOGLE_API_KEY`: Your Google Gemini API key

## Troubleshooting

**Content Not Loading?**
- Verify slide files exist in `uploads/ppt/fixed/picture/`
- Check transcription file exists: `transcriptions/turbo_transcription_Introduction to Cancer Biology.txt`
- Enable debug logs in the app to see loading status

**API Issues?**
- Ensure GOOGLE_API_KEY is set correctly
- Check Google Gemini API quota and permissions

## Content Customization

To change to different learning content:

1. **Replace slides**: Add new slide images to `uploads/ppt/fixed/picture/`
2. **Replace transcription**: Update the transcription file in `transcriptions/`
3. **Update references**: Modify the file paths in the `main()` function (lines ~394-403)

The app will automatically detect and load the new content on restart.