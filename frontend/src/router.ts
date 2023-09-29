import Vue from 'vue';
import Router from 'vue-router';

import RouterComponent from './components/RouterComponent.vue';
import {useUserStore} from '@/stores/user';
import {useMainStore} from '@/stores/main';

async function routeGuard(to, from, next) {
  const userStore = useUserStore();
  const mainStore = useMainStore();
  if (!mainStore.license) {
    await mainStore.fetchLicense();
  }
  if (!mainStore.license?.active) {
    if (to.path !== '/setup') {
      next('/setup');
    } else {
      next();
    }
  } else {
    await userStore.checkLoggedIn();

    if (userStore.isLoggedIn && (to.path === '/auth/login' || to.path === '/')) {
      next('/main/dashboard');
    } else if (
      !userStore.isLoggedIn &&
      (to.path === '/' || (to.path as string).startsWith('/main') || (to.path as string).startsWith('/setup'))
    ) {
      next('/auth/login');
    } else if (to.path.startsWith('/main/admin') && !userStore.hasAdminAccess) {
      next('/main');
    } else {
      next();
    }
  }
}

Vue.use(Router);
Vue.mixin({
  async beforeRouteEnter(to, from, next) {
    await routeGuard(to, from, next);
  },
  async beforeRouteUpdate(to, from, next) {
    await routeGuard(to, from, next);
  },
});

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      component: () => import(/* webpackChunkName: "start" */ './views/main/Start.vue'),
      children: [
        {
          name: 'setup',
          path: 'setup',
          component: () => import(/* webpackChunkName: "setup" */ './views/setup/Setup.vue'),
        },
        {
          path: 'auth',
          component: () => import(/* webpackChunkName: "login" */ './views/auth/AuthPortal.vue'),
          redirect: '/auth/login',
          children: [
            {
              path: 'login',
              component: () => import(/* webpackChunkName: "login" */ './views/auth/Login.vue'),
            },
            {
              path: 'signup',
              component: () => import(/* webpackChunkName: "login" */ './views/auth/Signup.vue'),
            },
          ],
        },
        {
          path: 'recover-password',
          component: () => import(/* webpackChunkName: "recover-password" */ './views/auth/PasswordRecovery.vue'),
        },
        {
          path: 'reset-password',
          component: () => import(/* webpackChunkName: "reset-password" */ './views/auth/ResetPassword.vue'),
        },
        {
          path: 'main',
          component: () => import(/* webpackChunkName: "main" */ './views/main/Main.vue'),
          redirect: '/main/dashboard',
          children: [
            {
              name: 'main-dashboard',
              path: 'dashboard',
              component: () => import(/* webpackChunkName: "main-dashboard" */ './views/main/Dashboard.vue'),
            },
            {
              path: 'projects',
              name: 'projects-home',
              component: () => import(/* webpackChunkName: "main-dashboard" */ './views/main/project/ProjectsHome.vue'),
            },
            {
              path: 'projects/:id',
              name: 'project-home',
              redirect: 'projects/:id/testing',
              component: () => import('./views/main/project/Project.vue'),
              props: route => {
                return { id: Number(route.params.id) };
              },
              children: [
                {
                  path: 'properties',
                  name: 'project-properties',
                  component: () => import('./views/main/project/ProjectProperties.vue'),
                  props: route => {
                    return { projectId: Number(route.params.id) };
                  },
                },
                {
                  path: 'inspection/:inspectionId',
                  name: 'project-inspector',
                  component: () => import('./views/main/project/InspectorWrapper.vue'),
                  props: route => ({
                    inspectionId: Number(route.params.inspectionId),
                    projectId: Number(route.params.id),
                  }),
                },
                {
                  path: 'feedbacks',
                  name: 'project-feedback',
                  component: () => import('./views/main/project/FeedbackList.vue'),
                  props: route => {
                    return { projectId: Number(route.params.id) };
                  },
                  children: [
                    {
                      path: ':feedbackId',
                      name: 'project-feedback-detail',
                      component: () => import('./views/main/project/FeedbackDetail.vue'),
                      props: route => {
                        return {projectId: Number(route.params.id), id: Number(route.params.feedbackId)};
                      },
                      meta: { openFeedbackDetail: true },
                    },
                  ],
                },
                {
                  path: 'debugger',
                  name: 'project-debugger',
                  component: () => import('./views/main/project/Debugger.vue'),
                  props: route => {
                    return {
                      projectId: Number(route.params.id),
                    };
                  },
                  children: [
                    {
                      path: ':inspectionId',
                      name: 'project-debugger-inspection',
                      component: () => import('./views/main/project/InspectorWrapper.vue'),
                      props: route => {
                        return {
                          inspectionId: Number(route.params.inspectionId),
                          projectId: Number(route.params.id),
                        };
                      },
                    },
                  ],
                },
                {
                  path: 'catalog',
                  name: 'project-catalog',
                  component: () => import('./views/main/project/Catalog.vue'),
                  props: route => {
                    return {
                      projectId: Number(route.params.id),
                      suiteId: route.query.suiteId ? Number(route.query.suiteId) : undefined,
                    };
                  },
                  children: [
                    {
                      path: 'datasets',
                      name: 'project-catalog-datasets',
                      component: () => import('./views/main/project/Datasets.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                        };
                      },
                    },
                    {
                      path: 'models',
                      name: 'project-catalog-models',
                      component: () => import('./views/main/project/Models.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                        };
                      },
                    },
                    {
                      path: 'tests',
                      name: 'project-catalog-tests',
                      component: () => import('./views/main/project/TestsCatalog.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                          suiteId: route.query.suiteId ? Number(route.query.suiteId) : undefined,
                        };
                      },
                    },
                    {
                      path: 'slicing-functions',
                      name: 'project-catalog-slicing-functions',
                      component: () => import('./views/main/project/FiltersCatalog.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                          suiteId: route.query.suiteId ? Number(route.query.suiteId) : undefined,
                        };
                      },
                    },
                    {
                      path: 'transformation-functions',
                      name: 'project-catalog-transformation-functions',
                      component: () => import('./views/main/project/TransformationsCatalog.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                          suiteId: route.query.suiteId ? Number(route.query.suiteId) : undefined,
                        };
                      },
                    },
                  ],
                },
                {
                  path: 'testing',
                  name: 'project-testing',
                  component: () => import('./views/main/project/TestSuites.vue'),
                  props: route => {
                    return { projectId: Number(route.params.id) };
                  },
                  children: [],
                },
                {
                  path: 'testing/:suiteId',
                  name: 'project-testing-test-suite',
                  component: () => import('./views/main/project/TestSuite.vue'),
                  props: route => {
                    return {
                      projectId: Number(route.params.id),
                      suiteId: Number(route.params.suiteId),
                    };
                  },
                  children: [
                    {
                      path: 'overview',
                      name: 'project-testing-test-suite-overview',
                      component: () => import('./views/main/project/TestSuiteOverview.vue'),
                      props: route => {
                        return {
                          projectId: Number(route.params.id),
                          suiteId: Number(route.params.suiteId),
                        };
                      },
                    },
                    {
                      path: 'compare-execution',
                      name: 'project-testing-test-suite-compare-executions',
                      component: () => import('./views/main/project/TestSuiteCompareExecutions.vue'),
                      props: route => {
                        return {
                          suiteId: Number(route.params.suiteId),
                          projectId: Number(route.params.id),
                          latestCount: route.query.latestCount ? Number(route.query.latestCount) : undefined,
                          selectedIds: route.query.selectedIds ? JSON.parse(route.query.selectedIds as string) : undefined,
                        };
                      },
                    },
                    {
                      path: 'execution',
                      name: 'project-testing-test-suite-executions',
                      component: () => import('./views/main/project/TestSuiteExecutions.vue'),
                      props: route => {
                        return {
                          suiteId: Number(route.params.suiteId),
                          projectId: Number(route.params.id),
                        };
                      },
                      children: [
                        {
                          path: ':executionId',
                          name: 'project-testing-test-suite-execution',
                          component: () => import('./views/main/project/TestSuiteExecution.vue'),
                          props: route => {
                            return {
                              suiteId: Number(route.params.suiteId),
                              projectId: Number(route.params.id),
                              executionId: Number(route.params.executionId),
                            };
                          },
                        },
                      ],
                    },
                  ],
                },
              ],
            },
            {
              path: 'profile',
              component: RouterComponent,
              redirect: 'profile/view',
              children: [
                {
                  path: 'view',
                  component: () => import(/* webpackChunkName: "main-profile" */ './views/main/profile/UserProfile.vue'),
                },
                {
                  path: 'password',
                  component: () =>
                    import(/* webpackChunkName: "main-profile-password" */ './views/main/profile/UserProfileEditPassword.vue'),
                },
              ],
            },
            {
              name: 'admin',
              path: 'admin',
              component: () => import(/* webpackChunkName: "main-admin" */ './views/main/admin/Admin.vue'),
              redirect: 'admin/general',
              children: [
                {
                  name: 'admin-general',
                  path: 'general',
                  component: () => import(/* webpackChunkName: "main-admin" */ './views/main/admin/settings/SettingsGeneral.vue'),
                },
                {
                  path: 'users',
                  redirect: 'users/all',
                },
                {
                  path: 'users/all',
                  component: () => import(/* webpackChunkName: "main-admin-users" */ './views/main/admin/AdminUsers.vue'),
                },
                {
                  path: 'users/invite',
                  component: () => import(/* webpackChunkName: "main-admin-users" */ './views/main/admin/InviteUsers.vue'),
                },
                {
                  path: 'users/edit/:id',
                  name: 'main-admin-users-edit',
                  component: () => import(/* webpackChunkName: "main-admin-users-edit" */ './views/main/admin/EditUser.vue'),
                },
                {
                  path: 'users/create',
                  name: 'main-admin-users-create',
                  component: () => import(/* webpackChunkName: "main-admin-users-create" */ './views/main/admin/CreateUser.vue'),
                },
              ],
            },
          ],
        },
        {
          path: 'hfspaces',
          name: 'Hugging Face Spaces',
          redirect: 'hfspaces/setup-tip',
          component: () => import(/* webpackChunkName: "main" */ './views/main/Main.vue'),
          children: [
            {
              path: 'setup-tip',
              name: 'setup-tip',
              component: () => import(/* webpackChunkName: "hugging-face-spaces-setup-tip" */ './views/setup/HuggingFaceSpacesSetupTip.vue'),
            },
          ],
        },
      ],
    },
    {
      path: '/*',
      redirect: '/',
    },
  ],
});
