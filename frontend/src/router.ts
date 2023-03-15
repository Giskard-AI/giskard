import Vue from 'vue';
import Router from 'vue-router';

import RouterComponent from './components/RouterComponent.vue';
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";


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
        } else if (!userStore.isLoggedIn && (to.path === '/' || (to.path as string).startsWith('/main') || (to.path as string).startsWith('/setup'))) {
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
    }
})

export default new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
        {
            path: '/',
            component: () => import(/* webpackChunkName: "start" */ './views/main/Start.vue'),
            children: [
                {
                    name: "setup",
                    path: 'setup',
                    component: () => import(/* webpackChunkName: "setup" */ './views/setup/Setup.vue')
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
                    ]
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
                            component: () => import('./views/main/project/Project.vue'),
                            props: (route) => {
                                return {id: Number(route.params.id)}
                            },
                            children: [
                                {
                                    path: 'overview',
                                    name: 'project-overview',
                                    component: () => import('./views/main/project/ProjectOverview.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    }
                                },
                                {
                                    path: 'datasets',
                                    name: 'project-datasets',
                                    component: () => import('./views/main/project/Datasets.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    }
                                },
                                {
                                    path: 'models',
                                    name: 'project-models',
                                    component: () => import('./views/main/project/Models.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    }
                                },
                                {
                                    path: 'inspection/:inspectionId',
                                    name: 'project-inspector',
                                    component: () => import('./views/main/project/InspectorWrapper.vue'),
                                    props: route => ({
                                        inspectionId: Number(route.params.inspectionId),
                                        projectId: Number(route.params.id)
                                    })
                                },
                                {
                                    path: 'feedbacks',
                                    name: 'project-feedbacks',
                                    component: () => import('./views/main/project/FeedbackList.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    },
                                    children: [
                                        {
                                            path: ':feedbackId',
                                            name: 'feedback-detail',
                                            component: () => import('./views/main/project/FeedbackDetail.vue'),
                                            props: (route) => {
                                                return {id: Number(route.params.feedbackId)}
                                            },
                                            meta: {openFeedbackDetail: true}
                                        }
                                    ]
                                },
                                {
                                    path: 'project-tests-catalog',
                                    name: 'project-tests-catalog',
                                    component: () => import('./views/main/project/TestsCatalog.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    },
                                },
                                {
                                    path: 'test-suites',
                                    name: 'project-test-suites',
                                    component: () => import('./views/main/project/TestSuites.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    },
                                    children: []
                                },
                                {
                                    path: 'test-suites-new',
                                    name: 'project-test-suites-new',
                                    component: () => import('./views/main/project/TestSuitesNew.vue'),
                                    props: (route) => {
                                        return {projectId: Number(route.params.id)}
                                    },
                                    children: []
                                }, {
                                    path: 'test-suite-new/:suiteId',
                                    name: 'test-suite-new',
                                    component: () => import('./views/main/project/TestSuiteNew.vue'),
                                    props: (route) => {
                                        return {
                                            projectId: Number(route.params.id),
                                            suiteId: Number(route.params.suiteId),
                                        }
                                    },
                                    children: [
                                        {
                                            path: 'inputs',
                                            name: 'test-suite-new-inputs',
                                            component: () => import('./views/main/project/TestSuiteNewInputs.vue'),
                                            props: (route) => {
                                                return {
                                                    projectId: Number(route.params.id),
                                                    suiteId: Number(route.params.suiteId),
                                                }
                                            }
                                        },
                                        {
                                            path: 'test',
                                            name: 'test-suite-new-tests',
                                            component: () => import('./views/main/project/TestSuiteNewTests.vue'),
                                            props: (route) => {
                                                return {
                                                    projectId: Number(route.params.id),
                                                    suiteId: Number(route.params.suiteId),
                                                }
                                            }
                                        },
                                        {
                                            path: 'configuration',
                                            name: 'test-suite-new-configuration',
                                            component: () => import('./views/main/project/TestSuiteNewConfiguration.vue'),
                                            props: (route) => {
                                                return {
                                                    projectId: Number(route.params.id),
                                                    suiteId: Number(route.params.suiteId),
                                                }
                                            }
                                        },
                                        {
                                            path: 'execution/compare',
                                            name: 'test-suite-new-compare-executions',
                                            component: () => import('./views/main/project/TestSuiteCompareExecutions.vue'),
                                            props: (route) => {
                                                return {
                                                    suiteId: Number(route.params.suiteId),
                                                    projectId: Number(route.params.id)
                                                }
                                            }
                                        },
                                        {
                                            path: 'test/:testId/compare',
                                            name: 'test-suite-new-compare-test',
                                            component: () => import('./views/main/project/TestSuiteCompareTest.vue'),
                                            props: (route) => {
                                                return {
                                                    suiteId: Number(route.params.suiteId),
                                                    projectId: Number(route.params.id),
                                                    testId: Number(route.params.id)
                                                }
                                            }
                                        },
                                        {
                                            path: 'execution',
                                            name: 'test-suite-new-executions',
                                            component: () => import('./views/main/project/TestSuiteExecutions.vue'),
                                            props: (route) => {
                                                return {
                                                    suiteId: Number(route.params.suiteId),
                                                    projectId: Number(route.params.id),
                                                }
                                            },
                                            children: [
                                                {
                                                    path: ':executionId',
                                                    name: 'test-suite-new-execution',
                                                    component: () => import('./views/main/project/TestSuiteExecution.vue'),
                                                    props: (route) => {
                                                        return {
                                                            suiteId: Number(route.params.suiteId),
                                                            projectId: Number(route.params.id),
                                                            executionId: Number(route.params.executionId)
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    path: 'test-suites/:suiteId',
                                    name: 'suite-details',
                                    component: () => import('./views/main/project/TestSuite.vue'),
                                    redirect: {name: 'suite-test-list'},
                                    props: (route) => {
                                        return {
                                            suiteId: Number(route.params.suiteId),
                                            projectId: Number(route.params.id)
                                        }
                                    },
                                    children: [
                                        {
                                            path: '',
                                            name: 'suite-test-list',
                                            component: () => import('./views/main/project/Tests.vue'),
                                            props: (route) => {
                                                return {
                                                    suiteId: Number(route.params.suiteId),
                                                    projectId: Number(route.params.id)
                                                }
                                            }
                                        },
                                        {
                                            path: 'test/:testId',
                                            name: 'test-editor',
                                            component: () => import('./views/main/project/TestEditor.vue'),
                                            props: (route) => {
                                                return {
                                                    testId: Number(route.params.testId),
                                                    suiteId: Number(route.params.suiteId),

                                                }
                                            }
                                        }
                                    ]
                                }

                            ]
                        },
                        {
                            path: 'profile',
                            component: RouterComponent,
                            redirect: 'profile/view',
                            children: [
                                {
                                    path: 'view',
                                    component: () => import(
                                        /* webpackChunkName: "main-profile" */ './views/main/profile/UserProfile.vue'),
                                },
                                {
                                    path: 'password',
                                    component: () => import(
                                        /* webpackChunkName: "main-profile-password" */ './views/main/profile/UserProfileEditPassword.vue'),
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
                                    path: 'general',
                                    component: () => import(
                                        /* webpackChunkName: "main-admin" */ './views/main/admin/settings/SettingsGeneral.vue'),
                                },
                                {
                                    path: 'users',
                                    redirect: 'users/all',
                                },
                                {
                                    path: 'users/all',
                                    component: () => import(
                                        /* webpackChunkName: "main-admin-users" */ './views/main/admin/AdminUsers.vue'),
                                },
                                {
                                    path: 'users/invite',
                                    component: () => import(
                                        /* webpackChunkName: "main-admin-users" */ './views/main/admin/InviteUsers.vue'),
                                },
                                {
                                    path: 'users/edit/:id',
                                    name: 'main-admin-users-edit',
                                    component: () => import(
                                        /* webpackChunkName: "main-admin-users-edit" */ './views/main/admin/EditUser.vue'),
                                },
                                {
                                    path: 'users/create',
                                    name: 'main-admin-users-create',
                                    component: () => import(
                                        /* webpackChunkName: "main-admin-users-create" */ './views/main/admin/CreateUser.vue'),
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            path: '/*', redirect: '/',
        },
    ],
});
