import { requestClient } from '#/api/request';

export interface Category {
  id: string;
  parentId: string | null;
  name: string;
  code: string;
  isLeaf: boolean;
  children?: Category[];
}

export interface Brand {
  id: string;
  name: string;
  code: string;
}

export interface Model {
    id: string;
    brandId: string;
    name: string;
}

export interface SkuSuffix {
    code: string;
    meaning: string;
}

export interface CategoryAttribute {
    id: string;
    key: string;
    label: string;
    type: 'text' | 'number' | 'select' | 'boolean';
    options?: { label: string; value: string | number }[];
    required: boolean;
}

/**
 * 获取分类列表（模拟树形结构）
 */
export async function getCategoriesApi() {
  // 模拟数据，实际应请求后端
  const mockData: Category[] = [
    {
      id: '1',
      parentId: null,
      name: '汽车照明 (Lighting)',
      code: 'LGT',
      isLeaf: false,
      children: [
        {
          id: '11',
          parentId: '1',
          name: '前大灯 (Headlight)',
          code: 'HL',
          isLeaf: true,
        },
        {
          id: '12',
          parentId: '1',
          name: '尾灯 (Tail Light)',
          code: 'TL',
          isLeaf: true,
        },
      ],
    },
    {
      id: '2',
      parentId: null,
      name: '车身覆盖件 (Body Parts)',
      code: 'BDY',
      isLeaf: false,
      children: [
        {
          id: '21',
          parentId: '2',
          name: '保险杠 (Bumper)',
          code: '188',
          isLeaf: true,
        },
      ],
    },
  ];
  
  return Promise.resolve(mockData);
}

/**
 * 获取品牌列表
 */
export async function getBrandsApi() {
  const mockData: Brand[] = [
    { id: '01', name: '宝马 (BMW)', code: '01' },
    { id: '02', name: '奔驰 (Mercedes)', code: '02' },
    { id: '03', name: '奥迪 (Audi)', code: '03' },
    { id: '04', name: '丰田 (Toyota)', code: '04' },
  ];
  return Promise.resolve(mockData);
}

/**
 * 获取车型列表
 */
export async function getModelsApi(brandId: string) {
    // 模拟数据
    const allModels: Model[] = [
        // BMW
        { id: '101', brandId: '01', name: '3 Series (3系)' },
        { id: '102', brandId: '01', name: '5 Series (5系)' },
        { id: '103', brandId: '01', name: 'X3' },
        { id: '104', brandId: '01', name: 'X5' },
        { id: '105', brandId: '01', name: '7 Series (7系)' },
        
        // Mercedes
        { id: '201', brandId: '02', name: 'C-Class (C级)' },
        { id: '202', brandId: '02', name: 'E-Class (E级)' },
        { id: '203', brandId: '02', name: 'S-Class (S级)' },
        { id: '204', brandId: '02', name: 'GLC' },
        { id: '205', brandId: '02', name: 'GLE' },
        
        // Audi
        { id: '301', brandId: '03', name: 'A3' },
        { id: '302', brandId: '03', name: 'A4L' },
        { id: '303', brandId: '03', name: 'A6L' },
        { id: '304', brandId: '03', name: 'Q5L' },
        { id: '305', brandId: '03', name: 'Q7' },
        
        // Toyota
        { id: '401', brandId: '04', name: 'Camry (凯美瑞)' },
        { id: '402', brandId: '04', name: 'Corolla (卡罗拉)' },
        { id: '403', brandId: '04', name: 'RAV4 (荣放)' },
        { id: '404', brandId: '04', name: 'Highlander (汉兰达)' },
        { id: '405', brandId: '04', name: 'Sienna (赛那)' },
    ];
    return Promise.resolve(allModels.filter(m => m.brandId === brandId));
}

/**
 * 获取SKU后缀字典
 */
export async function getSkuSuffixesApi() {
    const mockData: SkuSuffix[] = [
        { code: 'L', meaning: '左侧/驾驶位 (Left)' },
        { code: 'R', meaning: '右侧/副驾位 (Right)' },
        { code: 'S', meaning: '套装 (Set)' },
        { code: 'B', meaning: '黑色 (Black)' },
    ];
    return Promise.resolve(mockData);
}

/**
 * 获取下一个SKU流水号（模拟）
 */
export async function getNextSkuSerialApi(prefix: string) {
    // 模拟：简单随机生成或者自增
    // 实际：后端查询数据库
    const mockSerial = Math.floor(Math.random() * 1000).toString().padStart(4, '0');
    return Promise.resolve(mockSerial);
}
export async function getCategoryAttributesApi(categoryId: string) {
    // 模拟不同分类返回不同属性
    const commonAttrs: CategoryAttribute[] = [
        { id: 'a1', key: 'material', label: '材质', type: 'text', required: true }
    ];
    
    let specificAttrs: CategoryAttribute[] = [];
    
    if (categoryId === '11' || categoryId === '12') { // 车灯
        specificAttrs = [
            { id: 'b1', key: 'voltage', label: '电压', type: 'select', options: [{label:'12V', value:'12V'}, {label:'24V', value:'24V'}], required: true },
            { id: 'b2', key: 'bulb_type', label: '灯泡类型', type: 'text', required: false },
            { id: 'b3', key: 'lens_color', label: '透镜颜色', type: 'select', options: [{label:'透明', value:'Clear'}, {label:'烟熏', value:'Smoke'}, {label:'琥珀', value:'Amber'}], required: true }
        ];
    } else if (categoryId === '21') { // 保险杠
         specificAttrs = [
             { id: 'c1', key: 'color', label: '颜色', type: 'text', required: true },
             { id: 'c2', key: 'finish', label: '表面处理', type: 'select', options: [{label:'底漆', value:'Primed'}, {label:'镀铬', value:'Chrome'}, {label:'纹理黑', value:'Textured Black'}], required: true },
             { id: 'c3', key: 'parking_sensor_holes', label: '雷达孔', type: 'boolean', required: true }
         ];
    }

    return Promise.resolve([...commonAttrs, ...specificAttrs]);
}
