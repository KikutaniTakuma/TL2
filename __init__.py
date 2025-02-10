import bpy
import math
import mathutils
import bpy_extras
import gpu
import gpu_extras.batch
import copy
import json

from strech_vertex import MYADDON_OT_stretch_vertex
from spawn import MYADDON_OT_spawn_symbol_import
from spawn import MYADDON_OT_spawn_symbol_create
from spawn import MYADDON_OT_player_spawn_symbol_create
from spawn import MYADDON_OT_enemy_spawn_symbol_create

#ブレンダーに登録するアドオン情報
bl_info = {
    "name" : "レベルエディタ",
    "author" : "Taro Kamata",
    "version" : (1, 0),
    "blender" : (4,0,0),
    "location" : "",
    "description" : "レベルエディタ",
    "warning" : "",
    #"support" : "TESTING",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Object"
}

#オペレータ シーン出力
class MYADDON_OT_export_scene(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーン出力"
    bl_description = "シーン情報をExportします"
    #出力するファイルの拡張子
    filename_ext = ".json"

    def write_and_print(self, file, str):
        print(str)

        file.write(str)
        file.write('\n')

    def parse_sceme_recursive(self, file, object, level):
        """シーン解析用再帰関数"""

        indent = ' '
        for i in range(level):
            indent += "\t"

        #オブジェクト名書き込み
        self.write_and_print(file, indent + object.type + " - " + object.name)
                
        #ローカルトランスフォーム行列から平行移動、回転、スケーリングを抽出
        #型は Vector, Quternion, Vector
        trans, rot, scale = object.matrix_local.decompose()
        #回転をQuternion から Euler(3軸での回転角) に変換
        rot = rot.to_euler()
        #ラジアンから度数法に変換
        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        #トランスフォーム情報を表示
        self.write_and_print(file, indent + "T(%f,%f,%f)" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "R(%f,%f,%f)" % (rot.x, rot.y, rot.z))
        self.write_and_print(file, indent + "S(%f,%f,%f)" % (scale.x, scale.y, scale.z))
        #カスタムプロパティ'file_name'
        if "file_name" in object:
            self.write_and_print(file, indent + "N %s" % object["file_name"])
        #カスタムプロパティ 'collision'
        if "collider" in object:
            self.write_and_print(file, indent + "C %s" % object["collider"])
            temp_str = indent + "CC %f %f %f"
            temp_str %= (object["collider_center"][0], object["collider_center"][1], object["collider_center"][2])
            self.write_and_print(file,temp_str)
            temp_str = indent + "CS %f %f %f"
            temp_str %=(object["collider_size"][0], object["collider_size"][1], object["collider_size"][2])
            self.write_and_print(file,temp_str)
        #カスタムプロパティ'skyblock'
        if "skyblock" in object:
            self.write_and_print(file, indent + "N %s" % object["skyblock"])
        #カスタムプロパティ'player'
        if "player" in object:
            self.write_and_print(file, indent + "N %s" % object["player"])


        self.write_and_print(file, indent + 'END')
        self.write_and_print(file, '')


        for child in object.children:
            self.parse_sceme_recursive(file, child, level + 1)
        

    def export(self):
        """ファイルに出力"""

        print("シーン情報出力開始... %r" % self.filepath)

        #ファイルをテキスト形式で書きだしようにオープン
        #スコープを抜けると自動的にクローズされる
        with open(self.filepath, "wt") as file:

            #ファイルに文字列を書き込む
            file.write("SCENE\n")
            #シーン全てのオブジェクト
            for object in bpy.context.scene.objects:
                if(object.parent):
                    continue

                self.parse_sceme_recursive(file, object, 0)

    def export_json(self):
        """JSON形式でファイルの出力"""

        #保存する情報をまとめるdict
        json_object_root = dict()

        #ノード名
        json_object_root["name"] = "scene"
        #オブジェクトリストを作成
        json_object_root["objects"] = list()
        
        #シーン内の全オブジェクト走査してパック
        for object in bpy.context.scene.objects:
            if(object.parent):
                continue
            
            self.parse_sceme_recursive_json(json_object_root["objects"], object, 0)


        #オブジェクトをJSON文字列にエンコード
        json_text = json.dumps(json_object_root, ensure_ascii=False, cls=json.JSONEncoder, indent=4)
        #コンソールに表示
        print(json_text)

        #ファイルにテキスト形式で書き出し用にオープン
        with open(self.filepath, "wt", encoding="utf-8") as file:

            #文字列を書き込む
            file.write(json_text)

    def parse_sceme_recursive_json(self, data_parent, object, level):
        json_object = dict()
        #カスタムプロパティ'skyblock'
        if "skyblock" in object:
            json_object["skyblock"] = object["skyblock"]
        #カスタムプロパティ'player'
        if "player" in object:
            json_object["player"] = object["player"]
        if "disabled" in object:
            json_object["disabled"] = object["disabled"]

        json_object["type"] = object.type
        if "type" in object:
            json_object["type"] = object["type"]
        else:
            json_object["type"] = object.type

        json_object["name"] = object.name

        trans, rot, scale = object.matrix_local.decompose()
        rot = rot.to_euler()
        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        transform = dict()
        transform["translation"] = (trans.x, trans.y, trans.z)
        transform["rotation"] = (rot.x, rot.y, rot.z)
        transform["scaling"] = (scale.x, scale.y, scale.z)

        json_object["transform"] = transform

        #Cameraだった場合の処理
        if 'CAMERA' == object.type:
            camera_data = object.data

            # レンダリング設定から解像度を取得
            render = bpy.context.scene.render
            aspect_ratio = render.resolution_x / render.resolution_y
            
            #透視投影
            if camera_data.type == 'PERSP':
                #fov取得
                sensor_width = camera_data.sensor_width
                focal_length = camera_data.lens
                fov_horiz = math.atan((sensor_width / 2) / focal_length)
                fov = math.degrees(fov_horiz)
                fov = math.radians(fov)
                #度数法に変換
                #fov = math.degrees(fov)

                json_object["camera_type"] = "Perspective"
                json_object["fov"] = fov
                json_object["aspect_ratio"] = aspect_ratio

            #平行投影
            if camera_data.type == 'ORTHO':
                # 平行投影の幅 (Ortho Width)
                width = camera_data.ortho_scale
                #縦
                height = width / aspect_ratio
                
                json_object["camera_type"] = "Othographic"
                json_object["width"] = width
                json_object["height"] = height

            #far clip
            far_clip = camera_data.clip_end
            #near clip
            near_clip = camera_data.clip_start

            json_object["far_clip"] = far_clip
            json_object["near_clip"] = near_clip


        if "file_name" in object:
            json_object["file_name"] = object["file_name"]

        if "collider" in object:
            collider = dict()
            collider["type"] = object["collider"]
            collider["center"] = object["collider_center"].to_list()
            collider["size"] = object["collider_size"].to_list()
            json_object["collider"] = collider


        data_parent.append(json_object)

        if len(object.children) > 0:
            json_object["children"] = list()

            for child in object.children:
                self.parse_sceme_recursive_json(json_object["children"], child, level + 1)


    def execute(self, context):
        print("シーン情報をExportします")

        #ファイルに出力
        self.export_json()
        #self.export()

        
        print("シーン情報をExportしました")
        self.report({'INFO'}, "シーン情報をExportしました")

        return {'FINISHED'}
    

#オペレータ ICO球生成
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_ico_sphere"
    bl_label = "ICO球生成"
    bl_description = "ICO球を生成します"
    #リドゥ、アンドゥ可能オプション
    bl_options = {'REGISTER', 'UNDO'}

    #メニューを実行したときに呼ばれるコールバック関数
    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        print("ICO球を生成しました")

        #オペレータの命令終了を通知
        return {'FINISHED'}

class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"
    bl_description = "拡張メニュー by " + bl_info["author"]

    #サブメニューの描画
    def draw(self, context):
        self.layout.operator(MYADDON_OT_export_scene.bl_idname,
            text=MYADDON_OT_export_scene.bl_label)

        self.layout.separator()
        #トップバーの「エディタメニュー」に項目(オペレータ)を追加
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname,
            text=MYADDON_OT_stretch_vertex.bl_label)
        #トップバーの「エディタメニュー」に項目(オペレータ)を追加
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname,
            text=MYADDON_OT_create_ico_sphere.bl_label)
        
        self.layout.operator(MYADDON_OT_player_spawn_symbol_create.bl_idname,
            text=MYADDON_OT_player_spawn_symbol_create.bl_label)
        
        self.layout.operator(MYADDON_OT_enemy_spawn_symbol_create.bl_idname,
            text=MYADDON_OT_enemy_spawn_symbol_create.bl_label)
        
        self.layout.separator()

        self.layout.operator("wm.url_open_preset", 
            text="Manual", icon = 'HELP')
        
    #既存のメニューにサブメニューを追加
    def submenu(self, context):

        #ID指定でサブメニュー追加
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)



