import Vue from 'vue';
import Router from 'vue-router';

import RouterComponent from './components/RouterComponent.vue';

Vue.use(Router);

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      component: () => import(/* webpackChunkName: "start" */ './views/main/Start.vue'),
      children: [
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
              props: (route) => { return {id: Number(route.params.id)} },
              children: [
                {
                  path: '',
                  name: 'project-overview',
                  component: () => import('./views/main/project/ProjectOverview.vue'),
                  props: (route) => { return {projectId: Number(route.params.id)} }
                },
                {
                  path: 'datasets',
                  name: 'project-datasets',
                  component: () => import('./views/main/project/Datasets.vue'),
                  props: (route) => { return {projectId: Number(route.params.id)} }
                },
                {
                  path: 'models',
                  name: 'project-models',
                  component: () => import('./views/main/project/Models.vue'),
                  props: (route) => { return {projectId: Number(route.params.id)} }
                },
                {
                  path: 'inspect',
                  name: 'project-inspector',
                  component: () => import('./views/main/project/InspectorWrapper.vue'),
                  props: route => ({ 
                    modelId: parseInt(route.query.model.toString()), 
                    datasetId: parseInt(route.query.dataset.toString()),
                    targetFeature: route.query.target,
                  }),
                  beforeEnter(to, from, next) {
                    if (!to.query.dataset || !to.query.model 
                      || isNaN(parseInt(to.query.model.toString())) 
                      || isNaN(parseInt(to.query.dataset.toString()))) {
                        // query is not valid, redirect back to basic project view
                        next({name: 'project-models', params: {id: to.params.id}})
                    } else next()
                  }
                },
                {
                  path: 'feedbacks',
                  name: 'project-feedbacks',
                  component: () => import('./views/main/project/FeedbackList.vue'),
                  props: (route) => { return {projectId: Number(route.params.id)} },
                  children: [
                    {
                      path: ':feedbackId',
                      name: 'feedback-detail',
                      component: () => import('./views/main/project/FeedbackDetail.vue'),
                      props: (route) => { return {id: Number(route.params.feedbackId)} },
                      meta: {openFeedbackDetail: true}
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
              path: 'admin',
              component: () => import(/* webpackChunkName: "main-admin" */ './views/main/admin/Admin.vue'),
              redirect: 'admin/users/all',
              children: [
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
