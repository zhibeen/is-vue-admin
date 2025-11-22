import { requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 登录接口返回值 */
  export interface LoginResult {
    access_token: string;
    refresh_token: string;
    username: string;
    roles: string[];
  }

  export interface RefreshTokenResult {
    access_token: string;
  }
}

/**
 * 登录
 */
export async function loginApi(data: AuthApi.LoginParams) {
  // 加上 /v1 前缀 (假设 Vite Proxy 代理了 /api -> localhost:5000/api)
  // 请求路径将是: /api/v1/auth/login
  return requestClient.post<AuthApi.LoginResult>('/v1/auth/login', data);
}

/**
 * 刷新accessToken
 */
export async function refreshTokenApi() {
  return requestClient.post<AuthApi.RefreshTokenResult>('/v1/auth/refresh', {}, {
    // 后端需要 Authorization: Bearer <refresh_token>
    // 这部分逻辑通常在 request interceptor 里处理，或者这里手动传
    // 暂时留白，依赖 axios 拦截器或 store 逻辑
  });
}

/**
 * 退出登录
 */
export async function logoutApi() {
  // 前端直接清理 token 即可，后端无状态 jwt 不需要显式 logout
  // 也可以调用后端清理 redis 黑名单
  return Promise.resolve();
}

/**
 * 获取用户权限码
 */
export async function getAccessCodesApi() {
  return requestClient.get<string[]>('/v1/auth/codes');
}
