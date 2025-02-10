import bpy
import os
import bpy.ops

class SpawnNames():
    PROROTYPE = 0
    INSTANCE = 1
    FILENAME = 2

    names = {}

    names["Enemy"] = ("PrototypeEnemySpawn", "EnemySpawn", "needlle/needle.obj")
    names["Player"] = ("PrototypePlayerSpawn", "PlayerSpawn", "player/player.obj")


class MYADDON_OT_spawn_symbol_import(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_spawn_symbol_import"
    bl_label = "出現ポイントImport"
    bl_description = "出現ポイントImportします"
    prototype_object_name = "PrototypePlayerSpawn"
    object_name = "PlayerSpawn"
    #リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    def load_obj(self, type):
        print("出現ポイントのシンボルをImportします")
        spawn_object = bpy.data.objects.get(MYADDON_OT_spawn_symbol_import.prototype_object_name)
        if spawn_object is not None:
            return {'CANCELLED'}
        
        addon_directory = os.path.dirname(__file__)
        relative_path = "player/player.obj"
        full_path = os.path.join(addon_directory, relative_path)

        bpy.ops.wm.obj_import('EXEC_DEFAULT',filepath=full_path, display_type='THUMBNAIL',forward_axis='Z', up_axis='Y')

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False,properties=False,isolate_users=False)

        object = bpy.context.active_object

        object.name = SpawnNames.names[type][SpawnNames.PROROTYPE]

        object["type"] = SpawnNames.names[type][SpawnNames.INSTANCE]

        bpy.context.collection.objects.unlink(object)

        #オペレータの命令終了を通知
        return {'FINISHED'}


    #メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):

        self.load_obj(self, "Enemy")
        self.load_obj(self, "Player")

        #オペレータの命令終了を通知
        return {'FINISHED'}
    
    
class MYADDON_OT_spawn_symbol_create(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_spawn_symbol_create"
    bl_label = "出現ポイントを作成"
    bl_description = "出現ポイントを作成します"
    prototype_object_name = "PrototypePlayerSpawn"
    object_name = "PlayerSpawn"
    #リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.StringProperty(name="Type",default="Player")

    #メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        spawn_object = bpy.data.objects.get(SpawnNames.names[self.type][SpawnNames.PROROTYPE])

        if spawn_object is None:
            bpy.ops.myaddon.myaddon_ot_spawn_symbol_import('EXEC_DEFAULT')
            spawn_object = bpy.data.objects.get(SpawnNames.names[self.type][SpawnNames.PROROTYPE])
        
        print("出現ポイントのシンボルを作成します")

        bpy.ops.object.select_all(action='DESELECT')

        object = spawn_object.copy()

        bpy.context.collection.objects.link(object)

        object.name = MYADDON_OT_spawn_symbol_create.object_name

        #オペレータの命令終了を通知
        return {'FINISHED'}
    
class MYADDON_OT_player_spawn_symbol_create(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_player_spawn_symbol_create"
    bl_label = "プレイヤー出現ポイントを作成"
    bl_description = "プレイヤー出現ポイントを作成します"
    #リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}


    #メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        bpy.ops.myaddon.myaddon_ot_spawn_symbol_create('EXEC_DEFAULT', type = "Player")

        #オペレータの命令終了を通知
        return {'FINISHED'}
    
class MYADDON_OT_enemy_spawn_symbol_create(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_enemy_spawn_symbol_create"
    bl_label = "エネミー出現ポイントを作成"
    bl_description = "エネミー出現ポイントを作成します"
    #リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}


    #メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        bpy.ops.myaddon.myaddon_ot_spawn_symbol_create('EXEC_DEFAULT', type = "Enemy")

        #オペレータの命令終了を通知
        return {'FINISHED'}