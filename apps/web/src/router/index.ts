import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '../pages/DashboardPage.vue'
import ImportPage from '../pages/ImportPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ProjectTypesPage from '../pages/ProjectTypesPage.vue'
import RecordDetailPage from '../pages/RecordDetailPage.vue'
import RecordsPage from '../pages/RecordsPage.vue'
import UsersPage from '../pages/UsersPage.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginPage, meta: { public: true } },
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', name: 'dashboard', component: DashboardPage },
    { path: '/records', name: 'records', component: RecordsPage },
    { path: '/records/:id', name: 'record-detail', component: RecordDetailPage },
    { path: '/project-types', name: 'project-types', component: ProjectTypesPage },
    { path: '/imports', name: 'imports', component: ImportPage },
    { path: '/users', name: 'users', component: UsersPage, meta: { admin: true } },
  ],
})
