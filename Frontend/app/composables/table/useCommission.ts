import { ref, computed, watch } from "vue";
import type { TableColumn } from "@nuxt/ui";
import { getGroupedRowModel } from "@tanstack/vue-table";
import type { GroupingOptions } from "@tanstack/vue-table";
import type { CommissionEntry } from "~/types";
import { useCommissionApi } from "~/utils/api";
import { formatCurrency } from "~/utils/format/currency";
import { useServerListTable } from "~/features/shared/useServerListTable";
import { useViewFilterOptions } from "~/composables/useViewFilterOptions";
import { useAuthStore } from "~/stores/auth";
import { sumCommissionRows } from "~/utils/commission/aggregates";

export function useCommission() {
  const { t } = useI18n();
  const auth = useAuthStore();
  const perms = useModulePermissions('commission');
  const isAdmin = computed(() => auth.hasRole(['admin']));
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

  const commissionSummary = computed(() => sumCommissionRows(resource.rows.value));

  const columns = computed<TableColumn<CommissionEntry>[]>(() => [
    { id: "seller_key", accessorKey: "seller" },
    { accessorKey: "seller", header: t("pages.commission.columns.seller") },
    {
      accessorKey: "product",
      header: t("pages.commission.columns.product"),
      footer: t("pages.commission.footer.productCount", {
        count: commissionSummary.value.productCount,
      }),
    },
    { accessorKey: "customer", header: t("pages.commission.columns.customer") },
    { accessorKey: "date", header: t("pages.commission.columns.date") },
    {
      accessorKey: "amount",
      header: t("pages.commission.columns.amount"),
      footer: formatCurrency(commissionSummary.value.amountTotal, "USD"),
    },
    {
      accessorKey: "commission",
      header: t("pages.commission.columns.commission"),
      footer: formatCurrency(commissionSummary.value.commissionTotal, "USD"),
    },
  ]);

  const groupingOptions = ref<GroupingOptions>({
    groupedColumnMode: "remove",
    getGroupedRowModel: getGroupedRowModel(),
  });
  const grouping = ref<string[]>(isAdmin.value ? ["seller_key"] : []);
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
    isAdmin,
    canExport: perms.canExport,
  };
}
