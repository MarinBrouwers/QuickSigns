bl_info = {
    "name": "QuickSigns",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Signs",
    "description": "Create 3D text signs with Google Fonts integration",
    "category": "3D View",
}

import bpy
import os
import tempfile
import json
import urllib.request
import urllib.error
from bpy.props import (
    StringProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
    CollectionProperty,
    IntProperty,
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
    UIList,
)


# ============================================================================
# Helper Functions
# ============================================================================

def check_online_access(operator):
    """Check if online access is enabled in user preferences"""
    if not bpy.context.preferences.system.use_online_access:
        operator.report({'ERROR'}, "Online access is disabled. Enable it in Edit -> Preferences -> System -> Network -> Allow Online Access")
        return False
    return True


# ============================================================================
# Google Fonts API Integration
# ============================================================================

class SIGNS_OT_SearchFonts(Operator):
    """Search Google Fonts"""
    bl_idname = "signs.search_fonts"
    bl_label = "Search Fonts"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check online access permission
        if not check_online_access(self):
            return {'CANCELLED'}

        props = context.scene.signs_props
        api_key = props.google_fonts_api_key

        if not api_key:
            self.report({'ERROR'}, "Please enter your Google Fonts API key")
            return {'CANCELLED'}

        try:
            url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={api_key}&sort=popularity"

            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                fonts = data.get('items', [])

                # Clear existing font list
                props.font_list.clear()

                # Get filter values
                search_query = props.font_search_query.lower()
                category_filter = props.font_category_filter

                for font in fonts:
                    # Filter by search query
                    if search_query and search_query not in font['family'].lower():
                        continue

                    # Filter by category
                    font_category = font.get('category', 'sans-serif')
                    if category_filter != 'ALL' and font_category != category_filter:
                        continue

                    item = props.font_list.add()
                    item.name = font['family']
                    item.family = font['family']
                    item.category = font_category

                    # Store the regular variant URL
                    if 'files' in font and 'regular' in font['files']:
                        item.url = font['files']['regular']

                self.report({'INFO'}, f"Found {len(props.font_list)} fonts")
                return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}


class SIGNS_OT_DownloadFont(Operator):
    """Download and install selected font"""
    bl_idname = "signs.download_font"
    bl_label = "Download Font"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check online access permission
        if not check_online_access(self):
            return {'CANCELLED'}

        props = context.scene.signs_props

        if props.font_list_index < 0 or props.font_list_index >= len(props.font_list):
            self.report({'ERROR'}, "No font selected")
            return {'CANCELLED'}

        selected_font = props.font_list[props.font_list_index]

        if not selected_font.url:
            self.report({'ERROR'}, "Font URL not available")
            return {'CANCELLED'}

        try:
            # Create fonts directory if it doesn't exist
            fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
            os.makedirs(fonts_dir, exist_ok=True)

            # Download font
            with urllib.request.urlopen(selected_font.url, timeout=30) as response:
                font_data = response.read()

                # Save font file
                font_filename = f"{selected_font.family.replace(' ', '_')}.ttf"
                font_path = os.path.join(fonts_dir, font_filename)

                with open(font_path, 'wb') as f:
                    f.write(font_data)

                # Load font into Blender
                if os.path.exists(font_path):
                    bpy.data.fonts.load(font_path)
                    props.selected_font_path = font_path
                    self.report({'INFO'}, f"Downloaded and loaded: {selected_font.family}")
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, "Failed to save font file")
                    return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error downloading font: {str(e)}")
            return {'CANCELLED'}


