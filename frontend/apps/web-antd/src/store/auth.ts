import type { Recordable, UserInfo } from '@vben/types';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';
import { resetAllStores, useAccessStore, useUserStore } from '@vben/stores';

import { notification } from 'ant-design-vue';
import { defineStore } from 'pinia';

import { getAccessCodesApi, getUserInfoApi, loginApi, logoutApi } from '#/api';
import { $t } from '#/locales';

export const useAuthStore = defineStore('auth', () => {
  const accessStore = useAccessStore();
  const userStore = useUserStore();
  const router = useRouter();

  const loginLoading = ref(false);

  /**
   * 异步处理登录操作
   */
  async function authLogin(
    params: Recordable<any>,
    onSuccess?: () => Promise<void> | void,
  ) {
    let userInfo: null | UserInfo = null;
    try {
      loginLoading.value = true;
      
      const cleanParams = {
        username: params.username,
        password: params.password,
      };

      console.log('[Auth] Requesting login api...');
      // Change destructuring to variable assignment to debug response
      const response = await loginApi(cleanParams);
      console.log('[Auth] Raw API Response:', response);

      // Handle both { access_token: ... } and { data: { access_token: ... } } just in case
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const access_token = (response as any).access_token || (response as any).data?.access_token;

      console.log('[Auth] Extracted Access Token:', access_token);

      if (access_token) {
        accessStore.setAccessToken(access_token);

        console.log('[Auth] Fetching user info...');
        const [fetchUserInfoResult, accessCodes] = await Promise.all([
          fetchUserInfo(),
          Promise.resolve([] as string[]), 
        ]);
        console.log('[Auth] User info fetched:', fetchUserInfoResult);

        userInfo = fetchUserInfoResult;
        
        const roles = userInfo.roles || [];
        accessStore.setAccessCodes(roles);

        userStore.setUserInfo(userInfo);

        if (accessStore.loginExpired) {
          accessStore.setLoginExpired(false);
        } else {
          const { query } = router.currentRoute.value;
          const redirect = query.redirect as string;

          onSuccess
            ? await onSuccess?.()
            : await router.push(
                redirect
                  ? decodeURIComponent(redirect)
                  : userInfo.homePath || preferences.app.defaultHomePath,
              );
        }

        if (userInfo?.realName || userInfo?.username) {
          notification.success({
            description: `${$t('authentication.loginSuccessDesc')}:${userInfo?.realName || userInfo?.username}`,
            duration: 3,
            message: $t('authentication.loginSuccess'),
          });
        }
      } else {
        console.error('[Auth] No access_token found in response!');
      }
    } catch (error) {
      console.error('[Auth] Login failed:', error);
      throw error; 
    } finally {
      loginLoading.value = false;
    }

    return {
      userInfo,
    };
  }

  async function logout(redirect: boolean = true) {
    try {
      await logoutApi();
    } catch {
      // 不做任何处理
    }
    resetAllStores();
    accessStore.setLoginExpired(false);

    await router.replace({
      path: LOGIN_PATH,
      query: redirect
        ? {
            redirect: encodeURIComponent(router.currentRoute.value.fullPath),
          }
        : {},
    });
  }

  async function fetchUserInfo() {
    let userInfo: null | UserInfo = null;
    userInfo = await getUserInfoApi();
    
    const mappedInfo: UserInfo = {
      userId: userInfo.id,
      username: userInfo.username,
      realName: userInfo.username,
      avatar: 'https://unpkg.com/@vbenjs/static-source@0.1.7/source/avatar-v1.webp',
      desc: 'Manager',
      homePath: '/dashboard/analytics', 
      roles: userInfo.roles || [], 
    };
    
    userStore.setUserInfo(mappedInfo);
    return mappedInfo;
  }

  function $reset() {
    loginLoading.value = false;
  }

  return {
    $reset,
    authLogin,
    fetchUserInfo,
    loginLoading,
    logout,
  };
});
