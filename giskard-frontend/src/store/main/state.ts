import {IUserProfile, IProject, IUserProfileMinimal, IAppSettings} from '@/interfaces';

export interface AppNotification {
    content: string;
    color?: string;
    showProgress?: boolean;
}

export interface MainState {
    token: string;
    isLoggedIn: boolean | null;
    logInError: string | null;
    userProfile: IUserProfile | null;
    appSettings: IAppSettings | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
    projects: IProject[];
}
