# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------------------------
import importlib
import bpy
import bmesh

from bpy.types import (Panel, Operator)

import os, sys
# Add the current directory to the search path so our local imports will work
sys.path.append(os.path.dirname(__file__))

from import_cpj import create_custom_data_layers
from export_cpj import calc_boundbox_max_min

from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)


# ----------------------------------------------------------------------------
bl_info = {
    "name": "Cannibal Project (CPJ) format",
    "author": "patwork, ZedDB",
    "version": (0, 0, 1),
    "blender": (3, 1, 0),
    "location": "File > Import-Export",
    "description": "Import-Export CPJ",
    "warning": "",
    "doc_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


# ----------------------------------------------------------------------------
@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportCPJ(bpy.types.Operator, ImportHelper):
    """Load a Cannibal Project (CPJ) File"""
    bl_idname = "import_model.cpj"
    bl_label = "Import CPJ"
    bl_options = {'UNDO'}

    filename_ext = ".cpj"
    filter_glob: StringProperty(default="*.cpj", options={'HIDDEN'})

    def execute(self, context):
        from . import import_cpj
        keywords = self.as_keywords(ignore=(
            "axis_forward",
            "axis_up",
            "filter_glob",
        ))
        return import_cpj.load(context, **keywords)


# ----------------------------------------------------------------------------
@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportCPJ(bpy.types.Operator, ExportHelper):
    """Save a Cannibal Project (CPJ) File"""
    bl_idname = "export_model.cpj"
    bl_label = "Export CPJ"

    filename_ext = ".cpj"
    filter_glob: StringProperty(default="*.cpj", options={'HIDDEN'})

    def execute(self, context):
        from . import export_cpj
        keywords = self.as_keywords(ignore=(
            "axis_forward",
            "axis_up",
            "check_existing",
            "filter_glob",
        ))
        return export_cpj.save(context, **keywords)


# ----------------------------------------------------------------------------
def menu_func_import(self, context):
    self.layout.operator(ImportCPJ.bl_idname, text="Cannibal Project (.cpj)")


# ----------------------------------------------------------------------------
def menu_func_export(self, context):
    self.layout.operator(ExportCPJ.bl_idname, text="Cannibal Project (.cpj)")

# ----------------------------------------------------------------------------
class CPJ_InitOperator(Operator):
    """Initialize CPJ variables on active object"""
    bl_idname = "object.cpj_init"
    bl_label = "CPJ data init Operator"

    def execute(self, context):
        obj = context.object

        if obj.type != 'MESH':
            raise Exception("Must be a mesh object")
        create_custom_data_layers(obj.data)

        mac_text_name = "cpj_" + obj.name
        text_block = bpy.data.texts.new(mac_text_name)
        text_block.write("--- autoexec\n")
        text_block.write('SetAuthor "Unknown"\n')
        text_block.write('SetDescription "None"\n')
        # TODO These should be set automatically when exporting
        text_block.write('SetOrigin 0.000000 0.000000 0.000000\n')
        text_block.write('SetScale 1.000000 1.000000 1.000000\n')
        text_block.write('SetRotation 0.000000 0.000000 0.000000\n')
        max_bb, min_bb = calc_boundbox_max_min(obj)
        text_block.write(f'SetBoundsMin {min_bb[0]:.6f} {min_bb[1]:.6f} {min_bb[2]:.6f}\n')
        text_block.write(f'SetBoundsMax {max_bb[0]:.6f} {max_bb[1]:.6f} {max_bb[2]:.6f}\n')

        text_block.write('SetGeometry "' + obj.name + '"\n')
        text_block.write('SetSurface 0 "' + obj.data.uv_layers[0].name + '"\n')
        text_block.write('AddFrames "NULL"\n')
        text_block.write('AddSequences "NULL"\n')

        return {'FINISHED'}

def set_selected_face_bit_value(context,layer, value):
    obj = context.object

    if obj.type != 'MESH':
        raise Exception("Must be a mesh object")
    # assuming the object is currently in Edit Mode.
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    value_layer = bm.faces.layers.int[layer]

    for f in bm.faces:
        if f.select:
            f[value_layer] |= value

    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me)

def clear_selected_face_bit_value(context,layer, value):
    obj = context.object

    if obj.type != 'MESH':
        raise Exception("Must be a mesh object")
    # assuming the object is currently in Edit Mode.
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    value_layer = bm.faces.layers.int[layer]

    for f in bm.faces:
        if f.select:
            f[value_layer] &= ~value

    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me)

class CPJ_FaceFlagAssign(Operator):
    """Mark selected faces with active CPJ flag"""
    bl_idname = "object.cpj_face_mark_assign"
    bl_label = "Mark selected with active CPJ flag"

    def execute(self, context):
        flag_type = int(context.scene.cpj_flag_types, 16)
        set_selected_face_bit_value(context, 'flags', flag_type)

        return {'FINISHED'}

