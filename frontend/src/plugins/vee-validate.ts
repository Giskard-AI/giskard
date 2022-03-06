import Vue from 'vue';
import { ValidationProvider, ValidationObserver, extend } from 'vee-validate';
import { required, email, alpha_dash, min, max } from 'vee-validate/dist/rules';

// Add from pre-existing rules
extend('email', {...email, message: 'Not a valid email'});
extend('required', {...required, message: '{_field_} is required'});
extend('alpha_dash', {...alpha_dash, message: '{_field_} may only contain alphabetic characters, numbers, dashes or underscores'});
extend('min', {...min, message: 'Minimum of {length} characters'});
extend('max', {...max, message: 'Maximum of {length} characters'});

// custom rule for passwords
extend('password', (value) => {
    // TODO: enforce more secure rules later
    if (value.length < 5) {
        return "Passwords must be at least 5 characters long"
    }
    if (value.match(/[0-9]/g) == null) {
        return "Passwords must contain at least 1 digit"
    }
    return true
})
extend('confirms', {
    params: ['target'],
    validate(value, { target }:any) {
      return value === target;
    },
    message: 'Password confirmation does not match'
  });

// Register it globally
Vue.component('ValidationProvider', ValidationProvider);
Vue.component('ValidationObserver', ValidationObserver);