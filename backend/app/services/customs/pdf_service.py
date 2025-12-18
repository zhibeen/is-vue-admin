"""
报关单PDF生成服务
使用 WeasyPrint 从HTML生成PDF文档（更好的中文支持）
"""
from io import BytesIO
from weasyprint import HTML, CSS
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)


def generate_declaration_pdf(declaration, includes: List[str], current_user=None) -> BytesIO:
    """
    生成报关单PDF
    
    Args:
        declaration: 报关单对象
        includes: 包含的内容类型列表 ['declaration', 'packing', 'invoice', ...]
        current_user: 当前下载用户对象（可选）
    
    Returns:
        BytesIO: PDF文件流
    """
    # 生成HTML内容
    html_content = _build_html_content(declaration, includes, current_user)
    
    # 使用WeasyPrint生成PDF
    buffer = BytesIO()
    HTML(string=html_content).write_pdf(buffer, stylesheets=[CSS(string=_get_css_styles())])
    buffer.seek(0)
    
    return buffer


def _get_css_styles() -> str:
    """获取PDF样式 - 仿官方报关单格式（横版）"""
    return """
        @page {
            size: A4 landscape;
            margin: 1cm 1.5cm 2.5cm 1.5cm; /* 顶部 右边 底部（给页脚留2.5cm空间） 左边 */
            
            @bottom-left {
                content: element(page-footer);
                font-size: 6.5pt;
                color: #666;
                border-top: 1px solid #ccc;
                padding-top: 5px;
                width: 100%;
            }
        }
        body {
            font-family: "SimSun", "Microsoft YaHei", serif;
            font-size: 8pt;
            line-height: 1.3;
            color: #000;
        }
        
        /* 报关单标题（横版） */
        .declaration-title {
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 5px;
            border-bottom: 3px double #000;
            padding-bottom: 5px;
            letter-spacing: 2px;
        }
        
        .declaration-subtitle {
            text-align: center;
            font-size: 10pt;
            margin-bottom: 12px;
            color: #333;
        }
        
        /* 基本信息区块（横版优化） */
        .info-section {
            border: 2px solid #000;
            padding: 10px;
            margin-bottom: 10px;
            page-break-inside: avoid; /* 防止信息区跨页分割 */
        }
        
        .info-row {
            display: flex;
            margin-bottom: 4px;
            font-size: 8pt;
            align-items: center;
            page-break-inside: avoid; /* 防止单行信息跨页分割 */
        }
        
        .info-label {
            font-weight: bold;
            min-width: 110px;
            color: #000;
            white-space: nowrap;
        }
        
        .info-value {
            flex: 1;
            padding: 2px 5px;
            min-height: 18px;
        }
        
        /* 官方格式的表格（横版优化） */
        .declaration-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 10px;
            font-size: 7pt;
            page-break-inside: auto; /* 表格可以跨页，但行不能 */
        }
        
        .declaration-table thead {
            display: table-header-group; /* 表头在每页重复显示 */
        }
        
        .declaration-table tr {
            page-break-inside: avoid; /* 防止表格行跨页分割 */
            page-break-after: auto;
        }
        
        .declaration-table th,
        .declaration-table td {
            border: 1px solid #000;
            padding: 3px 4px;
            text-align: center;
            vertical-align: middle;
        }
        
        .declaration-table th {
            background-color: #e8e8e8;
            font-weight: bold;
            font-size: 7pt;
            line-height: 1.2;
        }
        
        .declaration-table td {
            background-color: #fff;
            line-height: 1.2;
        }
        
        /* 合计行 */
        .declaration-table .total-row {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        
        .signature-line {
            margin-top: 30px;
            border-top: 1px solid #000;
            text-align: center;
            padding-top: 3px;
            font-size: 7pt;
        }
        
        /* 页脚 - 使用 running() 在每页左下角显示 */
        .page-footer {
            position: running(page-footer);
            font-size: 6.5pt;
            color: #666;
            line-height: 1.4;
        }
        
        .page-break {
            page-break-after: always;
        }
    """


def _build_html_content(declaration, includes: List[str], current_user=None) -> str:
    """构建HTML内容 - 仿官方报关单格式"""
    sections = []
    
    # 获取制单人信息
    creator_name = '-'
    if declaration.creator:
        creator_name = declaration.creator.realname or declaration.creator.username or '-'
    creator_time = declaration.created_at.strftime('%Y-%m-%d %H:%M') if declaration.created_at else '-'
    
    # 获取下载人信息
    downloader_name = '-'
    if current_user:
        downloader_name = current_user.realname or current_user.username or '-'
    download_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 获取申报单位
    shipper_name = '-'
    if declaration.internal_shipper:
        shipper_name = getattr(declaration.internal_shipper, 'legal_name', None) or getattr(declaration.internal_shipper, 'name', '-')
    
    # 页脚 - 必须放在文档开头，running()机制才能在所有页面生效
    footer_content = f"""
        <div class="page-footer">
            预录入编号：{declaration.pre_entry_no or 'N/A'} | 
            申报单位：{shipper_name} | 
            制单人：{creator_name} ({creator_time}) | 
            下载人：{downloader_name} ({download_time})
        </div>
    """
    sections.append(footer_content)
    
    # 根据包含的内容动态生成标题
    title = ""
    subtitle = f"预录入编号：{declaration.pre_entry_no or 'N/A'}"
    
    if 'files' in includes:
        # 归档资料清单标题
        title = "随附单证清单"
        subtitle += " | Attached Documents List"
    elif len(includes) == 1:
        # 单一文档类型，使用专属标题
        doc_titles = {
            'declaration': '报关单',
            'packing': '装箱单 / Packing List',
            'invoice': '商业发票 / Commercial Invoice',
            'contract': '销售合同 / Sales Contract',
            'proxy': '报关委托书 / Customs Clearance Authorization'
        }
        title = doc_titles.get(includes[0], '报关单')
    else:
        # 多个文档类型，使用通用标题
        title = "报关单资料汇总"
    
    sections.append(f"""
        <div class="declaration-title">{title}</div>
        <div class="declaration-subtitle">{subtitle}</div>
    """)
    
    # 1. 报关单主表
    if 'declaration' in includes:
        sections.append(_generate_declaration_html(declaration, current_user))
    
    # 2. 装箱单
    if 'packing' in includes:
        sections.append('<div class="page-break"></div>')
        sections.append(_generate_packing_html(declaration))
    
    # 3. 发票
    if 'invoice' in includes:
        sections.append('<div class="page-break"></div>')
        sections.append(_generate_invoice_html(declaration))
    
    # 4. 合同
    if 'contract' in includes:
        sections.append('<div class="page-break"></div>')
        sections.append(_generate_contract_html(declaration))
    
    # 5. 委托书
    if 'proxy' in includes:
        sections.append('<div class="page-break"></div>')
        sections.append(_generate_proxy_html(declaration))
    
    # 6. 归档资料清单（不添加 page-break，因为标题已经在上面了）
    if 'files' in includes:
        sections.append(_generate_files_html(declaration))
    
    return f"<html><body>{''.join(sections)}</body></html>"


