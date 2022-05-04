import { AdminUserDTO, RoleDTO } from '@/generated-sources';
import AdminUserDTOMigration = AdminUserDTO.AdminUserDTOMigration;

export interface AdminState {
    users: AdminUserDTOMigration[];
    roles: RoleDTO[];
}
