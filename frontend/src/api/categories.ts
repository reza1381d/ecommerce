import { apiClient } from "./client";

export interface Category {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface CategoryInput {
  name: string;
  description?: string | null;
}

export type CategoryUpdate = Partial<CategoryInput> & {
  is_active?: boolean;
};

export function getCategories() {
  return apiClient<Category[]>("/categories");
}

export function createCategory(token: string, data: CategoryInput) {
  return apiClient<Category>("/categories", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function updateCategory(
  token: string,
  categoryId: number,
  data: CategoryUpdate,
) {
  return apiClient<Category>(`/categories/${categoryId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}

export function deleteCategory(token: string, categoryId: number) {
  return apiClient<void>(`/categories/${categoryId}`, {
    method: "DELETE",
    token,
  });
}
