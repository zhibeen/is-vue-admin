<script lang="ts" setup>
import { ref, computed } from 'vue';
import { 
  Input, 
  Button, 
  Tooltip, 
  Dropdown, 
  Menu, 
  MenuItem 
} from 'ant-design-vue';
import { 
  PlusOutlined, 
  ReloadOutlined, 
  SearchOutlined, 
  SafetyCertificateOutlined,
  MoreOutlined
} from '@ant-design/icons-vue';
import type { RoleItem } from '#/api/core/system';

// Props
const props = defineProps<{
  roles: RoleItem[];
  activeRoleId?: number;
  loading: boolean;
}>();

// Emits
const emit = defineEmits<{
  (e: 'select', role: RoleItem): void;
  (e: 'refresh'): void;
  (e: 'create'): void;
  (e: 'edit', role: RoleItem): void;
  (e: 'copy', role: RoleItem): void;
  (e: 'delete', role: RoleItem): void;
}>();

const searchText = ref('');

const filteredRoles = computed(() => {
  if (!searchText.value) return props.roles;
  return props.roles.filter(r => r.name.toLowerCase().includes(searchText.value.toLowerCase()));
});
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Sidebar Header -->
    <div class="p-4 border-b border-gray-100 dark:border-gray-800">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center">
          <span class="text-base font-bold pl-1">角色列表</span>
          <Tooltip title="刷新列表">
            <Button type="text" shape="circle" size="small" @click="emit('refresh')" :loading="loading" class="ml-1">
              <template #icon><ReloadOutlined class="text-gray-400" style="font-size: 12px" /></template>
            </Button>
          </Tooltip>
        </div>
        <Tooltip title="新增角色">
          <Button type="text" shape="circle" @click="emit('create')">
            <PlusOutlined class="text-primary text-lg" />
          </Button>
        </Tooltip>
      </div>
      
      <Input 
        v-model:value="searchText" 
        placeholder="搜索角色" 
        class="rounded-md"
      >
        <template #prefix>
          <SearchOutlined class="text-gray-400" />
        </template>
      </Input>
    </div>
    
    <!-- List -->
    <div class="flex-1 overflow-y-auto px-2 pb-2 space-y-1 mt-2">
      <div 
        v-for="role in filteredRoles" 
        :key="role.id"
        class="relative px-3 py-3 rounded-md cursor-pointer flex justify-between items-center group transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800"
        :class="activeRoleId === role.id ? 'bg-blue-50 dark:bg-blue-900/20 text-primary' : 'text-gray-600 dark:text-gray-300'"
        @click="emit('select', role)"
      >
        <!-- Active Indicator Bar -->
        <div 
          v-if="activeRoleId === role.id" 
          class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-1 bg-primary rounded-r"
        ></div>

        <div class="flex items-center ml-2 truncate">
          <SafetyCertificateOutlined class="mr-2 text-lg" :class="activeRoleId === role.id ? 'text-primary' : 'text-gray-400'" />
          <span :class="activeRoleId === role.id ? 'font-semibold' : ''" class="truncate">{{ role.name }}</span>
        </div>

        <!-- Menu -->
        <Dropdown :trigger="['click']" @click.stop>
          <MoreOutlined 
            class="text-gray-400 hover:text-primary text-lg px-1"
            @click.stop
          />
          <template #overlay>
            <Menu>
              <MenuItem @click="emit('edit', role)">编辑</MenuItem>
              <MenuItem @click="emit('copy', role)">复制</MenuItem>
              <MenuItem v-if="role.name !== 'admin'" @click="emit('delete', role)" class="text-red-500">删除</MenuItem>
            </Menu>
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