class SIGNS_OT_PreviewFont(Operator):
    """Preview selected font with sample text"""
    bl_idname = "signs.preview_font"
    bl_label = "Preview Font"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.signs_props

        if props.font_list_index < 0 or props.font_list_index >= len(props.font_list):
            self.report({'ERROR'}, "No font selected")
            return {'CANCELLED'}

        selected_font = props.font_list[props.font_list_index]

        # Download font first if not already downloaded
        font_filename = f"{selected_font.family.replace(' ', '_')}.ttf"
        fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        font_path = os.path.join(fonts_dir, font_filename)

        if not os.path.exists(font_path):
            # Check online access permission before downloading
            if not check_online_access(self):
                return {'CANCELLED'}

            # Download the font
            try:
                os.makedirs(fonts_dir, exist_ok=True)
                with urllib.request.urlopen(selected_font.url, timeout=30) as response:
                    font_data = response.read()
                    with open(font_path, 'wb') as f:
                        f.write(font_data)
            except Exception as e:
                self.report({'ERROR'}, f"Error downloading font: {str(e)}")
                return {'CANCELLED'}

        # Create preview text object
        try:
            # Delete existing preview if it exists
            if "Font_Preview" in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects["Font_Preview"], do_unlink=True)

            # Create new preview text
            bpy.ops.object.text_add(location=(0, 0, 0))
            preview_obj = context.active_object
            preview_obj.name = "Font_Preview"

            preview_text = preview_obj.data
            preview_text.body = selected_font.family
            preview_text.size = 0.5
            preview_text.align_x = 'CENTER'

            # Load and apply font
            font = bpy.data.fonts.load(font_path, check_existing=True)
            preview_text.font = font

            self.report({'INFO'}, f"Preview: {selected_font.family}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error creating preview: {str(e)}")
            return {'CANCELLED'}


# ============================================================================
# 3D Text Sign Generation
# ============================================================================

class SIGNS_OT_RandomName(Operator):
    """Generate a random store name"""
    bl_idname = "signs.random_name"
    bl_label = "Random Name"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import random

        # Word lists for store names
        adjectives = [
            "Golden", "Silver", "Royal", "Grand", "Elite", "Prime", "Supreme",
            "Classic", "Modern", "Urban", "Rustic", "Vintage", "Fresh", "Bright",
            "Happy", "Cozy", "Swift", "Noble", "Lucky", "Magic", "Mystic",
            "Crystal", "Diamond", "Pearl", "Sunset", "Sunrise", "Midnight",
            "Blue", "Green", "Red", "Cosmic", "Stellar", "Azure", "Crimson"
        ]

        nouns = [
            "Coffee", "Bakery", "Bistro", "Cafe", "Deli", "Kitchen", "Grill",
            "Market", "Shop", "Store", "Boutique", "Gallery", "Studio", "Bar",
            "Lounge", "Pizza", "Burger", "Tacos", "Sushi", "Noodles", "Bowl",
            "Plate", "Fork", "Spoon", "Cup", "Mug", "Bean", "Brew", "Slice",
            "Corner", "Place", "Spot", "House", "Depot", "Emporium", "Trading"
        ]

        # Generate random name
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        name = f"{adj} {noun}"

        # Set the text
        props = context.scene.signs_props
        props.sign_text = name

        self.report({'INFO'}, f"Generated: {name}")
        return {'FINISHED'}


class SIGNS_OT_CreateSign(Operator):
    """Create a 3D text sign with materials"""
    bl_idname = "signs.create_sign"
    bl_label = "Create Sign"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.signs_props

        if not props.sign_text:
            self.report({'ERROR'}, "Please enter text for the sign")
            return {'CANCELLED'}

        # Create text object
        bpy.ops.object.text_add(location=(0, 0, 0))
        text_obj = context.active_object
        text_obj.name = f"Sign_{props.sign_text[:10]}"

        # Set text data
        text_data = text_obj.data
        text_data.body = props.sign_text
        text_data.size = props.text_size
        text_data.extrude = props.text_extrude
        text_data.bevel_depth = props.text_bevel

        # Apply font if one is selected
        if props.selected_font_path and os.path.exists(props.selected_font_path):
            try:
                font = bpy.data.fonts.load(props.selected_font_path, check_existing=True)
                text_data.font = font
            except:
                pass

        # Create material
        self.create_material(text_obj, props)

        self.report({'INFO'}, f"Created sign: {props.sign_text}")
        return {'FINISHED'}

    def create_material(self, obj, props):
        """Create and assign material"""
        # Create material
        mat = bpy.data.materials.new(name="Sign_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (*props.text_color, 1.0)
            bsdf.inputs['Metallic'].default_value = props.text_metallic
            bsdf.inputs['Roughness'].default_value = props.text_roughness

        # Assign material
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


# ============================================================================
# Property Definitions
# ============================================================================

def update_auto_preview(self, context):
    """Handle auto-preview toggle"""
    if not self.auto_preview:
        # Delete preview when disabled
        if "Font_Preview" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["Font_Preview"], do_unlink=True)