class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "Filename 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        #['file_name']カスタムプロパティを追加
        context.object["file_name"] = ""

        return {'FINISHED'}
    
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_collider"
    bl_label = "コライダー 追加"
    bl_description = "['collider']カスタムプロパティを追加します"
    bl_options = { "REGISTER", "UNDO" }

    def execute(self, context):
        #['collider]カスタムプロパティを追加
        context.object["collider"] = "BOX"
        context.object["collider_center"] = mathutils.Vector((0,0,0))
        context.object["collider_size"] = mathutils.Vector((2,2,2))

        return { "FINISHED" }
    
class MYADDON_OT_add_skyblock(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_skyblock"
    bl_label = "Skyblock 追加"
    bl_description = "['skyblock']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        #['file_name']カスタムプロパティを追加
        context.object["skyblock"] = "skyblock"

        return {'FINISHED'}
    
class MYADDON_OT_add_player(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_player"
    bl_label = "Player 追加"
    bl_description = "['player']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        #['file_name']カスタムプロパティを追加
        context.object["player"] = "player"

        return {'FINISHED'}
    
class MYADDON_OT_disabled(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_disabled"
    bl_label = "disabled 追加"
    bl_description = "['disabled']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        #['file_name']カスタムプロパティを追加
        context.object["disabled"] = True

        return {'FINISHED'}
    
class MYADDON_PT_disabled(bpy.types.Panel):
    bl_idname = "MYADDON_PT_disabled"
    bl_label = "disabled"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        #パネルに項目を追加
        if "disabled" in context.object:
            #すでにプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["disabled"]', text = self.bl_label)
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_disabled.bl_idname)


class OBJECT_PT_collider(bpy.types.Panel):
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        #パネルに項目を追加
        if "collider" in context.object:
            #すでにプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["collider"]', text = "Type")
            self.layout.prop(context.object, '["collider_center"]', text = "Center")
            self.layout.prop(context.object, '["collider_size"]', text = "Size")
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_collider.bl_idname)



#パネル ファイル名
class OBJECT_PT_file_name(bpy.types.Panel):
    """オブジェクトのファイルネームパネル"""
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        #パネルに項目を追加
        if "file_name" in context.object:
            #すでにプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["file_name"]', text = self.bl_label)
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_filename.bl_idname)

