import {IUserProfileMinimal} from '@/interfaces';
import {AppConfigDTO, ProjectDTO} from '@/generated-sources';



export interface MainState {
    // token: string;
    // isLoggedIn: boolean | null;
    // logInError: string | null;
    // userProfile: AdminUserDTO | null;
    // appSettings: AppInfoDTO | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
    projects: ProjectDTO[];
}