def _generate_declaration_html(decl, current_user=None) -> str:
    """生成报关单主表HTML - 仿官方格式（横版）"""
    result = '<div class="info-section">'
    
    # 获取申报单位（境内发货人）
    internal_shipper_name = '-'
    if decl.internal_shipper:
        internal_shipper_name = getattr(decl.internal_shipper, 'legal_name', None) or getattr(decl.internal_shipper, 'name', '-')
    
    # 获取制单人
    creator_name = '-'
    creator_date = '-'
    if decl.creator:
        creator_name = decl.creator.realname or decl.creator.username or '-'
        if decl.created_at:
            creator_date = decl.created_at.strftime('%Y-%m-%d %H:%M')
    
    # 获取下载人
    downloader_name = '-'
    download_date = '-'
    if current_user:
        downloader_name = current_user.realname or current_user.username or '-'
        from datetime import datetime
        download_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # HTML转义所有文本字段
    import html as html_module
    
    # 包装种类代码映射（海关代码 -> 中文说明）
    PACKAGE_TYPE_MAP = {
        '1': '散装',
        '2': '托盘',
        '3': '集装箱',
        '4': '木箱',
        '5': '纸箱',
        '6': '桶',
        '7': '袋',
        '8': '包',
        '9': '罐',
        '1M': '散装',
        '2M': '托盘',
        '3M': '集装箱',
        '4M': '纸箱',
        '5M': '木箱',
        '6M': '桶',
        '7M': '袋',
        '8M': '包',
        '9M': '罐',
        'PK': '包',
        'CT': '纸箱',
        'CS': '箱',
        'BX': '盒',
        'BA': '桶',
        'DR': '桶',
        'PL': '托盘',
        'SK': '袋',
    }
    
    # 监管方式代码映射
    TRADE_MODE_MAP = {
        '0110': '一般贸易',
        '0214': '来料加工',
        '0215': '进料加工',
        '1039': '来料设备',
        '9610': '跨境电商B2C',
        '9710': '跨境电商B2B直接出口',
        '9810': '跨境电商出口海外仓',
        '1210': '保税跨境贸易电子商务',
        '1239': '保税区仓储转口货物',
        '3039': '无代价抵偿货物',
        '2025': '暂时进出境货物',
    }
    
    # 征免性质代码映射
    EXEMPTION_NATURE_MAP = {
        '101': '照章征税',
        '301': '其他法定',
        '501': '特定地区',
        '502': '特定企业',
        '503': '特定用途',
        '601': '减免税货物',
        '799': '暂免征税',
        '801': '加工贸易',
    }
    
    # 转换包装种类为"代码 - 中文"格式
    package_type_display = '-'
    if decl.package_type:
        code = decl.package_type.strip().upper()
        if code in PACKAGE_TYPE_MAP:
            package_type_display = f"{code} - {PACKAGE_TYPE_MAP[code]}"
        else:
            package_type_display = code  # 未知代码直接显示
    
    # 转换监管方式为"代码 - 中文"格式
    trade_mode_display = '-'
    if decl.trade_mode:
        code = decl.trade_mode.strip()
        if code in TRADE_MODE_MAP:
            trade_mode_display = f"{code} - {TRADE_MODE_MAP[code]}"
        else:
            trade_mode_display = code
    
    # 转换征免性质为"代码 - 中文"格式
    exemption_nature_display = '-'
    if decl.nature_of_exemption:
        code = decl.nature_of_exemption.strip()
        if code in EXEMPTION_NATURE_MAP:
            exemption_nature_display = f"{code} - {EXEMPTION_NATURE_MAP[code]}"
        else:
            exemption_nature_display = code
    
    pre_entry_no = html_module.escape(decl.pre_entry_no or '-')
    customs_no = html_module.escape(decl.customs_no or '-')
    internal_shipper_name = html_module.escape(internal_shipper_name)
    overseas_consignee = html_module.escape(decl.overseas_consignee or '-')
    transport_mode = html_module.escape(decl.transport_mode or '-')
    conveyance_ref = html_module.escape(decl.conveyance_ref or '-')
    bill_of_lading_no = html_module.escape(decl.bill_of_lading_no or '-')
    transaction_mode = html_module.escape(decl.transaction_mode or '-')
    currency = html_module.escape(decl.currency or 'USD')
    contract_no = html_module.escape(decl.contract_no or '-')
    entry_port = html_module.escape(decl.entry_port or '-')
    departure_port = html_module.escape(decl.departure_port or '-')
    loading_port = html_module.escape(decl.loading_port or '-')
    destination_country = html_module.escape(decl.destination_country or '-')
    trade_country = html_module.escape(decl.trade_country or '-')
    creator_name = html_module.escape(creator_name)
    creator_date = html_module.escape(creator_date)
    downloader_name = html_module.escape(downloader_name)
    download_date = html_module.escape(download_date)
    
    # 计算体积总和
    total_cbm_display = '-'
    if decl.items:
        total_cbm_value = sum(float(getattr(item, 'cbm', 0) or 0) for item in decl.items)
        total_cbm_display = f'{total_cbm_value:.4f}'
    
    # 基本信息（横版布局，每行3个字段）
    result += f'''
        <div class="info-row">
            <span class="info-label">海关编号：</span>
            <span class="info-value">{customs_no}</span>
            <span class="info-label">预录入编号：</span>
            <span class="info-value">{pre_entry_no}</span>
            <span class="info-label">申报口岸：</span>
            <span class="info-value">{entry_port}</span>
        </div>
        <div class="info-row">
            <span class="info-label">境内发货人：</span>
            <span class="info-value" style="flex: 2;">{internal_shipper_name}</span>
            <span class="info-label">境外收货人：</span>
            <span class="info-value" style="flex: 2;">{overseas_consignee}</span>
        </div>
        <div class="info-row">
            <span class="info-label">合同协议号：</span>
            <span class="info-value">{contract_no}</span>
            <span class="info-label">申报日期：</span>
            <span class="info-value">{str(decl.declare_date) if decl.declare_date else '-'}</span>
            <span class="info-label">出口日期：</span>
            <span class="info-value">{str(decl.export_date) if decl.export_date else '-'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">运输方式：</span>
            <span class="info-value">{transport_mode}</span>
            <span class="info-label">运输工具名称及航次号：</span>
            <span class="info-value" style="flex: 2;">{conveyance_ref}</span>
        </div>
        <div class="info-row">
            <span class="info-label">提运单号：</span>
            <span class="info-value">{bill_of_lading_no}</span>
            <span class="info-label">出境关别：</span>
            <span class="info-value">{departure_port}</span>
            <span class="info-label">指运港：</span>
            <span class="info-value">{loading_port}</span>
        </div>
        <div class="info-row">
            <span class="info-label">运抵国（地区）：</span>
            <span class="info-value">{destination_country}</span>
            <span class="info-label">贸易国（地区）：</span>
            <span class="info-value">{trade_country}</span>
            <span class="info-label">币种：</span>
            <span class="info-value">{currency}</span>
        </div>
        <div class="info-row">
            <span class="info-label">监管方式：</span>
            <span class="info-value">{html_module.escape(trade_mode_display)}</span>
            <span class="info-label">征免性质：</span>
            <span class="info-value">{html_module.escape(exemption_nature_display)}</span>
            <span class="info-label">成交方式：</span>
            <span class="info-value">{transaction_mode}</span>
        </div>
        <div class="info-row">
            <span class="info-label">件数：</span>
            <span class="info-value">{decl.pack_count or '-'}</span>
            <span class="info-label">包装种类：</span>
            <span class="info-value">{html_module.escape(package_type_display)}</span>
            <span class="info-label">毛重(KG)：</span>
            <span class="info-value">{decl.gross_weight or '-'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">净重(KG)：</span>
            <span class="info-value">{decl.net_weight or '-'}</span>
            <span class="info-label">体积(CBM)：</span>
            <span class="info-value">{total_cbm_display}</span>
            <span class="info-label"></span>
            <span class="info-value"></span>
        </div>
    </div>
    '''
    
    # 商品明细（官方格式表格 - 横版优化，包含申报要素）
    if decl.items:
        result += '''
        <table class="declaration-table">
            <thead>
                <tr>
                    <th style="width: 25px;">项号</th>
                    <th style="width: 60px;">商品编号</th>
                    <th style="width: 100px;">商品名称</th>
                    <th style="width: 150px;">申报要素</th>
                    <th style="width: 50px;">数量</th>
                    <th style="width: 30px;">单位</th>
                    <th style="width: 50px;">单价(USD)</th>
                    <th style="width: 60px;">总价(USD)</th>
                    <th style="width: 50px;">净重(KG)</th>
                    <th style="width: 50px;">毛重(KG)</th>
                    <th style="width: 50px;">体积(CBM)</th>
                    <th style="width: 45px;">原产国</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        total_amount = 0
        total_net_weight = 0
        total_gross_weight = 0
        total_cbm = 0
        
        for idx, item in enumerate(decl.items, 1):
            # 安全转换数值类型
            qty = float(item.qty) if item.qty else 0
            unit_price = float(item.usd_unit_price) if item.usd_unit_price else 0
            total = float(item.usd_total) if item.usd_total else 0
            net_weight = float(item.net_weight) if item.net_weight else 0
            gross_weight = float(item.gross_weight) if item.gross_weight else 0
            cbm = float(getattr(item, 'cbm', 0)) if getattr(item, 'cbm', None) else 0
            
            total_amount += total
            total_net_weight += net_weight
            total_gross_weight += gross_weight
            total_cbm += cbm
            
            # 获取商品名称
            product_name = item.product.name if item.product else (item.product_name_spec or '-')
            
            # 构建申报要素
            elements = []
            
            # 1. 品名
            elements.append(f"1.品名:{product_name}")
            
            # 2. 品牌
            if item.product and hasattr(item.product, 'brand') and item.product.brand:
                elements.append(f"2.品牌:{item.product.brand}")
            else:
                elements.append("2.品牌:无品牌")
            
            # 3. 型号/规格
            if item.product_name_spec:
                elements.append(f"3.规格:{item.product_name_spec[:30]}")
            else:
                elements.append("3.规格:-")
            
            # 4. 原产国
            origin = item.origin_country or '中国'
            elements.append(f"4.原产国:{origin}")
            
            # 5. 用途
            elements.append("5.用途:汽车零配件")
            
            elements_text = "; ".join(elements)
            
            # HTML转义，防止XSS和格式问题
            product_name = html_module.escape(product_name)
            elements_text = html_module.escape(elements_text)
            hs_code = html_module.escape(item.hs_code or '-')
            unit = html_module.escape(item.unit or '')
            origin_country = html_module.escape(origin)
            
            result += f'''
                <tr>
                    <td style="text-align:center;">{idx}</td>
                    <td style="text-align:center; font-size:7pt;">{hs_code}</td>
                    <td style="text-align:left; padding-left:3px; font-size:7pt;">{product_name}</td>
                    <td style="text-align:left; padding-left:3px; font-size:6pt; line-height:1.2;">{elements_text}</td>
                    <td style="text-align:right;">{qty:.2f}</td>
                    <td style="text-align:center;">{unit}</td>
                    <td style="text-align:right;">{unit_price:.4f}</td>
                    <td style="text-align:right; font-weight:bold;">{total:.2f}</td>
                    <td style="text-align:right;">{net_weight:.2f}</td>
                    <td style="text-align:right;">{gross_weight:.2f}</td>
                    <td style="text-align:right;">{cbm:.4f}</td>
                    <td style="text-align:center; font-size:7pt;">{origin_country}</td>
                </tr>
            '''
        
        # 合计行
        result += f'''
                <tr class="total-row">
                    <td colspan="7" style="text-align:right; font-weight:bold; padding-right:10px;">合计：</td>
                    <td style="text-align:right; font-weight:bold;">{total_amount:.2f}</td>
                    <td style="text-align:right; font-weight:bold;">{total_net_weight:.2f}</td>
                    <td style="text-align:right; font-weight:bold;">{total_gross_weight:.2f}</td>
                    <td style="text-align:right; font-weight:bold;">{total_cbm:.4f}</td>
                    <td></td>
                </tr>
            </tbody>
        </table>
        '''
    
    return result


def _generate_packing_html(decl) -> str:
    """生成装箱单HTML - 专业格式"""
    import html as html_module
    
    # 获取发货人和收货人信息
    shipper_name = "-"
    if decl.internal_shipper:
        shipper_name = getattr(decl.internal_shipper, 'legal_name', None) or getattr(decl.internal_shipper, 'name', '-')
    shipper_name = html_module.escape(shipper_name)
    consignee = html_module.escape(decl.overseas_consignee or '-')
    
    result = f'''
        <div style="text-align:center; font-size:18pt; font-weight:bold; margin-bottom:20px; letter-spacing:2px;">
            装箱单 / PACKING LIST
        </div>
        
        <div style="margin-bottom:15px;">
            <table style="width:100%; border-collapse:collapse; font-size:9pt;">
                <tr>
                    <td style="width:15%; font-weight:bold;">发货人 Shipper:</td>
                    <td style="width:35%; border-bottom:1px solid #999;">{shipper_name}</td>
                    <td style="width:15%; font-weight:bold;">日期 Date:</td>
                    <td style="width:35%; border-bottom:1px solid #999;">{str(decl.export_date) if decl.export_date else '-'}</td>
                </tr>
                <tr><td colspan="4" style="height:10px;"></td></tr>
                <tr>
                    <td style="font-weight:bold;">收货人 Consignee:</td>
                    <td style="border-bottom:1px solid #999;">{consignee}</td>
                    <td style="font-weight:bold;">提单号 B/L No:</td>
                    <td style="border-bottom:1px solid #999;">{html_module.escape(decl.bill_of_lading_no or '-')}</td>
                </tr>
                <tr><td colspan="4" style="height:10px;"></td></tr>
                <tr>
                    <td style="font-weight:bold;">运输方式 Shipment:</td>
                    <td style="border-bottom:1px solid #999;">{html_module.escape(decl.transport_mode or '-')}</td>
                    <td style="font-weight:bold;">目的地 Destination:</td>
                    <td style="border-bottom:1px solid #999;">{html_module.escape(decl.destination_country or '-')}</td>
                </tr>
            </table>
        </div>
    '''
    
    # 商品明细表
    if decl.items:
        result += '''
        <table class="declaration-table">
            <thead>
                <tr>
                    <th style="width:30px;">项号<br/>No.</th>
                    <th style="width:110px;">商品描述<br/>Description</th>
                    <th style="width:110px;">英文名称<br/>English Name</th>
                    <th style="width:60px;">HS编码<br/>HS Code</th>
                    <th style="width:45px;">件数<br/>Pcs</th>
                    <th style="width:50px;">数量<br/>Qty</th>
                    <th style="width:35px;">单位<br/>Unit</th>
                    <th style="width:60px;">毛重(KG)<br/>G.W.</th>
                    <th style="width:60px;">净重(KG)<br/>N.W.</th>
                    <th style="width:65px;">体积(CBM)<br/>Vol.</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        total_qty = 0
        total_gw = 0
        total_nw = 0
        total_cbm = 0
        total_pieces = 0  # 件数合计
        
        for idx, item in enumerate(decl.items, 1):
            # 商品中文名称
            product_desc = item.product.name if item.product else (item.product_name_spec or '-')
            product_desc = html_module.escape(product_desc)
            
            # 商品英文名称（从报关单明细字段读取）
            product_en_name = html_module.escape(item.product_name_en_spec or '-')
            
            # HS编码
            hs_code = html_module.escape(item.hs_code or '-')
            
            # 件数：pack_count 字段表示该商品项的件数（一箱多件）
            pieces = int(getattr(item, 'pack_count', 1)) if getattr(item, 'pack_count', None) else 1
            qty = float(item.qty) if item.qty else 0
            unit = html_module.escape(item.unit or '')
            gw = float(item.gross_weight) if item.gross_weight else 0
            nw = float(item.net_weight) if item.net_weight else 0
            cbm = float(getattr(item, 'cbm', 0)) if getattr(item, 'cbm', None) else 0
            
            total_qty += qty
            total_gw += gw
            total_nw += nw
            total_cbm += cbm
            total_pieces += pieces  # 累加件数
            
            result += f'''
                <tr>
                    <td style="text-align:center;">{idx}</td>
                    <td style="text-align:left; padding-left:3px; font-size:7pt; line-height:1.3;">{product_desc}</td>
                    <td style="text-align:left; padding-left:3px; font-size:7pt; line-height:1.3;">{product_en_name}</td>
                    <td style="text-align:center; font-size:7pt;">{hs_code}</td>
                    <td style="text-align:center;">{pieces}</td>
                    <td style="text-align:right;">{qty:.2f}</td>
                    <td style="text-align:center; font-size:7pt;">{unit}</td>
                    <td style="text-align:right;">{gw:.2f}</td>
                    <td style="text-align:right;">{nw:.2f}</td>
                    <td style="text-align:right;">{cbm:.4f}</td>
                </tr>
            '''
        
        # 合计行
        result += f'''
                <tr class="total-row">
                    <td colspan="4" style="text-align:right; font-weight:bold;">合计 TOTAL:</td>
                    <td style="text-align:center; font-weight:bold;">{total_pieces}</td>
                    <td style="text-align:right; font-weight:bold;">{total_qty:.2f}</td>
                    <td></td>
                    <td style="text-align:right; font-weight:bold;">{total_gw:.2f}</td>
                    <td style="text-align:right; font-weight:bold;">{total_nw:.2f}</td>
                    <td style="text-align:right; font-weight:bold;">{total_cbm:.4f}</td>
                </tr>
            </tbody>
        </table>
        '''
    
    # 签名区
    result += '''
        <div style="margin-top:40px;">
            <table style="width:100%; font-size:9pt;">
                <tr>
                    <td style="width:50%;">
                        <div style="font-weight:bold; margin-bottom:30px;">制单人签字 Prepared by:</div>
                        <div style="border-top:1px solid #000; width:200px; text-align:center; padding-top:5px;">签名 Signature</div>
                    </td>
                    <td style="width:50%; text-align:right;">
                        <div style="font-weight:bold; margin-bottom:30px;">公司盖章 Company Seal:</div>
                        <div style="text-align:center; padding-top:20px;">(此处盖章)</div>
                    </td>
                </tr>
            </table>
        </div>
    '''
    
    return result


