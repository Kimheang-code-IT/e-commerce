import { ref, computed } from "vue";
import type { TableColumn } from "@nuxt/ui";
import { getGroupedRowModel } from "@tanstack/vue-table";
import type { GroupingOptions } from "@tanstack/vue-table";
import type { CommissionEntry } from "~/types";
import { useCommissionApi } from "~/utils/api";
import { useServerListTable } from "~/features/shared/useServerListTable";

export function useCommission() {
  const { t } = useI18n();
  const commissionApi = useCommissionApi();
  const localRows = ref<CommissionEntry[]>([]);
  const { sorting, columnFilters, pagination, searchQuery, resource } =
    useServerListTable<CommissionEntry>({
      resourceKey: "commission-view",
      initialSorting: [{ id: "date", desc: true }],
      localData: localRows,
      listFn: (query, signal) => commissionApi.list(query, signal),
    });

  const columns = computed<TableColumn<CommissionEntry>[]>(() => [
    { id: "seller_key", accessorKey: "seller" },
    { accessorKey: "seller", header: t("pages.commission.columns.seller") },
    { accessorKey: "product", header: t("pages.commission.columns.product") },
    { accessorKey: "customer", header: t("pages.commission.columns.customer") },
    { accessorKey: "source", header: t("pages.commission.columns.source") },
    { accessorKey: "date", header: t("pages.commission.columns.date") },
    { accessorKey: "amount", header: t("pages.commission.columns.amount") },
    {
      accessorKey: "commission",
      header: t("pages.commission.columns.commission"),
    },
  ]);

  const groupingOptions = ref<GroupingOptions>({
    groupedColumnMode: "remove",
    getGroupedRowModel: getGroupedRowModel(),
  });
  const grouping = ref<string[]>(["seller_key"]);
  return {
    data: resource.rows,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    sorting,
    searchQuery,
    columnFilters,
    pagination,
    columns,
    groupingOptions,
    grouping,
  };
}
