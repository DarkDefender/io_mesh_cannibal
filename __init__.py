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

class CPJ_DoubleOperator(Operator):
    """Mark selected faces as double sided"""
    bl_idname = "object.cpj_selected_as_double"
    bl_label = "CPJ mark faces as double sided"

    def execute(self, context):
        obj = context.object

        if obj.type != 'MESH':
            raise Exception("Must be a mesh object")
        # assuming the object is currently in Edit Mode.
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        flags_layer = bm.faces.layers.int['flags']

        for f in bm.faces:
            if f.select:
                f[flags_layer] = 0x40 # Set two sided flag

        # Show the updates in the viewport
        # and recalculate n-gon tessellation.
        bmesh.update_edit_mesh(me)

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

class EDIT_PT_panel(bpy.types.Panel):
    bl_label = "CPJ helper operators"
    bl_category = "CPJ Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Operators:")

        col = layout.column(align=True)
        col.operator(CPJ_DoubleOperator.bl_idname, text="Selected as Double Sided")

        layout.separator()

# ----------------------------------------------------------------------------
classes = {
    ImportCPJ,
    ExportCPJ,
    OBJ_PT_panel,
    EDIT_PT_panel,
    CPJ_InitOperator,
    CPJ_DoubleOperator,
}


# ----------------------------------------------------------------------------
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    print("CPJ plugin loaded")  # FIXME debug


# ----------------------------------------------------------------------------
def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    print("CPJ plugin unloaded")  # FIXME debug


# ----------------------------------------------------------------------------
if "import_cpj" in locals():
    importlib.reload(import_cpj)

if "export_cpj" in locals():
    importlib.reload(export_cpj)

if __name__ == "__main__":
    register()

# EoF
