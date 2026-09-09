import {
  apiPost,
  clearAccessToken,
  setAccessToken,
} from "./api";


export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;

  user: {
    id: string;
    email: string;
  };

  profile: {
    id: string;
    full_name: string;
    email: string;
    role: string;
    discipline?: string | null;
  } | null;
}


export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {

  const response =
    await apiPost<LoginResponse>(
      "/auth/login",
      {
        email,
        password,
      }
    );

  setAccessToken(
    response.access_token
  );

  if (response.profile) {
    localStorage.setItem(
      "user_profile",
      JSON.stringify(response.profile)
    );
  }

  return response;
}


export function logout() {
  clearAccessToken();

  localStorage.removeItem(
    "user_profile"
  );

  sessionStorage.removeItem(
    "field-progress-dashboard-project-id"
  );
}


export function getStoredProfile() {
  const value =
    localStorage.getItem(
      "user_profile"
    );

  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}
