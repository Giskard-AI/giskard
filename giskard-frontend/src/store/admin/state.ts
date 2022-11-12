import {AdminUserDTO, RoleDTO} from '@/generated-sources';

export interface AdminState {
    users: AdminUserDTO[];
    roles: RoleDTO[];
}
