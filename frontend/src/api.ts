import axios, {AxiosError} from 'axios';
import {apiURL} from '@/env';
import {getLocalToken, removeLocalToken} from '@/utils';
import Vue from "vue";

import {
    AdminUserDTO,
    AppConfigDTO,
    CatalogDTO,
    CreateFeedbackDTO,
    CreateFeedbackReplyDTO,
    DatasetDTO,
    DatasetPageDTO,
    ExplainResponseDTO,
    ExplainTextResponseDTO,
    FeatureMetadataDTO,
    FeedbackDTO,
    FeedbackMinimalDTO,
    GeneralSettings,
    GenerateTestSuiteDTO,
    InspectionCreateDTO,
    InspectionDTO,
    JobDTO,
    JWTToken,
    LicenseDTO,
    ManagedUserVM,
    MessageDTO,
    MLWorkerInfoDTO,
    ModelDTO,
    PasswordResetRequest,
    PredictionDTO,
    PredictionInputDTO,
    PrepareDeleteDTO,
    PrepareImportProjectDTO,
    ProjectDTO,
    ProjectPostDTO,
    RoleDTO,
    SliceDTO,
    SlicingResultDTO,
    SuiteTestDTO,
    TestInputDTO,
    TestSuiteCompleteDTO,
    TestSuiteDTO,
    TestSuiteExecutionDTO,
    TestTemplateExecutionResultDTO,
    TokenAndPasswordVM,
    TransformationResultDTO,
    UpdateMeDTO,
    UserDTO
} from './generated-sources';
import {PostImportProjectDTO} from './generated-sources/ai/giskard/web/dto/post-import-project-dto';
import {TYPE} from "vue-toastification";
import ErrorToast from "@/views/main/utils/ErrorToast.vue";
import router from "@/router";
import mixpanel from "mixpanel-browser";
import {useUserStore} from "@/stores/user";
import {SetupDTO} from "@/generated-sources/ai/giskard/web/dto/setup-dto";
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
            const userStore = useUserStore();
            removeLocalToken();
            userStore.token = '';
            userStore.isLoggedIn = false;
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
    async getLicense() {
        return apiV2.get<unknown, LicenseDTO>(`/settings/license`);
    },
    async getUserAndAppSettings() {
        return apiV2.get<unknown, AppConfigDTO>(`/settings`);
    },
    async getMLWorkerSettings() {
        return apiV2.get<unknown, MLWorkerInfoDTO[]>(`/ml-workers`);
    },
    async stopMLWorker(internal: boolean) {
        return apiV2.post<unknown, MLWorkerInfoDTO[]>(`/ml-workers/stop`, null, {
            params: {
                internal
            }
        });
    },
    async getRunningWorkerJobs() {
        return apiV2.get<unknown, JobDTO[]>(`/jobs/running`);
    },
    async trackJob(jobUuid: string) {
        return apiV2.get<unknown, JobDTO>(`/jobs/${jobUuid}`);
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
    async deleteUser(login: string) {
        return apiV2.delete<unknown, void>(`/admin/users/${login}`);
    },
    async enableUser(login: string) {
        return apiV2.patch<unknown, void>(`/admin/users/${login}/enable`);
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
    async prepareImport(formData: FormData) {
        const headers = {'Content-Type': 'multipart/form-data'};
        return axiosProject.post<unknown, PrepareImportProjectDTO>(`/import/prepare`, formData, {
            headers: headers
        });
    },
    async importProject(postImportProject: PostImportProjectDTO) {
        return axiosProject.post<unknown, ProjectDTO>(`/import`, postImportProject);
    },
    async deleteDatasetFile(datasetId: string) {
        return apiV2.delete<unknown, MessageDTO>(`/dataset/${datasetId}`);
    },
    async prepareDeleteDataset(datasetId: string) {
        return apiV2.get<unknown, PrepareDeleteDTO>(`/dataset/prepare-delete/${datasetId}`);
    },
    async prepareDeleteModel(modelId: string) {
        return apiV2.get<unknown, PrepareDeleteDTO>(`/models/prepare-delete/${modelId}`);
    },
    async deleteModelFiles(modelId: string) {
        return apiV2.delete<unknown, MessageDTO>(`/models/${modelId}`);
    },
    downloadModelFile(id: number) {
        downloadURL(`${API_V2_ROOT}/download/model/${id}`);
    },
    async editModelName(modelId: string, name: string) {
        return apiV2.patch<unknown, ModelDTO>(`/models/${modelId}/name/${encodeURIComponent(name)}`, null)
    },
    downloadDataFile(id: string) {
        downloadURL(`${API_V2_ROOT}/download/dataset/${id}`);
    },
    downloadExportedProject(id: number) {
        downloadURL(`${API_V2_ROOT}/download/project/${id}/export`);
    },
    async peekDataFile(datasetId: string) {
        return this.getDatasetRows(datasetId, 0, 10);
    },
    async getDatasetRows(datasetId: string, offset: number, size: number) {
        return apiV2.get<unknown, DatasetPageDTO>(`/dataset/${datasetId}/rows`, {params: {offset, size}});
    },
    async getFeaturesMetadata(datasetId: string) {
        return apiV2.get<unknown, FeatureMetadataDTO[]>(`/dataset/${datasetId}/features`);
    },
    async filterDataset(datasetId: number, sliceName: string, code: string) {
        return apiV2.post<unknown, unknown>(`/dataset/${datasetId}/filter`, {sliceName: sliceName, code: code});
    },
    async getDataFilteredByRange(inspectionId, props, filter) {
        return apiV2.post<unknown, any>(`/inspection/${inspectionId}/rowsFiltered`, filter, {params: props});
    },
    async editDatasetName(datasetId: string, name: string) {
        return apiV2.patch<unknown, DatasetDTO>(`/dataset/${datasetId}/name/${encodeURIComponent(name)}`, null)
    },
    async getDataFilteredBySlice(inspectionId, sliceId) {
        return apiV2.post<unknown, any>(`/inspection/${inspectionId}/slice/${sliceId}`);
    },
    async getLabelsForTarget(inspectionId: number) {
        return apiV2.get<unknown, string[]>(`/inspection/${inspectionId}/labels`);
    },
    async getProjectDatasets(projectId: number) {
        return axiosProject.get<unknown, DatasetDTO[]>(`/${projectId}/datasets`);
    },
    async getTestSuites(projectId: number) {
        return apiV2.get<unknown, TestSuiteDTO[]>(`testing/project/${projectId}/suites`);
    },
    async createTestSuite(projectKey: string, testSuite: TestSuiteDTO) {
        return apiV2.post<unknown, number>(`testing/project/${projectKey}/suites`, testSuite);
    },
    async deleteSuite(projectKey: string, testSuiteId: number) {
        return apiV2.delete<unknown, void>(`testing/project/${projectKey}/suite/${testSuiteId}`);
    },
    async generateTestSuite(projectKey: string, generateTestSuite: GenerateTestSuiteDTO) {
        return apiV2.post<unknown, number>(`testing/project/${projectKey}/suites/generate`, generateTestSuite);
    },
    async updateTestSuite(projectKey: string, suite: TestSuiteDTO) {
        return apiV2.put<unknown, TestSuiteDTO>(`testing/project/${projectKey}/suite/${suite.id}`, suite);
    },
    async getTestSuite(projectId: number, suiteId: number) {
        return apiV2.get<unknown, TestSuiteDTO>(`testing/project/${projectId}/suite/${suiteId}`);
    },
    async getTestSuiteComplete(projectId: number, suiteId: number) {
        return apiV2.get<unknown, TestSuiteCompleteDTO>(`testing/project/${projectId}/suite/${suiteId}/complete`);
    },
    async addTestToSuite(projectId: number, suiteId: number, suiteTest: SuiteTestDTO) {
        return apiV2.post<unknown, TestSuiteDTO>(`testing/project/${projectId}/suite/${suiteId}/test`,
            suiteTest);
    },
    async getProjectSlices(id: number) {
        return axiosProject.get<unknown, SliceDTO[]>(`/${id}/slices`);
    },
    async executeTestSuite(projectId: number, suiteId: number, inputs: { [key: string]: string }) {
        return apiV2.post<unknown, any>(`testing/project/${projectId}/suite/${suiteId}/schedule-execution`, inputs);
    },
    async updateTestInputs(projectId: number, suiteId: number, testId: number, inputs: TestInputDTO[]) {
        return apiV2.put<unknown, TestSuiteExecutionDTO[]>(`testing/project/${encodeURIComponent(projectId)}/suite/${suiteId}/test/${testId}/inputs`, inputs);
    },
    async removeTest(projectId: string, suiteId: number, suiteTestId: number) {
        return apiV2.delete<unknown, void>(`testing/project/${encodeURIComponent(projectId)}/suite/${suiteId}/suite-test/${suiteTestId}`);
    },
    async getInspection(inspectionId: number) {
        return apiV2.get<unknown, InspectionDTO>(`/inspection/${inspectionId}`);
    },
    async predict(modelId: string, datasetId: string, inputData: { [key: string]: string }, controller: AbortController) {
        const data: PredictionInputDTO = {
            datasetId: datasetId,
            features: inputData
        }
        return apiV2.post<unknown, PredictionDTO>(`/models/${modelId}/predict`, data, {signal: controller.signal});
    },

    async prepareInspection(payload: InspectionCreateDTO) {
        return apiV2.post<unknown, InspectionDTO>(`/inspection`, payload);
    },
    async explain(modelId: string, datasetId: string, inputData: object, controller: AbortController) {
        return apiV2.post<unknown, ExplainResponseDTO>(`/models/${modelId}/explain/${datasetId}`,
            {features: inputData},
            {signal: controller.signal});
    },
    async explainText(modelId: string, datasetId: string, inputData: object, featureName: string) {
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
    async deleteFeedback(id: number) {
        return apiV2.delete<unknown, void>(`/feedbacks/${id}`);
    },
    async createSlice(projectId: number, name: string, code: string) {
        return apiV2.post<unknown, SliceDTO>(`/slices`, {
            name: name,
            projectId: projectId,
            code: code
        })
    },
    async editSlice(projectId: number, name: string, code: string, id: number) {
        return apiV2.put<unknown, SliceDTO>(`/slices`, {
            name: name,
            projectId: projectId,
            code: code,
            id: id
        })
    },
    async deleteSlice(projectId: number, sliceId: number) {
        return apiV2.delete(`/project/${projectId}/slices/${sliceId}`);
    },
    async validateSlice(datasetId: number, code: string) {
        return apiV2.post("/slices/validate", {
            datasetId: datasetId,
            code: code
        });
    },
    async runAdHocTest(projectId: number, testUuid: string, inputs: { [key: string]: string }) {
        return apiV2.post<unknown, TestTemplateExecutionResultDTO>(`/testing/tests/run-test`, {
            projectId,
            testUuid,
            inputs
        });
    },
    async getCatalog(projectId: number) {
        return apiV2.get<unknown, CatalogDTO>(`/catalog`, {
            params: {
                projectId
            }
        });
    },
    async uploadLicense(form: FormData) {
        return apiV2.post<unknown, unknown>(`/ee/license`, form, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    },
    async finalizeSetup(allowAnalytics: boolean, license: string) {
        return apiV2.post<SetupDTO, unknown>(`/setup`, {
            allowAnalytics: allowAnalytics,
            license: license
        });
    },
    async runAdHocSlicingFunction(slicingFnUuid: string, datasetUuid: string) {
        return apiV2.get<unknown, SlicingResultDTO>(
            `/slices/${encodeURIComponent(slicingFnUuid)}/dataset/${encodeURIComponent(datasetUuid)}`);
    },
    async runAdHocTransformationFunction(transformationFnUuid: string, datasetUuid: string) {
        return apiV2.get<unknown, TransformationResultDTO>(
            `/transformations/${encodeURIComponent(transformationFnUuid)}/dataset/${encodeURIComponent(datasetUuid)}`);
    },
};
