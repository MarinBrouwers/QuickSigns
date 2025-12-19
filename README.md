# QuickSigns

A Blender add-on for creating 3D text signs with Google Fonts integration and customizable materials.

## Features

- **Google Fonts Integration**: Search, preview, and download fonts from Google Fonts
- **3D Text Generation**: Create extruded 3D text with customizable depth and bevel
- **Material System**: Customizable materials with metallic/roughness controls
- **Easy-to-Use UI**: All controls in a dedicated sidebar panel

## Installation

1. **Locate the add-on folder**: `\QuickSigns`

2. **Install in Blender**:
   - Open Blender
   - Go to `Edit` → `Preferences` → `Add-ons`
   - Click `Install...` button
   - Navigate to `\QuickSigns`
   - Select `__init__.py`
   - Click `Install Add-on`

3. **Enable the add-on**:
   - Search for "QuickSigns" in the add-ons list
   - Check the box to enable it

4. **Access the panel**:
   - In the 3D Viewport, press `N` to open the sidebar
   - Look for the `Signs` tab

## Setup

### Get Google Fonts API Key

Your API key: `AIzaSyC0_P6INbKLWV5kUIbjk-HGkMv4XCazzG0`

(If you need a new one: Go to https://console.developers.google.com/ → Enable Google Fonts API → Create credentials)

### Enter API Key in Blender

1. Open the `Signs` tab in the sidebar
2. In the "Google Fonts API" section, paste your API key
3. The key will be saved with your Blender project

## Usage

### 1. Search and Download Fonts

1. **Search for fonts**:
   - (Optional) Enter a search term in the "Search" field
   - Click "Search Fonts" button
   - Browse the list of available fonts

2. **Download a font**:
   - Click on a font in the list to select it
   - Click "Download Font" button
   - The font will be downloaded to `QuickSigns/fonts/` and loaded into Blender

### 2. Configure Your Sign

**Text Settings Panel**:
- **Text**: Enter the text you want to create
- **Size**: Adjust the overall size of the text
- **Depth**: Control how far the text extrudes (3D depth)
- **Bevel**: Add rounded edges to the text

**Material Panel**:
- **Color**: Choose the color of your text
- **Metallic**: Make it look metallic (0 = non-metal, 1 = full metal)
- **Roughness**: Control surface roughness (0 = shiny, 1 = matte)

### 3. Create the Sign

1. Configure all settings as desired
2. Click the "Create Sign" button
3. Your 3D sign will be created at the origin (0, 0, 0)

## Tips

- **Font Preview**: The font list shows font names sorted by popularity. Click to select before downloading.
- **Material Tweaking**: After creating a sign, you can further adjust materials in the Shader Editor.
- **Multiple Signs**: Create as many signs as you want - each will be a separate object.

## Project Structure

```
QuickSigns/
├── __init__.py          # Main add-on file
├── fonts/               # Downloaded fonts stored here (created automatically)
└── README.md           # This file
```

## Troubleshooting

**"Please enter your Google Fonts API key" error**:
- Make sure you've pasted your API key in the Google Fonts API section

**"API Error: 400" or similar**:
- Check that your API key is valid
- Make sure Google Fonts API is enabled in your Google Cloud Console

**Font not appearing correctly**:
- Some fonts may have limited character sets
- Try downloading and using a different font

## Requirements

- Blender 3.0 or higher
- Internet connection (for downloading fonts)
- Google Fonts API key

## Technical Details

- **Materials**: Principled BSDF shader nodes
- **Font Format**: TrueType (.ttf)
- **API**: Google Fonts API v1
