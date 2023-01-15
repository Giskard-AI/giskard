import axios, {AxiosError} from 'axios';
import {apiURL} from '@/env';
import {getLocalToken, removeLocalToken} from '@/utils';
import Vue from "vue";

import {
    AdminUserDTO,
    AppConfigDTO,
    CreateFeedbackDTO,
    CreateFeedbackReplyDTO,
    DatasetDTO,
    ExplainResponseDTO,
    ExplainTextResponseDTO,
    FeatureMetadataDTO,
    FeedbackDTO,
    FeedbackMinimalDTO,
    GeneralSettings,
    ImportProjectDTO,
    InspectionCreateDTO,
    InspectionDTO,
    JWTToken,
    ManagedUserVM,
    MessageDTO,
    MLWorkerInfoDTO,
    ModelDTO,
    PasswordResetRequest,
    PredictionDTO,
    PredictionInputDTO,
    PrepareDeleteDTO,
    ProjectDTO,
    ProjectPostDTO,
    RoleDTO,
    TestDTO,
    TestExecutionResultDTO,
    TestSuiteCreateDTO,
    TestSuiteDTO,
    TestTemplatesResponse,
    TokenAndPasswordVM,
    UpdateMeDTO,
    UpdateTestSuiteDTO,
    UserDTO
} from './generated-sources';
import {TYPE} from "vue-toastification";
import ErrorToast from "@/views/main/utils/ErrorToast.vue";
import router from "@/router";
import {commitSetLoggedIn, commitSetToken} from "@/store/main/mutations";
import store from "@/store";
import mixpanel from "mixpanel-browser";
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

function jwtRequestInterceptor(config) {
    // Do something before request is sent
    let jwtToken = getLocalToken();
    if (jwtToken && config && config.headers) {
        config.headers.Authorization = `Bearer ${jwtToken}`;
    }
    return config;
}

function authHeaders(token: string | null) {
    return {
        headers: {
            Authorization: `Bearer ${token}`
        }
    };
}

const API_V2_ROOT = `${apiURL}/api/v2`;

const axiosProject = axios.create({
    baseURL: `${API_V2_ROOT}/project`
});
const apiV2 = axios.create({
    baseURL: API_V2_ROOT
});

function unpackInterceptor(response) {
    return response.data;
}

function trackError(error) {
    try {
        mixpanel.track('API error', {
            'code': error.code,
            'message': error.message,
            'detail': error.response.data.detail,
            'httpCode': error.response.code,
            'method': error.config.method,
            'url': error.config.url,
            'data': error.response.data
        });
    } catch (e) {
        console.error("Failed to track API Error", e)
    }
}

function replacePlaceholders(detail: string) {
    return detail.replaceAll("GISKARD_ADDRESS", window.location.hostname);
}

async function errorInterceptor(error) {
    if (error.code !== AxiosError.ERR_CANCELED) {
        trackError(error);
    }


    if (error.response) {
        if (error.response.status === 401) {
            removeLocalToken();
            commitSetToken(store, '');
            commitSetLoggedIn(store, false);
            if (router.currentRoute.path !== '/auth/login') {
                await router.push('/auth/login');
            }
        } else {
            let title: string;
            let detail: string;
            let stack: string | undefined = undefined;
            if (error.response.status === 502) {
                title = error.response.statusText;
                detail = "Error while connecting to Giskard server, check that it's running";
            } else {
                title = error.response.data.title || error.message;
                detail = error.response.data.detail || error.request.responseURL;
                stack = error.response.data.stack;
            }

            detail = replacePlaceholders(detail);

            Vue.$toast(
                {
                    component: ErrorToast,
                    props: {
                        title: title || 'Error',
                        detail: detail,
                        stack: stack
                    }
                },
                {
                    toastClassName: "error-toast",
                    type: TYPE.ERROR,
                });
        }
    }
    return Promise.reject(error);
}


