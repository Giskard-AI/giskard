import axios from 'axios';
import {apiUrl, apiUrlJava} from '@/env';
import {IDataMetadata, IModelMetadata} from './interfaces';
import {getLocalToken} from '@/utils';
import {
  AdminUserDTO,
  AppConfigDTO,
  CodeTestCollection,
  CreateFeedbackDTO,
  CreateFeedbackReplyDTO,
  FeedbackDTO,
  FeedbackMinimalDTO,
  FileDTO,
  JWTToken,
  ManagedUserVM,
  ModelDTO,
  PasswordResetRequest,
  ProjectDTO,
  ProjectPostDTO,
  RoleDTO,
  TestDTO,
  TestExecutionResultDTO,
  TestSuiteDTO,
  TokenAndPasswordVM,
  UpdateMeDTO,
  UpdateTestSuiteDTO,
  UserDTO
} from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

function authHeaders(token: string) {
  return {
    headers: {
      Authorization: `Bearer ${token}`
    }
  };
}

const axiosProject = axios.create({
  baseURL: `${apiUrlJava}/api/v2/project`
});
axios.interceptors.request.use(function(config) {
  // Do something before request is sent
  let jwtToken = getLocalToken();
  if (jwtToken && config && config.headers) {
    config.headers.Authorization = `Bearer ${jwtToken}`;
  }
  return config;
});

// this is to automatically parse responses from the projects API, be it array or single objects
axiosProject.interceptors.response.use(resp => {
  if (Array.isArray(resp.data)) {
    resp.data.map(p => p.created_on = new Date(p.created_on));
  } else if (resp.data.hasOwnProperty('created_on')) {
    resp.data.created_on = new Date(resp.data.created_on);
  }
  return resp;
});