class OBJECT_PT_skyblock(bpy.types.Panel):
    bl_idname = "OBJECT_PT_skyblock"
    bl_label = "Skyblock"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        #パネルに項目を追加
        if "skyblock" in context.object:
            #すでにプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["skyblock"]', text = "Type")
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_skyblock.bl_idname)

class OBJECT_PT_player(bpy.types.Panel):
    bl_idname = "OBJECT_PT_player"
    bl_label = "Player"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        #パネルに項目を追加
        if "player" in context.object:
            #すでにプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["player"]', text = "Type")
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_player.bl_idname)

#コライダー描画
class DrawCollider:

    #描画ハンドル
    handle = None
    #3Dビューに登録する描画関数
    def darw_collider():
        #頂点データ
        vertices = {"pos":[]}
        #インデックスデータ
        indices = []

        #各頂点の、オブジェクト中心からのオフセット
        offsets = [
            [-0.5,-0.5,-0.5],
            [+0.5,-0.5,-0.5],
            [-0.5,+0.5,-0.5],
            [+0.5,+0.5,-0.5],
            [-0.5,-0.5,+0.5],
            [+0.5,-0.5,+0.5],
            [-0.5,+0.5,+0.5],
            [+0.5,+0.5,+0.5],
        ]

        #立方体のサイズ
        size = [2,2,2]

        #現在のオブジェクトリストを走査
        for object in bpy.context.scene.objects:
            if not "collider" in object:
                continue
            #中心点、サイズの変数を宣言
            center = mathutils.Vector((0,0,0))
            size = mathutils.Vector((2,2,2))

            #プロパティをから値を取得
            center[0] = object["collider_center"][0]
            center[1] = object["collider_center"][1]
            center[2] = object["collider_center"][2]
            size[0] = object["collider_size"][0]
            size[1] = object["collider_size"][1]
            size[2] = object["collider_size"][2]

            start = len(vertices["pos"])

            for offset in offsets:
                pos = copy.copy(center)
                pos[0] += offset[0]*size[0]
                pos[1] += offset[1]*size[1]
                pos[2] += offset[2]*size[2]
                #ローカルからワールドへ
                pos = object.matrix_world @ pos
                vertices['pos'].append(pos)
                
                indices.append([start+0, start+1])
                indices.append([start+2, start+3])
                indices.append([start+0, start+2])
                indices.append([start+1, start+3])

                indices.append([start+4, start+5])
                indices.append([start+6, start+7])
                indices.append([start+4, start+6])
                indices.append([start+5, start+7])

                indices.append([start+0, start+4])
                indices.append([start+1, start+5])
                indices.append([start+2, start+6])
                indices.append([start+3, start+7])

        #ビルドインのシェーダを取得
        shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")

        #バッチを作成
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices = indices)

        #シェーダのパラメータ
        color = [0.5, 1.0, 1.0, 1.0]
        shader.bind()
        shader.uniform_float("color", color)
        #描画
        batch.draw(shader)


#Blenderに登録するクラスリスト
classes = (
    MYADDON_OT_export_scene,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_stretch_vertex,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
    MYADDON_OT_add_collider,
    OBJECT_PT_collider,
    MYADDON_OT_add_skyblock,
    OBJECT_PT_skyblock,
    MYADDON_OT_add_player,
    OBJECT_PT_player,
    MYADDON_OT_disabled,
    MYADDON_PT_disabled,
    MYADDON_OT_spawn_symbol_import,
    MYADDON_OT_spawn_symbol_create,
    MYADDON_OT_player_spawn_symbol_create,
    MYADDON_OT_enemy_spawn_symbol_create
)

# メニュー項目画面
def draw_menu_manual(self, context):
    self.layout.operator("wm.url_open_preset", text="Manual", icon = 'HELP')

#アドオン有効化時のコールバック
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    #3Dビューみ描画関数を追加
    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(DrawCollider.darw_collider, (), "WINDOW", "POST_VIEW")
    print("レベルエディタが有効化されました。")

#アドオン無効化時コールバック
def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
    bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")

    for cls in classes:
        bpy.utils.unregister_class(cls)

    print("レベルエディタが無効化されました。")

#テスト実行用コード
if __name__ == "__main__":
    register()