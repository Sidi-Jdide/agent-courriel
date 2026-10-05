import { createRouter, createWebHistory } from 'vue-router'
import TableauDeBord from './views/TableauDeBord.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'tableau', component: TableauDeBord, meta: { titre: 'Tableau de bord' } },
    { path: '/courriels', name: 'courriels', component: () => import('./views/VueCourriels.vue'), meta: { titre: 'Courriels' } },
    { path: '/courriels/:id', name: 'detail', component: () => import('./views/DetailCourriel.vue'), props: true, meta: { titre: 'Détail' } },
    { path: '/:chemin(.*)*', name: 'introuvable', component: () => import('./views/PageIntrouvable.vue'), meta: { titre: 'Introuvable' } },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((vers) => {
  document.title = `${vers.meta.titre ?? ''} · Agent courriel`
})
