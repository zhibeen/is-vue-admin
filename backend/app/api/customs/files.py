from apiflask import Schema
from apiflask.fields import String, Integer, Boolean, File, List, Nested, DateTime
from apiflask.views import MethodView
from werkzeug.datastructures import FileStorage
from flask import send_file, Response, request, current_app
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func

from app.services.synology_client import SynologyClient
from app.services.customs_service import customs_service
from app.models.customs.attachment import CustomsAttachment
from app.extensions import db
from app.errors import BusinessError
from app.security import auth
from app.decorators import permission_required
from . import customs_bp

# --- Schemas ---

class FileItemSchema(Schema):
    id = Integer()
    name = String()
    path = String()  # Relative path (Category/Filename)
    category = String()
    slot_title = String()
    size = Integer()
    file_type = String()
    uploaded_by_name = String()
    created_at = DateTime()
    url = String(dump_only=True) 

class FileUploadSchema(Schema):
    file = File(required=True)
    category = String(load_default='04_Others') 
    slot_title = String(load_default=None) 

class FileListResponseSchema(Schema):
    # data = List(Nested(FileItemSchema))
    # APIFlask 会自动包装响应，我们这里直接定义 List 结构会更好，
    # 或者直接在 View 中使用 output(FileItemSchema(many=True))
    pass

# --- Views ---

