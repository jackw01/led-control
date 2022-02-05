import SetupPage from './pages/SetupPage.js';
import ControlPage from './pages/ControlPage.js';

import SliderNumberInput from './components/SliderNumberInput.js';

const routes = [
  { path: '/', component: ControlPage },
  { path: '/setup', component: SetupPage },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
})

const app = Vue.createApp({});
app.component('slider-number-input', SliderNumberInput);
app.use(router);
app.mount('#main');
