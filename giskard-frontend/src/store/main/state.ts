import {IUserProfileMinimal} from '@/interfaces';
import { AdminUserDTO, AppConfigDTO, ProjectDTO } from '@/generated-sources';
import AppInfoDTO = AppConfigDTO.AppInfoDTO;
import AdminUserDTOMigration = AdminUserDTO.AdminUserDTOMigration;

export interface AppNotification {
    content: string;
    color?: string;
    showProgress?: boolean;
}

export interface MainState {
    token: string;
    isLoggedIn: boolean | null;
    logInError: string | null;
    userProfile: AdminUserDTOMigration | null;
    appSettings: AppInfoDTO | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
    projects: ProjectDTO[];
}
