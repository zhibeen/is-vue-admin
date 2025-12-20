<template>
  <div v-if="isDev && errorCount > 0" class="error-panel">
    <div class="error-badge" @click="togglePanel">
      <span class="error-icon">🔴</span>
      <span class="error-count">{{ errorCount }}</span>
    </div>

    <Drawer
      v-model:open="panelVisible"
      title="错误日志"
      placement="right"
      width="600"
      :z-index="9999"
    >
      <div class="error-actions">
        <Button type="primary" @click="handleCopyLatest" size="small">
          📋 复制最新错误
        </Button>
        <Button @click="handleCopyAll" size="small">
          📋 复制全部错误
        </Button>
        <Button danger @click="handleClear" size="small">
          🗑️ 清空
        </Button>
      </div>

      <div class="error-list">
        <div
          v-for="(error, index) in errors"
          :key="index"
          class="error-item"
          :class="`error-${error.type}`"
        >
          <div class="error-header">
            <Tag :color="getErrorColor(error.type)">
              {{ error.type.toUpperCase() }}
            </Tag>
            <span class="error-time">{{ error.timestamp }}</span>
          </div>
          
          <div class="error-message">
            {{ error.message }}
          </div>

          <div v-if="error.component" class="error-meta">
            <strong>组件:</strong> {{ error.component }}
          </div>

          <div v-if="error.file" class="error-meta">
            <strong>文件:</strong> {{ error.file }}:{{ error.line }}:{{ error.col }}
          </div>

          <div v-if="error.url" class="error-meta">
            <strong>URL:</strong> {{ error.url }}
          </div>

          <div v-if="error.stack" class="error-stack">
            <div class="error-stack-toggle" @click="toggleStack(index)">
              <span>{{ expandedStacks.has(index) ? '▼' : '▶' }}</span>
              调用栈
            </div>
            <pre v-show="expandedStacks.has(index)" class="error-stack-content">{{
              error.stack
            }}</pre>
          </div>

          <Button
            type="link"
            size="small"
            @click="copyError(error)"
            class="copy-btn"
          >
            复制此错误
          </Button>
        </div>

        <div v-if="errors.length === 0" class="empty-state">
          <span>✅ 暂无错误</span>
        </div>
      </div>
    </Drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { Button, Drawer, Tag } from 'ant-design-vue';
import { getErrorHistory, copyLatestError, clearErrorHistory } from '../utils/error-handler';

const isDev = import.meta.env.DEV;
const panelVisible = ref(false);
const errors = ref<any[]>([]);
const expandedStacks = ref(new Set<number>());

const errorCount = computed(() => errors.value.length);

function togglePanel() {
  panelVisible.value = !panelVisible.value;
}

function updateErrors() {
  errors.value = [...getErrorHistory()];
}

function handleCopyLatest() {
  copyLatestError();
}

function handleCopyAll() {
  const allErrors = errors.value
    .map((error, index) => {
      return `错误 #${index + 1}:\n${formatError(error)}\n`;
    })
    .join('\n');

  if (navigator.clipboard) {
    navigator.clipboard.writeText(allErrors).then(() => {
      console.log('全部错误已复制');
    });
  }
}

function handleClear() {
  clearErrorHistory();
  updateErrors();
}

function copyError(error: any) {
  const text = formatError(error);
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      console.log('错误已复制');
    });
  }
}

function formatError(error: any): string {
  const lines = [
    `类型: ${error.type}`,
    `时间: ${error.timestamp}`,
    `信息: ${error.message}`,
  ];

  if (error.component) lines.push(`组件: ${error.component}`);
  if (error.file) lines.push(`文件: ${error.file}:${error.line}:${error.col}`);
  if (error.url) lines.push(`URL: ${error.url}`);
  if (error.stack) lines.push(`\n调用栈:\n${error.stack}`);

  return lines.join('\n');
}

function toggleStack(index: number) {
  if (expandedStacks.value.has(index)) {
    expandedStacks.value.delete(index);
  } else {
    expandedStacks.value.add(index);
  }
}

function getErrorColor(type: string): string {
  const colors: Record<string, string> = {
    vue: 'green',
    js: 'red',
    promise: 'orange',
    resource: 'blue',
    api: 'purple',
  };
  return colors[type] || 'default';
}

// 定期更新错误列表
onMounted(() => {
  updateErrors();
  setInterval(updateErrors, 1000);
});
</script>

<style scoped>
.error-panel {
  position: fixed;
  z-index: 9998;
}

.error-badge {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50px;
  padding: 12px 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  transition: all 0.3s ease;
  animation: pulse 2s infinite;
}

.error-badge:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }
  50% {
    box-shadow: 0 4px 25px rgba(255, 0, 0, 0.5);
  }
}

.error-icon {
  font-size: 18px;
  animation: shake 0.5s infinite;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}

.error-count {
  min-width: 20px;
  text-align: center;
}

.error-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-item {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  background: white;
  transition: all 0.2s;
}

.error-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.error-vue { border-left: 4px solid #52c41a; }
.error-js { border-left: 4px solid #ff4d4f; }
.error-promise { border-left: 4px solid #fa8c16; }
.error-resource { border-left: 4px solid #1890ff; }
.error-api { border-left: 4px solid #722ed1; }

.error-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.error-time {
  font-size: 12px;
  color: #999;
}

.error-message {
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  word-break: break-word;
}

.error-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.error-stack {
  margin-top: 8px;
}

.error-stack-toggle {
  cursor: pointer;
  color: #1890ff;
  font-size: 12px;
  user-select: none;
}

.error-stack-toggle:hover {
  text-decoration: underline;
}

.error-stack-content {
  margin-top: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
  max-height: 200px;
}

.copy-btn {
  margin-top: 8px;
  padding: 0;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}

/* 深色模式适配 */
html.dark .error-item {
  background: #1f1f1f;
  border-color: #333;
}

html.dark .error-message {
  color: #e8e8e8;
}

html.dark .error-meta {
  color: #999;
}

html.dark .error-stack-content {
  background: #141414;
  color: #e8e8e8;
}
</style>

