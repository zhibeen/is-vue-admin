import { type TaxCustomsDeclaration } from '#/api/customs/declaration';
import { computed } from 'vue';

// 模拟文档类型选中状态
export const docTypes = ['报关单', '装箱单', '发票', '申报要素', '合同', '委托书'];

// 常用申报单位映射
export const UNIT_MAP: Record<string, string> = {
  '007': '个',
  '035': '千克',
  '001': '台',
  '006': '套',
  '012': '支',
  '011': '双',
  '015': '包',
  '008': '只',
  '120': '箱'
};

export const getUnitName = (code: string) => {
    return UNIT_MAP[code] || code;
};

export const useDeclarationConfig = (detail: any) => {


  // --- 报关单 Tab 配置 ---
  const declarationFormItems = computed(() => [
    { label: '预录入编号', value: detail.value.pre_entry_no || '-', key: 'pre_entry_no', span: 1 },
    { label: '申报口岸', value: detail.value.entry_port || '-', key: 'entry_port', span: 1 },
    { label: '报关单单号', value: detail.value.customs_no || '-', key: 'customs_no', span: 1 },
    { label: '社会信用代码', value: '91330203316935152N', span: 1 },
    
    { label: '境内发货人', value: detail.value.internal_shipper_id ? '宁波华瑞逸德电子商务有限公司' : '-', span: 3 },
    { label: '出境关别', value: detail.value.departure_port || '-', key: 'departure_port', span: 1 },

    { label: '出口日期', value: detail.value.export_date, key: 'export_date', span: 1 },
    { label: '申报日期', value: detail.value.declare_date, key: 'declare_date', span: 1 },
    { label: '备案号', value: detail.value.filing_no || '-', key: 'filing_no', span: 1 },
    { label: 'AEO', value: '-', span: 1 },

    { label: '境外收货人', value: detail.value.overseas_consignee || '-', key: 'overseas_consignee', span: 3 },
    { label: '运输方式', value: detail.value.transport_mode || '-', key: 'transport_mode', span: 1 },

    { label: '运输工具名称及航次号', value: detail.value.conveyance_ref || '-', key: 'conveyance_ref', span: 2 },
    { label: '提运单号', value: detail.value.bill_of_lading_no || '-', key: 'bill_of_lading_no', span: 2 },

    { label: '生产销售单位', value: '宁波华瑞逸德电子商务有限公司', span: 2 },
    { label: '监管方式', value: detail.value.trade_mode || '-', key: 'trade_mode', span: 1 },
    { label: '征免性质', value: detail.value.nature_of_exemption || '-', key: 'nature_of_exemption', span: 1 },

    { label: '许可证号', value: detail.value.license_no || '-', key: 'license_no', span: 1 },
    { label: '合同协议号', value: detail.value.contract_no || '-', key: 'contract_no', span: 1 },
    { label: '贸易国(地区)', value: detail.value.trade_country || '-', key: 'trade_country', span: 1 },
    { label: '运抵国(地区)', value: detail.value.destination_country || '-', key: 'destination_country', span: 1 },

    { label: '指运港', value: detail.value.loading_port || '-', key: 'loading_port', span: 1 },
    { label: '离境口岸', value: detail.value.departure_port || '-', key: 'departure_port', span: 1 },
    { label: '包装种类', value: detail.value.package_type || '-', key: 'package_type', span: 2 },

    { label: '件数', value: detail.value.pack_count || '-', key: 'pack_count', span: 1 },
    { label: '净重(kg)', value: detail.value.net_weight, key: 'net_weight', span: 1 },
    { label: '毛重(kg)', value: detail.value.gross_weight, key: 'gross_weight', span: 1 },
    { label: '成交方式', value: detail.value.transaction_mode || '-', key: 'transaction_mode', span: 1 },

    { label: '运费', value: detail.value.freight || '-', key: 'freight', span: 1 },
    { label: '保费', value: detail.value.insurance || '-', key: 'insurance', span: 1 },
    { label: '杂费', value: detail.value.incidental || '-', key: 'incidental', span: 2 },

    { label: '特殊关系确认', value: '-', span: 1 },
    { label: '价格影响确认', value: '-', span: 1 },
    { label: '支付特许权使用费', value: '-', span: 1 },
    { label: '自报自缴', value: '-', span: 1 },

    { label: '随附单证及编号', value: detail.value.documents || '-', key: 'documents', span: 4 },
    { label: '标记唛码及备注', value: detail.value.marks_and_notes || '-', key: 'marks_and_notes', span: 4 },
    { label: '备注', value: '-', span: 4 },
  ]);

  const productColumns = [
    { title: '商品编号', dataIndex: 'hs_code', width: 120 },
    { title: '商品名称', dataIndex: 'product_name', width: 200, customRender: ({ text, record }: any) => record.product_name_spec?.split('|')[0] },
    { title: '规格型号', dataIndex: 'product_spec', width: 200, customRender: ({ text, record }: any) => record.product_name_spec?.split('|')[1] || '-' },
    { title: '品牌', dataIndex: 'brand', width: 100, customRender: () => '-' },
    { title: '数量及单位', dataIndex: 'qty_unit', width: 150, customRender: ({ record }: any) => 
      `${record.qty}${record.unit}`
    },
    { title: '净重', dataIndex: 'net_weight', width: 100, customRender: ({ record }: any) => record.net_weight || '-' },
    { title: '毛重', dataIndex: 'gross_weight', width: 100, customRender: ({ record }: any) => record.gross_weight || '-' },
    { title: '单价', dataIndex: 'usd_unit_price', width: 100, align: 'right' as const },
    { title: '总价', dataIndex: 'usd_total', width: 120, align: 'right' as const },
    { title: 'FOB单价', dataIndex: 'fob_unit_price', width: 100, align: 'right' as const },
    { title: '币制', dataIndex: 'currency', width: 80, customRender: () => detail.value.currency || 'USD' },
    { title: '原产地(地区)', dataIndex: 'origin_country', width: 120 },
    { title: '最终目的国(地区)', dataIndex: 'final_dest_country', width: 120 },
    { title: '境内货源地', dataIndex: 'district_code', width: 120 },
    { title: '采购单号', dataIndex: 'po_no', width: 120, customRender: () => '-' },
    { title: '征免', dataIndex: 'exemption_way', width: 100, customRender: ({ text }: any) => text || '照章征税' },
  ];

  // --- 装箱单/发票 Tab 配置 ---
  const packingInfoConfig = computed(() => [
      { label: '客户 To Messrs', value: detail.value.overseas_consignee, span: 1 },
      { label: '合同号 Contract No', value: detail.value.contract_no, span: 1 },
      { label: '发票编号 Invoice No', value: detail.value.contract_no, span: 1 }, 
      { label: '日期 Date', value: detail.value.export_date, span: 1 },
      { label: '船名 Shipped by', value: detail.value.conveyance_ref, span: 1 },
      { label: '由深圳至 From', value: detail.value.loading_port, span: 1 },
      { label: '付款条件 Terms of Payment', value: '-', span: 1 },
      { label: '唛头 Marks', value: '宁波华瑞逸德电子商务有限公司', span: 1 },
  ]);

  const packingListColumns = [
    { title: '箱号', dataIndex: 'box_no', width: 80 },
    { title: '箱数', dataIndex: 'pack_qty', width: 80, customRender: () => '1' }, 
    { title: '箱规', dataIndex: 'size', width: 120, customRender: () => '0 x 0 x 0' },
    { title: '体积（CBM）', dataIndex: 'cbm', width: 100 },
    { title: '净重(kg)', dataIndex: 'net_weight', width: 100 },
    { title: '毛重(kg)', dataIndex: 'gross_weight', width: 100 },
    { title: '货物名称及规格', dataIndex: 'product_name_spec', width: 200, customRender: ({text}: any) => text?.split('|')[0] },
    { title: '品牌', dataIndex: 'brand', width: 100, customRender: () => '-' },
    { title: '型号', dataIndex: 'model', width: 100, customRender: () => '-' },
    { title: '单箱数量', dataIndex: 'qty_per_box', width: 100, customRender: ({record}: any) => record.qty },
    { title: '数量及单位', dataIndex: 'qty_unit', width: 150, customRender: ({ record }: any) => `${record.qty}${record.unit}` },
  ];

  const invoiceColumns = [
      { title: '货物名称', dataIndex: 'product_name_spec', width: 200, customRender: ({text}: any) => text?.split('|')[0] },
      { title: '品牌', dataIndex: 'brand', width: 100, customRender: () => '-' },
      { title: '型号', dataIndex: 'model', width: 100, customRender: () => '-' },
      { title: '海关编码', dataIndex: 'hs_code', width: 120 },
      { title: '数量及单位', dataIndex: 'qty_unit', width: 150, customRender: ({ record }: any) => `${record.qty}${record.unit}` },
      { title: '单价($)', dataIndex: 'usd_unit_price', width: 100, align: 'right' as const },
      { title: '总金额($)', dataIndex: 'usd_total', width: 120, align: 'right' as const },
      { title: '币制', dataIndex: 'currency', width: 80, customRender: () => 'USD' },
  ];

  // --- 申报要素 Tab 配置 ---
  const elementColumns = [
      { title: '品名', dataIndex: 'product_name_spec', width: 150, customRender: ({text}: any) => text?.split('|')[0] },
      { title: '海关HS编码', dataIndex: 'hs_code', width: 120 },
      { title: '检疫附加码', dataIndex: 'ciq_code', width: 100, customRender: () => '-' },
      { title: '品牌', dataIndex: 'brand', width: 100, customRender: () => '-' },
      { title: '产品长宽厚', dataIndex: 'dimensions', width: 120, customRender: () => '0 x 0 x 0' },
      { title: '产品重量(g)', dataIndex: 'weight_g', width: 100, customRender: () => '0' },
      { title: '型号', dataIndex: 'model', width: 100, customRender: () => '-' },
      { title: '品牌类型', dataIndex: 'brand_type', width: 100, customRender: () => '无品牌' },
      { title: '出口享惠情况', dataIndex: 'benefit', width: 120, customRender: () => '不享惠' },
      { title: '其他申报要素', dataIndex: 'other_elements', width: 200, customRender: () => '-' },
  ];

  // --- 合同 Tab 配置 ---
  const contractInfoConfig = computed(() => [
      { label: '合同号 Contract No', value: detail.value.contract_no, span: 1 },
      { label: '日期 Date', value: detail.value.export_date, span: 1 },
      { label: '签约地点 Signed at', value: '-', span: 1 },
      { label: '成交方式 Trade Term', value: detail.value.transaction_mode || 'FOB', span: 1 },
      
      { label: '包装及唛头 Packing and shipping Marks', value: '-', span: 4 },
      
      { label: '装运期 Time of Shipment', value: '之前', span: 1 },
      { label: '付款条件 Terms of Payment', value: '-', span: 1 },
      { label: '装运标记 Shipping Marks', value: '-', span: 2 },
      
      { label: '卖方 Sellers', value: '宁波华瑞逸德电子商务有限公司', span: 1 },
      { label: '卖方电话 TEL', value: '-', span: 1 },
      { label: '卖方传真 FAX', value: '-', span: 1 },
      { label: '卖方地址 Address', value: '浙江省宁波市鄞州区天智巷359号6-1-8室', span: 1 },
      
      { label: '买方 Buyers', value: detail.value.overseas_consignee, span: 1 },
      { label: '买方电话 TEL', value: '-', span: 1 },
      { label: '买方传真 FAX', value: '-', span: 1 },
      { label: '买方地址 Address', value: '-', span: 1 },
  ]);

  // --- 委托书 Tab 配置 ---
  const proxyInfoConfig = computed(() => [
      { label: '委托方式', value: '-', span: 1 },
      { label: '委托事项', value: '-', span: 1 },
      { label: '签字日期', value: '-', span: 1 },
      { label: '有效截止期', value: '-', span: 1 },
      
      { label: '委托方', value: '宁波华瑞逸德电子商务有限公司', span: 1 },
      { label: '委托人电话', value: '-', span: 1 },
      { label: '提运单号', value: detail.value.bill_of_lading_no || 'ONEYSH5ACAJ68700', span: 1 },
      { label: '贸易方式', value: '跨境电商出口海外仓', span: 1 },
      
      { label: '进出口日期', value: '-', span: 1 },
      { label: '包装情况', value: '纸制或纤维板制盒/箱', span: 1 },
      { label: '净重(kg)', value: detail.value.net_weight, span: 1 },
      { label: '毛重(kg)', value: detail.value.gross_weight, span: 1 },
      
      { label: '货源地', value: '常州', span: 1 },
      { label: '被委托方', value: '-', span: 1 },
      { label: '报关单编号', value: '-', span: 1 },
      { label: '收到单证日期', value: '-', span: 1 },
      
      { label: '收到单证情况', value: '-', span: 2 },
      { label: '报关收费', value: '-', span: 2 },
      { label: '委托其他要求', value: '-', span: 4 },
      { label: '被委托承诺说明', value: '-', span: 4 },
  ]);

  return {
    declarationFormItems,
    productColumns,
    packingInfoConfig,
    packingListColumns,
    invoiceColumns,
    elementColumns,
    contractInfoConfig,
    proxyInfoConfig
  };
};
