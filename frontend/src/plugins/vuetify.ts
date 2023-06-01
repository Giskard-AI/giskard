import Vue from 'vue';
import Vuetify from 'vuetify/lib/framework';

import colors from 'vuetify/lib/util/colors';

Vue.use(Vuetify);
export default new Vuetify({
  iconfont: 'mdi',
  theme: {
    options: { customProperties: true },
    themes: {
      light: {
        primaryLight: "#91f7c0",   
        primary: "#087038",
        secondary: colors.grey.darken3,
        accent: colors.pink.darken3,
        error: colors.red.darken4,
        success: colors.lightBlue.accent4,
        info: colors.blueGrey,
        warning: colors.amber.darken2
      },
    },
  },
});
