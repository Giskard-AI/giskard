import type {AdminUserDTO} from './../../dto/user/admin-user-dto';

/**
 * Generated from ai.giskard.web.rest.vm.ManagedUserVM
 */
export interface ManagedUserVM extends AdminUserDTO {
    password: string;
    token: string;
}