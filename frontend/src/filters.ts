import Vue from 'vue';
import {Role} from "@/enums";

Vue.filter('humanReadableRole', function (value) {
    if (value in Role.rolesById) {
        return Role.rolesById[value];
    } else {
        console.warn(`humanReadableRole: Role ${value} not found`);
        return null;
    }

})