def _generate_invoice_html(decl) -> str:
    """生成商业发票HTML - 国际贸易标准格式"""
    import html as html_module
    
    # 获取发货人完整信息（含英文和地址）
    shipper_info = []
    if decl.internal_shipper:
        # 中文名称
        if decl.internal_shipper.legal_name:
            shipper_info.append(decl.internal_shipper.legal_name)
        # 英文名称
        if decl.internal_shipper.english_name:
            shipper_info.append(decl.internal_shipper.english_name)
        # 地址
        address = decl.internal_shipper.business_address or decl.internal_shipper.registered_address
        if address:
            shipper_info.append(f"地址 Address: {address}")
        # 联系方式
        if decl.internal_shipper.contact_phone:
            shipper_info.append(f"电话 Tel: {decl.internal_shipper.contact_phone}")
        if decl.internal_shipper.contact_email:
            shipper_info.append(f"邮箱 Email: {decl.internal_shipper.contact_email}")
    
    shipper_display = "<br/>".join(shipper_info) if shipper_info else "-"
    consignee = html_module.escape(decl.overseas_consignee or '-')
    
    # 发票号使用预录入编号或海关编号
    invoice_no = decl.pre_entry_no or decl.customs_no or f"INV-{decl.id}"
    
    result = f'''
        <div style="text-align:center; font-size:18pt; font-weight:bold; margin-bottom:20px; letter-spacing:2px;">
            商业发票 / COMMERCIAL INVOICE
        </div>
        
        <div style="margin-bottom:15px;">
            <table style="width:100%; border-collapse:collapse; font-size:9pt;">
                <tr>
                    <td style="width:50%; vertical-align:top;">
                        <div style="font-weight:bold; margin-bottom:5px;">卖方 SELLER:</div>
                        <div style="border:1px solid #000; padding:10px; min-height:100px; line-height:1.5; font-size:8pt;">
                            {shipper_display}
                        </div>
                    </td>
                    <td style="width:50%; vertical-align:top; padding-left:10px;">
                        <table style="width:100%; font-size:9pt;">
                            <tr>
                                <td style="font-weight:bold; width:40%;">发票号 Invoice No:</td>
                                <td style="border-bottom:1px solid #999;">{html_module.escape(invoice_no)}</td>
                            </tr>
                            <tr><td colspan="2" style="height:5px;"></td></tr>
                            <tr>
                                <td style="font-weight:bold;">日期 Date:</td>
                                <td style="border-bottom:1px solid #999;">{str(decl.export_date) if decl.export_date else str(decl.created_at.date()) if decl.created_at else '-'}</td>
                            </tr>
                            <tr><td colspan="2" style="height:5px;"></td></tr>
                            <tr>
                                <td style="font-weight:bold;">合同号 Contract No:</td>
                                <td style="border-bottom:1px solid #999;">{html_module.escape(decl.contract_no or '-')}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr><td colspan="2" style="height:10px;"></td></tr>
                <tr>
                    <td colspan="2">
                        <div style="font-weight:bold; margin-bottom:5px;">买方 BUYER:</div>
                        <div style="border:1px solid #000; padding:10px; min-height:80px; line-height:1.5; font-size:8pt;">
                            {consignee}
                        </div>
                    </td>
                </tr>
                <tr><td colspan="2" style="height:10px;"></td></tr>
                <tr>
                    <td>
                        <span style="font-weight:bold;">装运口岸 Port of Loading:</span>
                        <span style="margin-left:10px;">{html_module.escape(decl.departure_port or '-')}</span>
                    </td>
                    <td>
                        <span style="font-weight:bold;">目的港 Port of Discharge:</span>
                        <span style="margin-left:10px;">{html_module.escape(decl.loading_port or '-')}</span>
                    </td>
                </tr>
                <tr><td colspan="2" style="height:5px;"></td></tr>
                <tr>
                    <td>
                        <span style="font-weight:bold;">运输方式 Shipment:</span>
                        <span style="margin-left:10px;">{html_module.escape(decl.transport_mode or '-')}</span>
                    </td>
                    <td>
                        <span style="font-weight:bold;">贸易条款 Terms:</span>
                        <span style="margin-left:10px;">{html_module.escape(decl.transaction_mode or 'FOB')}</span>
                    </td>
                </tr>
                <tr><td colspan="2" style="height:5px;"></td></tr>
                <tr>
                    <td colspan="2">
                        <span style="font-weight:bold;">付款条件 Payment Terms:</span>
                        <span style="margin-left:10px;">As per contract 根据合同约定</span>
                    </td>
                </tr>
            </table>
        </div>
    '''
    
    # 商品明细表
    if decl.items:
        result += '''
        <table class="declaration-table">
            <thead>
                <tr>
                    <th style="width:40px;">项号<br/>No.</th>
                    <th style="width:100px;">HS编码<br/>HS Code</th>
                    <th style="width:200px;">商品描述<br/>Description of Goods</th>
                    <th style="width:60px;">数量<br/>Quantity</th>
                    <th style="width:45px;">单位<br/>Unit</th>
                    <th style="width:70px;">单价(USD)<br/>Unit Price</th>
                    <th style="width:80px;">总价(USD)<br/>Amount</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        total_amount = 0
        
        for idx, item in enumerate(decl.items, 1):
            product_desc = item.product.name if item.product else (item.product_name_spec or '-')
            # 添加规格说明
            if item.product_name_spec and ',' in item.product_name_spec:
                parts = item.product_name_spec.split(',', 1)
                if len(parts) > 1:
                    product_desc += f"<br/><span style='font-size:7pt; color:#666;'>{parts[1].strip()}</span>"
            
            product_desc = html_module.escape(product_desc).replace('&lt;br/&gt;', '<br/>')
            hs_code = html_module.escape(item.hs_code or '-')
            qty = float(item.qty) if item.qty else 0
            unit = html_module.escape(item.unit or '')
            unit_price = float(item.usd_unit_price) if item.usd_unit_price else 0
            amount = float(item.usd_total) if item.usd_total else 0
            total_amount += amount
            
            result += f'''
                <tr>
                    <td style="text-align:center;">{idx}</td>
                    <td style="text-align:center; font-size:7pt;">{hs_code}</td>
                    <td style="text-align:left; padding-left:5px; font-size:8pt;">{product_desc}</td>
                    <td style="text-align:right;">{qty:.2f}</td>
                    <td style="text-align:center;">{unit}</td>
                    <td style="text-align:right;">{unit_price:.4f}</td>
                    <td style="text-align:right; font-weight:bold;">{amount:.2f}</td>
                </tr>
            '''
        
        # 合计行
        currency = html_module.escape(decl.currency or 'USD')
        result += f'''
                <tr class="total-row">
                    <td colspan="6" style="text-align:right; font-weight:bold; padding-right:10px;">
                        总计 TOTAL ({currency}):
                    </td>
                    <td style="text-align:right; font-weight:bold; font-size:10pt;">{total_amount:.2f}</td>
                </tr>
            </tbody>
        </table>
        '''
        
        # 金额大写（使用报关单的实际币种）
        currency_display = html_module.escape(decl.currency or 'USD')
        result += f'''
        <div style="margin-top:15px; font-size:9pt;">
            <span style="font-weight:bold;">金额大写 Amount in Words:</span>
            <span style="margin-left:10px; font-style:italic;">{currency_display} {total_amount:.2f} ONLY</span>
        </div>
        '''
    
    # 签名区
    result += '''
        <div style="margin-top:40px;">
            <table style="width:100%; font-size:9pt;">
                <tr>
                    <td style="width:50%;">
                        <div style="font-weight:bold; margin-bottom:30px;">授权签字人 Authorized Signature:</div>
                        <div style="border-top:1px solid #000; width:200px; padding-top:5px;"></div>
                    </td>
                    <td style="width:50%; text-align:right;">
                        <div style="font-weight:bold; margin-bottom:30px;">公司盖章 Company Seal:</div>
                        <div style="text-align:center; padding-top:20px;">(此处盖章)</div>
                    </td>
                </tr>
            </table>
        </div>
    '''
    
    return result


def _generate_contract_html(decl) -> str:
    """生成销售合同HTML - 国际贸易标准格式"""
    import html as html_module
    
    # 获取发货人完整信息（含英文和地址）
    shipper_info = []
    if decl.internal_shipper:
        # 中文名称
        if decl.internal_shipper.legal_name:
            shipper_info.append(decl.internal_shipper.legal_name)
        # 英文名称
        if decl.internal_shipper.english_name:
            shipper_info.append(decl.internal_shipper.english_name)
        # 地址
        address = decl.internal_shipper.business_address or decl.internal_shipper.registered_address
        if address:
            shipper_info.append(f"地址 Address: {address}")
        # 联系方式
        if decl.internal_shipper.contact_phone:
            shipper_info.append(f"电话 Tel: {decl.internal_shipper.contact_phone}")
        if decl.internal_shipper.contact_email:
            shipper_info.append(f"邮箱 Email: {decl.internal_shipper.contact_email}")
    
    shipper_display = "<br/>".join(shipper_info) if shipper_info else "-"
    consignee = html_module.escape(decl.overseas_consignee or '-')
    
    contract_no = decl.contract_no or decl.pre_entry_no or f"SC-{decl.id}"
    contract_date = str(decl.export_date) if decl.export_date else (str(decl.created_at.date()) if decl.created_at else '-')
    
    result = f'''
        <div style="text-align:center; font-size:18pt; font-weight:bold; margin-bottom:10px; letter-spacing:2px;">
            销售合同
        </div>
        <div style="text-align:center; font-size:14pt; margin-bottom:20px;">
            SALES CONTRACT
        </div>
        
        <div style="margin-bottom:15px; font-size:9pt;">
            <table style="width:100%;">
                <tr>
                    <td style="width:20%; font-weight:bold;">合同编号 Contract No:</td>
                    <td style="width:30%; border-bottom:1px solid #999;">{html_module.escape(contract_no)}</td>
                    <td style="width:20%; font-weight:bold;">签订日期 Date:</td>
                    <td style="width:30%; border-bottom:1px solid #999;">{contract_date}</td>
                </tr>
            </table>
        </div>
        
        <div style="margin-bottom:15px; font-size:9pt;">
            <div style="font-weight:bold; margin-bottom:5px;">卖方 THE SELLER:</div>
            <div style="border:1px solid #000; padding:10px; margin-bottom:10px; line-height:1.5; font-size:8pt;">
                {shipper_display}
            </div>
            
            <div style="font-weight:bold; margin-bottom:5px;">买方 THE BUYER:</div>
            <div style="border:1px solid #000; padding:10px; line-height:1.5; font-size:8pt;">
                {consignee}
            </div>
        </div>
        
        <div style="margin-bottom:10px; font-size:9pt; line-height:1.6;">
            <p>买卖双方同意按下列条款成交：</p>
            <p>The Seller and the Buyer agree to conclude this transaction subject to the following terms and conditions:</p>
        </div>
    '''
    
    # 商品条款
    result += '''
        <div style="font-weight:bold; margin-top:15px; margin-bottom:10px; font-size:10pt; border-bottom:2px solid #000; padding-bottom:3px;">
            第一条 商品 ARTICLE 1 - COMMODITY
        </div>
    '''
    
    if decl.items:
        result += '''
        <table class="declaration-table" style="font-size:7pt;">
            <thead>
                <tr>
                    <th style="width:30px;">项号</th>
                    <th style="width:200px;">商品名称及规格</th>
                    <th style="width:60px;">数量</th>
                    <th style="width:40px;">单位</th>
                    <th style="width:70px;">单价(USD)</th>
                    <th style="width:80px;">总价(USD)</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        total_amount = 0
        for idx, item in enumerate(decl.items, 1):
            product_desc = item.product.name if item.product else (item.product_name_spec or '-')
            product_desc = html_module.escape(product_desc)
            qty = float(item.qty) if item.qty else 0
            unit = html_module.escape(item.unit or '')
            unit_price = float(item.usd_unit_price) if item.usd_unit_price else 0
            amount = float(item.usd_total) if item.usd_total else 0
            total_amount += amount
            
            result += f'''
                <tr>
                    <td style="text-align:center;">{idx}</td>
                    <td style="text-align:left; padding:3px;">{product_desc}</td>
                    <td style="text-align:right;">{qty:.2f}</td>
                    <td style="text-align:center;">{unit}</td>
                    <td style="text-align:right;">{unit_price:.4f}</td>
                    <td style="text-align:right; font-weight:bold;">{amount:.2f}</td>
                </tr>
            '''
        
        currency = html_module.escape(decl.currency or 'USD')
        result += f'''
                <tr class="total-row">
                    <td colspan="5" style="text-align:right; font-weight:bold;">合同总金额 Total Amount ({currency}):</td>
                    <td style="text-align:right; font-weight:bold; font-size:9pt;">{total_amount:.2f}</td>
                </tr>
            </tbody>
        </table>
        '''
    
    # 其他条款 - 从数据库读取
    transaction_mode = html_module.escape(decl.transaction_mode or 'FOB')
    loading_port = html_module.escape(decl.departure_port or '-')
    destination = html_module.escape(decl.destination_country or '-')
    transport_mode = html_module.escape(decl.transport_mode or '-')
    
    # 付款条件 - 从 marks_and_notes 或其他字段读取
    # 如果未来添加了专门的付款条件字段，这里可以直接读取
    payment_terms = "T/T 电汇 Telegraphic Transfer, 发货后30天内付款 Within 30 days after shipment"
    
    result += f'''
        <div style="font-size:8pt; line-height:1.5; margin-top:15px;">
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第二条 贸易条款 ARTICLE 2 - TRADE TERMS:</span><br/>
                价格条款 Price Terms: {transaction_mode}
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第三条 装运 ARTICLE 3 - SHIPMENT:</span><br/>
                装运港 Port of Loading: {loading_port}<br/>
                目的地 Destination: {destination}<br/>
                运输方式 Mode of Transport: {transport_mode}<br/>
                装运期 Time of Shipment: 根据合同约定 As per contract
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第四条 付款条件 ARTICLE 4 - PAYMENT TERMS:</span><br/>
                {payment_terms}
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第五条 检验 ARTICLE 5 - INSPECTION:</span><br/>
                商品检验以装运港检验为准。The goods shall be inspected at port of loading.
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第六条 索赔 ARTICLE 6 - CLAIMS:</span><br/>
                买方应在货物到达目的港后30天内提出索赔。Claims should be filed within 30 days after arrival.
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第七条 不可抗力 ARTICLE 7 - FORCE MAJEURE:</span><br/>
                因不可抗力致使合同不能履行或延期履行，双方互不承担责任。Neither party shall be held responsible for failure or delay in performance of the contract due to Force Majeure.
            </div>
            
            <div style="margin-bottom:8px;">
                <span style="font-weight:bold;">第八条 争议解决 ARTICLE 8 - DISPUTE RESOLUTION:</span><br/>
                本合同在执行中如发生争议，应通过友好协商解决。Any dispute arising from the execution of this contract shall be settled through friendly negotiation.
            </div>
        </div>
    '''
    
    # 签字区
    result += '''
        <div style="margin-top:30px;">
            <table style="width:100%; font-size:9pt;">
                <tr>
                    <td style="width:50%; vertical-align:top;">
                        <div style="font-weight:bold; margin-bottom:10px;">卖方 SELLER:</div>
                        <div style="margin-bottom:60px;">签字 Signature: _______________</div>
                        <div>日期 Date: _______________</div>
                    </td>
                    <td style="width:50%; vertical-align:top;">
                        <div style="font-weight:bold; margin-bottom:10px;">买方 BUYER:</div>
                        <div style="margin-bottom:60px;">签字 Signature: _______________</div>
                        <div>日期 Date: _______________</div>
                    </td>
                </tr>
            </table>
        </div>
    '''
    
    return result


