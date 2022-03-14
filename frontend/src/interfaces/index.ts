export interface IAppInitData {
    user: IUserProfile,
    app: IAppSettings
}

export interface IAppSettings {
    plan_code: 'basic' | 'enterprise'
    plan_name: string
    seats_available?: number
}

export interface IUserProfile {
    email: string;
    is_active: boolean;
    role: IRole;
    display_name: string;
    user_id: string;
    id: number;
}


export interface IUserProfileUpdate {
    email?: string;
    display_name?: string;
    password?: string;
    is_active?: boolean;
    role_id?: number;
}

export interface IUserProfileCreate {
    email: string;
    user_id: string;
    password: string;
    role_id?: number;
    display_name?: string;
}

export interface IUserProfileMinimal {
    user_id: string,
    display_name?: string
}

export interface IRole {
    id: number,
    name: string
}

export interface IProject {
    id: number,
    key: string,
    name: string,
    description: string,
    created_on: Date,
    owner_id: number,
    owner_details: IUserProfileMinimal,
    guest_list: IUserProfileMinimal[]
}

export interface IProjectCreate {
    name: string,
    description?: string,
}

export interface IProjectUpdate {
    name: string,
    description: string,
}

export interface IProjectFile {
    id: number,
    name: string,
    size: number,
    creation_date: string,
}

export interface IProjetFileModel extends IProjectFile {
    python_version: string
}

export interface IDataMetadata {
    feat_name: string,
    feat_type: string,
    feat_cat_values: string[]
}

export interface IModelMetadata {
    prediction_task: string,
    classification_labels: string[],
    classification_threshold: number
}

export interface IFeedbackCreate {
    project_id: number,
    model_id: number,
    dataset_id: number,
    target_feature?: string,
    user_data: object,
    original_data: object,
    feedback_type: string,
    feature_name?: string,
    feature_value?: any,
    feedback_choice?: string,
    feedback_message?: string
}

export interface IFeedbackForList {
    id: number,
    user_id: string,
    model_name: string,
    dataset_name: string,
    created_on: Date,
    feedback_type: string,
    feature_name?: string,
    feature_value?: any,
    feedback_choice?: string,
    feedback_message?: string
}

export interface IFeedbackDisplay {
    id: number,
    user: IUserProfileMinimal,
    created_on: Date,
    model: {id: number, file_name: string},
    dataset: {id: number, file_name: string},
    target_feature?: string,
    feedback_type: string,
    feature_name?: string,
    feature_value?: any,
    feedback_choice?: string,
    feedback_message?: string
    user_data: object,
    original_data: object
    replies: IFeedbackReply[]
}

export interface IFeedbackReply {
    id: number,
    user: IUserProfileMinimal,
    created_on: Date,
    content: string,
    reply_to_reply?: number
}