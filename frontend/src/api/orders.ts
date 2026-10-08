import { apiClient } from "./client";

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  unit_price: number;
  quantity: number;
  total_price: number;
}

export interface OrderAddress {
  recipient_name: string;
  phone: string;
  province: string;
  city: string;
  address_line: string;
  postal_code: string;
}

export interface Order {
  id: number;
  user_id: number;
  status: string;
  subtotal: number;
  discount_amount: number;
  shipping_amount: number;
  tax_amount: number;
  total_amount: number;
  address: OrderAddress;
  items: OrderItem[];
}

export interface OrdersResponse {
  items: Order[];
  page: number;
  limit: number;
  total: number;
}

export function checkout(token: string, addressId: number, couponCode?: string) {
  return apiClient<Order>("/orders/checkout", {
    method: "POST",
    token,
    body: JSON.stringify({ address_id: addressId, coupon_code: couponCode || null }),
  });
}

export function getOrders(
  token: string,
  page = 1,
  limit = 20,
) {
  return apiClient<OrdersResponse>(
    `/orders?page=${page}&limit=${limit}`,
    { token },
  );
}

export function getOrder(token: string, orderId: number) {
  return apiClient<Order>(`/orders/${orderId}`, { token });
}

export function cancelOrder(token: string, orderId: number) {
  return apiClient<Order>(`/orders/${orderId}/cancel`, {
    method: "POST",
    token,
  });
}
