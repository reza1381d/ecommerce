import { API_BASE_URL, apiClient } from "./client";

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  stock: number;
  reserved_stock: number;
  available_stock: number;
  category_id: number | null;
  is_active: boolean;
  image_url: string | null;
}

export interface ProductsResponse {
  items: Product[];
  page: number;
  limit: number;
  total: number;
}

export interface GetProductsParams {
  page?: number;
  limit?: number;
  search?: string;
  categoryId?: number;
  isActive?: boolean;
  sortBy?: "id" | "name" | "price" | "created_at";
  sortOrder?: "asc" | "desc";
}

export interface ProductInput {
  name: string;
  description?: string | null;
  price: number;
  stock: number;
  category_id?: number | null;
}

export type ProductUpdate = Partial<ProductInput> & {
  is_active?: boolean;
};

export async function getProducts(
  params: GetProductsParams = {},
): Promise<ProductsResponse> {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("limit", String(params.limit ?? 20));

  const search = params.search?.trim();
  if (search) searchParams.set("search", search);
  if (params.categoryId !== undefined) {
    searchParams.set("category_id", String(params.categoryId));
  }
  if (params.isActive !== undefined) {
    searchParams.set("is_active", String(params.isActive));
  }
  if (params.sortBy) searchParams.set("sort_by", params.sortBy);
  if (params.sortOrder) searchParams.set("sort_order", params.sortOrder);

  return apiClient<ProductsResponse>(
    `/products?${searchParams.toString()}`,
  );
}

export function getProduct(productId: number) {
  return apiClient<Product>(`/products/${productId}`);
}

export function createProduct(token: string, data: ProductInput) {
  return apiClient<Product>("/products", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function updateProduct(
  token: string,
  productId: number,
  data: ProductUpdate,
) {
  return apiClient<Product>(`/products/${productId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}

export function deleteProduct(token: string, productId: number) {
  return apiClient<void>(`/products/${productId}`, {
    method: "DELETE",
    token,
  });
}


export function productImageSrc(imageUrl: string | null | undefined): string | undefined {
  if (!imageUrl) return undefined;
  return /^https?:\/\//i.test(imageUrl) ? imageUrl : `${API_BASE_URL}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
}

export function uploadProductImage(token: string, productId: number, file: File) {
  const body = new FormData();
  body.append("file", file);
  return apiClient<Product>(`/products/${productId}/image`, { method: "POST", token, body });
}

export function removeProductImage(token: string, productId: number) {
  return apiClient<Product>(`/products/${productId}/image`, { method: "DELETE", token });
}
