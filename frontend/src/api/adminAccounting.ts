import { apiClient } from "./client";

export type NumericValue = number | string;
export type AnalyticsPeriod = "7d" | "30d" | "90d";
export type SalesGroupBy = "day" | "month" | "year";

export interface DashboardTrendPoint {
  date: string;
  orders: number;
  paid_orders: number;
  revenue: NumericValue;
}

export interface DashboardStats {
  period: AnalyticsPeriod;
  total_orders: number;
  pending_payment_orders: number;
  paid_orders: number;
  successful_payments: number;
  total_revenue: NumericValue;
  trend: DashboardTrendPoint[];
}

export interface ProductSalesItem {
  product_id: number;
  product_name: string;
  quantity_sold: number;
  order_count: number;
  revenue: NumericValue;
}

export interface ProductSalesResponse {
  period: AnalyticsPeriod;
  items: ProductSalesItem[];
}

export interface SalesTimelineItem {
  period: string;
  orders: number;
  units_sold: number;
  revenue: NumericValue;
}

export interface SalesTimelineResponse {
  group_by: SalesGroupBy;
  items: SalesTimelineItem[];
}

export function getDashboardStats(token: string, period: AnalyticsPeriod = "30d") {
  return apiClient<DashboardStats>(
    `/admin/dashboard/stats?period=${period}`,
    { token },
  );
}

export function getProductSales(
  token: string,
  period: AnalyticsPeriod = "30d",
  limit = 10,
) {
  const query = new URLSearchParams({ period, limit: String(limit) });
  return apiClient<ProductSalesResponse>(
    `/admin/dashboard/product-sales?${query}`,
    { token },
  );
}

export function getSalesTimeline(
  token: string,
  groupBy: SalesGroupBy,
  limit: number,
  startDate?: string,
  endDate?: string,
) {
  const query = new URLSearchParams({
    group_by: groupBy,
    limit: String(limit),
  });
  if (startDate && endDate) {
    query.set("start_date", startDate);
    query.set("end_date", endDate);
  }
  return apiClient<SalesTimelineResponse>(
    `/admin/dashboard/sales-timeline?${query}`,
    { token },
  );
}
