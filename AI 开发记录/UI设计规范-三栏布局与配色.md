# 页面设计规范总结：三栏布局与选中样式

为了保持系统整体风格一致，特别是在管理具有层级关系的数据（如：品牌 -> 车型 -> 子车型）时，建议遵循以下设计规范。

## 1. 布局结构 (三栏布局)

采用 `Ant Design Vue` 的 `Row` 和 `Col` 组件实现左右/三栏分栏布局。

- **适用场景**：具有明确父子层级关系的数据管理。
- **布局比例**：建议 `8 : 8 : 8` (均分) 或类似比例，根据内容重要性调整。
- **高度**：使用 `h-full` 撑满父容器，内部 `Card` 设置 `flex flex-col` 确保头部固定、内容区域滚动。

```vue
<Row :gutter="16" class="h-full">
  <!-- Level 1: 左侧父级 -->
  <Col :span="8" class="h-full">
    <Card class="h-full flex flex-col" :bodyStyle="{ flex: 1, overflow: 'hidden', padding: '12px' }">
       <!-- Header, List, Footer -->
    </Card>
  </Col>
  
  <!-- Level 2: 中间子级 -->
  <Col :span="8" class="h-full">...</Col>
  
  <!-- Level 3: 右侧详情/孙级 -->
  <Col :span="8" class="h-full">...</Col>
</Row>
```

## 2. 配色方案 (橙黄色系 & 暗黑模式适配)

系统统一采用 **橙黄色 (Orange)** 作为选中和高亮的主色调，在此基础上做了深浅色适配。

### 2.1 列表项样式 (List Item / Table Row)

| 状态 | 亮色模式 (Light) | 暗色模式 (Dark) | 说明 |
| :--- | :--- | :--- | :--- |
| **默认背景** | `bg-white` | `dark:bg-gray-800` | 默认卡片背景 |
| **Hover 背景** | `hover:bg-orange-50` | `dark:hover:bg-orange-900/30` | 鼠标悬停反馈 |
| **选中背景** | `bg-orange-100` | `dark:bg-orange-900/60` | 选中高亮，暗色模式下使用透明度 |
| **文字颜色** | `text-black` | `dark:text-white` | 保持高对比度，**选中时加粗** (`font-medium` / `font-bold`) |
| **边框** | `border-gray-100` | `dark:border-gray-800` | 分割线颜色 |

### 2.2 代码实现参考 (Tailwind CSS)

**List Item (左侧列表):**

```html
<List.Item 
  class="cursor-pointer hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded px-2 transition-colors border-b border-gray-100 dark:border-gray-800"
  :class="{ 'bg-orange-100 dark:bg-orange-900/60': selectedId === item.id }"
  @click="handleSelect(item.id)"
>
  <!-- Content -->
</List.Item>
```

**Table Row (表格行 - 使用 customRow):**

```typescript
const customRow = (record) => {
  const isSelected = selectedId.value === record.id;
  return {
    onClick: () => handleSelect(record.id),
    class: {
      'bg-orange-100 dark:bg-orange-900/60': isSelected,
      'font-medium': isSelected,
      'hover:bg-orange-50 dark:hover:bg-orange-900/30': !isSelected,
      'cursor-pointer': true,
      'transition-colors': true
    }
  };
};
```

### 2.3 图标与标签 (Tags & Icons)

- **Tag 标签**：
  - 选中行：使用 `orange` / `gold` 等暖色系 Tag。
  - 未选中行：使用 `blue` / `cyan` 等冷色系 Tag。
  
- **图标背景 (Avatar)**：
  - 未选中：`bg-gray-200 dark:bg-gray-700` (灰色)
  - 选中：`bg-orange-300 dark:bg-orange-700` (橙色高亮) + `text-black dark:text-white`

## 3. 交互规范

1.  **点击即选中**：点击行任意位置即可选中，不局限于复选框。
2.  **联动展示**：选中左侧/中间行后，右侧区域自动加载对应数据。
3.  **空状态 (Empty State)**：
    - 当父级未选中时，子级区域应显示 `Empty` 组件，提示“请先选择左侧...”。
    - 使用 `v-if="!selectedId"` 控制显示。
4.  **独立操作**：每栏应有独立的“新增”按钮（位于 Header `extra` 插槽），互不干扰。

## 4. 总结

在开发新的管理页面时，请直接复制上述 Tailwind 类名组合，即可快速实现风格统一、支持暗黑模式的高质量界面。

