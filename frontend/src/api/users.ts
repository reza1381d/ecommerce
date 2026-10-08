import { apiClient } from "./client";
import type { UserResponse } from "./auth";

export type UserProfile = UserResponse;

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string | null;
}

export function getMyProfile(token: string) {
  return apiClient<UserProfile>("/users/me", { token });
}

export function updateMyProfile(token: string, data: UserProfileUpdate) {
  return apiClient<UserProfile>("/users/me", {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}
