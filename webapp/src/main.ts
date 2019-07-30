import Vue from 'vue';
import App from './App.vue';
import AppV2 from './AppV2.vue';
import store from './store';
import Vuetify from 'vuetify';
import 'vuetify/dist/vuetify.min.css';
import socketio from 'socket.io-client'
import VueSocketIO from 'vue-socket.io'
import Trend from 'vuetrend';
import colors from 'vuetify/es5/util/colors'

Vue.use(Trend);
Vue.use(Vuetify, {
  theme: {
    primary: colors.grey.darken3,
    // secondary: '#424242',
    accent: colors.grey.lighten1,
    error: colors.grey,
    info: colors.grey.darken1,
    success: colors.grey.darken1,
    warning: colors.grey.darken1
  }}
);
Vue.config.productionTip = false;
let host = window.location.host;
let path = window.location.pathname;
path.endsWith("/") ? window.location.pathname : window.location.pathname + "/";
path = path + "socket.io";
console.log("socket connecting to: ", host, "path: ", path);
export const SocketInstance = socketio(host, { path: path });
// Vue.use(VueSocketIO, store);

Vue.use(new VueSocketIO({
  debug: false,
  connection: SocketInstance,
  vuex: {
      store,
      actionPrefix: 'SOCKET_',
      mutationPrefix: 'SOCKET_'
  },
  options: { 
    // path: "/my-app/"
   } //Optional options
}))

new Vue({
  store,
  // render: (h) => h(App),
  render: (h) => h(AppV2),
}).$mount('#app');