def update_font_preview(self, context):
    """Auto-update font preview when selection changes"""
    if not self.auto_preview:
        return

    if self.font_list_index < 0 or self.font_list_index >= len(self.font_list):
        return

    # Check online access permission
    if not bpy.context.preferences.system.use_online_access:
        return

    selected_font = self.font_list[self.font_list_index]

    # Download font if not already downloaded
    font_filename = f"{selected_font.family.replace(' ', '_')}.ttf"
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    font_path = os.path.join(fonts_dir, font_filename)

    if not os.path.exists(font_path):
        try:
            os.makedirs(fonts_dir, exist_ok=True)
            with urllib.request.urlopen(selected_font.url, timeout=30) as response:
                font_data = response.read()
                with open(font_path, 'wb') as f:
                    f.write(font_data)
        except:
            return

    # Create/update preview
    try:
        if "Font_Preview" in bpy.data.objects:
            preview_obj = bpy.data.objects["Font_Preview"]
        else:
            bpy.ops.object.text_add(location=(0, 0, 0))
            preview_obj = context.view_layer.objects.active
            preview_obj.name = "Font_Preview"

        preview_text = preview_obj.data
        preview_text.body = self.preview_sample_text if self.preview_sample_text else selected_font.family
        preview_text.size = 0.5
        preview_text.align_x = 'CENTER'

        # Load and apply font
        font = bpy.data.fonts.load(font_path, check_existing=True)
        preview_text.font = font
    except:
        pass


class FontListItem(PropertyGroup):
    """Property group for font list items"""
    family: StringProperty(name="Font Family", default="")
    category: StringProperty(name="Category", default="")
    url: StringProperty(name="Download URL", default="")


class SignsProperties(PropertyGroup):
    """Main properties for the Signs add-on"""

    # Auto-preview settings
    auto_preview: BoolProperty(
        name="Auto Preview",
        description="Automatically preview fonts when selected from the list",
        default=False,
        update=update_auto_preview
    )

    preview_sample_text: StringProperty(
        name="Sample Text",
        description="Text to display in font preview",
        default="AaBbCc 123"
    )

    # Google Fonts API
    google_fonts_api_key: StringProperty(
        name="API Key",
        description="Your Google Fonts API key",
        default="",
        subtype='PASSWORD'
    )

    font_search_query: StringProperty(
        name="Search",
        description="Search for fonts by name",
        default=""
    )

    font_category_filter: EnumProperty(
        name="Style",
        description="Filter fonts by style/category",
        items=[
            ('ALL', "All Styles", "Show all fonts"),
            ('serif', "Serif", "Classic, traditional fonts with decorative strokes"),
            ('sans-serif', "Sans Serif", "Modern, clean fonts without decorative strokes"),
            ('display', "Display/Vintage", "Decorative, vintage, and bold display fonts"),
            ('handwriting', "Handwritten", "Handwritten and script fonts"),
            ('monospace', "Monospace", "Fixed-width fonts (typewriter style)"),
        ],
        default='ALL'
    )

    font_list: CollectionProperty(type=FontListItem)
    font_list_index: IntProperty(update=update_font_preview)

    selected_font_path: StringProperty(
        name="Font Path",
        description="Path to the selected font file",
        default="",
        subtype='FILE_PATH'
    )

    # Sign Text Properties
    sign_text: StringProperty(
        name="Text",
        description="Text for the sign",
        default="SIGN"
    )

    text_size: FloatProperty(
        name="Size",
        description="Text size",
        default=1.0,
        min=0.01,
        max=100.0
    )

    text_extrude: FloatProperty(
        name="Depth",
        description="Text extrusion depth",
        default=0.1,
        min=0.0,
        max=10.0
    )

    text_bevel: FloatProperty(
        name="Bevel",
        description="Text bevel depth",
        default=0.01,
        min=0.0,
        max=1.0
    )

    # Material Properties
    text_color: FloatVectorProperty(
        name="Text Color",
        subtype='COLOR',
        default=(0.8, 0.1, 0.1),
        min=0.0,
        max=1.0
    )

    text_metallic: FloatProperty(
        name="Metallic",
        default=0.0,
        min=0.0,
        max=1.0
    )

    text_roughness: FloatProperty(
        name="Roughness",
        default=0.5,
        min=0.0,
        max=1.0
    )