export const api = {
  async logInGetToken(username: string, password: string) {
    return axios.post(`${apiUrlJava}/api/v2/authenticate`, { username, password });
  },
  async getMe(token: string) {
    return axios.get<AppConfigDTO>(`${apiUrlJava}/api/v2/account`, authHeaders(token));
  },
  async updateMe(token: string, data: UpdateMeDTO) {
    return axios.put<AdminUserDTO>(`${apiUrlJava}/api/v2/account`, data, authHeaders(token));
  },
  async getUsers(token: string) {
    return axios.get<AdminUserDTO[]>(`${apiUrlJava}/api/v2/admin/users`, authHeaders(token));
  },
  async getRoles() {
    return axios.get<RoleDTO[]>(`${apiUrlJava}/api/v2/roles`);
  },
  async updateUser(token: string, data: Partial<AdminUserDTOWithPassword>) {
    return axios.put(`${apiUrlJava}/api/v2/admin/users`, data, authHeaders(token));
  },
  async createUser(token: string, data: AdminUserDTOWithPassword) {
    return axios.post(`${apiUrlJava}/api/v2/admin/users/`, data, authHeaders(token));
  },
  async signupUser(userData: ManagedUserVM) {
    return axios.post(`${apiUrlJava}/api/v2/register`, userData);
  },
  async deleteUser(token: string, userId: number) {
    return axios.delete(`${apiUrlJava}/api/v2/admin/users/${userId}`, authHeaders(token));
  },
  async passwordRecovery(email: string) {
    return axios.post(`${apiUrlJava}/api/v2/account/password-recovery`, <PasswordResetRequest>{ email });
  },
  async resetPassword(password: string, token: string) {
    return axios.post(`${apiUrlJava}/api/v2/account/reset-password`, <TokenAndPasswordVM>{
      newPassword: password,
      token
    });
  },
  async getSignupLink(token: string) {
    return axios.get(`${apiUrlJava}/api/v2/signuplink`, authHeaders(token));
  },
  async inviteToSignup(token: string, email: string) {
    const params = new URLSearchParams();
    params.append('email', email);

    return axios.post(`${apiUrlJava}/api/v2/users/invite`, params, authHeaders(token));
  },
  async getCoworkersMinimal(token: string) {
    return axios.get<UserDTO[]>(`${apiUrlJava}/api/v2/users/coworkers`, authHeaders(token));
  },
  async getApiAccessToken(token: string) {
    return axios.get<JWTToken>(`${apiUrlJava}/api/v2/api-access-token`, authHeaders(token));
  },

  // Projects
  async getProjects(token: string) {
    return axiosProject.get<ProjectDTO[]>(`/`, authHeaders(token));
  },
  async getProject(token: string, id: number) {
    return axiosProject.get<ProjectDTO>(`/${id}`, authHeaders(token));
  },
  async createProject(token: string, data: ProjectPostDTO) {
    return axiosProject.post<ProjectDTO>(`/`, data, authHeaders(token));
  },
  async deleteProject(token: string, id: number) {
    return axiosProject.delete<ProjectDTO>(`/${id}`, authHeaders(token));
  },
  async editProject(token: string, id: number, data: ProjectPostDTO) {
    return axiosProject.put<ProjectDTO>(`/${id}`, data, authHeaders(token));
  },
  async inviteUserToProject(token: string, projectId: number, userId: number) {
    return axiosProject.put<ProjectDTO>(`/${projectId}/guests/${userId}`, null, authHeaders(token));
  },
  async uninviteUserFromProject(token: string, projectId: number, userId: number) {
    return axiosProject.delete<ProjectDTO>(`/${projectId}/guests/${userId}`, authHeaders(token));
  },
  // Models
  async getProjectModels(token: string, id: number) {
    return axiosProject.get<ModelDTO[]>(`/${id}/models`, authHeaders(token));
  },
  async deleteDatasetFile(token: string, id: number) {
    return axios.delete(`${apiUrl}/api/v1/files/datasets/${id}`, authHeaders(token));
  },
  async downloadModelFile(token: string, modelId: number) {
    return axios.get(`${apiUrlJava}/api/v2/files/models/${modelId}`, { ...authHeaders(token), 'responseType': 'blob' });
  },
  async downloadDataFile(token: string, id: number) {
    return axios.get(`${apiUrlJava}/api/v2/files/datasets/${id}`, { ...authHeaders(token), 'responseType': 'blob' });
  },
  async peakDataFile(token: string, id: number) {
    return axios.get(`${apiUrl}/api/v1/files/datasets/${id}/peak`, authHeaders(token));
  },
  async getFeaturesMetadata(token: string, modelId: number, datasetId: number) {
    return axios.get<IDataMetadata[]>(`${apiUrl}/api/v1/models/${modelId}/features/${datasetId}`, authHeaders(token));
  },
    async getDataFilteredByRange(token, inspectionId, props, filter) {
        return axios.post(`${apiUrlJava}/api/v2/inspection/${inspectionId}/rowsFiltered`,filter,{ ...authHeaders(token),  params:props});
            },
  async getLabelsForTarget(token: string, inspectionId: number) {
    return axios.get(`${apiUrlJava}/api/v2/inspection/${inspectionId}/labels`, authHeaders(token));
  },
    async getProjectDatasets(token: string, id: number) {
    return axiosProject.get<FileDTO[]>(`/${id}/datasets`, authHeaders(token));
  },
  async getInspection(token: string, inspectionId: number) {
    return axios.get(`${apiUrlJava}/api/v2/inspection/${inspectionId}`, authHeaders(token));
  },
  async uploadDataFile(token: string, projectId: number, fileData: any) {
    const formData = new FormData();
    formData.append('file', fileData);
    const config = authHeaders(token);
    config.headers['content-type'] = 'multipart/form-data';
    return axios.post(`${apiUrl}/api/v1/files/data/upload?projectId=${projectId}`, formData, config);
  },
  async getModelMetadata(token: string, modelId: number) {
    return axios.get<IModelMetadata>(`${apiUrl}/api/v1/models/${modelId}/metadata`, authHeaders(token));
  },
  async predict(token: string, modelId: number, inputData: object) {
    return axios.post(`${apiUrl}/api/v1/models/${modelId}/predict`, { features: inputData }, authHeaders(token));
    },
    async predictDf(token: string, modelId: number, inputData: object) {
        return axios.post(`${apiUrl}/api/v1/models/${modelId}/predicts`, { features: inputData }, authHeaders(token));
    },
    async prepareInspection(token: string, modelId: string, datasetId: string, target:string) {
        return axios.get(`${apiUrl}/api/v1/files/inspect`,  {...authHeaders(token),params: { model_id: modelId,dataset_id:datasetId , target:target }});
  },
  async explain(token: string, modelId: number, datasetId: number, inputData: object) {
    return axios.post(`${apiUrl}/api/v1/models/${modelId}/${datasetId}/explain`, { features: inputData }, authHeaders(token));
  },
  async explainText(token: string, modelId: number, inputData: object, featureName: string) {
    return axios.post(`${apiUrl}/api/v1/models/${modelId}/explain_text/${featureName}`, { features: inputData }, authHeaders(token));
  },
  // feedbacks
  async submitFeedback(token: string, payload: CreateFeedbackDTO, projectId: number) {
    return axios.post(`${apiUrlJava}/api/v2/feedbacks/${projectId}`, payload, authHeaders(token));
  },
  async getProjectFeedbacks(token: string, projectId: number) {
    return axios.get<FeedbackMinimalDTO[]>(`${apiUrlJava}/api/v2/feedbacks/all/${projectId}`, authHeaders(token));
  },
  async getFeedback(token: string, id: number) {
    return axios.get<FeedbackDTO>(`${apiUrlJava}/api/v2/feedbacks/${id}`, authHeaders(token));
  },
  async replyToFeedback(token: string, feedbackId: number, content: string, replyToId: number | null = null) {
    return axios.post(`${apiUrlJava}/api/v2/feedbacks/${feedbackId}/reply`,
        <CreateFeedbackReplyDTO>{
          content,
          replyToReply: replyToId
        }, authHeaders(token));
  },
  async getTestSuites(projectId: number) {
    return await axios.get<Array<TestSuiteDTO>>(`${apiUrlJava}/api/v2/testing/suites/${projectId}`);
  },
  async getTests(suiteId: number) {
    return await axios.get<Array<TestDTO>>(`${apiUrlJava}/api/v2/testing/tests`, { params: { suiteId } });
  },
  async getTestSuite(suiteId: number) {
    return await axios.get<TestSuiteDTO>(`${apiUrlJava}/api/v2/testing/suite/${suiteId}`);
  },
  async deleteTestSuite(suiteId: number) {
    return await axios.delete<TestSuiteDTO>(`${apiUrlJava}/api/v2/testing/suite/${suiteId}`);
  },
  async createTestSuite(projectId: number, name: string, modelId: number) {
    return await axios.post(`${apiUrlJava}/api/v2/testing/suites`, {
      name: name,
      project: { id: projectId },
      model: { id: modelId }
    });
  },
  async saveTestSuite(testSuite: UpdateTestSuiteDTO) {
    return await axios.put(`${apiUrlJava}/api/v2/testing/suites`, testSuite);
  },
  async getTestDetails(testId: number) {
    return await axios.get(`${apiUrlJava}/api/v2/testing/tests/${testId}`);
  },
  async getCodeTestTemplates() {
    return await axios.get<CodeTestCollection[]>(`${apiUrlJava}/api/v2/testing/tests/code-test-templates`);
  },
  async deleteTest(testId: number) {
    return await axios.delete<TestSuiteDTO>(`${apiUrlJava}/api/v2/testing/tests/${testId}`);
  },
  async saveTest(testDetails: TestDTO) {
    return await axios.put(`${apiUrlJava}/api/v2/testing/tests`, testDetails);
  },
  async runTest(testId: number) {
    return await axios.post<TestExecutionResultDTO>(`${apiUrlJava}/api/v2/testing/tests/${testId}/run`);
  },
  async createTest(suiteId: number, name: string) {
    return await axios.post(`${apiUrlJava}/api/v2/testing/tests`, {
      name: name,
      suiteId: suiteId
    });
  },
  async executeTestSuite(suiteId: number) {
    return await axios.post<Array<TestExecutionResultDTO>>(`${apiUrlJava}/api/v2/testing/suites/execute`, { suiteId });
  }
};
