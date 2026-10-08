import { apiClient } from "./client";

export interface AdminUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminUsersResponse {
  items: AdminUser[];
  page: number;
  limit: number;
  total: number;
}

export type AdminUserSortBy =
  | "id"
  | "email"
  | "first_name"
  | "last_name"
  | "role"
  | "created_at";
export type SortOrder = "asc" | "desc";

export interface GetAdminUsersParams {
  page?: number;
  limit?: number;
  search?: string;
  sortBy?: AdminUserSortBy;
  sortOrder?: SortOrder;
}

export function getAdminUsers(token: string, params: GetAdminUsersParams = {}) {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    limit: String(params.limit ?? 20),
    sort_by: params.sortBy ?? "created_at",
    sort_order: params.sortOrder ?? "desc",
  });
  if (params.search?.trim()) query.set("search", params.search.trim());
  return apiClient<AdminUsersResponse>(`/admin/users?${query.toString()}`, { token });
}