# ============================================================================
# UI List for Fonts
# ============================================================================

class SIGNS_UL_FontList(UIList):
    """UI List for displaying fonts"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=item.family, icon='FONT_DATA')
            row.label(text=item.category, icon='SMALL_CAPS')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.family, icon='FONT_DATA')


# ============================================================================
# UI Panels
# ============================================================================

class SIGNS_PT_MainPanel(Panel):
    """Main panel for QuickSigns"""
    bl_label = "QuickSigns"
    bl_idname = "SIGNS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Signs'

    def draw(self, context):
        layout = self.layout
        props = context.scene.signs_props

        # API Key Section
        box = layout.box()
        box.label(text="Google Fonts API", icon='WORLD')
        box.prop(props, "google_fonts_api_key")

        # Font Search Section
        box = layout.box()
        box.label(text="Font Library", icon='FONT_DATA')
        box.prop(props, "font_search_query", icon='VIEWZOOM')
        box.prop(props, "font_category_filter", text="")
        box.operator("signs.search_fonts", icon='FILE_REFRESH')

        # Font List
        box.template_list(
            "SIGNS_UL_FontList",
            "",
            props,
            "font_list",
            props,
            "font_list_index",
            rows=5
        )

        # Auto-preview settings
        box.prop(props, "auto_preview", toggle=True)
        if props.auto_preview:
            box.prop(props, "preview_sample_text", text="", icon='SMALL_CAPS')

        row = box.row(align=True)
        row.operator("signs.preview_font", icon='HIDE_OFF', text="Manual Preview")
        row.operator("signs.download_font", icon='IMPORT')

        # Current Font Display
        if props.selected_font_path:
            box.label(text=f"Current: {os.path.basename(props.selected_font_path)}", icon='CHECKMARK')


class SIGNS_PT_TextPanel(Panel):
    """Panel for text settings"""
    bl_label = "Text Settings"
    bl_idname = "SIGNS_PT_text_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Signs'

    def draw(self, context):
        layout = self.layout
        props = context.scene.signs_props

        box = layout.box()
        row = box.row(align=True)
        row.prop(props, "sign_text")
        row.operator("signs.random_name", text="", icon='FILE_REFRESH')
        box.prop(props, "text_size")
        box.prop(props, "text_extrude")
        box.prop(props, "text_bevel")


class SIGNS_PT_MaterialsPanel(Panel):
    """Panel for material settings"""
    bl_label = "Material"
    bl_idname = "SIGNS_PT_materials_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Signs'

    def draw(self, context):
        layout = self.layout
        props = context.scene.signs_props

        box = layout.box()
        box.prop(props, "text_color")
        box.prop(props, "text_metallic")
        box.prop(props, "text_roughness")


class SIGNS_PT_CreatePanel(Panel):
    """Panel for creating the sign"""
    bl_label = "Create Sign"
    bl_idname = "SIGNS_PT_create_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Signs'

    def draw(self, context):
        layout = self.layout
        layout.operator("signs.create_sign", icon='ADD', text="Create Sign")


# ============================================================================
# Registration
# ============================================================================

classes = (
    FontListItem,
    SignsProperties,
    SIGNS_OT_SearchFonts,
    SIGNS_OT_DownloadFont,
    SIGNS_OT_PreviewFont,
    SIGNS_OT_RandomName,
    SIGNS_OT_CreateSign,
    SIGNS_UL_FontList,
    SIGNS_PT_MainPanel,
    SIGNS_PT_TextPanel,
    SIGNS_PT_MaterialsPanel,
    SIGNS_PT_CreatePanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.signs_props = bpy.props.PointerProperty(type=SignsProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.signs_props


if __name__ == "__main__":
    register()