@customs_bp.route('/declarations/<int:id>/files')
class DeclarationFilesAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    def _get_client(self):
        return SynologyClient()

    @customs_bp.doc(summary="获取报关单归档文件列表")
    @customs_bp.output(FileItemSchema(many=True))
    @permission_required('customs:view')
    def get(self, id):
        """
        获取指定报关单的所有归档文件 (从数据库读取，并尝试自动同步)
        """
        # 1. 尝试触发一次快速同步 (保证数据新鲜度)
        customs_service.sync_nas_files(id)
        
        # 2. 查询数据库
        attachments = db.session.query(CustomsAttachment).filter_by(declaration_id=id).all()
        
        # 将对象列表转换为字典列表，确保与 Schema 兼容
        data_list = []
        for att in attachments:
            data_list.append({
                'id': att.id,
                'name': att.file_name,
                'path': att.file_path,
                'category': att.category,
                'slot_title': att.slot_title,
                'size': att.file_size,
                'file_type': att.file_type,
                'uploaded_by_name': att.uploader.nickname if att.uploader else 'System',
                'created_at': att.created_at
            })
            
        # 直接返回列表，APIFlask (BASE_RESPONSE_SCHEMA) 会自动包装成 {'code': 0, 'data': [...]}
        return {'data': data_list}

    def _normalize_category(self, category: str) -> str:
        """
        标准化 category 值，确保与前端 docMatrix 一致
        前端使用: 01_Customs, 02_Trade, 03_Logistics, 04_Others
        """
        # 旧值映射到新值
        legacy_mapping = {
            '01_Basic': '01_Customs',
            '02_Container': '03_Logistics',  
            '03_Finance': '02_Trade',
        }
        
        # 如果是旧值，转换为新值
        if category in legacy_mapping:
            return legacy_mapping[category]
        
        # 标准值直接返回
        valid_categories = ['01_Customs', '02_Trade', '03_Logistics', '04_Others']
        if category in valid_categories:
            return category
        
        # 默认返回其他资料
        return '04_Others'
    
    def _save_file_to_nas_and_db(self, id, file_obj, target_filename, category, slot_title, user_id):
        # --- 1. 标准化 category ---
        normalized_category = self._normalize_category(category)
        
        # --- 2. 上传到 NAS (扁平化结构) ---
        rel_root = customs_service.get_archive_path(id)
        target_folder_rel = rel_root
        
        client = self._get_client()
        try:
            client.upload_file(file_obj, target_folder_rel, filename=target_filename)
        except Exception as e:
            current_app.logger.error(f"NAS Upload failed: {e}")
            raise BusinessError(f"文件上传NAS失败: {str(e)}")

        # --- 3. 保存到数据库 ---
        file_path = target_filename
        
        file_size = 0
        if file_obj.content_length:
             file_size = file_obj.content_length
        elif hasattr(file_obj, 'stream'):
             # Try to get size from stream
             try:
                 pos = file_obj.stream.tell()
                 file_obj.stream.seek(0, 2)
                 file_size = file_obj.stream.tell()
                 file_obj.stream.seek(pos)
             except:
                 pass
        
        ext = target_filename.split('.')[-1].lower() if '.' in target_filename else ''

        att = db.session.query(CustomsAttachment).filter_by(
            declaration_id=id,
            file_path=file_path
        ).first()
        
        if att:
            att.file_size = file_size
            att.uploaded_by_id = user_id
            att.category = normalized_category  # 更新为标准化的 category
            att.slot_title = slot_title 
            att.created_at = func.now() 
            att.status = 'synced' # Reset status
            att.sync_message = None
        else:
            att = CustomsAttachment(
                declaration_id=id,
                file_name=target_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=ext,
                category=normalized_category,  # 使用标准化的 category
                slot_title=slot_title,
                uploaded_by_id=user_id,
                status='synced',
                source='upload'
            )
            db.session.add(att)
            
        db.session.commit()
        db.session.refresh(att)
        return att

    def _att_to_dict(self, att):
        return {
            'id': att.id,
            'name': att.file_name,
            'path': att.file_path,
            'category': att.category,
            'slot_title': att.slot_title,
            'size': att.file_size,
            'file_type': att.file_type,
            'uploaded_by_name': att.uploader.nickname if att.uploader else 'System',
            'created_at': att.created_at
        }

    @customs_bp.doc(summary="上传文件到报关单归档")
    @customs_bp.input(FileUploadSchema, location='form_and_files', arg_name='data')
    @customs_bp.output(FileItemSchema(many=True), status_code=201) # Return list of created items
    @permission_required('customs:edit')
    def post(self, id, data):
        """
        上传文件 (自动归档到NAS并记录数据库)
        支持 PDF 智能拆分
        """
        file_obj: FileStorage = data['file']
        category = data.get('category', '04_Others')
        slot_title = data.get('slot_title')
        user_id = get_jwt_identity()
        
        decl = customs_service.get_declaration(id)
        if not decl:
            raise BusinessError("Declaration not found", 404)
            
        created_atts = []
        
        # 尝试拆分 (仅当未指定 slot_title 且是 PDF 时)
        split_results = None
        if not slot_title:
             ext = file_obj.filename.split('.')[-1].lower()
             
             if ext == 'pdf':
                 split_results = customs_service.split_pdf(file_obj, id)
                 
             elif ext in ['jpg', 'jpeg', 'png']:
                 # 强制转换为 PDF
                 convert_res = customs_service.image_to_pdf(file_obj, id)
                 if convert_res:
                     split_results = [{
                        'filename': convert_res['filename'],
                        'stream': convert_res['stream'],
                        'slot_title': None, # 保持原样，归入 Others
                        'file_size': convert_res['file_size']
                     }]
                     current_app.logger.info(f"Converted image to PDF: {convert_res['filename']}")
        elif slot_title:
             # 如果指定了 slot_title，也检查是否是图片，如果是则转换
             ext = file_obj.filename.split('.')[-1].lower()
             if ext in ['jpg', 'jpeg', 'png']:
                 convert_res = customs_service.image_to_pdf(file_obj, id)
                 if convert_res:
                     # 单独处理，因为 logic flow 有点不同 (下面有 slot_title 判断)
                     # 为了复用下面的 _save_file_to_nas_and_db，我们修改 file_obj
                     file_obj = FileStorage(
                        stream=convert_res['stream'], 
                        filename=convert_res['filename'], 
                        content_type='application/pdf'
                     )
                     # 注意：需要把 target_filename 也改了
                     # 这里的逻辑稍微有点绕，因为下面会重新计算 target_filename
                     # 简单的做法：直接替换 file_obj，并让下面的逻辑重新获取 ext 和 filename
                     pass
        
        if split_results:
             current_app.logger.info(f"Processing {len(split_results)} files (Split/Convert)")
             for res in split_results:
                 # res = {'filename': ..., 'stream': ..., 'slot_title': ...}
                 fs = FileStorage(stream=res['stream'], filename=res['filename'], content_type='application/pdf')
                 
                 # 重新计算/传递文件大小
                 # 注意：FileStorage 不会自动从 stream 计算 content_length，但 _save_file_to_nas_and_db 会处理
                 
                 # 如果是自动拆分的，res['slot_title'] 有值，会归档到对应 Slot
                 # 如果是图片转的，res['slot_title'] 是 None，会归档到 Others
                 
                 att = self._save_file_to_nas_and_db(id, fs, res['filename'], category, res['slot_title'], user_id)
                 created_atts.append(att)
        else:
             # --- 1. 常规文件名生成 ---
             # 再次检查是否为图片 (针对指定 Slot 的情况)
             ext = file_obj.filename.split('.')[-1].lower() if '.' in file_obj.filename else ''
             
             # 基础文件名部分
             ref_no = decl.pre_entry_no or decl.customs_no or str(decl.id)
             ref_no = "".join([c for c in ref_no if c.isalnum() or c in '-_'])
             
             target_filename = file_obj.filename
             
             if slot_title:
                 safe_slot_title = slot_title.replace('/', '_').replace('\\', '_')
                 target_filename = f"{safe_slot_title}_{ref_no}.{ext}"
             
             att = self._save_file_to_nas_and_db(id, file_obj, target_filename, category, slot_title, user_id)
             created_atts.append(att)
        
        return {
            'data': [self._att_to_dict(a) for a in created_atts]
        }


