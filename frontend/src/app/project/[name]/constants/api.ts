export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  PROJECT_FILES: (projectName: string) => `${API_BASE_URL}/api/project/${encodeURIComponent(projectName)}/files`,
  FILE_CONTENT: (projectName: string, filePath: string) => `${API_BASE_URL}/api/project/${encodeURIComponent(projectName)}/file?path=${encodeURIComponent(filePath)}`,
  FILE_OPERATIONS: {
    ADD_COMMENTS: `${API_BASE_URL}/api/file/add-comments`,
    RENAME_VARIABLES: `${API_BASE_URL}/api/file/rename-variables`,
  },
  PROJECT_UNTRACEABLE: (projectName: string) => `${API_BASE_URL}/api/project/${encodeURIComponent(projectName)}/make-untraceable`,
  GIT_HISTORY: (projectName: string) => `${API_BASE_URL}/api/project/${encodeURIComponent(projectName)}/git/history`,
} as const; 