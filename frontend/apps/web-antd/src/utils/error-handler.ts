/**
 * 前端错误捕获和格式化工具
 * 用于在开发时快速定位和复制错误信息
 */

import type { App } from 'vue';
import { message } from 'ant-design-vue';

interface ErrorInfo {
  type: 'vue' | 'js' | 'promise' | 'resource' | 'api';
  message: string;
  stack?: string;
  component?: string;
  file?: string;
  line?: number;
  col?: number;
  url?: string;
  timestamp: string;
}

// 存储最近的错误
const errorHistory: ErrorInfo[] = [];
const MAX_ERRORS = 50;

/**
 * 格式化错误信息为易于复制的文本
 */
function formatErrorForCopy(error: ErrorInfo): string {
  const lines = [
    '========== 前端错误信息 ==========',
    `时间: ${error.timestamp}`,
    `类型: ${error.type}`,
    `信息: ${error.message}`,
  ];

  if (error.component) {
    lines.push(`组件: ${error.component}`);
  }

  if (error.file) {
    lines.push(`文件: ${error.file}:${error.line}:${error.col}`);
  }

  if (error.url) {
    lines.push(`URL: ${error.url}`);
  }

  if (error.stack) {
    lines.push('\n调用栈:');
    lines.push(error.stack);
  }

  lines.push('================================\n');
  return lines.join('\n');
}

/**
 * 记录错误到历史
 */
function recordError(error: ErrorInfo) {
  errorHistory.unshift(error);
  if (errorHistory.length > MAX_ERRORS) {
    errorHistory.pop();
  }

  // 在开发环境下自动打印格式化的错误
  if (import.meta.env.DEV) {
    console.group(`🔴 ${error.type.toUpperCase()} 错误`);
    console.log(formatErrorForCopy(error));
    console.groupEnd();
  }
}

/**
 * 复制最新的错误到剪贴板
 */
export function copyLatestError() {
  if (errorHistory.length === 0) {
    message.info('暂无错误记录');
    return;
  }

  const errorText = formatErrorForCopy(errorHistory[0]);
  
  if (navigator.clipboard) {
    navigator.clipboard.writeText(errorText).then(() => {
      message.success('错误信息已复制到剪贴板！');
    }).catch(() => {
      // 降级方案
      fallbackCopy(errorText);
    });
  } else {
    fallbackCopy(errorText);
  }
}

/**
 * 降级复制方案（兼容旧浏览器）
 */
function fallbackCopy(text: string) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand('copy');
    message.success('错误信息已复制到剪贴板！');
  } catch (err) {
    message.error('复制失败，请手动复制控制台中的错误信息');
    console.error('复制失败:', err);
  }
  document.body.removeChild(textarea);
}

/**
 * 获取错误历史
 */
export function getErrorHistory() {
  return errorHistory;
}

/**
 * 清空错误历史
 */
export function clearErrorHistory() {
  errorHistory.length = 0;
  message.success('错误历史已清空');
}

/**
 * Vue 错误处理器
 */
function handleVueError(err: any, instance: any, info: string) {
  const componentName = instance?.$options?.name || instance?.$options?.__name || '未知组件';
  
  const errorInfo: ErrorInfo = {
    type: 'vue',
    message: err.message || String(err),
    stack: err.stack,
    component: componentName,
    timestamp: new Date().toLocaleString('zh-CN'),
  };

  recordError(errorInfo);

  // 在生产环境显示友好的错误提示
  if (import.meta.env.PROD) {
    message.error('页面出现错误，请刷新重试或联系管理员');
  }
}

/**
 * 全局 JavaScript 错误处理器
 */
function handleJsError(event: ErrorEvent) {
  const errorInfo: ErrorInfo = {
    type: 'js',
    message: event.message,
    stack: event.error?.stack,
    file: event.filename,
    line: event.lineno,
    col: event.colno,
    timestamp: new Date().toLocaleString('zh-CN'),
  };

  recordError(errorInfo);
  
  // 阻止默认的控制台错误输出（因为我们已经有格式化输出了）
  // event.preventDefault();
}

/**
 * Promise 未捕获错误处理器
 */
function handlePromiseError(event: PromiseRejectionEvent) {
  const error = event.reason;
  
  const errorInfo: ErrorInfo = {
    type: 'promise',
    message: error?.message || String(error),
    stack: error?.stack,
    timestamp: new Date().toLocaleString('zh-CN'),
  };

  recordError(errorInfo);
  
  // 阻止默认行为
  event.preventDefault();
}

/**
 * 资源加载错误处理器
 */
function handleResourceError(event: Event) {
  const target = event.target as HTMLElement;
  
  if (target.tagName) {
    const errorInfo: ErrorInfo = {
      type: 'resource',
      message: `资源加载失败: ${target.tagName}`,
      url: (target as any).src || (target as any).href,
      timestamp: new Date().toLocaleString('zh-CN'),
    };

    recordError(errorInfo);
  }
}

/**
 * 设置全局错误处理器
 */
export function setupErrorHandler(app: App) {
  // Vue 错误处理
  app.config.errorHandler = handleVueError;

  // 全局 JavaScript 错误
  window.addEventListener('error', handleJsError, true);

  // Promise 未捕获错误
  window.addEventListener('unhandledrejection', handlePromiseError, true);

  // 资源加载错误
  window.addEventListener('error', handleResourceError, true);

  // 在开发环境下，将复制错误的方法挂载到 window 对象上
  if (import.meta.env.DEV) {
    (window as any).__copyError = copyLatestError;
    (window as any).__errorHistory = errorHistory;
    (window as any).__clearErrors = clearErrorHistory;
    
    console.log(
      '%c 🛠️ 错误捕获工具已启用',
      'color: #00d1b2; font-size: 14px; font-weight: bold;'
    );
    console.log(
      '%c 在控制台输入以下命令快速操作：',
      'color: #3273dc; font-size: 12px;'
    );
    console.log(
      '%c __copyError()     - 复制最新的错误信息',
      'color: #666; font-size: 11px;'
    );
    console.log(
      '%c __errorHistory    - 查看错误历史',
      'color: #666; font-size: 11px;'
    );
    console.log(
      '%c __clearErrors()   - 清空错误历史',
      'color: #666; font-size: 11px;'
    );
  }
}

/**
 * API 错误处理（用于 request.ts 中）
 */
export function handleApiError(error: any, url: string) {
  const errorInfo: ErrorInfo = {
    type: 'api',
    message: error.message || 'API 请求失败',
    stack: error.stack,
    url: url,
    timestamp: new Date().toLocaleString('zh-CN'),
  };

  recordError(errorInfo);
}