def _generate_proxy_html(decl) -> str:
    """生成报关委托书HTML - 海关标准格式"""
    import html as html_module
    from datetime import datetime, timedelta
    
    # 获取委托方信息
    shipper_name = "-"
    if decl.internal_shipper:
        shipper_name = getattr(decl.internal_shipper, 'legal_name', None) or getattr(decl.internal_shipper, 'name', '-')
    shipper_name = html_module.escape(shipper_name)
    
    # 委托书编号
    proxy_no = f"WT-{decl.pre_entry_no or decl.id}"
    proxy_date = str(decl.created_at.date()) if decl.created_at else datetime.now().strftime('%Y-%m-%d')
    
    # 有效期（默认1年）
    if decl.created_at:
        valid_until = (decl.created_at + timedelta(days=365)).strftime('%Y-%m-%d')
    else:
        valid_until = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    
    result = f'''
        <div style="text-align:center; font-size:20pt; font-weight:bold; margin-bottom:30px; letter-spacing:3px;">
            海关报关委托书
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt;">
            <table style="width:100%;">
                <tr>
                    <td style="width:25%; font-weight:bold;">委托书编号:</td>
                    <td style="width:25%;">{html_module.escape(proxy_no)}</td>
                    <td style="width:25%; font-weight:bold;">委托日期:</td>
                    <td style="width:25%;">{proxy_date}</td>
                </tr>
            </table>
        </div>
        
        <div style="font-size:10pt; line-height:2; text-indent:2em; margin-bottom:20px;">
            <p>本委托人（以下简称"甲方"）现委托贵公司（以下简称"乙方"）代理办理以下进出口货物的报关及相关事宜。经双方协商，达成如下协议：</p>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt;">
            <div style="font-weight:bold; margin-bottom:10px; font-size:10pt;">一、委托方（甲方）信息</div>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="width:25%; padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">公司名称:</td>
                    <td style="width:75%; padding:5px; border:1px solid #000;">{shipper_name}</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">地址:</td>
                    <td style="padding:5px; border:1px solid #000;">_________________________________________</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">联系电话:</td>
                    <td style="padding:5px; border:1px solid #000;">_________________________________________</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">海关注册登记编码:</td>
                    <td style="padding:5px; border:1px solid #000;">_________________________________________</td>
                </tr>
            </table>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt;">
            <div style="font-weight:bold; margin-bottom:10px; font-size:10pt;">二、受托方（乙方）信息</div>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="width:25%; padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">报关企业名称:</td>
                    <td style="width:75%; padding:5px; border:1px solid #000;">_________________________________________</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">海关注册登记编码:</td>
                    <td style="padding:5px; border:1px solid #000;">_________________________________________</td>
                </tr>
            </table>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt;">
            <div style="font-weight:bold; margin-bottom:10px; font-size:10pt;">三、委托事项</div>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="width:25%; padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">预录入编号:</td>
                    <td style="width:75%; padding:5px; border:1px solid #000;">{html_module.escape(decl.pre_entry_no or '-')}</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">进出口类型:</td>
                    <td style="padding:5px; border:1px solid #000;">出口 Export</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">运输方式:</td>
                    <td style="padding:5px; border:1px solid #000;">{html_module.escape(decl.transport_mode or '-')}</td>
                </tr>
                <tr>
                    <td style="padding:5px; border:1px solid #000; background-color:#f5f5f5; font-weight:bold;">提运单号:</td>
                    <td style="padding:5px; border:1px solid #000;">{html_module.escape(decl.bill_of_lading_no or '-')}</td>
                </tr>
            </table>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt; line-height:1.8;">
            <div style="font-weight:bold; margin-bottom:10px; font-size:10pt;">四、授权范围</div>
            <div style="padding-left:20px;">
                <div>☑ 代理报关报检</div>
                <div>☑ 代缴关税、增值税等税费</div>
                <div>☑ 代办商检、产地证等相关手续</div>
                <div>☑ 代收货物及单证</div>
                <div>☑ 代办其他与报关相关的事宜</div>
            </div>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt; line-height:1.8;">
            <div style="font-weight:bold; margin-bottom:10px; font-size:10pt;">五、双方责任与义务</div>
            <div style="padding-left:20px;">
                <div><span style="font-weight:bold;">甲方责任：</span></div>
                <div>1. 保证所提供的单证、资料真实、完整、有效；</div>
                <div>2. 按时支付报关代理费用及相关税费；</div>
                <div>3. 配合乙方完成报关相关手续。</div>
                <div style="margin-top:10px;"><span style="font-weight:bold;">乙方责任：</span></div>
                <div>1. 按照海关规定及甲方要求办理报关手续；</div>
                <div>2. 妥善保管甲方提供的单证资料；</div>
                <div>3. 及时向甲方反馈报关进度及结果。</div>
            </div>
        </div>
        
        <div style="margin-bottom:20px; font-size:9pt;">
            <div><span style="font-weight:bold;">委托有效期：</span>自 {proxy_date} 至 {valid_until}</div>
        </div>
        
        <div style="margin-bottom:10px; font-size:9pt; line-height:1.8;">
            <div>本委托书一式两份，甲乙双方各执一份，具有同等法律效力。</div>
        </div>
    '''
    
    # 签字区
    result += '''
        <div style="margin-top:40px;">
            <table style="width:100%; font-size:9pt;">
                <tr>
                    <td style="width:50%; vertical-align:top;">
                        <div style="font-weight:bold; margin-bottom:10px;">委托方（甲方）</div>
                        <div style="margin-bottom:15px;">公司名称（盖章）：</div>
                        <div style="margin-bottom:40px; padding-left:20px;">(此处盖章)</div>
                        <div>法定代表人签字：_______________</div>
                        <div style="margin-top:10px;">日期：_______________</div>
                    </td>
                    <td style="width:50%; vertical-align:top;">
                        <div style="font-weight:bold; margin-bottom:10px;">受托方（乙方）</div>
                        <div style="margin-bottom:15px;">公司名称（盖章）：</div>
                        <div style="margin-bottom:40px; padding-left:20px;">(此处盖章)</div>
                        <div>授权代表签字：_______________</div>
                        <div style="margin-top:10px;">日期：_______________</div>
                    </td>
                </tr>
            </table>
        </div>
    '''
    
    return result


