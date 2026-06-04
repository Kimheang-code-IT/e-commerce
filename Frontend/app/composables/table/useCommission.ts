import { ref, computed, watch } from "vue";
import type { TableColumn } from "@nuxt/ui";
import { getGroupedRowModel } from "@tanstack/vue-table";
import type { GroupingOptions } from "@tanstack/vue-table";
import type { CommissionEntry } from "~/types";
import { useCommissionApi } from "~/utils/api";
import { useServerListTable } from "~/features/shared/useServerListTable";
import { useViewFilterOptions } from "~/composables/useViewFilterOptions";

export function useCommission() {
  const { t } = useI18n();
  const perms = useModulePermissions('commission');
  const commissionApi = useCommissionApi();
  const localRows = ref<CommissionEntry[]>([]);
  const selectedProducts = ref<string[]>([]);
  const extraQuery = computed(() => ({
    product: selectedProducts.value.join(",") || undefined,
  }));
  const { sorting, columnFilters, pagination, searchQuery, resource } =
    useServerListTable<CommissionEntry>({
      resourceKey: "commission-view",
      initialSorting: [{ id: "date", desc: true }],
      localData: localRows,
      extraQuery,
      listFn: (query, signal) => commissionApi.list(query, signal),
    });

  const { itemsFor } = useViewFilterOptions(
    (query, signal) => commissionApi.filterOptions(query, signal),
    ["products"]
  );
  const productItems = itemsFor("products");

  watch(selectedProducts, () => {
    pagination.value.pageIndex = 0;
  });

  const columns = computed<TableColumn<CommissionEntry>[]>(() => [
    { id: "seller_key", accessorKey: "seller" },
    { accessorKey: "seller", header: t("pages.commission.columns.seller") },
    { accessorKey: "product", header: t("pages.commission.columns.product") },
    { accessorKey: "customer", header: t("pages.commission.columns.customer") },
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
    productItems,
    selectedProducts,
    groupingOptions,
    grouping,
    canExport: perms.canExport,
  };
}
