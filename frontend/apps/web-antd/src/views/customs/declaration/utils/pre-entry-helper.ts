/**
 * 预录入编号工具函数
 */

import type { SysCompany } from '#/api/serc/model';

/**
 * 生成预录入编号预览
 * @param companyCode 公司代码
 * @returns 预录入编号格式示例，如：HR-YL-2412-XXXX
 */
export function generatePreEntryPreview(companyCode?: string): string {
  if (!companyCode) {
    return '-';
  }
  
  const now = new Date();
  const yy = String(now.getFullYear()).slice(2); // 24
  const mm = String(now.getMonth() + 1).padStart(2, '0'); // 12
  const yymm = `${yy}${mm}`; // 2412
  
  return `${companyCode}-YL-${yymm}-XXXX`;
}

/**
 * 从公司列表中查找公司并生成预览
 * @param companyId 公司ID
 * @param companies 公司列表
 * @returns 预录入编号格式示例
 */
export function getPreEntryPreviewByCompanyId(
  companyId: number | undefined,
  companies: SysCompany[]
): string {
  if (!companyId) {
    return '-';
  }
  
  const company = companies.find(c => c.id === companyId);
  return generatePreEntryPreview(company?.code);
}

/**
 * 解析预录入编号
 * @param preEntryNo 预录入编号，如：HR-YL-2412-0001
 * @returns 解析结果
 */
export function parsePreEntryNo(preEntryNo?: string): {
  companyCode: string;
  prefix: string;
  yearMonth: string;
  seq: string;
  isValid: boolean;
} | null {
  if (!preEntryNo) {
    return null;
  }
  
  // 格式：{COMPANY_CODE}-YL-{YYMM}-{SEQ}
  const parts = preEntryNo.split('-');
  if (parts.length !== 4) {
    return {
      companyCode: '',
      prefix: '',
      yearMonth: '',
      seq: '',
      isValid: false
    };
  }
  
  return {
    companyCode: parts[0],
    prefix: parts[1],
    yearMonth: parts[2],
    seq: parts[3],
    isValid: parts[1] === 'YL' && parts[2].length === 4 && parts[3].length === 4
  };
}

/**
 * 格式化预录入编号显示（添加样式提示）
 * @param preEntryNo 预录入编号
 * @returns 格式化后的字符串
 */
export function formatPreEntryNoDisplay(preEntryNo?: string): string {
  if (!preEntryNo) {
    return '未生成';
  }
  
  const parsed = parsePreEntryNo(preEntryNo);
  if (!parsed || !parsed.isValid) {
    return preEntryNo; // 返回原值
  }
  
  // 可以在此添加更多格式化逻辑
  return preEntryNo;
}