def _generate_compact_files_list_html(decl) -> str:
    """生成简洁版归档资料清单HTML - 用于归档PDF的第一页（无标题、无页脚）"""
    import html as html_module
    
    result = f'''
    <html>
    <head>
        <meta charset="UTF-8">
        <title>随附单证清单</title>
    </head>
    <body>
        <div style="padding: 15px;">
            <h2 style="text-align: center; font-size: 14pt; margin-bottom: 10px; font-weight: bold;">
                随附单证清单 / Attached Documents List
            </h2>
            
            <div style="margin-bottom: 15px; font-size: 9pt; text-align: center;">
                <span style="font-weight: bold;">预录入编号：</span>{html_module.escape(decl.pre_entry_no or '-')} &nbsp;&nbsp;
                <span style="font-weight: bold;">申报单位：</span>{html_module.escape(decl.internal_shipper.legal_name if decl.internal_shipper else '-')}
            </div>
    '''
    
    # 附件清单表格
    if decl.attachments:
        result += '''
            <table style="width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 10px;">
                <thead style="background-color: #f0f0f0;">
                    <tr>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 40px;">序号</th>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 200px;">文件名称</th>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 80px;">文件类型</th>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 80px;">文件大小</th>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 110px;">上传时间</th>
                        <th style="border: 1px solid #ccc; padding: 8px; width: 100px;">业务分类</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for idx, attachment in enumerate(decl.attachments, 1):
            file_name = html_module.escape(attachment.file_name or '-')
            file_type = html_module.escape(attachment.file_type or '-')
            
            # 文件大小转换
            if attachment.file_size:
                if attachment.file_size < 1024:
                    file_size = f"{attachment.file_size}B"
                elif attachment.file_size < 1024 * 1024:
                    file_size = f"{attachment.file_size / 1024:.2f}KB"
                else:
                    file_size = f"{attachment.file_size / (1024 * 1024):.2f}MB"
            else:
                file_size = "-"
            
            upload_time = attachment.created_at.strftime('%Y-%m-%d %H:%M') if attachment.created_at else '-'
            
            # 业务分类映射
            category_map = {
                '01_Customs': '关务核心单证',
                '02_Trade': '贸易全套单据',
                '03_Logistics': '物流凭证',
                '04_Others': '其他资料'
            }
            category = category_map.get(attachment.category, '其他资料')
            
            result += f'''
                <tr>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: center;">{idx}</td>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: left; font-size: 7pt;">{file_name}</td>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: center;">{file_type}</td>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: right;">{file_size}</td>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: center; font-size: 7pt;">{upload_time}</td>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: center;">{category}</td>
                </tr>
            '''
        
        result += '''
                </tbody>
            </table>
        '''
    else:
        result += '''
            <div style="text-align: center; padding: 30px; color: #999; font-size: 9pt;">
                暂无附件
            </div>
        '''
    
    # 说明文字
    result += '''
            <div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; font-size: 8pt; border-left: 3px solid #666;">
                <div style="font-weight: bold; margin-bottom: 5px;">归档说明：</div>
                <div>1. 本清单列出该报关单的所有随附单证；</div>
                <div>2. 所有文件均已归档至文档管理系统；</div>
                <div>3. 后续页面为完整的归档文档内容。</div>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return result


