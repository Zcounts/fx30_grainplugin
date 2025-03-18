bl_info = {
    "name": "FX30 Grain Match",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 3, 0),  # Updated for Blender 4.3
    "location": "Node Editor > Add > Output > FX30 Grain Match",
    "description": "Match FX30 ISO grain structure for compositing",
    "category": "Node",
}

import bpy
import numpy as np
from bpy.types import Node, NodeSocket, NodeTree, PropertyGroup
from bpy.props import FloatProperty, EnumProperty, PointerProperty, StringProperty, BoolProperty

# Define the ISO presets for FX30
ISO_PRESETS = [
    ("80", "ISO 80", "Sony FX30 ISO 80 grain structure"),
    ("100", "ISO 100", "Sony FX30 ISO 100 grain structure"),
    ("200", "ISO 200", "Sony FX30 ISO 200 grain structure"),
    ("400", "ISO 400", "Sony FX30 ISO 400 grain structure"),
    ("800", "ISO 800", "Sony FX30 ISO 800 grain structure"),
    ("1600", "ISO 1600", "Sony FX30 ISO 1600 grain structure"),
    ("3200", "ISO 3200", "Sony FX30 ISO 3200 grain structure"),
    ("6400", "ISO 6400", "Sony FX30 ISO 6400 grain structure"),
    ("12800", "ISO 12800", "Sony FX30 ISO 12800 grain structure"),
    ("25600", "ISO 25600", "Sony FX30 ISO 25600 grain structure"),
    ("32000", "ISO 32000", "Sony FX30 ISO 32000 grain structure"),
    ("64000", "ISO 64000", "Sony FX30 ISO 64000 grain structure"),
    ("102400", "ISO 102400", "Sony FX30 ISO 102400 grain structure"),
]

# Refined grain structure parameters based on FX30 characteristics
# Format: (intensity, size, roughness, color_influence, luma_influence, chroma_bias)
GRAIN_PARAMETERS = {
    # Base ISO - Very clean with minimal grain
    "80": (0.08, 0.32, 0.60, 0.03, 0.95, 0.02),
    "100": (0.10, 0.35, 0.62, 0.04, 0.94, 0.03),
    
    # Low ISO - Still clean with slight grain in shadows
    "200": (0.15, 0.40, 0.65, 0.05, 0.92, 0.04),
    "400": (0.22, 0.45, 0.68, 0.07, 0.90, 0.06),
    
    # Medium ISO - Visible grain, still acceptable for professional work
    "800": (0.35, 0.52, 0.72, 0.09, 0.87, 0.08),
    "1600": (0.48, 0.58, 0.76, 0.12, 0.83, 0.11),
    
    # High ISO - More pronounced grain with color noise appearing
    "3200": (0.65, 0.64, 0.80, 0.16, 0.78, 0.15),
    "6400": (0.85, 0.70, 0.84, 0.21, 0.72, 0.20),
    
    # Very high ISO - Significant grain and noise
    "12800": (1.15, 0.78, 0.88, 0.28, 0.65, 0.26),
    "25600": (1.40, 0.84, 0.92, 0.36, 0.58, 0.32),
    
    # Extreme ISO - Heavy noise
    "32000": (1.65, 0.88, 0.94, 0.42, 0.52, 0.38),
    "64000": (1.95, 0.92, 0.96, 0.48, 0.45, 0.46),
    "102400": (2.30, 0.96, 0.98, 0.55, 0.38, 0.52),
}

# Camera-specific ISO settings
class FX30GrainCameraSettings(PropertyGroup):
    iso: EnumProperty(
        name="ISO Setting",
        description="ISO setting for this camera",
        items=ISO_PRESETS,
        default="800"
    )
    
    strength_multiplier: FloatProperty(
        name="Strength Multiplier",
        description="Fine-tune the grain strength",
        default=1.0,
        min=0.0,
        max=2.0
    )
    
    shadow_boost: FloatProperty(
        name="Shadow Grain Boost",
        description="Increase grain in shadows (FX30 characteristic)",
        default=1.2,
        min=1.0,
        max=2.0
    )
    
    highlight_suppress: FloatProperty(
        name="Highlight Grain Reduction",
        description="Reduce grain in highlights (FX30 characteristic)",
        default=0.6,
        min=0.1,
        max=1.0
    )

# Register camera property
def register_camera_property():
    bpy.types.Camera.fx30_grain = PointerProperty(type=FX30GrainCameraSettings)

# FX30 Grain Pattern Generator
class FX30GrainPattern:
    def __init__(self, iso="800", seed=1):
        self.iso = iso
        self.seed = seed
        self.parameters = GRAIN_PARAMETERS.get(iso, GRAIN_PARAMETERS["800"])
        
    def generate_pattern(self, width, height):
        np.random.seed(self.seed)
        
        intensity, size, roughness, color_influence, luma_influence, chroma_bias = self.parameters
        
        # Generate base luminance noise (mostly monochromatic)
        luma_noise = np.random.normal(0, 1, (height, width))
        
        # Generate color noise components (appears more at higher ISOs)
        r_noise = np.random.normal(0, 1, (height, width)) * color_influence * 1.2
        g_noise = np.random.normal(0, 1, (height, width)) * color_influence * 0.8
        b_noise = np.random.normal(0, 1, (height, width)) * color_influence * 1.4
        
        return {
            'luma': luma_noise * intensity * luma_influence,
            'red': r_noise * intensity * (1 - luma_influence),
            'green': g_noise * intensity * (1 - luma_influence),
            'blue': b_noise * intensity * (1 - luma_influence),
            'size': size,
            'roughness': roughness,
            'chroma_bias': chroma_bias
        }