class CPJ_FaceFlagRemove(Operator):
    """Remove active CPJ flag from selected faces"""
    bl_idname = "object.cpj_face_mark_remove"
    bl_label = "Remove active cpj flag from faces"

    def execute(self, context):
        flag_type = int(context.scene.cpj_flag_types, 16)
        clear_selected_face_bit_value(context, 'flags', flag_type)

        return {'FINISHED'}

class CPJ_FaceFlagSelect(Operator):
    """Select faces with active cpj flag"""
    bl_idname = "object.cpj_face_mark_select"
    bl_label = "Select all faces with active cpj flag"

    deselect: BoolProperty()

    def execute(self, context):
        obj = context.object

        if obj.type != 'MESH':
            raise Exception("Must be a mesh object")
        # assuming the object is currently in Edit Mode.
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        flags_layer = bm.faces.layers.int['flags']

        flag_type = int(context.scene.cpj_flag_types, 16)

        for f in bm.faces:
            if f[flags_layer] & flag_type != 0:
                f.select = not self.deselect

        # Show the updates in the viewport
        # and recalculate n-gon tessellation.
        bmesh.update_edit_mesh(me)

        return {'FINISHED'}

def set_selected_face_value(context,layer, value):
    obj = context.object

    if obj.type != 'MESH':
        raise Exception("Must be a mesh object")
    # assuming the object is currently in Edit Mode.
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    value_layer = bm.faces.layers.int[layer]

    for f in bm.faces:
        if f.select:
            f[value_layer] = value

    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me)

class CPJ_SmoothGroupAssign(Operator):
    """Set selected cpj face group"""
    bl_idname = "object.cpj_smooth_g_set"
    bl_label = "Set cpj face group"

    def execute(self, context):
        smooth_group = context.scene.cpj_smooth_g
        set_selected_face_value(context, 'smooth_group', smooth_group)

        return {'FINISHED'}

class CPJ_AlphaAssign(Operator):
    """Set selected cpj face alpha level"""
    bl_idname = "object.cpj_alpha_lvl_set"
    bl_label = "Set cpj alpha level"

    def execute(self, context):
        a_lvl = context.scene.cpj_alpha_lvl
        set_selected_face_value(context, 'alpha_level', a_lvl)

        return {'FINISHED'}

class CPJ_GlazeAssign(Operator):
    """Set selected cpj face glaze texture"""
    bl_idname = "object.cpj_glaze_set"
    bl_label = "Set cpj glaze"

    def execute(self, context):
        glaze_tex = context.scene.cpj_glaze_tex
        set_selected_face_value(context, 'glaze_index', glaze_tex)

        return {'FINISHED'}

class CPJ_GlazeFuncAssign(Operator):
    """Set selected cpj face glaze function"""
    bl_idname = "object.cpj_glaze_func_set"
    bl_label = "Set cpj glaze function"

    def execute(self, context):
        glaze_func = context.scene.cpj_glaze_func
        set_selected_face_value(context, 'glaze_func', glaze_func)

        return {'FINISHED'}

def set_selected_vert_value(context,layer, value):
    obj = context.object

    if obj.type != 'MESH':
        raise Exception("Must be a mesh object")
    # assuming the object is currently in Edit Mode.
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    value_layer = bm.verts.layers.int[layer]

    for v in bm.verts:
        if v.select:
            v[value_layer] = value

    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me)

class CPJ_LODLockAssign(Operator):
    """Set LOD lock on selected vertices"""
    bl_idname = "object.cpj_lod_lock_set"
    bl_label = "Set cpj lod lock"

    def execute(self, context):
        lod_lock = context.scene.cpj_lod_lock
        set_selected_vert_value(context, 'lod_lock', lod_lock)

        return {'FINISHED'}

class CPJ_FRMGroupIndexAssign(Operator):
    """Set FRM Group index on the seleted vertss"""
    bl_idname = "object.cpj_frm_group_set"
    bl_label = "Set cpj FRM group index"

    def execute(self, context):
        frm_group = context.scene.cpj_frm_group_index
        set_selected_vert_value(context, 'frm_group_index', frm_group)

        return {'FINISHED'}

# ----------------------------------------------------------------------------
class OBJ_PT_panel(bpy.types.Panel):
    bl_label = "CPJ helper operators"
    bl_category = "CPJ Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Operators:")

        col = layout.column(align=True)
        col.operator(CPJ_InitOperator.bl_idname, text="Initialize CPJ for object", icon="CONSOLE")

        layout.separator()

