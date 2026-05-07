import { ref, computed, watch } from "vue";
import type { TableColumn, DropdownMenuItem } from "@nuxt/ui";
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { Category } from "~/types";
import { useCategoryApi } from '~/utils/api'
import type { ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from "~/composables/table/useServerTableResource";

export function useTotalRevenue() {
  const useBackendApi = useBackendMode();
  const categoryApi = useCategoryApi();
  const { formattedRange } = useGlobalFilter();
  const { t, toast, rowSelection, columnVisibility, isConfirmOpen } =
    useBaseTable({});

  const { sorting, columnFilters, pagination, serverQuery } = useTableQuery({
    initialSorting: [{ id: "id", desc: false }],
  });
  const searchQuery = ref("");

  // --- Data ---
  const entries = ref<Category[]>([]);

  // --- Add Form State ---
  const newName = ref("");
  const newDescription = ref("");

  // --- Confirm State ---
  const editingId = ref<string | null>(null);
  const pendingDeleteId = ref<string | null>(null);
  const confirmMode = ref<"add" | "edit" | "delete">("add");
  const pendingPayload = ref<{ id?: string; name: string; description: string } | null>(null);
  const selectedClassifications = ref<string[]>([]);

  // --- Computed ---
  const filteredEntries = computed(() => resource.rows.value);
  const categoryDateQuery = computed(() => ({
    startDate: formattedRange.value.start || "",
    endDate: formattedRange.value.end || "",
  }));
  const mergedServerQuery = computed(() => ({
    ...serverQuery.value,
    search: searchQuery.value.trim() || undefined,
    dateFrom: categoryDateQuery.value.startDate || undefined,
    dateTo: categoryDateQuery.value.endDate || undefined
  }))

  watch(searchQuery, () => {
    pagination.value.pageIndex = 0;
  });
  const resource = useServerTableResource<Category, ApiQueryParams>({
    resourceKey: 'categories',
    useBackendApi,
    serverQuery: mergedServerQuery,
    localData: entries,
    listFn: (query, signal) => categoryApi.list(query, signal),
    debounceMs: 250
  })

  // --- Columns ---
  const columns = computed<TableColumn<Category>[]>(() => [
    { accessorKey: "id", header: t("category.id") },
    { accessorKey: "name", header: t("category.name") },
    { accessorKey: "description", header: t("category.description") },
    { accessorKey: "total", header: t("category.total") },
    { accessorKey: "createdAt", header: t("category.createdAt") },
    { id: "action", header: "" },
  ]);

  // --- Row Actions ---
  function getDropdownActions(entry: Category): DropdownMenuItem[][] {
    return [
      [
        {
          label: t("actions.edit"),
          icon: "i-lucide-edit",
          onSelect: () => {
            newName.value = entry.name;
            newDescription.value = entry.description;
            editingId.value = entry.id;
          },
        },
        {
          label: t("actions.delete"),
          icon: "i-lucide-trash",
          color: "error" as const,
          onSelect: () => {
            pendingDeleteId.value = entry.id;
            confirmMode.value = "delete";
            isConfirmOpen.value = true;
          },
        },
      ],
    ];
  }

  // --- Request Intent (open confirm first) ---
  async function handleAdd() {
    const name = newName.value.trim();
    if (!name) return;

    pendingPayload.value = {
      id: editingId.value ?? undefined,
      name,
      description: newDescription.value.trim(),
    };
    confirmMode.value = editingId.value !== null ? "edit" : "add";
    isConfirmOpen.value = true;
  }

  function resetForm() {
    newName.value = "";
    newDescription.value = "";
    editingId.value = null;
    pendingPayload.value = null;
  }

  async function createCategory(payload: { name: string; description: string }) {
    await categoryApi.create(payload);
    toast.add({ title: "Category Added", color: "primary" });
  }

  async function updateCategory(id: string, payload: { name: string; description: string }) {
    await categoryApi.update(id, payload);
    toast.add({ title: "Category Updated", color: "primary" });
  }

  async function deleteCategory(id: string) {
    await categoryApi.remove(id);
    toast.add({ title: "Category Deleted", color: "error" });
  }

  // --- Finalize Confirmed Action (API-first) ---
  async function finalizeAction() {
    try {
      if (confirmMode.value === "delete" && pendingDeleteId.value !== null) {
        await deleteCategory(pendingDeleteId.value);
        pendingDeleteId.value = null;
      } else if (confirmMode.value === "edit" && pendingPayload.value?.id) {
        await updateCategory(pendingPayload.value.id, {
          name: pendingPayload.value.name,
          description: pendingPayload.value.description,
        });
        resetForm();
      } else if (confirmMode.value === "add" && pendingPayload.value) {
        await createCategory({
          name: pendingPayload.value.name,
          description: pendingPayload.value.description,
        });
        resetForm();
      }

      await resource.refresh();
    } catch (err: any) {
      console.error('Action failed:', err)
      const msg = err.data?.message || err.message || "Please try again."
      toast.add({
        title: "Request failed",
        description: msg,
        color: "error",
      });
    }

    isConfirmOpen.value = false;
  }

  const confirmConfig = computed(() => {
    if (confirmMode.value === "delete") {
      return {
        title: t("actions.delete"),
        description: "Are you sure you want to delete this category? This action is permanent.",
        type: "error" as const,
        submitLabel: t("actions.delete"),
      };
    }
    if (confirmMode.value === "edit") {
      return {
        title: t("actions.save"),
        description: `Confirm updating category "${pendingPayload.value?.name || ""}"?`,
        type: "primary" as const,
        submitLabel: t("actions.save"),
      };
    }
    return {
      title: t("actions.add"),
      description: `Confirm adding category "${pendingPayload.value?.name || ""}"?`,
      type: "primary" as const,
      submitLabel: t("actions.confirm"),
    };
  });

  return {
    // Table
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    selectedClassifications,
    // Data
    entries,
    isLoading: resource.isLoading,
    totalRows: resource.totalRows,
    filteredEntries,
    columns,
    // Add Form
    newName,
    newDescription,
    handleAdd,
    // Delete
    isConfirmOpen,
    confirmConfig,
    finalizeAction,
    // Row actions
    getDropdownActions,
  };
}
