import { apiClient } from "./client";
import type { Order } from "./orders";
import type { Payment } from "./payments";

export interface AdminOrderCustomer {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AdminOrder extends Order {
  customer: AdminOrderCustomer;
  payment_status: string;
  latest_payment: Payment | null;
}

export interface AdminOrdersResponse {
  items: AdminOrder[];
  page: number;
  limit: number;
  total: number;
}

export interface GetAdminOrdersParams {
  page?: number;
  limit?: number;
  orderStatus?: string;
  paymentStatus?: string;
}

export function getAdminOrders(
  token: string,
  params: GetAdminOrdersParams = {},
) {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    limit: String(params.limit ?? 20),
  });

  if (params.orderStatus) query.set("order_status", params.orderStatus);
  if (params.paymentStatus) query.set("payment_status", params.paymentStatus);

  return apiClient<AdminOrdersResponse>(`/admin/orders?${query}`, { token });
}
