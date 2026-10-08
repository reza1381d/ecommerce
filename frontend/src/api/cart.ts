import { apiClient } from "./client";

export interface CartItem {
  id: number;
  product_id: number;
  quantity: number;
}

export interface CartResponse {
  id: number;
  user_id: number;
  items: CartItem[];
}

export interface CartItemCreateRequest {
  product_id: number;
  quantity: number;
}

export interface CartItemUpdateRequest {
  quantity: number;
}

export function getCart(token: string) {
  return apiClient<CartResponse>("/cart", { token });
}

export function addCartItem(
  token: string,
  data: CartItemCreateRequest,
) {
  return apiClient<CartItem>("/cart/items", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function updateCartItem(
  token: string,
  itemId: number,
  data: CartItemUpdateRequest,
) {
  return apiClient<CartItem>(`/cart/items/${itemId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}

export function removeCartItem(token: string, itemId: number) {
  return apiClient<void>(`/cart/items/${itemId}`, {
    method: "DELETE",
    token,
  });
}