def _get_compact_css_styles() -> str:
    """获取简洁版CSS样式 - 用于归档清单（无页脚、最小页边距）"""
    return '''
        @page {
            size: A4 landscape;
            margin: 1.5cm 1cm;
        }
        
        body {
            font-family: "SimSun", serif;
            margin: 0;
            padding: 0;
        }
        
        table {
            page-break-inside: avoid;
        }
        
        tr {
            page-break-inside: avoid;
        }
    '''


def _generate_files_html(decl) -> str:
    """生成归档资料清单HTML"""
    import html as html_module
    
    # 基本信息
    result = f'''
        <div style="margin-bottom:15px; font-size:9pt;">
            <table style="width:100%;">
                <tr>
                    <td style="width:25%; font-weight:bold;">预录入编号:</td>
                    <td style="width:75%;">{html_module.escape(decl.pre_entry_no or '-')}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">申报单位:</td>
                    <td>{html_module.escape(decl.internal_shipper.legal_name if decl.internal_shipper else '-')}</td>
                </tr>
            </table>
        </div>
    '''
    
    # 附件清单
    if decl.attachments:
        result += '''
        <table class="declaration-table">
            <thead>
                <tr>
                    <th style="width:50px;">序号</th>
                    <th style="width:150px;">文件名称</th>
                    <th style="width:100px;">文件类型</th>
                    <th style="width:80px;">文件大小</th>
                    <th style="width:120px;">上传时间</th>
                    <th style="width:100px;">业务分类</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for idx, attachment in enumerate(decl.attachments, 1):
            file_name = html_module.escape(attachment.file_name or '-')
            file_type = html_module.escape(attachment.file_type or '-')
            
            # 文件大小转换
            if attachment.file_size:
                if attachment.file_size < 1024:
                    file_size = f"{attachment.file_size}B"
                elif attachment.file_size < 1024 * 1024:
                    file_size = f"{attachment.file_size / 1024:.2f}KB"
                else:
                    file_size = f"{attachment.file_size / (1024 * 1024):.2f}MB"
            else:
                file_size = "-"
            
            upload_time = attachment.created_at.strftime('%Y-%m-%d %H:%M') if attachment.created_at else '-'
            
            # 业务分类映射（与前端 docMatrix 保持一致）
            category_map = {
                '01_Customs': '关务核心单证',
                '02_Trade': '贸易全套单据',
                '03_Logistics': '物流凭证',
                '04_Others': '其他资料'
            }
            category = category_map.get(attachment.category, '其他资料')
            
            result += f'''
                <tr>
                    <td style="text-align:center;">{idx}</td>
                    <td style="text-align:left; padding-left:5px; font-size:7pt;">{file_name}</td>
                    <td style="text-align:center;">{file_type}</td>
                    <td style="text-align:right;">{file_size}</td>
                    <td style="text-align:center; font-size:7pt;">{upload_time}</td>
                    <td style="text-align:center;">{category}</td>
                </tr>
            '''
        
        result += '''
            </tbody>
        </table>
        '''
    else:
        result += '''
        <div style="text-align:center; padding:30px; color:#999; font-size:9pt;">
            暂无附件
        </div>
        '''
    
    # 说明文字
    result += '''
        <div style="margin-top:20px; padding:10px; background-color:#f5f5f5; font-size:8pt; border-left:3px solid #666;">
            <div style="font-weight:bold; margin-bottom:5px;">归档说明：</div>
            <div>1. 本清单列出该报关单的所有随附单证；</div>
            <div>2. 所有文件均已归档至文档管理系统；</div>
            <div>3. 如需查看完整文件，请通过系统下载或联系管理员。</div>
        </div>
    '''
    
    return result


def generate_archived_files_pdf(declaration, current_user=None) -> BytesIO:
    """
    生成归档资料PDF - 第一页是材料清单，后续合并所有附件PDF
    
    Args:
        declaration: 报关单对象（需要预加载attachments关系）
        current_user: 当前用户（可选）
    
    Returns:
        BytesIO: 合并后的PDF文件流
    """
    from pypdf import PdfWriter, PdfReader
    import os
    
    try:
        # 创建PDF写入器
        pdf_writer = PdfWriter()
        
        # 1. 生成简洁的材料清单作为第一页（无标题、无页脚、无页边距）
        logger.info(f"生成归档资料清单 - 报关单ID: {declaration.id}")
        files_list_html = _generate_compact_files_list_html(declaration)
        files_list_buffer = BytesIO()
        HTML(string=files_list_html).write_pdf(files_list_buffer, stylesheets=[CSS(string=_get_compact_css_styles())])
        files_list_buffer.seek(0)
        
        # 添加清单页到合并PDF
        list_reader = PdfReader(files_list_buffer)
        for page in list_reader.pages:
            pdf_writer.add_page(page)
        
        logger.info(f"材料清单已添加，共 {len(list_reader.pages)} 页")
        
        # 2. 合并所有附件PDF
        if declaration.attachments:
            logger.info(f"开始合并附件，共 {len(declaration.attachments)} 个文件")
            
            # 获取归档路径前缀
            from app.services.customs_service import CustomsService
            customs_svc = CustomsService()
            archive_base_path = customs_svc.get_archive_path(declaration.id)
            
            for idx, attachment in enumerate(declaration.attachments, 1):
                try:
                    # 只处理PDF文件（注意：file_type 可能是 'pdf' 或 '.pdf'）
                    file_ext = attachment.file_type.lower().strip('.') if attachment.file_type else ''
                    if file_ext != 'pdf':
                        logger.info(f"跳过非PDF文件: {attachment.file_name} (类型: {attachment.file_type})")
                        continue
                    
                    # 构建完整文件路径
                    # attachment.file_path 只存储文件名，需要拼接完整路径
                    full_file_path = f"{archive_base_path}/{attachment.file_path}"
                    
                    # 从NAS读取文件
                    from app.services.synology_client import SynologyClient
                    synology = SynologyClient()
                    
                    # 下载附件到临时缓冲区
                    logger.info(f"正在读取附件 {idx}/{len(declaration.attachments)}: {attachment.file_name} (路径: {full_file_path})")
                    attachment_buffer = synology.download_file_to_buffer(full_file_path)
                    
                    if attachment_buffer:
                        # 读取PDF并添加到合并器
                        try:
                            attachment_reader = PdfReader(attachment_buffer)
                            page_count = len(attachment_reader.pages)
                            
                            for page_num, page in enumerate(attachment_reader.pages, 1):
                                pdf_writer.add_page(page)
                            
                            logger.info(f"✓ 附件已合并: {attachment.file_name} ({page_count} 页)")
                        except Exception as pdf_err:
                            logger.error(f"✗ 无法解析PDF文件 {attachment.file_name}: {str(pdf_err)}")
                            continue
                    else:
                        logger.warning(f"✗ 无法从NAS读取附件: {attachment.file_name}")
                        
                except Exception as e:
                    logger.error(f"合并附件失败 {attachment.file_name}: {str(e)}")
                    # 继续处理下一个附件，不中断整个流程
                    continue
        else:
            logger.info("没有附件需要合并")
        
        # 3. 写入最终PDF
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        total_pages = len(pdf_writer.pages)
        logger.info(f"归档资料PDF生成完成，总页数: {total_pages}")
        
        return output_buffer
        
    except Exception as e:
        logger.error(f"生成归档资料PDF失败: {str(e)}")
        # 如果合并失败，至少返回材料清单
        logger.info("尝试返回仅包含材料清单的PDF")
        files_list_html = _generate_compact_files_list_html(declaration)
        fallback_buffer = BytesIO()
        HTML(string=files_list_html).write_pdf(fallback_buffer, stylesheets=[CSS(string=_get_compact_css_styles())])
        fallback_buffer.seek(0)
        return fallback_buffer

