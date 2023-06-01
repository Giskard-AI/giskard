import { mutations } from './mutations';
import { getters } from './getters';
import { actions } from './actions';
import { MainState } from './state';

const defaultState: MainState = {
  isLoggedIn: null,
  token: '',
  logInError: null,
  userProfile: null,
  appSettings: null,
  coworkers: [],
  notifications: [],
  projects: [],
};

export const mainModule = {
  state: defaultState,
  mutations,
  actions,
  getters,
};