# Node for the compositor
class FX30GrainMatchNode(Node):
    bl_idname = "FX30GrainMatchNodeType"
    bl_label = "FX30 Grain Match"
    bl_icon = "NODETREE"
    
    camera_override: EnumProperty(
        name="Camera Override",
        description="Select which camera's settings to use (or None for active camera)",
        items=lambda self, context: [(obj.name, obj.name, "") for obj in bpy.data.objects if obj.type == 'CAMERA'] + [("NONE", "Active Camera", "")],
        default="NONE"
    )
    
    seed: FloatProperty(
        name="Seed",
        description="Random seed for grain pattern",
        default=1.0,
        min=0.0,
        max=1000.0
    )
    
    custom_iso: EnumProperty(
        name="Custom ISO",
        description="ISO setting to use if not using camera settings",
        items=ISO_PRESETS,
        default="800"
    )
    
    use_camera_settings: BoolProperty(
        name="Use Camera Settings",
        description="Use ISO settings from the camera properties",
        default=True
    )
    
    shadow_boost: FloatProperty(
        name="Shadow Grain Boost",
        description="Increase grain in shadows (FX30 characteristic)",
        default=1.2,
        min=1.0,
        max=2.0
    )
    
    highlight_suppress: FloatProperty(
        name="Highlight Grain Reduction",
        description="Reduce grain in highlights (FX30 characteristic)",
        default=0.6,
        min=0.1,
        max=1.0
    )
    
    def init(self, context):
        # Input for the image to add grain to
        self.inputs.new('NodeSocketColor', "Image")
        self.inputs.new('NodeSocketFloat', "Shadow Mask")
        
        # Output separated passes for compositing flexibility
        self.outputs.new('NodeSocketColor', "Combined")
        self.outputs.new('NodeSocketColor', "Grain Only")
        self.outputs.new('NodeSocketColor', "Color Noise")
        self.outputs.new('NodeSocketFloat', "Luma Noise")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "use_camera_settings")
        
        if self.use_camera_settings:
            layout.prop(self, "camera_override")
        else:
            layout.prop(self, "custom_iso")
        
        layout.prop(self, "seed")
        
        col = layout.column(heading="Advanced")
        col.prop(self, "shadow_boost")
        col.prop(self, "highlight_suppress")
    
    def update(self):
        pass

# Custom node group for the compositor implementation
class FX30GrainMatchGroup(bpy.types.NodeCustomGroup):
    bl_name = "FX30GrainMatchGroup"
    bl_label = "FX30 Grain Match"
    
    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and context.space_data.tree_type == 'CompositorNodeTree'
    
    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(type='CompositorNodeTree', name="FX30 Grain Match")
        
        # Create input and output nodes
        input_node = self.node_tree.nodes.new('NodeGroupInput')
        output_node = self.node_tree.nodes.new('NodeGroupOutput')
        
        # Create the necessary interface
        self.node_tree.inputs.new('NodeSocketColor', "Image")
        self.node_tree.inputs.new('NodeSocketFloat', "Shadow Mask")
        
        self.node_tree.outputs.new('NodeSocketColor', "Combined")
        self.node_tree.outputs.new('NodeSocketColor', "Grain Only")
        self.node_tree.outputs.new('NodeSocketColor', "Color Noise")
        self.node_tree.outputs.new('NodeSocketFloat', "Luma Noise")
        
        # Position nodes
        input_node.location = (-300, 0)
        output_node.location = (300, 0)

# Add to the node menu
def add_node_to_menu(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator("node.add_node", text="FX30 Grain Match").type = "FX30GrainMatchNodeType"

# Panel for camera settings
class FX30GrainCameraPanel(bpy.types.Panel):
    bl_label = "FX30 Grain Settings"
    bl_idname = "CAMERA_PT_fx30_grain"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        return context.camera
    
    def draw(self, context):
        layout = self.layout
        camera = context.camera
        
        layout.prop(camera.fx30_grain, "iso")
        layout.prop(camera.fx30_grain, "strength_multiplier")
        
        col = layout.column(heading="Advanced")
        col.prop(camera.fx30_grain, "shadow_boost")
        col.prop(camera.fx30_grain, "highlight_suppress")

# Register and unregister functions
def register():
    bpy.utils.register_class(FX30GrainCameraSettings)
    register_camera_property()
    bpy.utils.register_class(FX30GrainMatchNode)
    bpy.utils.register_class(FX30GrainMatchGroup)
    bpy.utils.register_class(FX30GrainCameraPanel)
    bpy.types.NODE_MT_add.append(add_node_to_menu)

def unregister():
    bpy.types.NODE_MT_add.remove(add_node_to_menu)
    bpy.utils.unregister_class(FX30GrainCameraPanel)
    bpy.utils.unregister_class(FX30GrainMatchGroup)
    bpy.utils.unregister_class(FX30GrainMatchNode)
    bpy.utils.unregister_class(FX30GrainCameraSettings)
    del bpy.types.Camera.fx30_grain

if __name__ == "__main__":
    register()