@customs_bp.route('/declarations/<int:id>/files/<int:file_id>')
class DeclarationFileDetailAPI(MethodView):
    # decorators = [customs_bp.auth_required(auth)]
    # 下载接口使用 URL 访问，可能无法携带 Header Token (如 iframe/img src)
    # 临时移除认证，后续建议改为 Query Token 认证
    
    def _get_client(self):
        return SynologyClient()

    @customs_bp.doc(summary="下载/预览文件")
    # @permission_required('customs:view')
    def get(self, id, file_id):
        """
        下载或预览文件
        """
        att = db.session.get(CustomsAttachment, file_id)
        if not att or att.declaration_id != id:
            raise BusinessError("File not found", 404)

        rel_path = customs_service.get_archive_path(id)
        # Full path: Company/EntryNo/Category/Filename
        file_path = f"{rel_path}/{att.file_path}"
        
        client = self._get_client()
        try:
            nas_response = client.get_file_stream(file_path)
        except Exception as e:
            current_app.logger.error(f"NAS download failed: {e}")
            raise BusinessError("文件在NAS上不存在或无法读取", 404)
        
        # 使用 attachment 确保下载时有文件名
        # RFC 5987 标准: filename*=UTF-8''{encoded_filename}
        from urllib.parse import quote
        
        # 优先使用 slot_title 作为下载文件名 (如果有的话)
        download_name = att.file_name
        if att.slot_title:
            ext = att.file_name.split('.')[-1] if '.' in att.file_name else ''
            
            # --- 修复 Bug: Sanitization ---
            # 1. Sanitize slot_title (replace / with _)
            safe_slot_title = att.slot_title.replace('/', '_').replace('\\', '_')
            
            # 2. Extract RefNo
            ref_part = ""
            parts = att.file_name.split('_')
            if len(parts) >= 2:
                # Check if second part looks like a ref no (alphanumeric)
                # This is heuristic, but better than nothing
                candidate = parts[1]
                if candidate and all(c.isalnum() or c in '-.' for c in candidate):
                     ref_part = candidate
            
            if ref_part:
                download_name = f"{safe_slot_title}_{ref_part}.{ext}"
            else:
                download_name = f"{safe_slot_title}.{ext}"

        encoded_filename = quote(download_name)
        
        headers = {
            'Content-Type': nas_response.headers.get('Content-Type', 'application/octet-stream'),
            'Content-Length': nas_response.headers.get('Content-Length'),
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        if request.args.get('preview') == 'true':
            headers['Content-Disposition'] = 'inline'
            # 尝试根据扩展名设置正确的 Content-Type
            if att.file_type in ['pdf']:
                headers['Content-Type'] = 'application/pdf'
            elif att.file_type in ['jpg', 'jpeg']:
                headers['Content-Type'] = 'image/jpeg'
            elif att.file_type in ['png']:
                headers['Content-Type'] = 'image/png'
            
        return Response(
            nas_response.iter_content(chunk_size=8192),
            status=nas_response.status_code,
            headers=headers,
            direct_passthrough=True
        )

    @customs_bp.doc(summary="删除文件")
    @customs_bp.auth_required(auth)
    @permission_required('customs:edit')
    def delete(self, id, file_id):
        """
        删除归档文件
        """
        att = db.session.get(CustomsAttachment, file_id)
        if not att or att.declaration_id != id:
            raise BusinessError("File not found", 404)
            
        rel_path = customs_service.get_archive_path(id)
        file_path = f"{rel_path}/{att.file_path}"
        
        # 1. 删除 NAS 文件
        client = self._get_client()
        try:
            client.delete_file(file_path)
        except Exception as e:
            current_app.logger.error(f"NAS delete failed: {e}")
            # 如果 NAS 上文件已经没了，我们也应该允许删除数据库记录
            # 除非是连接错误
            pass
            
        # 2. 删除数据库记录
        db.session.delete(att)
        db.session.commit()
        
        return {'code': 0, 'message': 'success', 'data': None}


@customs_bp.route('/declarations/<int:id>/files/check-complete')
class DeclarationFilesCompleteCheckAPI(MethodView):
    decorators = [customs_bp.auth_required(auth)]
    
    @customs_bp.doc(summary="检查报关单资料是否齐全", description="检查报关单是否已上传所有必需文件，用于归档前验证")
    @customs_bp.output(Schema.from_dict({
        'is_complete': Boolean(metadata={'description': '是否齐全'}),
        'required_slots': List(String(), metadata={'description': '必需的文件槽位列表'}),
        'missing_slots': List(String(), metadata={'description': '缺失的文件槽位列表'}),
        'uploaded_slots': List(String(), metadata={'description': '已上传的文件槽位列表'}),
        'missing_count': Integer(metadata={'description': '缺失文件数量'})
    }))
    @permission_required('customs:view')
    def get(self, id):
        """
        检查报关单资料是否齐全
        
        返回：
        - is_complete: 是否齐全
        - required_slots: 必需的文件槽位列表
        - missing_slots: 缺失的文件槽位列表
        - uploaded_slots: 已上传的文件槽位列表
        - missing_count: 缺失文件数量
        """
        # 1. 获取报关单
        decl = customs_service.get_declaration(id)
        if not decl:
            raise BusinessError('报关单不存在', code=404)
        
        # 2. 获取必需的文件槽位（动态生成，根据整柜/散货自动调整）
        required_slots = decl.required_file_slots
        
        # 3. 获取已上传的文件槽位（去重）
        uploaded_slots_query = db.session.query(CustomsAttachment.slot_title).filter(
            CustomsAttachment.declaration_id == id,
            CustomsAttachment.slot_title.isnot(None)
        ).distinct().all()
        
        uploaded_slots = [slot[0] for slot in uploaded_slots_query if slot[0]]
        
        # 4. 计算缺失的槽位
        missing_slots = [slot for slot in required_slots if slot not in uploaded_slots]
        
        # 5. 判断是否齐全
        is_complete = len(missing_slots) == 0
        
        return {
            'data': {
                'is_complete': is_complete,
                'required_slots': required_slots,
                'missing_slots': missing_slots,
                'uploaded_slots': uploaded_slots,
                'missing_count': len(missing_slots)
            }
        }