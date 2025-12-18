import { requestClient } from '#/api/request';

/**
 * 文件信息接口
 */
export interface FileItem {
  id: number;          // 数据库 ID
  name: string;        // 显示文件名
  path: string;        // 相对路径
  category: string;    // 分类
  slot_title?: string; // 业务插槽
  size: number;
  file_type?: string;
  uploaded_by_name?: string;
  created_at?: string;
  
  // 新增同步状态字段
  status?: 'synced' | 'missing';
  source?: 'upload' | 'nas_sync';
  sync_message?: string;
  
  // 兼容旧字段 (可选)
  isdir?: boolean;
  mtime?: number; 
}

/**
 * 获取报关单归档文件列表
 */
export function getDeclarationFiles(id: number) {
  return requestClient.get<FileItem[]>(`/v1/customs/declarations/${id}/files`);
}

/**
 * 上传文件到报关单归档
 * @param id 报关单ID
 * @param file 文件对象
 * @param category 分类目录
 * @param slotTitle 插槽标题（用于自动重命名，可选）
 * @param onProgress 进度回调函数
 */
export function uploadDeclarationFile(
  id: number, 
  file: File, 
  category?: string, 
  slotTitle?: string,
  onProgress?: (progressEvent: any) => void
) {
  const formData = new FormData();
  formData.append('file', file);
  if (category) {
    formData.append('category', category);
  }
  if (slotTitle) {
    formData.append('slot_title', slotTitle);
  }

  return requestClient.post<FileItem>(
    `/v1/customs/declarations/${id}/files`, 
    formData, 
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress,
      timeout: 60000, // 增加超时时间到 60秒
    }
  );
}

/**
 * 获取文件下载/预览URL
 * @param id 报关单ID
 * @param fileId 文件数据库ID
 * @param preview 是否为预览模式 (inline)
 */
export function getDeclarationFileUrl(id: number, fileId: number, preview = false) {
  const baseUrl = import.meta.env.VITE_GLOB_API_URL || '/api';
  // URL 改为使用 fileId
  return `${baseUrl}/v1/customs/declarations/${id}/files/${fileId}?preview=${preview}`;
}

/**
 * 删除归档文件
 * @param id 报关单ID
 * @param fileId 文件数据库ID
 */
export function deleteDeclarationFile(id: number, fileId: number) {
  return requestClient.delete(`/v1/customs/declarations/${id}/files/${fileId}`);
}