apiV2.interceptors.response.use(unpackInterceptor, errorInterceptor);
apiV2.interceptors.request.use(jwtRequestInterceptor);

axios.interceptors.request.use(jwtRequestInterceptor);

// this is to automatically parse responses from the projects API, be it array or single objects
axiosProject.interceptors.response.use(resp => {
    if (Array.isArray(resp.data)) {
        resp.data.forEach(p => p.created_on = new Date(p.created_on));
    } else if (resp.data.hasOwnProperty('created_on')) {
        resp.data.created_on = new Date(resp.data.created_on);
    }
    return resp;
});
axiosProject.interceptors.response.use(unpackInterceptor, errorInterceptor);
axiosProject.interceptors.request.use(jwtRequestInterceptor);


function downloadURL(urlString) {
    let url = new URL(urlString, window.location.origin);
    let token = getLocalToken();
    if (token) {
        url.searchParams.append('token', token);
    }
    let hiddenIFrameID = '_hidden_download_frame_',
        iframe: HTMLIFrameElement = <HTMLIFrameElement>document.getElementById(hiddenIFrameID);
    if (iframe == null) {
        iframe = document.createElement('iframe');
        iframe.id = hiddenIFrameID;
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
    }
    iframe.src = url.toString();
}


export const api = {
    async logInGetToken(username: string, password: string) {
        return apiV2.post<unknown, JWTToken>(`/authenticate`, {username, password});
    },
    async getUserAndAppSettings() {
        return apiV2.get<unknown, AppConfigDTO>(`/settings`);
    },
    async getMLWorkerSettings() {
        return apiV2.get<unknown, MLWorkerInfoDTO[]>(`/settings/ml-worker-info`);
    },
    async saveGeneralSettings(settings: GeneralSettings) {
        return apiV2.post<unknown, GeneralSettings>(`/settings`, settings);
    },
    async updateMe(data: UpdateMeDTO) {
        return apiV2.put<unknown, AdminUserDTO>(`/account`, data);
    },
    async getUsers() {
        return apiV2.get<unknown, AdminUserDTO[]>(`/admin/users`);
    },
    async getRoles() {
        return apiV2.get<unknown, RoleDTO[]>(`/roles`);
    },
    async updateUser(data: Partial<AdminUserDTOWithPassword>) {
        return apiV2.put<unknown, AdminUserDTO.AdminUserDTOWithPassword>(`/admin/users`, data);
    },
    async createUser(data: AdminUserDTOWithPassword) {
        return apiV2.post<unknown, AdminUserDTO>(`/admin/users/`, data);
    },
    async signupUser(userData: ManagedUserVM) {
        return apiV2.post<unknown, void>(`/register`, userData);
    },
    async deleteUser(userId: number) {
        return apiV2.delete<unknown, void>(`/admin/users/${userId}`);
    },
    async passwordRecovery(email: string) {
        return apiV2.post<unknown, void>(`/account/password-recovery`, <PasswordResetRequest>{email});
    },
    async resetPassword(password: string) {
        return apiV2.post<unknown, void>(`/account/reset-password`, <TokenAndPasswordVM>{
            newPassword: password
        });
    },
    async getSignupLink() {
        return apiV2.get<unknown, string>(`/signuplink`);
    },
    async inviteToSignup(email: string) {
        const params = new URLSearchParams();
        params.append('email', email);

        return apiV2.post<unknown, void>(`/users/invite`, params);
    },
    async getCoworkersMinimal() {
        return apiV2.get<unknown, UserDTO[]>(`/users/coworkers`);
    },
    async getApiAccessToken() {
        return apiV2.get<unknown, JWTToken>(`/api-access-token`);
    },

    // Projects
    async getProjects() {
        return apiV2.get<unknown, ProjectDTO[]>(`projects`);
    },
    async getProject(id: number) {
        return axiosProject.get<unknown, ProjectDTO>(`/`, {params: {id}});
    },
    async createProject(data: ProjectPostDTO) {
        return axiosProject.post<unknown, ProjectDTO>(`/`, data);
    },
    async deleteProject(id: number) {
        return axiosProject.delete<unknown, ProjectDTO>(`/${id}`);
    },
    async editProject(id: number, data: ProjectPostDTO) {
        return axiosProject.put<unknown, ProjectDTO>(`/${id}`, data);
    },
    async inviteUserToProject(projectId: number, userId: number) {
        return axiosProject.put<unknown, ProjectDTO>(`/${projectId}/guests/${userId}`, null);
    },
    async uninviteUserFromProject(projectId: number, userId: number) {
        return axiosProject.delete<unknown, ProjectDTO>(`/${projectId}/guests/${userId}`);
    },
    // Models
    async getProjectModels(id: number) {
        return axiosProject.get<unknown, ModelDTO[]>(`/${id}/models`);
    },
    async exportProjet(id: number){
        return axiosProject.get<unknown, Blob>(`/${id}/export`, {responseType:'blob'})
    },
    async importProject(formData: FormData){
        const headers = { 'Content-Type': 'multipart/form-data' };
        return axiosProject.post<unknown, ImportProjectDTO>(`/import`, formData, {
            headers: headers
        });
    },
    async importConflictedProject(newKey: String, pathToTmpDirectory: String){
        return axiosProject.post<unknown, ImportProjectDTO>(`/import/conflict`,  {newKey: newKey, pathToTmpDirectory:  pathToTmpDirectory});
    },
    async deleteDatasetFile(datasetId: number) {
        return apiV2.delete<unknown, MessageDTO>(`/dataset/${datasetId}`);
    },
    async prepareDeleteDataset(datasetId: number) {
        return apiV2.get<unknown, PrepareDeleteDTO>(`/dataset/prepare-delete/${datasetId}`);
    },
    async prepareDeleteModel(modelId: number) {
        return apiV2.get<unknown, PrepareDeleteDTO>(`/models/prepare-delete/${modelId}`);
    },
    async deleteModelFiles(modelId: number) {
        return apiV2.delete<unknown, MessageDTO>(`/models/${modelId}`);
    },
    downloadModelFile(id: number) {
        downloadURL(`${API_V2_ROOT}/download/model/${id}`);
    },
    downloadDataFile(id: number) {
        downloadURL(`${API_V2_ROOT}/download/dataset/${id}`);
    },
    async peekDataFile(datasetId: number) { //TODO
        return apiV2.get<unknown, any>(`/dataset/${datasetId}/rows`, {params: {offset: 0, size: 10}});
    },
    async getFeaturesMetadata(datasetId: number) {
        return apiV2.get<unknown, FeatureMetadataDTO[]>(`/dataset/${datasetId}/features`);
    },
    async getDataFilteredByRange(inspectionId, props, filter) {
        return apiV2.post<unknown, any>(`/inspection/${inspectionId}/rowsFiltered`, filter, {params: props});
    },
    async getLabelsForTarget(inspectionId: number) {
        return apiV2.get<unknown, string[]>(`/inspection/${inspectionId}/labels`);
    },
    async getProjectDatasets(id: number) {
        return axiosProject.get<unknown, DatasetDTO[]>(`/${id}/datasets`);
    },
    async getInspection(inspectionId: number) {
        return apiV2.get<unknown, InspectionDTO>(`/inspection/${inspectionId}`);
    },
    async uploadDataFile(projectKey: string, fileData: any) {
        const formData = new FormData();
        formData.append('metadata',
            new Blob([JSON.stringify({"projectKey": projectKey})], {
                type: "application/json"
            }));
        formData.append('file', fileData);
        const config = authHeaders(getLocalToken());
        config.headers['content-type'] = 'multipart/form-data';
        return apiV2.post<unknown, DatasetDTO>(`/project/data/upload`, formData, config);
    },
    async predict(modelId: number, datasetId: number, inputData: { [key: string]: string }, controller: AbortController) {
        const data: PredictionInputDTO = {
            datasetId: datasetId,
            features: inputData
        }
        return apiV2.post<unknown, PredictionDTO>(`/models/${modelId}/predict`, data, {signal: controller.signal});
    },

    async prepareInspection(payload: InspectionCreateDTO) {
        return apiV2.post<unknown, InspectionDTO>(`/inspection`, payload);
    },
    async explain(modelId: number, datasetId: number, inputData: object, controller: AbortController) {
        return apiV2.post<unknown, ExplainResponseDTO>(`/models/${modelId}/explain/${datasetId}`,
            {features: inputData},
            {signal: controller.signal});
    },
    async explainText(modelId: number, datasetId: number, inputData: object, featureName: string) {
        return apiV2.post<unknown, ExplainTextResponseDTO>(`/models/explain-text/${featureName}`,
            {
                features: inputData
            }, {params: {modelId, datasetId}});
    },
    // feedbacks
    async submitFeedback(payload: CreateFeedbackDTO, projectId: number) {
        return apiV2.post<unknown, void>(`/feedbacks/${projectId}`, payload);
    },
    async getProjectFeedbacks(projectId: number) {
        return apiV2.get<unknown, FeedbackMinimalDTO[]>(`/feedbacks/all/${projectId}`);
    },
    async getFeedback(id: number) {
        return apiV2.get<unknown, FeedbackDTO>(`/feedbacks/${id}`);
    },
    async replyToFeedback(feedbackId: number, content: string, replyToId: number | null = null) {
        return apiV2.post<unknown, void>(`/feedbacks/${feedbackId}/reply`,
            <CreateFeedbackReplyDTO>{
                content,
                replyToReply: replyToId
            });
    },
    async getTestSuites(projectId: number) {
        return apiV2.get<unknown, Array<TestSuiteDTO>>(`/testing/suites/${projectId}`);
    },
    async getTests(suiteId: number) {
        return apiV2.get<unknown, Array<TestDTO>>(`/testing/tests`, {params: {suiteId}});
    },
    async getTestSuite(suiteId: number) {
        return apiV2.get<unknown, TestSuiteDTO>(`/testing/suite/${suiteId}`);
    },
    async deleteTestSuite(suiteId: number) {
        return apiV2.delete<unknown, TestSuiteDTO>(`/testing/suite/${suiteId}`);
    },
    async createTestSuite(data: TestSuiteCreateDTO) {
        return apiV2.post<unknown, TestSuiteDTO>(`/testing/suites`, data);
    },
    async saveTestSuite(testSuite: UpdateTestSuiteDTO) {
        return apiV2.put<unknown, TestSuiteDTO>(`/testing/suites`, testSuite);
    },
    async getTestDetails(testId: number) {
        return apiV2.get<unknown, TestDTO>(`/testing/tests/${testId}`);
    },
    async getCodeTestTemplates(suiteId: number) {
        return apiV2.get<unknown, TestTemplatesResponse>(`/testing/tests/code-test-templates`, {params: {suiteId}});
    },

    async deleteTest(testId: number) {
        return apiV2.delete<unknown, TestSuiteDTO>(`/testing/tests/${testId}`);
    },
    async saveTest(testDetails: TestDTO) {
        return apiV2.put<unknown, TestDTO>(`/testing/tests`, testDetails);
    },
    async runTest(testId: number) {
        return apiV2.post<unknown, TestExecutionResultDTO>(`/testing/tests/${testId}/run`);
    },
    async createTest(suiteId: number, name: string) {
        return apiV2.post<unknown, TestDTO>(`/testing/tests`, {
            name: name,
            suiteId: suiteId
        });
    },
    async executeTestSuite(suiteId: number) {
        return apiV2.post<unknown, Array<TestExecutionResultDTO>>(`/testing/suites/execute`, {suiteId});
    },
};