class EDIT_PT_Fpanel(bpy.types.Panel):
    bl_label = "Face attributes"
    bl_category = "CPJ Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Face Flags:")
        layout.prop(context.scene, "cpj_flag_types", text="")

        row = layout.row(align=True)
        row.operator(CPJ_FaceFlagAssign.bl_idname, text="Assign")
        row.operator(CPJ_FaceFlagRemove.bl_idname, text="Remove")
        row = layout.row(align=True)
        row.operator(CPJ_FaceFlagSelect.bl_idname, text="Select").deselect = False
        row.operator(CPJ_FaceFlagSelect.bl_idname, text="Deselect").deselect = True

        layout.label(text="Smooth Group:")
        row = layout.row(align=True)
        row.operator(CPJ_SmoothGroupAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_smooth_g", text="")

        layout.label(text="Alpha Level:")
        row = layout.row(align=True)
        row.operator(CPJ_AlphaAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_alpha_lvl", text="")

        layout.label(text="Glaze Texture Index:")
        row = layout.row(align=True)
        row.operator(CPJ_GlazeAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_glaze_tex", text="")

        layout.label(text="Glaze Function:")
        row = layout.row(align=True)
        row.operator(CPJ_GlazeFuncAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_glaze_func", text="")

class EDIT_PT_Vpanel(bpy.types.Panel):
    bl_label = "Vertex attributes"
    bl_category = "CPJ Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout

        layout.label(text="LOD lock:")
        row = layout.row(align=True)
        row.operator(CPJ_LODLockAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_lod_lock", text="")

        layout.label(text="FRM Group:")
        row = layout.row(align=True)
        row.operator(CPJ_FRMGroupIndexAssign.bl_idname, text="Assign")
        row.prop(context.scene, "cpj_frm_group_index", text="")

# ----------------------------------------------------------------------------
classes = {
    ImportCPJ,
    ExportCPJ,
    OBJ_PT_panel,
    EDIT_PT_Fpanel,
    EDIT_PT_Vpanel,
    CPJ_InitOperator,
    CPJ_FaceFlagAssign,
    CPJ_FaceFlagRemove,
    CPJ_FaceFlagSelect,
    CPJ_SmoothGroupAssign,
    CPJ_AlphaAssign,
    CPJ_GlazeAssign,
    CPJ_GlazeFuncAssign,
    CPJ_LODLockAssign,
    CPJ_FRMGroupIndexAssign,
}


# ----------------------------------------------------------------------------
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.types.Scene.cpj_lod_lock = BoolProperty()
    bpy.types.Scene.cpj_frm_group_index = IntProperty(min = 0, max = 256)

    bpy.types.Scene.cpj_flag_types = EnumProperty(name="Face Flags",
        description="Used to mark faces for special handling like double sided rendering",
        items=[
            ('0x1', "Inactive",
                "The triangle is not active"),
            ('0x2', "Invisible",
                "Present but invisible"),
            ('0x4', "VN Ignore",
                "Ignore this face when calculating vertex normals"),
            ('0x8', "Transparent",
                "Enable transparency rendering on this face"),
            ('0x20', "Unlit",
                "Face is not affected by dynamic lighting"),
            ('0x40', "Two Sided",
                "Face is visible from both sides"),
            ('0x80', "Color Masking",
                "Color key masking is active"),
            ('0x100', "Modulated",
                "Modulated rendering is enabled"),
            ('0x200', "Env Map",
                "Enviroment mapped"),
            ('0x400', "Non Collide",
                "Trace rays will not collide with this face"),
            ('0x800', "Tex Blend",
                ""),
            ('0x1000', "Z Later",
                ""),
            ('0x10000', "Reserved",
                ""),
          ]
        )

    bpy.types.Scene.cpj_smooth_g = IntProperty(min = 0, max = 256)
    bpy.types.Scene.cpj_alpha_lvl = IntProperty(min = 0, max = 256)
    bpy.types.Scene.cpj_glaze_tex = IntProperty(min = 0, max = 256)
    bpy.types.Scene.cpj_glaze_func = BoolProperty()


    print("CPJ plugin loaded")  # FIXME debug


# ----------------------------------------------------------------------------
def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.cpj_flag_types
    del bpy.types.Scene.cpj_smooth_g
    del bpy.types.Scene.cpj_alpha_lvl
    del bpy.types.Scene.cpj_glaze_tex
    del bpy.types.Scene.cpj_glaze_func

    print("CPJ plugin unloaded")  # FIXME debug


# ----------------------------------------------------------------------------
if "import_cpj" in locals():
    importlib.reload(import_cpj)

if "export_cpj" in locals():
    importlib.reload(export_cpj)

if __name__ == "__main__":
    register()

# EoF
